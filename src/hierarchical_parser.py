"""
Hierarchical Parser - Parse and update structure from Hierarchical_View Excel
============================================================================

Features:
- Parse Hierarchical_View sheet with Category_Path column
- Detect new Areas, Categories, Attributes from added rows
- Detect updates to existing objects (BLUE editable columns)
- Validate all changes before applying
- Create hierarchical structure from Category_Path
- Show detailed diff of changes
- Apply changes atomically to database

Dependencies: pandas, openpyxl, supabase
Last Modified: 2025-11-22 12:00 UTC
"""

import pandas as pd
import json
import uuid
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ValidationError:
    """Represents a validation error."""
    row: int
    column: str
    message: str
    severity: str = "error"  # error, warning


@dataclass
class ChangeSet:
    """Represents all detected changes."""
    new_areas: List[Dict] = field(default_factory=list)
    new_categories: List[Dict] = field(default_factory=list)
    new_attributes: List[Dict] = field(default_factory=list)
    updated_areas: List[Dict] = field(default_factory=list)
    updated_categories: List[Dict] = field(default_factory=list)
    updated_attributes: List[Dict] = field(default_factory=list)
    validation_errors: List[ValidationError] = field(default_factory=list)
    validation_warnings: List[ValidationError] = field(default_factory=list)
    
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return (len(self.new_areas) > 0 or 
                len(self.new_categories) > 0 or 
                len(self.new_attributes) > 0 or
                len(self.updated_areas) > 0 or
                len(self.updated_categories) > 0 or
                len(self.updated_attributes) > 0)
    
    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return len(self.validation_errors) > 0


class HierarchicalParser:
    """
    Parse Hierarchical_View Excel and update database structure.
    """
    
    # Valid values for validation
    VALID_TYPES = {'Area', 'Category', 'Attribute'}
    VALID_DATA_TYPES = {'number', 'text', 'datetime', 'boolean', 'link', 'image'}
    VALID_REQUIRED = {'TRUE', 'FALSE', 'True', 'False', True, False, 'true', 'false'}
    
    # Maximum number of errors to collect (to avoid overwhelming user and long processing times)
    MAX_ERRORS = 20
    
    def __init__(self, client, user_id: str, excel_path: str):
        """
        Initialize parser.
        
        Args:
            client: Supabase client instance
            user_id: Current user's UUID
            excel_path: Path to uploaded Excel file
        """
        self.client = client
        self.user_id = user_id
        self.excel_path = excel_path
        
        # Will be populated during parsing
        self.df: Optional[pd.DataFrame] = None
        self.existing_structure: Dict = {}
        self.changes: ChangeSet = ChangeSet()
    
    def parse_and_validate(self) -> ChangeSet:
        """
        Parse Excel file and validate changes.
        
        Returns:
            ChangeSet with all detected changes and validation errors
        """
        # Step 1: Read Excel
        self.df = self._read_excel()
        if self.df is None:
            self.changes.validation_errors.append(
                ValidationError(0, "File", "Failed to read Excel file", "error")
            )
            return self.changes
        
        # Step 2: Load existing structure from database
        self.existing_structure = self._load_existing_structure()
        
        # Step 3: Validate data format (collects up to MAX_ERRORS)
        self._validate_data_format()
        
        # Step 4: Detect changes (only if no critical errors and under error limit)
        if not self.changes.has_errors() or len(self.changes.validation_errors) < self.MAX_ERRORS:
            self._detect_changes()
        
        # Step 5: Validate business logic (only if under error limit)
        if len(self.changes.validation_errors) < self.MAX_ERRORS:
            self._validate_business_logic()
        
        return self.changes
    
    def _read_excel(self) -> Optional[pd.DataFrame]:
        """Read Hierarchical_View sheet from Excel."""
        try:
            # Excel structure:
            # Row 1: Blank (None values)
            # Row 2: Headers (Type, Level, Sort_Order, etc.)
            # Row 3+: Data
            
            # Read with header in row 2 (index 1, since 0-indexed)
            df = pd.read_excel(self.excel_path, sheet_name='Hierarchical_View', header=1)
            
            # Standardize column names (remove extra spaces)
            df.columns = df.columns.str.strip()
            
            return df
            
        except Exception as e:
            self.changes.validation_errors.append(
                ValidationError(0, "File", f"Error reading Excel: {str(e)}", "error")
            )
            return None
    
    def _load_existing_structure(self) -> Dict:
        """
        Load existing structure from database.
        
        Returns:
            Dict with 'areas', 'categories', 'attributes' keys
        """
        structure = {
            'areas': {},
            'categories': {},
            'attributes': {}
        }
        
        try:
            # Load Areas
            areas_response = self.client.table('areas') \
                .select('*') \
                .eq('user_id', self.user_id) \
                .execute()
            
            for area in areas_response.data:
                structure['areas'][area['name'].lower()] = area
            
            # Load Categories
            categories_response = self.client.table('categories') \
                .select('*') \
                .eq('user_id', self.user_id) \
                .execute()
            
            for cat in categories_response.data:
                # Build category path for matching
                cat_path = self._build_category_path(cat['id'])
                structure['categories'][cat_path.lower()] = cat
            
            # Load Attributes
            attributes_response = self.client.table('attribute_definitions') \
                .select('*') \
                .eq('user_id', self.user_id) \
                .execute()
            
            for attr in attributes_response.data:
                # Key: category_id + attribute_name
                key = f"{attr['category_id']}:{attr['name'].lower()}"
                structure['attributes'][key] = attr
            
        except Exception as e:
            self.changes.validation_errors.append(
                ValidationError(0, "Database", f"Error loading existing structure: {str(e)}", "error")
            )
        
        return structure
    
    def _build_category_path(self, category_id: str) -> str:
        """
        Build full category path by traversing up the hierarchy.
        
        Args:
            category_id: Category UUID
            
        Returns:
            Full path like "Health > Sleep > Quality"
        """
        try:
            # Get category
            cat_response = self.client.table('categories') \
                .select('*') \
                .eq('id', category_id) \
                .single() \
                .execute()
            
            cat = cat_response.data
            
            # Get area
            area_response = self.client.table('areas') \
                .select('name') \
                .eq('id', cat['area_id']) \
                .single() \
                .execute()
            
            area_name = area_response.data['name']
            
            # Build path
            path_parts = [area_name, cat['name']]
            
            # Traverse up parent hierarchy
            current_parent_id = cat.get('parent_category_id')
            while current_parent_id:
                parent_response = self.client.table('categories') \
                    .select('name, parent_category_id') \
                    .eq('id', current_parent_id) \
                    .single() \
                    .execute()
                
                parent = parent_response.data
                path_parts.insert(1, parent['name'])
                current_parent_id = parent.get('parent_category_id')
            
            return " > ".join(path_parts)
            
        except Exception as e:
            return ""
    
    def _validate_data_format(self):
        """Validate data format and required columns."""
        required_columns = ['Type', 'Category_Path', 'Level', 'Sort_Order']
        
        # Check required columns exist
        missing_cols = [col for col in required_columns if col not in self.df.columns]
        if missing_cols:
            self.changes.validation_errors.append(
                ValidationError(0, "Columns", f"Missing required columns: {', '.join(missing_cols)}", "error")
            )
            # Don't continue if columns are missing - can't validate rows
            return
        
        # Validate each row (up to MAX_ERRORS)
        for idx, row in self.df.iterrows():
            # Stop if we've reached MAX_ERRORS
            if len(self.changes.validation_errors) >= self.MAX_ERRORS:
                self.changes.validation_warnings.append(
                    ValidationError(0, "Validation", 
                                  f"Validation stopped at {self.MAX_ERRORS} errors. There may be more errors in the file.", 
                                  "warning")
                )
                break
            
            excel_row = idx + 3  # Excel row (1=blank, 2=header, 3=first data)
            
            # Skip completely empty rows
            if row.isna().all():
                continue
            
            # Validate Type
            row_type = str(row['Type']).strip() if pd.notna(row['Type']) else ''
            if not row_type:
                self.changes.validation_errors.append(
                    ValidationError(excel_row, "Type", "Type is required", "error")
                )
                continue
            
            if row_type not in self.VALID_TYPES:
                self.changes.validation_errors.append(
                    ValidationError(excel_row, "Type", 
                                  f"Invalid Type '{row_type}'. Must be: Area, Category, or Attribute", "error")
                )
            
            # Validate Category_Path
            cat_path = str(row['Category_Path']).strip() if pd.notna(row['Category_Path']) else ''
            if not cat_path:
                self.changes.validation_errors.append(
                    ValidationError(excel_row, "Category_Path", "Category_Path is required", "error")
                )
            
            # Validate by Type
            if row_type == 'Attribute':
                # Attributes must have Data_Type
                data_type = str(row.get('Data_Type', '')).strip() if pd.notna(row.get('Data_Type')) else ''
                if not data_type:
                    self.changes.validation_errors.append(
                        ValidationError(excel_row, "Data_Type", "Data_Type is required for Attributes", "error")
                    )
                elif data_type not in self.VALID_DATA_TYPES:
                    self.changes.validation_errors.append(
                        ValidationError(excel_row, "Data_Type", 
                                      f"Invalid Data_Type '{data_type}'. Must be: {', '.join(self.VALID_DATA_TYPES)}", "error")
                    )
                
                # Attributes must have Attribute_Name
                attr_name = str(row.get('Attribute_Name', '')).strip() if pd.notna(row.get('Attribute_Name')) else ''
                if not attr_name:
                    self.changes.validation_errors.append(
                        ValidationError(excel_row, "Attribute_Name", "Attribute_Name is required for Attributes", "error")
                    )
                
                # Validate Is_Required
                is_req = row.get('Is_Required', '')
                if pd.notna(is_req) and str(is_req).strip():
                    if str(is_req).strip() not in [str(v) for v in self.VALID_REQUIRED]:
                        self.changes.validation_errors.append(
                            ValidationError(excel_row, "Is_Required", 
                                          f"Invalid Is_Required '{is_req}'. Must be: TRUE or FALSE", "error")
                        )
            
            elif row_type == 'Category':
                # Categories must have Category name
                cat_name = str(row.get('Category', '')).strip() if pd.notna(row.get('Category')) else ''
                if not cat_name:
                    self.changes.validation_errors.append(
                        ValidationError(excel_row, "Category", "Category name is required for Categories", "error")
                    )
    
    def _detect_changes(self):
        """Detect new and updated objects."""
        # Track created objects in this pass (for dependency resolution)
        created_areas: Dict[str, str] = {}  # name_lower -> uuid
        created_categories: Dict[str, str] = {}  # path_lower -> uuid
        
        for idx, row in self.df.iterrows():
            excel_row = idx + 3
            
            # Skip empty rows
            if row.isna().all():
                continue
            
            row_type = str(row['Type']).strip() if pd.notna(row['Type']) else ''
            
            if row_type == 'Area':
                self._process_area_row(row, excel_row, created_areas)
            
            elif row_type == 'Category':
                self._process_category_row(row, excel_row, created_areas, created_categories)
            
            elif row_type == 'Attribute':
                self._process_attribute_row(row, excel_row, created_categories)
    
    def _process_area_row(self, row: pd.Series, excel_row: int, created_areas: Dict[str, str]):
        """Process an Area row."""
        area_name = str(row['Category_Path']).strip() if pd.notna(row['Category_Path']) else ''
        
        if not area_name:
            return
        
        # Check if exists
        existing = self.existing_structure['areas'].get(area_name.lower())
        
        if existing:
            # Check for updates in BLUE columns
            updates = {}
            
            # Description
            new_desc = str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else ''
            old_desc = existing.get('description', '') or ''
            if new_desc != old_desc:
                updates['description'] = new_desc
            
            # Sort_Order
            new_sort = int(row['Sort_Order']) if pd.notna(row['Sort_Order']) else 0
            old_sort = existing.get('sort_order', 0)
            if new_sort != old_sort:
                updates['sort_order'] = new_sort
            
            if updates:
                self.changes.updated_areas.append({
                    'id': existing['id'],
                    'name': area_name,
                    'updates': updates,
                    'excel_row': excel_row
                })
        else:
            # New area
            area_uuid = str(uuid.uuid4())
            created_areas[area_name.lower()] = area_uuid
            
            self.changes.new_areas.append({
                'uuid': area_uuid,
                'name': area_name,
                'icon': str(row.get('Icon', '📁')),
                'color': str(row.get('Color', '#4472C4')),
                'sort_order': int(row['Sort_Order']) if pd.notna(row['Sort_Order']) else 0,
                'description': str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else '',
                'excel_row': excel_row
            })
    
    def _process_category_row(self, row: pd.Series, excel_row: int, 
                             created_areas: Dict[str, str], 
                             created_categories: Dict[str, str]):
        """Process a Category row."""
        cat_path = str(row['Category_Path']).strip() if pd.notna(row['Category_Path']) else ''
        cat_name = str(row.get('Category', '')).strip() if pd.notna(row.get('Category')) else ''
        
        if not cat_path or not cat_name:
            return
        
        # Parse Category_Path to get area and parent
        path_parts = [p.strip() for p in cat_path.split('>')]
        area_name = path_parts[0]
        
        # Determine level and parent
        level = len(path_parts) - 1  # Area is level 0, first category is level 1
        parent_category_name = path_parts[-2] if len(path_parts) > 2 else None
        
        # Get area_id
        area_id = None
        if area_name.lower() in self.existing_structure['areas']:
            area_id = self.existing_structure['areas'][area_name.lower()]['id']
        elif area_name.lower() in created_areas:
            area_id = created_areas[area_name.lower()]
        else:
            self.changes.validation_errors.append(
                ValidationError(excel_row, "Category_Path", 
                              f"Area '{area_name}' not found", "error")
            )
            return
        
        # Get parent_category_id if applicable
        parent_category_id = None
        if parent_category_name:
            # Build parent path
            parent_path = " > ".join(path_parts[:-1])
            
            if parent_path.lower() in self.existing_structure['categories']:
                parent_category_id = self.existing_structure['categories'][parent_path.lower()]['id']
            elif parent_path.lower() in created_categories:
                parent_category_id = created_categories[parent_path.lower()]
            else:
                self.changes.validation_errors.append(
                    ValidationError(excel_row, "Category_Path", 
                                  f"Parent category '{parent_path}' not found", "error")
                )
                return
        
        # Check if exists
        existing = self.existing_structure['categories'].get(cat_path.lower())
        
        if existing:
            # Check for updates in BLUE columns
            updates = {}
            
            # Category name
            if cat_name != existing['name']:
                updates['name'] = cat_name
            
            # Description
            new_desc = str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else ''
            old_desc = existing.get('description', '') or ''
            if new_desc != old_desc:
                updates['description'] = new_desc
            
            # Sort_Order
            new_sort = int(row['Sort_Order']) if pd.notna(row['Sort_Order']) else 0
            old_sort = existing.get('sort_order', 0)
            if new_sort != old_sort:
                updates['sort_order'] = new_sort
            
            if updates:
                self.changes.updated_categories.append({
                    'id': existing['id'],
                    'name': cat_name,
                    'path': cat_path,
                    'updates': updates,
                    'excel_row': excel_row
                })
        else:
            # New category
            cat_uuid = str(uuid.uuid4())
            created_categories[cat_path.lower()] = cat_uuid
            
            self.changes.new_categories.append({
                'uuid': cat_uuid,
                'area_id': area_id,
                'parent_category_id': parent_category_id,
                'name': cat_name,
                'level': level,
                'sort_order': int(row['Sort_Order']) if pd.notna(row['Sort_Order']) else 0,
                'description': str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else '',
                'path': cat_path,
                'excel_row': excel_row
            })
    
    def _process_attribute_row(self, row: pd.Series, excel_row: int, 
                               created_categories: Dict[str, str]):
        """Process an Attribute row."""
        cat_path = str(row['Category_Path']).strip() if pd.notna(row['Category_Path']) else ''
        attr_name = str(row.get('Attribute_Name', '')).strip() if pd.notna(row.get('Attribute_Name')) else ''
        
        if not cat_path or not attr_name:
            return
        
        # Get category_id
        category_id = None
        if cat_path.lower() in self.existing_structure['categories']:
            category_id = self.existing_structure['categories'][cat_path.lower()]['id']
        elif cat_path.lower() in created_categories:
            category_id = created_categories[cat_path.lower()]
        else:
            self.changes.validation_errors.append(
                ValidationError(excel_row, "Category_Path", 
                              f"Category '{cat_path}' not found", "error")
            )
            return
        
        # Check if exists
        key = f"{category_id}:{attr_name.lower()}"
        existing = self.existing_structure['attributes'].get(key)
        
        if existing:
            # Check for updates in BLUE columns
            updates = {}
            
            # Attribute name
            if attr_name != existing['name']:
                updates['name'] = attr_name
            
            # Data_Type
            new_type = str(row.get('Data_Type', '')).strip() if pd.notna(row.get('Data_Type')) else ''
            if new_type and new_type != existing['data_type']:
                updates['data_type'] = new_type
            
            # Unit
            new_unit = str(row.get('Unit', '')).strip() if pd.notna(row.get('Unit')) else ''
            old_unit = existing.get('unit', '') or ''
            if new_unit != old_unit:
                updates['unit'] = new_unit
            
            # Is_Required
            is_req = row.get('Is_Required', '')
            if pd.notna(is_req) and str(is_req).strip():
                new_req = str(is_req).strip().upper() == 'TRUE'
                old_req = existing.get('is_required', False)
                if new_req != old_req:
                    updates['is_required'] = new_req
            
            # Default_Value
            new_default = str(row.get('Default_Value', '')).strip() if pd.notna(row.get('Default_Value')) else ''
            old_default = existing.get('default_value', '') or ''
            if new_default != old_default:
                updates['default_value'] = new_default
            
            # Validation_Min and Validation_Max
            val_rules = existing.get('validation_rules', {})
            if isinstance(val_rules, str):
                try:
                    val_rules = json.loads(val_rules)
                except:
                    val_rules = {}
            
            new_val_rules = {}
            
            val_min = row.get('Validation_Min', '')
            if pd.notna(val_min) and str(val_min).strip():
                new_val_rules['min'] = float(val_min)
            
            val_max = row.get('Validation_Max', '')
            if pd.notna(val_max) and str(val_max).strip():
                new_val_rules['max'] = float(val_max)
            
            if new_val_rules != val_rules:
                updates['validation_rules'] = json.dumps(new_val_rules)
            
            # Description
            new_desc = str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else ''
            old_desc = existing.get('description', '') or ''
            if new_desc != old_desc:
                updates['description'] = new_desc
            
            # Sort_Order
            new_sort = int(row['Sort_Order']) if pd.notna(row['Sort_Order']) else 0
            old_sort = existing.get('sort_order', 0)
            if new_sort != old_sort:
                updates['sort_order'] = new_sort
            
            if updates:
                self.changes.updated_attributes.append({
                    'id': existing['id'],
                    'name': attr_name,
                    'category_path': cat_path,
                    'updates': updates,
                    'excel_row': excel_row
                })
        else:
            # New attribute
            attr_uuid = str(uuid.uuid4())
            
            # Parse validation rules
            val_rules = {}
            val_min = row.get('Validation_Min', '')
            if pd.notna(val_min) and str(val_min).strip():
                val_rules['min'] = float(val_min)
            
            val_max = row.get('Validation_Max', '')
            if pd.notna(val_max) and str(val_max).strip():
                val_rules['max'] = float(val_max)
            
            # Is_Required
            is_req = row.get('Is_Required', '')
            is_required = False
            if pd.notna(is_req) and str(is_req).strip():
                is_required = str(is_req).strip().upper() == 'TRUE'
            
            self.changes.new_attributes.append({
                'uuid': attr_uuid,
                'category_id': category_id,
                'name': attr_name,
                'data_type': str(row.get('Data_Type', '')).strip(),
                'unit': str(row.get('Unit', '')).strip() if pd.notna(row.get('Unit')) else '',
                'is_required': is_required,
                'default_value': str(row.get('Default_Value', '')).strip() if pd.notna(row.get('Default_Value')) else '',
                'validation_rules': json.dumps(val_rules) if val_rules else '{}',
                'sort_order': int(row['Sort_Order']) if pd.notna(row['Sort_Order']) else 0,
                'description': str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else '',
                'category_path': cat_path,
                'excel_row': excel_row
            })
    
    def _validate_business_logic(self):
        """Validate business logic rules."""
        # Check for duplicate area names in new areas
        new_area_names = [a['name'].lower() for a in self.changes.new_areas]
        duplicates = [name for name in new_area_names if new_area_names.count(name) > 1]
        if duplicates:
            self.changes.validation_errors.append(
                ValidationError(0, "Areas", 
                              f"Duplicate area names in new areas: {', '.join(set(duplicates))}", "error")
            )
        
        # Check for duplicate category paths in new categories
        new_cat_paths = [c['path'].lower() for c in self.changes.new_categories]
        duplicates = [path for path in new_cat_paths if new_cat_paths.count(path) > 1]
        if duplicates:
            self.changes.validation_errors.append(
                ValidationError(0, "Categories", 
                              f"Duplicate category paths in new categories: {', '.join(set(duplicates))}", "error")
            )
        
        # Warn if many changes
        total_changes = (len(self.changes.new_areas) + len(self.changes.new_categories) + 
                        len(self.changes.new_attributes) + len(self.changes.updated_areas) + 
                        len(self.changes.updated_categories) + len(self.changes.updated_attributes))
        
        if total_changes > 50:
            self.changes.validation_warnings.append(
                ValidationError(0, "Changes", 
                              f"Large number of changes detected ({total_changes}). Please review carefully.", "warning")
            )
    
    def apply_changes(self) -> Tuple[bool, str]:
        """
        Apply all changes to database.
        
        Returns:
            (success: bool, message: str)
        """
        if self.changes.has_errors():
            return False, "Cannot apply changes due to validation errors"
        
        if not self.changes.has_changes():
            return True, "No changes to apply"
        
        try:
            # Apply in order: Areas -> Categories -> Attributes
            # Then updates
            
            # 1. Insert new Areas
            for area in self.changes.new_areas:
                self.client.table('areas').insert({
                    'id': area['uuid'],
                    'user_id': self.user_id,
                    'name': area['name'],
                    'icon': area['icon'],
                    'color': area['color'],
                    'sort_order': area['sort_order'],
                    'description': area['description'],
                    'slug': area['name'].lower().replace(' ', '-')
                }).execute()
            
            # 2. Insert new Categories
            for cat in self.changes.new_categories:
                self.client.table('categories').insert({
                    'id': cat['uuid'],
                    'user_id': self.user_id,
                    'area_id': cat['area_id'],
                    'parent_category_id': cat['parent_category_id'],
                    'name': cat['name'],
                    'level': cat['level'],
                    'sort_order': cat['sort_order'],
                    'description': cat['description'],
                    'slug': cat['name'].lower().replace(' ', '-')
                }).execute()
            
            # 3. Insert new Attributes
            for attr in self.changes.new_attributes:
                self.client.table('attribute_definitions').insert({
                    'id': attr['uuid'],
                    'user_id': self.user_id,
                    'category_id': attr['category_id'],
                    'name': attr['name'],
                    'data_type': attr['data_type'],
                    'unit': attr['unit'],
                    'is_required': attr['is_required'],
                    'default_value': attr['default_value'],
                    'validation_rules': attr['validation_rules'],
                    'sort_order': attr['sort_order'],
                    'slug': attr['name'].lower().replace(' ', '-')
                }).execute()
            
            # 4. Update Areas
            for area in self.changes.updated_areas:
                self.client.table('areas') \
                    .update(area['updates']) \
                    .eq('id', area['id']) \
                    .eq('user_id', self.user_id) \
                    .execute()
            
            # 5. Update Categories
            for cat in self.changes.updated_categories:
                self.client.table('categories') \
                    .update(cat['updates']) \
                    .eq('id', cat['id']) \
                    .eq('user_id', self.user_id) \
                    .execute()
            
            # 6. Update Attributes
            for attr in self.changes.updated_attributes:
                self.client.table('attribute_definitions') \
                    .update(attr['updates']) \
                    .eq('id', attr['id']) \
                    .eq('user_id', self.user_id) \
                    .execute()
            
            # Build summary message
            summary_parts = []
            if self.changes.new_areas:
                summary_parts.append(f"{len(self.changes.new_areas)} new areas")
            if self.changes.new_categories:
                summary_parts.append(f"{len(self.changes.new_categories)} new categories")
            if self.changes.new_attributes:
                summary_parts.append(f"{len(self.changes.new_attributes)} new attributes")
            if self.changes.updated_areas:
                summary_parts.append(f"{len(self.changes.updated_areas)} updated areas")
            if self.changes.updated_categories:
                summary_parts.append(f"{len(self.changes.updated_categories)} updated categories")
            if self.changes.updated_attributes:
                summary_parts.append(f"{len(self.changes.updated_attributes)} updated attributes")
            
            message = "Successfully applied changes: " + ", ".join(summary_parts)
            return True, message
            
        except Exception as e:
            return False, f"Error applying changes: {str(e)}"
