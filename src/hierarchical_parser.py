
"""Hierarchical Parser v4

Reads the v4 HierarchicalView Excel format and updates Supabase structure.
Adds support for:
- ValidationType column (K): none/suggest/enum
- For text attributes, ValidationMin column (M) can contain pipe-separated options
  which are stored as validationrules.{enum|suggest} depending on ValidationType.
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
    newareas: List[Dict] = field(default_factory=list)
    newcategories: List[Dict] = field(default_factory=list)
    newattributes: List[Dict] = field(default_factory=list)
    updatedareas: List[Dict] = field(default_factory=list)
    updatedcategories: List[Dict] = field(default_factory=list)
    updatedattributes: List[Dict] = field(default_factory=list)
    validationerrors: List[ValidationError] = field(default_factory=list)
    validationwarnings: List[ValidationError] = field(default_factory=list)

    def haschanges(self) -> bool:
        return any([self.newareas, self.newcategories, self.newattributes, self.updatedareas, self.updatedcategories, self.updatedattributes])

    def haserrors(self) -> bool:
        return len(self.validationerrors) > 0


class HierarchicalParserV4:
    VALIDTYPES = {'Area', 'Category', 'Attribute'}
    VALIDDATATYPES = {'number', 'text', 'datetime', 'boolean', 'link', 'image'}
    VALIDREQUIRED = {'TRUE', 'FALSE', 'True', 'False', 'true', 'false'}
    VALIDVTYPE = {'none', 'suggest', 'enum'}
    MAXERRORS = 20

    def __init__(self, client, userid: str, excelpath: str):
        self.client = client
        self.userid = userid
        self.excelpath = excelpath
        self.df: Optional[pd.DataFrame] = None
        self.existingstructure: Dict = {}
        self.changes = ChangeSet()

    def parse_and_validate(self) -> ChangeSet:
        self.df = self._read_excel()
        if self.df is None:
            self.changes.validationerrors.append(ValidationError(0, 'File', 'Failed to read Excel file'))
            return self.changes

        self.existingstructure = self._load_existing_structure()
        self._validate_data_format()
        if not self.changes.haserrors() or len(self.changes.validationerrors) < self.MAXERRORS:
            self._detect_changes()
        if len(self.changes.validationerrors) < self.MAXERRORS:
            self._validate_business_logic()
        return self.changes

    def _read_excel(self) -> Optional[pd.DataFrame]:
        try:
            df = pd.read_excel(self.excelpath, sheet_name='HierarchicalView', header=1)
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            self.changes.validationerrors.append(ValidationError(0, 'File', f'Error reading Excel: {e}'))
            return None

    def _load_existing_structure(self) -> Dict:
        structure = {'areas': {}, 'categories': {}, 'attributes': {}}
        try:
            areas = self.client.table('areas').select('*').eq('userid', self.userid).execute().data or []
            for a in areas:
                structure['areas'][(a.get('name') or '').lower()] = a

            cats = self.client.table('categories').select('*').eq('userid', self.userid).execute().data or []
            attrs = self.client.table('attributedefinitions').select('*').eq('userid', self.userid).execute().data or []

            for at in attrs:
                key = f"{at.get('categoryid')}::{(at.get('name') or '').lower()}"
                structure['attributes'][key] = at

            cat_by_id = {c['id']: c for c in cats if c.get('id')}
            area_by_id = {a['id']: a for a in areas if a.get('id')}

            def build_path(cat_id: str) -> str:
                cat = cat_by_id.get(cat_id)
                if not cat:
                    return ''
                parts = [cat.get('name','')]
                pid = cat.get('parentcategoryid')
                while pid:
                    p = cat_by_id.get(pid)
                    if not p:
                        break
                    parts.insert(0, p.get('name',''))
                    pid = p.get('parentcategoryid')
                area = area_by_id.get(cat.get('areaid'))
                if area:
                    parts.insert(0, area.get('name',''))
                return ' '.join([p for p in parts if p])

            for c in cats:
                p = build_path(c['id']).lower()
                if p:
                    structure['categories'][p] = c

        except Exception as e:
            self.changes.validationerrors.append(ValidationError(0, 'Database', f'Error loading existing structure: {e}'))
        return structure

    def _validate_data_format(self):
        required = ['Type', 'CategoryPath', 'Level', 'SortOrder']
        missing = [c for c in required if c not in self.df.columns]
        if missing:
            self.changes.validationerrors.append(ValidationError(0, 'Columns', f"Missing required columns: {', '.join(missing)}"))
            return

        seenpaths: Dict[str, int] = {}
        for idx, row in self.df.iterrows():
            if len(self.changes.validationerrors) >= self.MAXERRORS:
                self.changes.validationwarnings.append(ValidationError(0, 'Validation', f'Validation stopped at {self.MAXERRORS} errors.', 'warning'))
                break
            excelrow = idx + 3
            if row.isna().all():
                continue

            rowtype = str(row.get('Type', '')).strip()
            if not rowtype:
                self.changes.validationerrors.append(ValidationError(excelrow, 'Type', 'Type is required'))
                continue
            if rowtype not in self.VALIDTYPES:
                self.changes.validationerrors.append(ValidationError(excelrow, 'Type', f'Invalid Type {rowtype}'))
                continue

            catpath = str(row.get('CategoryPath', '')).strip()
            if not catpath:
                self.changes.validationerrors.append(ValidationError(excelrow, 'CategoryPath', 'CategoryPath is required'))
                continue

            pathkey = catpath.lower()
            if rowtype in {'Area', 'Category'}:
                if pathkey in seenpaths:
                    self.changes.validationerrors.append(ValidationError(excelrow, 'CategoryPath', f'Duplicate CategoryPath; already used in row {seenpaths[pathkey]}'))
                else:
                    seenpaths[pathkey] = excelrow

            parts = [p.strip() for p in catpath.split(' ') if p.strip()]
            lastpart = parts[-1] if parts else ''

            if rowtype == 'Attribute':
                datatype = str(row.get('DataType', '')).strip()
                if not datatype:
                    self.changes.validationerrors.append(ValidationError(excelrow, 'DataType', 'DataType is required for Attributes'))
                elif datatype not in self.VALIDDATATYPES:
                    self.changes.validationerrors.append(ValidationError(excelrow, 'DataType', f'Invalid DataType {datatype}'))

                attrname = str(row.get('AttributeName', '')).strip()
                if not attrname:
                    self.changes.validationerrors.append(ValidationError(excelrow, 'AttributeName', 'AttributeName is required for Attributes'))

                isreq = row.get('IsRequired', '')
                if pd.notna(isreq) and str(isreq).strip() and str(isreq).strip() not in self.VALIDREQUIRED:
                    self.changes.validationerrors.append(ValidationError(excelrow, 'IsRequired', f'Invalid IsRequired {isreq}. Must be TRUE/FALSE'))

                vtype = str(row.get('ValidationType', '')).strip().lower()
                if vtype and vtype not in self.VALIDVTYPE:
                    self.changes.validationerrors.append(ValidationError(excelrow, 'ValidationType', f'Invalid ValidationType {vtype}. Must be none/suggest/enum'))

                catname = str(row.get('Category', '')).strip()
                if catname and catname != lastpart:
                    self.changes.validationerrors.append(ValidationError(excelrow, 'Category', f'Category mismatch: Category is {catname} but path ends with {lastpart}'))

            elif rowtype == 'Category':
                catname = str(row.get('Category', '')).strip()
                if not catname:
                    self.changes.validationerrors.append(ValidationError(excelrow, 'Category', 'Category name is required for Categories'))
                elif catname != lastpart:
                    self.changes.validationerrors.append(ValidationError(excelrow, 'Category', f'Category mismatch: Category is {catname} but path ends with {lastpart}'))

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

    def _build_validationrules(self, datatype: str, vtype: str, default_vtype_for_text: str, valmin_cell, valmax_cell) -> Optional[Dict]:
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
        createdareas: Dict[str, str] = {}
        createdcategories: Dict[str, str] = {}

        for idx, row in self.df.iterrows():
            excelrow = idx + 3
            if row.isna().all():
                continue
            rowtype = str(row.get('Type', '')).strip()
            if rowtype == 'Area':
                self._process_area_row(row, excelrow, createdareas)
            elif rowtype == 'Category':
                self._process_category_row(row, excelrow, createdareas, createdcategories)
            elif rowtype == 'Attribute':
                self._process_attribute_row(row, excelrow, createdcategories)

    def _process_area_row(self, row, excelrow: int, createdareas: Dict[str, str]):
        areaname = str(row.get('CategoryPath', '')).strip()
        if not areaname:
            return
        existing = self.existingstructure['areas'].get(areaname.lower())
        updates = {}
        newdesc = str(row.get('Description', '')).strip() if pd.notna(row.get('Description', '')) else ''
        newsort = int(row.get('SortOrder', 0)) if pd.notna(row.get('SortOrder', 0)) else 0
        if existing:
            if newdesc != (existing.get('description') or ''):
                updates['description'] = newdesc
            if newsort != (existing.get('sortorder') or 0):
                updates['sortorder'] = newsort
            if updates:
                self.changes.updatedareas.append({'id': existing['id'], 'updates': updates, 'excelrow': excelrow})
        else:
            aid = str(uuid.uuid4())
            createdareas[areaname.lower()] = aid
            self.changes.newareas.append({'uuid': aid, 'name': areaname, 'sortorder': newsort, 'description': newdesc, 'excelrow': excelrow})

    def _process_category_row(self, row, excelrow: int, createdareas: Dict[str, str], createdcategories: Dict[str, str]):
        catpath = str(row.get('CategoryPath', '')).strip()
        catname = str(row.get('Category', '')).strip()
        if not catpath or not catname:
            return
        parts = [p.strip() for p in catpath.split(' ') if p.strip()]
        areaname = parts[0] if parts else ''
        parentname = parts[-2] if len(parts) >= 2 else None
        level = len(parts) - 1

        areaid = None
        if areaname.lower() in self.existingstructure['areas']:
            areaid = self.existingstructure['areas'][areaname.lower()]['id']
        elif areaname.lower() in createdareas:
            areaid = createdareas[areaname.lower()]
        else:
            self.changes.validationerrors.append(ValidationError(excelrow, 'CategoryPath', f'Area {areaname} not found'))
            return

        parentcategoryid = None
        if parentname:
            parentpath = ' '.join(parts[:-1])
            if parentpath.lower() in self.existingstructure['categories']:
                parentcategoryid = self.existingstructure['categories'][parentpath.lower()]['id']
            elif parentpath.lower() in createdcategories:
                parentcategoryid = createdcategories[parentpath.lower()]
            else:
                self.changes.validationerrors.append(ValidationError(excelrow, 'CategoryPath', f'Parent category {parentpath} not found'))
                return

        existing = self.existingstructure['categories'].get(catpath.lower())
        updates = {}
        newdesc = str(row.get('Description', '')).strip() if pd.notna(row.get('Description', '')) else ''
        newsort = int(row.get('SortOrder', 0)) if pd.notna(row.get('SortOrder', 0)) else 0

        if existing:
            if catname != (existing.get('name') or ''):
                updates['name'] = catname
            if newdesc != (existing.get('description') or ''):
                updates['description'] = newdesc
            if newsort != (existing.get('sortorder') or 0):
                updates['sortorder'] = newsort
            if updates:
                self.changes.updatedcategories.append({'id': existing['id'], 'updates': updates, 'excelrow': excelrow})
        else:
            cid = str(uuid.uuid4())
            createdcategories[catpath.lower()] = cid
            self.changes.newcategories.append({
                'uuid': cid,
                'areaid': areaid,
                'parentcategoryid': parentcategoryid,
                'name': catname,
                'level': level,
                'sortorder': newsort,
                'description': newdesc,
                'path': catpath,
                'excelrow': excelrow
            })

    def _process_attribute_row(self, row, excelrow: int, createdcategories: Dict[str, str]):
        catpath = str(row.get('CategoryPath', '')).strip()
        attrname = str(row.get('AttributeName', '')).strip()
        if not catpath or not attrname:
            return

        category = None
        if catpath.lower() in self.existingstructure['categories']:
            category = self.existingstructure['categories'][catpath.lower()]
        elif catpath.lower() in createdcategories:
            category = {'id': createdcategories[catpath.lower()]}
        else:
            self.changes.validationerrors.append(ValidationError(excelrow, 'CategoryPath', f'Category {catpath} not found'))
            return

        categoryid = category['id']
        key = f"{categoryid}::{attrname.lower()}"
        existing = self.existingstructure['attributes'].get(key)

        datatype = str(row.get('DataType', '')).strip()
        unit = str(row.get('Unit', '')).strip() if pd.notna(row.get('Unit', '')) else ''
        isreq_raw = str(row.get('IsRequired', '')).strip() if pd.notna(row.get('IsRequired', '')) else ''
        isrequired = isreq_raw.upper() == 'TRUE'

        vtype_raw = str(row.get('ValidationType', '')).strip().lower() if pd.notna(row.get('ValidationType', '')) else ''
        default_value = str(row.get('DefaultValue', '')).strip() if pd.notna(row.get('DefaultValue', '')) else ''
        valmin_cell = row.get('ValidationMin', None)
        valmax_cell = row.get('ValidationMax', None)

        vr = self._build_validationrules(datatype, vtype_raw, default_vtype_for_text='suggest', valmin_cell=valmin_cell, valmax_cell=valmax_cell)

        desc = str(row.get('Description', '')).strip() if pd.notna(row.get('Description', '')) else ''
        sortorder = int(row.get('SortOrder', 0)) if pd.notna(row.get('SortOrder', 0)) else 0

        if existing:
            updates = {}
            if attrname != (existing.get('name') or ''):
                updates['name'] = attrname
            if datatype and datatype != (existing.get('datatype') or ''):
                updates['datatype'] = datatype
            if unit != (existing.get('unit') or ''):
                updates['unit'] = unit
            if isrequired != bool(existing.get('isrequired', False)):
                updates['isrequired'] = isrequired
            if default_value != (existing.get('defaultvalue') or ''):
                updates['defaultvalue'] = default_value

            old_vr = existing.get('validationrules')
            if isinstance(old_vr, str):
                try:
                    old_vr = json.loads(old_vr)
                except Exception:
                    old_vr = {}
            if not isinstance(old_vr, dict):
                old_vr = {}

            if vr != old_vr:
                updates['validationrules'] = json.dumps(vr) if vr else None

            if sortorder != (existing.get('sortorder') or 0):
                updates['sortorder'] = sortorder
            if desc != (existing.get('description') or ''):
                updates['description'] = desc

            if updates:
                self.changes.updatedattributes.append({'id': existing['id'], 'updates': updates, 'excelrow': excelrow})
        else:
            aid = str(uuid.uuid4())
            self.changes.newattributes.append({
                'uuid': aid,
                'categoryid': categoryid,
                'name': attrname,
                'datatype': datatype,
                'unit': unit,
                'isrequired': isrequired,
                'defaultvalue': default_value,
                'validationrules': json.dumps(vr) if vr else None,
                'sortorder': sortorder,
                'description': desc,
                'categorypath': catpath,
                'excelrow': excelrow
            })

    def _validate_business_logic(self):
        total = sum([
            len(self.changes.newareas), len(self.changes.newcategories), len(self.changes.newattributes),
            len(self.changes.updatedareas), len(self.changes.updatedcategories), len(self.changes.updatedattributes)
        ])
        if total > 50:
            self.changes.validationwarnings.append(ValidationError(0, 'Changes', f'Large number of changes detected ({total}). Please review carefully.', 'warning'))

    def apply_changes(self) -> Tuple[bool, str]:
        if self.changes.haserrors():
            return False, 'Cannot apply changes due to validation errors.'
        if not self.changes.haschanges():
            return True, 'No changes to apply.'

        try:
            if self.changes.newareas:
                payload = [{
                    'id': a['uuid'], 'userid': self.userid, 'name': a['name'],
                    'icon': '', 'color': '4472C4',
                    'sortorder': a.get('sortorder', 0),
                    'description': a.get('description', ''),
                    'slug': a['name'].lower().replace(' ', '-')
                } for a in self.changes.newareas]
                self.client.table('areas').insert(payload).execute()

            if self.changes.newcategories:
                payload = [{
                    'id': c['uuid'], 'userid': self.userid,
                    'areaid': c['areaid'],
                    'parentcategoryid': c.get('parentcategoryid'),
                    'name': c['name'],
                    'level': c['level'],
                    'sortorder': c.get('sortorder', 0),
                    'description': c.get('description', ''),
                    'slug': c['name'].lower().replace(' ', '-'),
                } for c in self.changes.newcategories]
                self.client.table('categories').insert(payload).execute()

            if self.changes.newattributes:
                payload = []
                for a in self.changes.newattributes:
                    payload.append({
                        'id': a['uuid'], 'userid': self.userid,
                        'categoryid': a['categoryid'],
                        'name': a['name'],
                        'datatype': a.get('datatype','text'),
                        'unit': a.get('unit',''),
                        'isrequired': a.get('isrequired', False),
                        'defaultvalue': a.get('defaultvalue',''),
                        'validationrules': a.get('validationrules'),
                        'sortorder': a.get('sortorder', 0),
                        'description': a.get('description',''),
                        'slug': a['name'].lower().replace(' ', '-')
                    })
                self.client.table('attributedefinitions').insert(payload).execute()

            for upd in self.changes.updatedareas:
                self.client.table('areas').update(upd['updates']).eq('id', upd['id']).eq('userid', self.userid).execute()
            for upd in self.changes.updatedcategories:
                self.client.table('categories').update(upd['updates']).eq('id', upd['id']).eq('userid', self.userid).execute()
            for upd in self.changes.updatedattributes:
                self.client.table('attributedefinitions').update(upd['updates']).eq('id', upd['id']).eq('userid', self.userid).execute()

            parts = []
            for name, lst in [
                ('new areas', self.changes.newareas),
                ('new categories', self.changes.newcategories),
                ('new attributes', self.changes.newattributes),
                ('updated areas', self.changes.updatedareas),
                ('updated categories', self.changes.updatedcategories),
                ('updated attributes', self.changes.updatedattributes),
            ]:
                if lst:
                    parts.append(f"{len(lst)} {name}")
            return True, 'Successfully applied changes: ' + ', '.join(parts)

        except Exception as e:
            return False, f'Error applying changes: {e}'
