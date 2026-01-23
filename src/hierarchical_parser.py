"""Hierarchical Parser v4 - FIXED VERSION

FIXES APPLIED (2026-01-23):
- Fixed database naming convention: all table/column names now use snake_case
- Table: attributedefinitions → attribute_definitions
- Columns: areaid → area_id, categoryid → category_id, etc.

Reads the v4 HierarchicalView Excel format and updates Supabase structure.
Adds support for:
- ValidationType column (K): none/suggest/enum
- For text attributes, ValidationMin column (M) can contain pipe-separated options
  which are stored as validation_rules.{enum|suggest} depending on ValidationType.
- Default ValidationType for text is 'suggest' when blank.

Keeps number min/max behavior.
"""

import pandas as pd
import json
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


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
        return any([self.new_areas, self.new_categories, self.new_attributes, self.updated_areas, self.updated_categories, self.updated_attributes])

    def has_errors(self) -> bool:
        return len(self.validation_errors) > 0


class HierarchicalParser:
    VALIDTYPES = {'Area', 'Category', 'Attribute'}
    VALIDDATATYPES = {'number', 'text', 'datetime', 'boolean', 'link', 'image'}
    VALIDREQUIRED = {'TRUE', 'FALSE', 'True', 'False', 'true', 'false'}
    VALIDVTYPE = {'none', 'suggest', 'enum'}
    MAXERRORS = 20

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
            return df
        except Exception as e:
            self.changes.validation_errors.append(ValidationError(0, 'File', f'Error reading Excel: {e}'))
            return None

    def _load_existing_structure(self) -> Dict:
        """Load existing structure from database using correct snake_case naming."""
        structure = {'areas': {}, 'categories': {}, 'attributes': {}}
        try:
            # FIXED: use snake_case column names
            areas = self.client.table('areas').select('*').eq('user_id', self.user_id).execute().data or []
            for a in areas:
                structure['areas'][(a.get('name') or '').lower()] = a

            cats = self.client.table('categories').select('*').eq('user_id', self.user_id).execute().data or []
            
            # FIXED: table name is attribute_definitions (with underscore)
            attrs = self.client.table('attribute_definitions').select('*').eq('user_id', self.user_id).execute().data or []

            for at in attrs:
                # FIXED: column is category_id not categoryid
                key = f"{at.get('category_id')}::{(at.get('name') or '').lower()}"
                structure['attributes'][key] = at

            cat_by_id = {c['id']: c for c in cats if c.get('id')}
            area_by_id = {a['id']: a for a in areas if a.get('id')}

            def build_path(cat_id: str) -> str:
                cat = cat_by_id.get(cat_id)
                if not cat:
                    return ''
                parts = [cat.get('name','')]
                # FIXED: column is parent_category_id not parentcategoryid
                pid = cat.get('parent_category_id')
                while pid:
                    p = cat_by_id.get(pid)
                    if not p:
                        break
                    parts.insert(0, p.get('name',''))
                    pid = p.get('parent_category_id')
                # FIXED: column is area_id not areaid
                area = area_by_id.get(cat.get('area_id'))
                if area:
                    parts.insert(0, area.get('name',''))
                return ' > '.join([p for p in parts if p])

            for c in cats:
                p = build_path(c['id']).lower()
                if p:
                    structure['categories'][p] = c

        except Exception as e:
            self.changes.validation_errors.append(ValidationError(0, 'Database', f'Error loading existing structure: {e}'))
        return structure

    def _validate_data_format(self):
        required = ['Type', 'CategoryPath', 'Level', 'SortOrder']
        missing = [c for c in required if c not in self.df.columns]
        if missing:
            self.changes.validation_errors.append(ValidationError(0, 'Columns', f"Missing required columns: {', '.join(missing)}"))
            return

        seenpaths: Dict[str, int] = {}
        for idx, row in self.df.iterrows():
            if len(self.changes.validation_errors) >= self.MAXERRORS:
                self.changes.validation_warnings.append(ValidationError(0, 'Validation', f'Validation stopped at {self.MAXERRORS} errors.', 'warning'))
                break
            excelrow = idx + 3
            if row.isna().all():
                continue

            rowtype = str(row.get('Type', '')).strip()
            if not rowtype:
                self.changes.validation_errors.append(ValidationError(excelrow, 'Type', 'Type is required'))
                continue
            if rowtype not in self.VALIDTYPES:
                self.changes.validation_errors.append(ValidationError(excelrow, 'Type', f'Invalid Type {rowtype}'))
                continue

            catpath = str(row.get('CategoryPath', '')).strip()
            if not catpath:
                self.changes.validation_errors.append(ValidationError(excelrow, 'CategoryPath', 'CategoryPath is required'))
                continue

            pathkey = catpath.lower()
            if rowtype in {'Area', 'Category'}:
                if pathkey in seenpaths:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'CategoryPath', f'Duplicate CategoryPath; already used in row {seenpaths[pathkey]}'))
                else:
                    seenpaths[pathkey] = excelrow

            parts = [p.strip() for p in catpath.split(' > ') if p.strip()]
            lastpart = parts[-1] if parts else ''

            if rowtype == 'Attribute':
                datatype = str(row.get('DataType', '')).strip()
                if not datatype:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'DataType', 'DataType is required for Attributes'))
                elif datatype not in self.VALIDDATATYPES:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'DataType', f'Invalid DataType {datatype}'))

                attrname = str(row.get('AttributeName', '')).strip()
                if not attrname:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'AttributeName', 'AttributeName is required for Attributes'))

                isreq = row.get('IsRequired', '')
                if pd.notna(isreq) and str(isreq).strip() and str(isreq).strip() not in self.VALIDREQUIRED:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'IsRequired', f'Invalid IsRequired {isreq}. Must be TRUE/FALSE'))

                vtype = row.get('ValidationType', '')
                # Handle NaN values properly
                if pd.isna(vtype):
                    vtype = ''
                else:
                    vtype = str(vtype).strip().lower()
                if vtype and vtype not in self.VALIDVTYPE:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'ValidationType', f'Invalid ValidationType {vtype}. Must be none/suggest/enum'))

                catname = str(row.get('Category', '')).strip()
                if catname and catname != lastpart:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'Category', f'Category mismatch: Category is {catname} but path ends with {lastpart}'))

            elif rowtype == 'Category':
                catname = str(row.get('Category', '')).strip()
                if not catname:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'Category', 'Category name is required for Categories'))
                elif catname != lastpart:
                    self.changes.validation_errors.append(ValidationError(excelrow, 'Category', f'Category mismatch: Category is {catname} but path ends with {lastpart}'))

    def _parse_text_options(self, s: str) -> List[str]:
        if not s:
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

    def _build_validation_rules(self, datatype: str, vtype: str, default_vtype_for_text: str, valmin_cell, valmax_cell) -> Optional[Dict]:
        """Build validation rules dict for an attribute."""
        datatype = (datatype or '').strip()
        vtype = (vtype or '').strip().lower()

        rules: Dict = {}

        if datatype == 'text':
            if not vtype:
                vtype = default_vtype_for_text
            rules['type'] = vtype
            opts = self._parse_text_options(str(valmin_cell).strip() if valmin_cell is not None else '')
            if opts:
                if vtype == 'enum':
                    rules['enum'] = opts
                elif vtype == 'suggest':
                    rules['suggest'] = opts
        elif datatype == 'number':
            rules['type'] = 'none' if not vtype else vtype
            mn = self._parse_number(valmin_cell)
            mx = self._parse_number(valmax_cell)
            if mn is not None:
                rules['min'] = mn
            if mx is not None:
                rules['max'] = mx
        else:
            rules['type'] = 'none' if not vtype else vtype

        return rules if rules else None

    def _detect_changes(self):
        created_areas: Dict[str, str] = {}
        created_categories: Dict[str, str] = {}

        for idx, row in self.df.iterrows():
            excelrow = idx + 3
            if row.isna().all():
                continue
            rowtype = str(row.get('Type', '')).strip()
            if rowtype == 'Area':
                self._process_area_row(row, excelrow, created_areas)
            elif rowtype == 'Category':
                self._process_category_row(row, excelrow, created_areas, created_categories)
            elif rowtype == 'Attribute':
                self._process_attribute_row(row, excelrow, created_categories)

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
            # FIXED: column is sort_order not sortorder
            if new_sort != (existing.get('sort_order') or 0):
                updates['sort_order'] = new_sort
            if updates:
                self.changes.updated_areas.append({'id': existing['id'], 'updates': updates, 'excelrow': excelrow})
        else:
            aid = str(uuid.uuid4())
            created_areas[area_name.lower()] = aid
            self.changes.new_areas.append({
                'uuid': aid, 
                'name': area_name, 
                'sort_order': new_sort,  # FIXED
                'description': new_desc, 
                'excelrow': excelrow
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
        if level > 1:  # Only look for parent category if level > 1
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
            # FIXED: column is sort_order
            if new_sort != (existing.get('sort_order') or 0):
                updates['sort_order'] = new_sort
            if updates:
                self.changes.updated_categories.append({'id': existing['id'], 'updates': updates, 'excelrow': excelrow})
        else:
            cid = str(uuid.uuid4())
            created_categories[catpath.lower()] = cid
            self.changes.new_categories.append({
                'uuid': cid,
                'area_id': area_id,  # FIXED
                'parent_category_id': parent_category_id,  # FIXED
                'name': catname,
                'level': level,
                'sort_order': new_sort,  # FIXED
                'description': new_desc,
                'path': catpath,
                'excelrow': excelrow
            })

    def _process_attribute_row(self, row, excelrow: int, created_categories: Dict[str, str]):
        catpath = str(row.get('CategoryPath', '')).strip()
        attrname = str(row.get('AttributeName', '')).strip()
        if not catpath or not attrname:
            return

        category = None
        if catpath.lower() in self.existing_structure['categories']:
            category = self.existing_structure['categories'][catpath.lower()]
        elif catpath.lower() in created_categories:
            category = {'id': created_categories[catpath.lower()]}
        else:
            self.changes.validation_errors.append(ValidationError(excelrow, 'CategoryPath', f'Category {catpath} not found'))
            return

        category_id = category['id']
        key = f"{category_id}::{attrname.lower()}"
        existing = self.existing_structure['attributes'].get(key)

        datatype = str(row.get('DataType', '')).strip()
        unit = str(row.get('Unit', '')).strip() if pd.notna(row.get('Unit', '')) else ''
        isreq_raw = str(row.get('IsRequired', '')).strip() if pd.notna(row.get('IsRequired', '')) else ''
        is_required = isreq_raw.upper() == 'TRUE'

        vtype_raw = str(row.get('ValidationType', '')).strip().lower() if pd.notna(row.get('ValidationType', '')) else ''
        default_value = str(row.get('DefaultValue', '')).strip() if pd.notna(row.get('DefaultValue', '')) else ''
        valmin_cell = row.get('ValidationMin', None)
        valmax_cell = row.get('ValidationMax', None)

        vr = self._build_validation_rules(datatype, vtype_raw, default_vtype_for_text='suggest', valmin_cell=valmin_cell, valmax_cell=valmax_cell)

        desc = str(row.get('Description', '')).strip() if pd.notna(row.get('Description', '')) else ''
        sort_order = int(row.get('SortOrder', 0)) if pd.notna(row.get('SortOrder', 0)) else 0

        if existing:
            updates = {}
            if attrname != (existing.get('name') or ''):
                updates['name'] = attrname
            # FIXED: column is data_type
            if datatype and datatype != (existing.get('data_type') or ''):
                updates['data_type'] = datatype
            if unit != (existing.get('unit') or ''):
                updates['unit'] = unit
            # FIXED: column is is_required
            if is_required != bool(existing.get('is_required', False)):
                updates['is_required'] = is_required
            # FIXED: column is default_value
            if default_value != (existing.get('default_value') or ''):
                updates['default_value'] = default_value

            # FIXED: column is validation_rules
            old_vr = existing.get('validation_rules')
            if isinstance(old_vr, str):
                try:
                    old_vr = json.loads(old_vr)
                except Exception:
                    old_vr = {}
            if not isinstance(old_vr, dict):
                old_vr = {}

            if vr != old_vr:
                updates['validation_rules'] = json.dumps(vr) if vr else None

            # FIXED: column is sort_order
            if sort_order != (existing.get('sort_order') or 0):
                updates['sort_order'] = sort_order
            if desc != (existing.get('description') or ''):
                updates['description'] = desc

            if updates:
                self.changes.updated_attributes.append({'id': existing['id'], 'updates': updates, 'excelrow': excelrow})
        else:
            aid = str(uuid.uuid4())
            self.changes.new_attributes.append({
                'uuid': aid,
                'category_id': category_id,  # FIXED
                'name': attrname,
                'data_type': datatype,  # FIXED
                'unit': unit,
                'is_required': is_required,  # FIXED
                'default_value': default_value,  # FIXED
                'validation_rules': json.dumps(vr) if vr else None,  # FIXED
                'sort_order': sort_order,  # FIXED
                'description': desc,
                'categorypath': catpath,
                'excelrow': excelrow
            })

    def _validate_business_logic(self):
        total = sum([
            len(self.changes.new_areas), len(self.changes.new_categories), len(self.changes.new_attributes),
            len(self.changes.updated_areas), len(self.changes.updated_categories), len(self.changes.updated_attributes)
        ])
        if total > 50:
            self.changes.validation_warnings.append(ValidationError(0, 'Changes', f'Large number of changes detected ({total}). Please review carefully.', 'warning'))

    def apply_changes(self) -> Tuple[bool, str]:
        """Apply validated changes to database using correct snake_case naming."""
        if self.changes.has_errors():
            return False, 'Cannot apply changes due to validation errors.'
        if not self.changes.has_changes():
            return True, 'No changes to apply.'

        try:
            # Insert new areas
            if self.changes.new_areas:
                payload = [{
                    'id': a['uuid'], 
                    'user_id': self.user_id,  # FIXED
                    'name': a['name'],
                    'icon': '', 
                    'color': '4472C4',
                    'sort_order': a.get('sort_order', 0),  # FIXED
                    'description': a.get('description', ''),
                    'slug': a['name'].lower().replace(' ', '-')
                } for a in self.changes.new_areas]
                self.client.table('areas').insert(payload).execute()

            # Insert new categories
            if self.changes.new_categories:
                payload = [{
                    'id': c['uuid'], 
                    'user_id': self.user_id,  # FIXED
                    'area_id': c['area_id'],  # FIXED
                    'parent_category_id': c.get('parent_category_id'),  # FIXED
                    'name': c['name'],
                    'level': c['level'],
                    'sort_order': c.get('sort_order', 0),  # FIXED
                    'description': c.get('description', ''),
                    'slug': c['name'].lower().replace(' ', '-'),
                } for c in self.changes.new_categories]
                self.client.table('categories').insert(payload).execute()

            # Insert new attributes - FIXED: table name is attribute_definitions
            if self.changes.new_attributes:
                payload = []
                for a in self.changes.new_attributes:
                    payload.append({
                        'id': a['uuid'], 
                        'user_id': self.user_id,  # FIXED
                        'category_id': a['category_id'],  # FIXED
                        'name': a['name'],
                        'data_type': a.get('data_type', 'text'),  # FIXED
                        'unit': a.get('unit', ''),
                        'is_required': a.get('is_required', False),  # FIXED
                        'default_value': a.get('default_value', ''),  # FIXED
                        'validation_rules': a.get('validation_rules'),  # FIXED
                        'sort_order': a.get('sort_order', 0),  # FIXED
                        'description': a.get('description', ''),
                        'slug': a['name'].lower().replace(' ', '-')
                    })
                # FIXED: table name
                self.client.table('attribute_definitions').insert(payload).execute()

            # Update existing records
            for upd in self.changes.updated_areas:
                self.client.table('areas').update(upd['updates']).eq('id', upd['id']).eq('user_id', self.user_id).execute()
            for upd in self.changes.updated_categories:
                self.client.table('categories').update(upd['updates']).eq('id', upd['id']).eq('user_id', self.user_id).execute()
            for upd in self.changes.updated_attributes:
                # FIXED: table name
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
