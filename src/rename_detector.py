"""
Events Tracker - Rename Detection Module
=========================================
Created: 2025-11-07 13:11 UTC
Last Modified: 2025-11-15 18:30 UTC
Python: 3.11

Description:
Multi-signal algorithm for detecting renamed objects vs new objects.
Uses native Python instead of NumPy for broader compatibility.
Smart matching based on name similarity, hierarchy, and metadata.
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from difflib import SequenceMatcher


@dataclass
class TemplateObject:
    """Represents an object from Excel template or database"""
    row_number: int  # Excel row (or 0 for DB objects)
    name: str
    object_type: str  # 'area', 'category', 'attribute'
    parent_name: Optional[str] = None
    level: int = 1
    uuid: Optional[str] = None  # Will be None for new objects
    area_name: Optional[str] = None
    category_name: Optional[str] = None  # For attributes
    attributes: Dict[str, str] = field(default_factory=dict)
    hierarchical_path: str = ""
    
    def __post_init__(self):
        """Build hierarchical path if not provided"""
        if not self.hierarchical_path:
            parts = []
            if self.area_name:
                parts.append(self.area_name)
            if self.parent_name:
                parts.append(self.parent_name)
            if self.object_type == 'category' and self.name:
                parts.append(self.name)
            self.hierarchical_path = " > ".join(parts) if parts else self.name


@dataclass
class Match:
    """Represents a matched pair of old/new objects"""
    old_obj: TemplateObject
    new_obj: TemplateObject
    confidence: float
    match_type: str  # 'EXACT', 'RENAME', 'UPDATE'
    signals: Dict[str, float] = field(default_factory=dict)
    
    def __str__(self):
        return (f"{self.match_type}: '{self.old_obj.name}' → '{self.new_obj.name}' "
                f"(confidence: {self.confidence:.2%})")


class RenameDetector:
    """
    Detects renames vs new objects using multi-signal matching algorithm.
    Pure Python implementation (no NumPy dependency).
    """
    
    # Signal weights (must sum to 1.0)
    WEIGHT_POSITION = 0.20
    WEIGHT_NAME_SIM = 0.40
    WEIGHT_PARENT = 0.20
    WEIGHT_SIBLING = 0.10
    WEIGHT_ATTRIBUTES = 0.10
    
    def __init__(self, confidence_threshold: float = 0.65):
        self.threshold = confidence_threshold
        self.matches: List[Match] = []
        self.unmatched_old: List[TemplateObject] = []
        self.unmatched_new: List[TemplateObject] = []
        
    def match_objects(
        self,
        old_objects: List[TemplateObject],
        new_objects: List[TemplateObject]
    ) -> List[Match]:
        """Match old and new objects using hybrid algorithm"""
        
        # Phase 1: Exact UUID matches (deterministic)
        uuid_matched_old, uuid_matched_new, uuid_matches = self._match_by_uuid(
            old_objects, new_objects
        )
        
        # Phase 2: Block by area and parent to reduce comparisons
        blocks = self._create_blocks(uuid_matched_old, uuid_matched_new)
        
        # Phase 3: Within each block, use multi-signal matching
        content_matches = []
        for block_key, (block_old, block_new) in blocks.items():
            block_matches = self._match_within_block(block_old, block_new)
            content_matches.extend(block_matches)
        
        # Phase 4: Identify unmatched objects
        all_matches = uuid_matches + content_matches
        self._identify_unmatched(old_objects, new_objects, all_matches)
        
        self.matches = all_matches
        return all_matches
    
    def _match_by_uuid(
        self,
        old_objects: List[TemplateObject],
        new_objects: List[TemplateObject]
    ) -> Tuple[List[TemplateObject], List[TemplateObject], List[Match]]:
        """Phase 1: Match objects with identical UUIDs"""
        matches = []
        matched_old_ids = set()
        matched_new_ids = set()
        
        # Build UUID lookup for new objects
        new_by_uuid = {
            obj.uuid: obj for obj in new_objects 
            if obj.uuid is not None and obj.uuid.strip()
        }
        
        for old_obj in old_objects:
            if old_obj.uuid and old_obj.uuid in new_by_uuid:
                new_obj = new_by_uuid[old_obj.uuid]
                
                # Determine match type
                if old_obj.name == new_obj.name:
                    match_type = 'EXACT'
                else:
                    match_type = 'RENAME'
                
                matches.append(Match(
                    old_obj=old_obj,
                    new_obj=new_obj,
                    confidence=1.0,
                    match_type=match_type,
                    signals={'uuid': 1.0}
                ))
                
                matched_old_ids.add(id(old_obj))
                matched_new_ids.add(id(new_obj))
        
        # Return unmatched objects for next phase
        unmatched_old = [obj for obj in old_objects if id(obj) not in matched_old_ids]
        unmatched_new = [obj for obj in new_objects if id(obj) not in matched_new_ids]
        
        return unmatched_old, unmatched_new, matches
    
    def _create_blocks(
        self,
        old_objects: List[TemplateObject],
        new_objects: List[TemplateObject]
    ) -> Dict[str, Tuple[List[TemplateObject], List[TemplateObject]]]:
        """Phase 2: Group objects by area/parent/type"""
        blocks: Dict[str, Tuple[List, List]] = {}
        
        def get_block_key(obj: TemplateObject) -> str:
            parts = [obj.object_type]
            if obj.area_name:
                parts.append(f"area:{obj.area_name}")
            if obj.parent_name:
                parts.append(f"parent:{obj.parent_name}")
            else:
                parts.append("parent:ROOT")
            parts.append(f"level:{obj.level}")
            return "|".join(parts)
        
        # Group old objects
        for obj in old_objects:
            key = get_block_key(obj)
            if key not in blocks:
                blocks[key] = ([], [])
            blocks[key][0].append(obj)
        
        # Group new objects
        for obj in new_objects:
            key = get_block_key(obj)
            if key not in blocks:
                blocks[key] = ([], [])
            blocks[key][1].append(obj)
        
        return blocks
    
    def _match_within_block(
        self,
        old_objects: List[TemplateObject],
        new_objects: List[TemplateObject]
    ) -> List[Match]:
        """Phase 3: Match objects within same block"""
        if not old_objects or not new_objects:
            return []
        
        # Calculate similarity matrix (using native Python lists)
        n_old = len(old_objects)
        n_new = len(new_objects)
        similarity_matrix = [[0.0 for _ in range(n_new)] for _ in range(n_old)]
        signals_matrix = [[{} for _ in range(n_new)] for _ in range(n_old)]
        
        for i, old_obj in enumerate(old_objects):
            for j, new_obj in enumerate(new_objects):
                score, signals = self._calculate_similarity(old_obj, new_obj)
                similarity_matrix[i][j] = score
                signals_matrix[i][j] = signals
        
        # Find best matches using greedy algorithm
        matches = []
        matched_old = set()
        matched_new = set()
        
        # Sort by confidence (highest first)
        candidates = []
        for i in range(n_old):
            for j in range(n_new):
                if similarity_matrix[i][j] >= self.threshold:
                    candidates.append((similarity_matrix[i][j], i, j))
        
        candidates.sort(reverse=True)
        
        # Greedy matching (one-to-one constraint)
        for score, i, j in candidates:
            if i not in matched_old and j not in matched_new:
                old_obj = old_objects[i]
                new_obj = new_objects[j]
                signals = signals_matrix[i][j]
                
                match_type = 'RENAME' if old_obj.name != new_obj.name else 'UPDATE'
                
                matches.append(Match(
                    old_obj=old_obj,
                    new_obj=new_obj,
                    confidence=score,
                    match_type=match_type,
                    signals=signals
                ))
                
                matched_old.add(i)
                matched_new.add(j)
        
        return matches
    
    def _calculate_similarity(
        self,
        old_obj: TemplateObject,
        new_obj: TemplateObject
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate similarity score using weighted signals"""
        signals = {}
        
        # Signal 1: Position similarity
        if old_obj.row_number > 0 and new_obj.row_number > 0:
            position_score = 1.0 if old_obj.row_number == new_obj.row_number else 0.0
        else:
            position_score = 0.5
        signals['position'] = position_score
        
        # Signal 2: Name similarity (Levenshtein-based)
        name_sim = SequenceMatcher(
            None, 
            old_obj.name.lower(), 
            new_obj.name.lower()
        ).ratio()
        signals['name'] = name_sim
        
        # Signal 3: Parent match
        if old_obj.parent_name == new_obj.parent_name:
            parent_score = 1.0
        elif old_obj.parent_name is None and new_obj.parent_name is None:
            parent_score = 1.0
        else:
            parent_score = 0.0
        signals['parent'] = parent_score
        
        # Signal 4: Sibling context (simplified)
        sibling_score = parent_score
        signals['sibling'] = sibling_score
        
        # Signal 5: Attributes similarity
        attr_score = self._compare_attributes(old_obj, new_obj)
        signals['attributes'] = attr_score
        
        # Weighted sum
        total_score = (
            self.WEIGHT_POSITION * position_score +
            self.WEIGHT_NAME_SIM * name_sim +
            self.WEIGHT_PARENT * parent_score +
            self.WEIGHT_SIBLING * sibling_score +
            self.WEIGHT_ATTRIBUTES * attr_score
        )
        
        return total_score, signals
    
    def _compare_attributes(
        self, 
        obj1: TemplateObject, 
        obj2: TemplateObject
    ) -> float:
        """Compare other attributes for similarity"""
        if not obj1.attributes or not obj2.attributes:
            return 0.5
        
        common_keys = set(obj1.attributes.keys()) & set(obj2.attributes.keys())
        if not common_keys:
            return 0.5
        
        matches = sum(
            1 for key in common_keys 
            if obj1.attributes.get(key) == obj2.attributes.get(key)
        )
        
        return matches / len(common_keys)
    
    def _identify_unmatched(
        self,
        old_objects: List[TemplateObject],
        new_objects: List[TemplateObject],
        matches: List[Match]
    ):
        """Phase 4: Identify objects that weren't matched"""
        matched_old_ids = {id(m.old_obj) for m in matches}
        matched_new_ids = {id(m.new_obj) for m in matches}
        
        self.unmatched_old = [
            obj for obj in old_objects 
            if id(obj) not in matched_old_ids
        ]
        
        self.unmatched_new = [
            obj for obj in new_objects 
            if id(obj) not in matched_new_ids
        ]
    
    def generate_operations(self) -> List[Dict]:
        """Generate database operations from matches"""
        operations = []
        
        # Process matches
        for match in self.matches:
            if match.match_type == 'RENAME':
                operations.append({
                    'operation': 'UPDATE',
                    'table_name': self._get_table_name(match.old_obj.object_type),
                    'id': match.old_obj.uuid,
                    'new_name': match.new_obj.name,
                    'old_name': match.old_obj.name,
                    'confidence': match.confidence,
                    'signals': match.signals
                })
            elif match.match_type == 'UPDATE':
                changes = self._detect_attribute_changes(
                    match.old_obj, match.new_obj
                )
                if changes:
                    operations.append({
                        'operation': 'UPDATE',
                        'table_name': self._get_table_name(match.old_obj.object_type),
                        'id': match.old_obj.uuid,
                        'changes': changes
                    })
        
        # Process unmatched old (deletions)
        for obj in self.unmatched_old:
            operations.append({
                'operation': 'DELETE',
                'table_name': self._get_table_name(obj.object_type),
                'id': obj.uuid,
                'name': obj.name,
                'requires_confirmation': True
            })
        
        # Process unmatched new (insertions)
        for obj in self.unmatched_new:
            operation = {
                'operation': 'INSERT',
                'table_name': self._get_table_name(obj.object_type),
                'name': obj.name,
                'sort_order': int(obj.attributes.get('sort_order', 0))
            }
            
            # Add type-specific fields
            if obj.object_type == 'area':
                operation.update({
                    'icon': obj.attributes.get('icon', ''),
                    'color': obj.attributes.get('color', ''),
                    'description': obj.attributes.get('description', '')
                })
            elif obj.object_type == 'category':
                operation.update({
                    'area_name': obj.area_name,
                    'parent_name': obj.parent_name,
                    'description': obj.attributes.get('description', '')
                })
            elif obj.object_type == 'attribute':
                operation.update({
                    'category_name': obj.category_name,
                    'data_type': obj.attributes.get('data_type', 'text'),
                    'unit': obj.attributes.get('unit', ''),
                    'is_required': obj.attributes.get('is_required', False),
                    'default_value': obj.attributes.get('default_value', ''),
                    'validation_rules': obj.attributes.get('validation_rules', '{}')
                })
            
            operations.append(operation)
        
        return operations
    
    def _get_table_name(self, object_type: str) -> str:
        """Map object type to database table name"""
        mapping = {
            'area': 'areas',
            'category': 'categories',
            'attribute': 'attribute_definitions'
        }
        return mapping.get(object_type, object_type)
    
    def _detect_attribute_changes(
        self, 
        old_obj: TemplateObject, 
        new_obj: TemplateObject
    ) -> Dict[str, Tuple[str, str]]:
        """Detect which attributes changed (excluding name)"""
        changes = {}
        all_keys = set(old_obj.attributes.keys()) | set(new_obj.attributes.keys())
        
        for key in all_keys:
            old_val = old_obj.attributes.get(key)
            new_val = new_obj.attributes.get(key)
            if old_val != new_val:
                changes[key] = (old_val, new_val)
        
        return changes
    
    def get_summary(self) -> Dict:
        """Get summary statistics of matching results"""
        avg_confidence = (
            sum(m.confidence for m in self.matches) / len(self.matches)
            if self.matches else 0.0
        )
        
        return {
            'total_matches': len(self.matches),
            'exact_matches': sum(1 for m in self.matches if m.match_type == 'EXACT'),
            'renames': sum(1 for m in self.matches if m.match_type == 'RENAME'),
            'updates': sum(1 for m in self.matches if m.match_type == 'UPDATE'),
            'insertions': len(self.unmatched_new),
            'deletions': len(self.unmatched_old),
            'avg_confidence': avg_confidence
        }
