"""Hierarchical Parser v5 - WITH DEPENDENCIES SUPPORT

CHANGES FROM V4 (2026-01-30):
- Added support for DependsOn column (P) - references parent attribute slug
- Added support for WhenValue column (Q) - specifies condition for options
- Multiple rows for same attribute are merged into options_map
- Renamed ValidationMin to TextOptions for clarity (backward compatible)
- Generates depends_on.options_map in validation_rules JSON

Column mapping:
A Type, B Level, C SortOrder, D Area, E CategoryPath, F Category, G AttributeName,
H DataType, I Unit, J IsRequired, K ValidationType, L DefaultValue, M TextOptions,
N ValidationMax, O Description, P DependsOn, Q WhenValue
"""

import pandas as pd
import json
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ValidationError:
    row: int
    column: str
    message: str
    severity: str = 'error'


@dataclass
class ChangeSet:
    new_areas: List[Dict] = field(default_factory=list)
    new_categories: List[Dict] = field(default_factory=list)
    new_attributes: List[Dict] = field(default_factory=list)
    updated_areas: List[Dict] = field(default_factory=list)
    updated_categories: List[Dict] = field(default_factory=list)
    updated_attributes: List[Dict] = field(default_factory=list)
    validation_errors: List[ValidationError] = field(default_factory=list)
    validation_warnings: List[ValidationError] = field(default_factory=list)

    def has_changes(self) -> bool:
        return any([self.new_areas, self.new_categories, self.new_attributes, 
                    self.updated_areas, self.updated_categories, self.updated_attributes])

    def has_errors(self) -> bool:
        return len(self.validation_errors) > 0


class HierarchicalParser:
    VALIDTYPES = {'Area', 'Category', 'Attribute'}
    VALIDDATATYPES = {'number', 'text', 'datetime', 'boolean', 'link', 'image'}
    VALIDREQUIRED = {'TRUE', 'FALSE', 'True', 'False', 'true', 'false'}
    VALIDVTYPE = {'none', 'suggest', 'enum'}
    MAXERRORS = 20

    # Column name mapping for backward compatibility
    # V4 used ValidationMin, V5 uses TextOptions (both work)
    COLUMN_ALIASES = {
        'ValidationMin': 'TextOptions',
        'TextOptions': 'TextOptions',
    }

    def __init__(self, client, user_id: str, excel_path: str):
        self.client = client
        self.user_id = user_id
        self.excel_path = excel_path
        self.df: Optional[pd.DataFrame] = None
        self.existing_structure: Dict = {}
        self.changes = ChangeSet()

    def parse_and_validate(self) -> ChangeSet:
        self.df = self._read_excel()
        if self.df is None:
            self.changes.validation_errors.append(ValidationError(0, 'File', 'Failed to read Excel file'))
            return self.changes

        self.existing_structure = self._load_existing_structure()
        self._validate_data_format()
        if not self.changes.has_errors() or len(self.changes.validation_errors) < self.MAXERRORS:
            self._detect_changes()
        if len(self.changes.validation_errors) < self.MAXERRORS:
            self._validate_business_logic()
        return self.changes

    def _read_excel(self) -> Optional[pd.DataFrame]:
        try:
            df = pd.read_excel(self.excel_path, sheet_name='HierarchicalView', header=1)
            df.columns = df.columns.str.strip()
            
            # Handle column aliases (ValidationMin -> TextOptions)
            if 'ValidationMin' in df.columns and 'TextOptions' not in df.columns:
                df = df.rename(columns={'ValidationMin': 'TextOptions'})
            
            return df
        except Exception as e:
            self.changes.validation_errors.append(ValidationError(0, 'File', f'Error reading Excel: {e}'))
            return None

    def _load_existing_structure(self) -> Dict:
        """Load existing structure from database."""
        structure = {'areas': {}, 'categories': {}, 'attributes': {}}
        try:
            areas = self.client.table('areas').select('*').eq('user_id', self.user_id).execute().data or []
            for a in areas:
                structure['areas'][(a.get('name') or '').lower()] = a

            cats = self.client.table('categories').select('*').eq('user_id', self.user_id).execute().data or []
            
            for c in cats:
                path = self._build_category_path(c, cats)
                structure['categories'][path.lower()] = c

            attrs = self.client.table('attribute_definitions').select('*').eq('user_id', self.user_id).execute().data or []
            for a in attrs:
                key = f"{a['category_id']}::{(a.get('name') or '').lower()}"
                structure['attributes'][key] = a

        except Exception as e:
            self.changes.validation_errors.append(ValidationError(0, 'Database', f'Failed to load existing structure: {e}'))
        return structure

    def _build_category_path(self, category: Dict, all_categories: List[Dict]) -> str:
        parts = [category.get('name', '')]
        current = category
        cat_map = {c['id']: c for c in all_categories}
        
        while current.get('parent_category_id'):
            parent = cat_map.get(current['parent_category_id'])
            if not parent:
                break
            parts.insert(0, parent.get('name', ''))
            current = parent
        
        area = self._get_area_name(category.get('area_id'))
        if area:
            parts.insert(0, area)
        return ' > '.join(parts)

    def _get_area_name(self, area_id: str) -> str:
        for name, a in self.existing_structure['areas'].items():
            if a['id'] == area_id:
                return a['name']
        return ''

    def _validate_data_format(self):
        if self.df is None or self.df.empty:
            self.changes.validation_errors.append(ValidationError(0, 'Data', 'No data found in sheet'))
            return

        for idx, row in self.df.iterrows():
            excelrow = idx + 3
            if row.isna().all():
                continue

            rowtype = str(row.get('Type', '')).strip()
            if not rowtype:
                continue
            if rowtype not in self.VALIDTYPES:
                self.changes.validation_errors.append(ValidationError(excelrow, 'Type', f'Invalid type {rowtype}'))
                continue

            catpath = str(row.get('CategoryPath', '')).strip()
            if not catpath:
                self.changes.validation_errors.append(ValidationError(excelrow, 'CategoryPath', 'CategoryPath is required'))
                continue

            parts = [p.strip() for p in catpath.split(' > ') if p.strip()]
            if not parts:
                self.changes.validation_errors.append(ValidationError(excelrow, 'CategoryPath', 'Invalid CategoryPath format'))
                continue

            lastpart = parts[-1]

            if rowtype == 'Attribute':
                attrname = str(row.get('AttributeName', '')).strip()
                if not attrname:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'AttributeName', 'AttributeName is required for Attributes'))

                datatype = str(row.get('DataType', '')).strip()
                if datatype and datatype not in self.VALIDDATATYPES:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'DataType', f'Invalid DataType {datatype}'))

                vtype = row.get('ValidationType', None)
                if pd.isna(vtype):
                    vtype = ''
                else:
                    vtype = str(vtype).strip().lower()
                if vtype and vtype not in self.VALIDVTYPE:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'ValidationType', f'Invalid ValidationType {vtype}'))

                # Validate DependsOn references existing attribute in same category
                depends_on = str(row.get('DependsOn', '')).strip() if pd.notna(row.get('DependsOn', '')) else ''
                if depends_on:
                    # Will be validated during _detect_changes when we have full picture
                    pass

    def _parse_text_options(self, s: str) -> List[str]:
        if not s or pd.isna(s):
            return []
        return [p.strip() for p in str(s).split('|') if p and str(p).strip()]

    def _parse_number(self, v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        s = str(v).strip()
        if not s:
            return None
        try:
            return float(s) if '.' in s else int(s)
        except Exception:
            return None

    def _collect_attribute_rows(self) -> Dict[str, List[Tuple[int, pd.Series]]]:
        """Collect all rows for each attribute, grouping by (category_path, attribute_name)."""
        attr_rows = defaultdict(list)
        
        for idx, row in self.df.iterrows():
            if row.isna().all():
                continue
            rowtype = str(row.get('Type', '')).strip()
            if rowtype != 'Attribute':
                continue
            
            catpath = str(row.get('CategoryPath', '')).strip()
            attrname = str(row.get('AttributeName', '')).strip()
            if not catpath or not attrname:
                continue
            
            key = f"{catpath.lower()}::{attrname.lower()}"
            attr_rows[key].append((idx + 3, row))  # Excel row number
        
        return attr_rows

    def _build_validation_rules_with_dependencies(self, rows: List[Tuple[int, pd.Series]]) -> Tuple[Dict, str, str, str, bool, str, int, str]:
        """
        Build validation rules from potentially multiple rows (for dependencies).
        
        Returns: (validation_rules, datatype, unit, default_value, is_required, description, sort_order, depends_on_slug)
        """
        first_row = rows[0][1]
        
        datatype = str(first_row.get('DataType', 'text')).strip() or 'text'
        unit = str(first_row.get('Unit', '')).strip() if pd.notna(first_row.get('Unit', '')) else ''
        default_value = str(first_row.get('DefaultValue', '')).strip() if pd.notna(first_row.get('DefaultValue', '')) else ''
        is_required = str(first_row.get('IsRequired', '')).strip().upper() == 'TRUE'
        description = str(first_row.get('Description', '')).strip() if pd.notna(first_row.get('Description', '')) else ''
        sort_order = int(first_row.get('SortOrder', 0)) if pd.notna(first_row.get('SortOrder', 0)) else 0
        vtype_raw = str(first_row.get('ValidationType', '')).strip().lower() if pd.notna(first_row.get('ValidationType', '')) else ''
        
        if not vtype_raw and datatype == 'text':
            vtype_raw = 'suggest'
        
        rules: Dict = {'type': vtype_raw or 'none'}
        
        # Check if any row has DependsOn
        depends_on_slug = ''
        options_map = {}
        
        for excelrow, row in rows:
            depends_on = str(row.get('DependsOn', '')).strip() if pd.notna(row.get('DependsOn', '')) else ''
            when_value = str(row.get('WhenValue', '')).strip() if pd.notna(row.get('WhenValue', '')) else ''
            text_options = str(row.get('TextOptions', '')).strip() if pd.notna(row.get('TextOptions', '')) else ''
            
            if depends_on:
                depends_on_slug = depends_on
                opts = self._parse_text_options(text_options)
                options_map[when_value] = opts
        
        if depends_on_slug and options_map:
            # Has dependencies
            rules['depends_on'] = {
                'attribute_slug': depends_on_slug,
                'options_map': options_map
            }
            rules['allow_other'] = True
        elif datatype == 'text':
            # Simple text attribute
            text_options = str(first_row.get('TextOptions', '')).strip() if pd.notna(first_row.get('TextOptions', '')) else ''
            opts = self._parse_text_options(text_options)
            if opts:
                if vtype_raw == 'enum':
                    rules['enum'] = opts
                elif vtype_raw == 'suggest':
                    rules['suggest'] = opts
        elif datatype == 'number':
            valmin = first_row.get('TextOptions', None)  # TextOptions holds min for numbers
            valmax = first_row.get('ValidationMax', None)
            mn = self._parse_number(valmin)
            mx = self._parse_number(valmax)
            if mn is not None:
                rules['min'] = mn
            if mx is not None:
                rules['max'] = mx
        
        return rules, datatype, unit, default_value, is_required, description, sort_order, depends_on_slug

    def _detect_changes(self):
        created_areas: Dict[str, str] = {}
        created_categories: Dict[str, str] = {}

        # First pass: process areas and categories
        for idx, row in self.df.iterrows():
            excelrow = idx + 3
            if row.isna().all():
                continue
            rowtype = str(row.get('Type', '')).strip()
            if rowtype == 'Area':
                self._process_area_row(row, excelrow, created_areas)
            elif rowtype == 'Category':
                self._process_category_row(row, excelrow, created_areas, created_categories)

        # Second pass: process attributes with dependency merging
        attr_rows = self._collect_attribute_rows()
        
        for attr_key, rows in attr_rows.items():
            self._process_attribute_rows(rows, created_categories)

    def _process_area_row(self, row, excelrow: int, created_areas: Dict[str, str]):
        area_name = str(row.get('CategoryPath', '')).strip()
        if not area_name:
            return
        existing = self.existing_structure['areas'].get(area_name.lower())
        updates = {}
        new_desc = str(row.get('Description', '')).strip() if pd.notna(row.get('Description', '')) else ''
        new_sort = int(row.get('SortOrder', 0)) if pd.notna(row.get('SortOrder', 0)) else 0

        if existing:
            if new_desc != (existing.get('description') or ''):
                updates['description'] = new_desc
            if new_sort != (existing.get('sort_order') or 0):
                updates['sort_order'] = new_sort
            if updates:
                self.changes.updated_areas.append({
                    'id': existing['id'],
                    'name': area_name,
                    'updates': updates,
                    'excel_row': excelrow
                })
        else:
            aid = str(uuid.uuid4())
            created_areas[area_name.lower()] = aid
            self.changes.new_areas.append({
                'uuid': aid,
                'name': area_name,
                'sort_order': new_sort,
                'description': new_desc,
                'excel_row': excelrow
            })

    def _process_category_row(self, row, excelrow: int, created_areas: Dict[str, str], created_categories: Dict[str, str]):
        catpath = str(row.get('CategoryPath', '')).strip()
        catname = str(row.get('Category', '')).strip()
        if not catpath or not catname:
            return
        parts = [p.strip() for p in catpath.split(' > ') if p.strip()]
        area_name = parts[0] if parts else ''
        level = len(parts) - 1

        area_id = None
        if area_name.lower() in self.existing_structure['areas']:
            area_id = self.existing_structure['areas'][area_name.lower()]['id']
        elif area_name.lower() in created_areas:
            area_id = created_areas[area_name.lower()]
        else:
            self.changes.validation_errors.append(ValidationError(excelrow, 'CategoryPath', f'Area {area_name} not found'))
            return

        parent_category_id = None
        if level > 1:
            parentpath = ' > '.join(parts[:-1])
            if parentpath.lower() in self.existing_structure['categories']:
                parent_category_id = self.existing_structure['categories'][parentpath.lower()]['id']
            elif parentpath.lower() in created_categories:
                parent_category_id = created_categories[parentpath.lower()]
            else:
                self.changes.validation_errors.append(ValidationError(excelrow, 'CategoryPath', f'Parent category {parentpath} not found'))
                return

        existing = self.existing_structure['categories'].get(catpath.lower())
        updates = {}
        new_desc = str(row.get('Description', '')).strip() if pd.notna(row.get('Description', '')) else ''
        new_sort = int(row.get('SortOrder', 0)) if pd.notna(row.get('SortOrder', 0)) else 0

        if existing:
            if catname != (existing.get('name') or ''):
                updates['name'] = catname
            if new_desc != (existing.get('description') or ''):
                updates['description'] = new_desc
            if new_sort != (existing.get('sort_order') or 0):
                updates['sort_order'] = new_sort
            if updates:
                self.changes.updated_categories.append({
                    'id': existing['id'],
                    'path': catpath,
                    'updates': updates,
                    'excel_row': excelrow
                })
        else:
            cid = str(uuid.uuid4())
            created_categories[catpath.lower()] = cid
            self.changes.new_categories.append({
                'uuid': cid,
                'area_id': area_id,
                'parent_category_id': parent_category_id,
                'name': catname,
                'level': level,
                'sort_order': new_sort,
                'description': new_desc,
                'path': catpath,
                'excel_row': excelrow
            })

    def _process_attribute_rows(self, rows: List[Tuple[int, pd.Series]], created_categories: Dict[str, str]):
        """Process potentially multiple rows for a single attribute (with dependencies)."""
        if not rows:
            return
        
        first_excelrow, first_row = rows[0]
        catpath = str(first_row.get('CategoryPath', '')).strip()
        attrname = str(first_row.get('AttributeName', '')).strip()
        
        if not catpath or not attrname:
            return

        # Get category
        category = None
        if catpath.lower() in self.existing_structure['categories']:
            category = self.existing_structure['categories'][catpath.lower()]
        elif catpath.lower() in created_categories:
            category = {'id': created_categories[catpath.lower()]}
        else:
            self.changes.validation_errors.append(ValidationError(first_excelrow, 'CategoryPath', f'Category {catpath} not found'))
            return

        category_id = category['id']
        key = f"{category_id}::{attrname.lower()}"
        existing = self.existing_structure['attributes'].get(key)

        # Build validation rules from all rows
        vr, datatype, unit, default_value, is_required, description, sort_order, depends_on = \
            self._build_validation_rules_with_dependencies(rows)

        if existing:
            updates = {}
            if datatype != (existing.get('data_type') or 'text'):
                updates['data_type'] = datatype
            if unit != (existing.get('unit') or ''):
                updates['unit'] = unit
            if is_required != (existing.get('is_required') or False):
                updates['is_required'] = is_required
            if default_value != (existing.get('default_value') or ''):
                updates['default_value'] = default_value
            if sort_order != (existing.get('sort_order') or 0):
                updates['sort_order'] = sort_order
            if description != (existing.get('description') or ''):
                updates['description'] = description

            # Compare validation_rules
            existing_vr = existing.get('validation_rules')
            if isinstance(existing_vr, str):
                try:
                    existing_vr = json.loads(existing_vr)
                except:
                    existing_vr = {}
            if not isinstance(existing_vr, dict):
                existing_vr = {}
            
            if json.dumps(vr, sort_keys=True) != json.dumps(existing_vr, sort_keys=True):
                updates['validation_rules'] = json.dumps(vr) if vr else None

            if updates:
                self.changes.updated_attributes.append({
                    'id': existing['id'],
                    'name': attrname,
                    'updates': updates,
                    'excel_row': first_excelrow
                })
        else:
            aid = str(uuid.uuid4())
            self.changes.new_attributes.append({
                'uuid': aid,
                'category_id': category_id,
                'name': attrname,
                'data_type': datatype,
                'unit': unit,
                'is_required': is_required,
                'default_value': default_value,
                'validation_rules': json.dumps(vr) if vr else None,
                'sort_order': sort_order,
                'description': description,
                'category_path': catpath,
                'excel_row': first_excelrow
            })

    def _validate_business_logic(self):
        total = sum([
            len(self.changes.new_areas), len(self.changes.new_categories), len(self.changes.new_attributes),
            len(self.changes.updated_areas), len(self.changes.updated_categories), len(self.changes.updated_attributes)
        ])
        if total > 50:
            self.changes.validation_warnings.append(
                ValidationError(0, 'Changes', f'Large number of changes detected ({total}). Please review carefully.', 'warning')
            )

    def apply_changes(self) -> Tuple[bool, str]:
        """Apply validated changes to database."""
        if self.changes.has_errors():
            return False, 'Cannot apply changes due to validation errors.'
        if not self.changes.has_changes():
            return True, 'No changes to apply.'

        try:
            if self.changes.new_areas:
                payload = [{
                    'id': a['uuid'],
                    'user_id': self.user_id,
                    'name': a['name'],
                    'icon': '',
                    'color': '4472C4',
                    'sort_order': a.get('sort_order', 0),
                    'description': a.get('description', ''),
                    'slug': a['name'].lower().replace(' ', '-')
                } for a in self.changes.new_areas]
                self.client.table('areas').insert(payload).execute()

            if self.changes.new_categories:
                payload = [{
                    'id': c['uuid'],
                    'user_id': self.user_id,
                    'area_id': c['area_id'],
                    'parent_category_id': c.get('parent_category_id'),
                    'name': c['name'],
                    'level': c['level'],
                    'sort_order': c.get('sort_order', 0),
                    'description': c.get('description', ''),
                    'slug': c['name'].lower().replace(' ', '-'),
                } for c in self.changes.new_categories]
                self.client.table('categories').insert(payload).execute()

            if self.changes.new_attributes:
                payload = []
                for a in self.changes.new_attributes:
                    payload.append({
                        'id': a['uuid'],
                        'user_id': self.user_id,
                        'category_id': a['category_id'],
                        'name': a['name'],
                        'data_type': a.get('data_type', 'text'),
                        'unit': a.get('unit', ''),
                        'is_required': a.get('is_required', False),
                        'default_value': a.get('default_value', ''),
                        'validation_rules': a.get('validation_rules'),
                        'sort_order': a.get('sort_order', 0),
                        'description': a.get('description', ''),
                        'slug': a['name'].lower().replace(' ', '-')
                    })
                self.client.table('attribute_definitions').insert(payload).execute()

            for upd in self.changes.updated_areas:
                self.client.table('areas').update(upd['updates']).eq('id', upd['id']).eq('user_id', self.user_id).execute()
            for upd in self.changes.updated_categories:
                self.client.table('categories').update(upd['updates']).eq('id', upd['id']).eq('user_id', self.user_id).execute()
            for upd in self.changes.updated_attributes:
                self.client.table('attribute_definitions').update(upd['updates']).eq('id', upd['id']).eq('user_id', self.user_id).execute()

            parts = []
            for name, lst in [
                ('new areas', self.changes.new_areas),
                ('new categories', self.changes.new_categories),
                ('new attributes', self.changes.new_attributes),
                ('updated areas', self.changes.updated_areas),
                ('updated categories', self.changes.updated_categories),
                ('updated attributes', self.changes.updated_attributes),
            ]:
                if lst:
                    parts.append(f"{len(lst)} {name}")
            return True, 'Successfully applied changes: ' + ', '.join(parts)

        except Exception as e:
            return False, f'Error applying changes: {e}'
