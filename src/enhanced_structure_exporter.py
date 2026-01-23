
"""Enhanced Structure Exporter v4

Adds ValidationType column (K) and supports text ValidationOptions stored in ValidationMin column (M).

Column layout (HierarchicalView):
A Type (pink)
B Level (pink)
C SortOrder (yellow)
D Area (pink)
E CategoryPath (yellow)
F Category (blue)
G AttributeName (blue)
H DataType (blue)
I Unit (blue)
J IsRequired (blue)
K ValidationType (blue) -> dropdown offers: none, enum
   - suggest is the default for text attributes (exporter writes it when blank)
L DefaultValue (blue)
M ValidationMin / TextOptions (blue)
N ValidationMax (blue)
O Description (blue)

Compatible with HierarchicalParser v4.
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment
from datetime import datetime
from typing import Dict, List, Optional
import json


class EnhancedStructureExporter:
    def __init__(self, client, userid: str, filterarea: Optional[str] = None, filtercategory: Optional[str] = None):
        self.client = client
        self.userid = userid
        self.filterarea = filterarea if filterarea != 'All Areas' else None
        self.filtercategory = filtercategory if filtercategory != 'All Categories' else None

        self.PINKFILL = PatternFill(start_color='FFE6F0', end_color='FFE6F0', fill_type='solid')
        self.BLUEFILL = PatternFill(start_color='E6F2FF', end_color='E6F2FF', fill_type='solid')
        self.YELLOWFILL = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
        self.HEADERFILL = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        self.BOLDFONT = Font(bold=True, color='FFFFFF')
        self.THINBORDER = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000'),
        )
        self.CENTERALIGN = Alignment(horizontal='center', vertical='center')
        self.LEFTALIGN = Alignment(horizontal='left', vertical='center')

        self.HEADERCOMMENTS = {
            'A': 'Type: Area, Category, or Attribute. Do NOT change for existing rows.',
            'B': 'Level: Auto-calculated from CategoryPath depth. Read-only.',
            'C': 'SortOrder: Position within parent element. Edit to change display order.',
            'D': 'Area: Auto-extracted from CategoryPath. Read-only.',
            'E': 'CategoryPath: KEY identifier. For existing rows DO NOT change, or you create duplicates.',
            'F': 'Category: Must match the LAST part of CategoryPath.',
            'G': 'AttributeName: Only for Attribute rows.',
            'H': 'DataType: number, text, datetime, boolean, link, image.',
            'I': 'Unit: kg, hours, EUR, km, bpm...',
            'J': 'IsRequired: TRUE or FALSE.',
            'K': 'ValidationType: controls text validation behavior. suggest = free text + optional suggestions from M. enum = STRICT; only values from M are allowed. none = no validation / no suggestions.',
            'L': 'DefaultValue: Default value for new events.',
            'M': 'ValidationMin (number) OR TextOptions (text). For text, use pipe-separated e.g. Run|Hiking|Cycling.',
            'N': 'ValidationMax: Maximum allowed value (number only).',
            'O': 'Description: Documentation / notes (recommended).',
        }

    def export_hierarchical_view(self, outputpath: Optional[str] = None) -> str:
        df = self._load_hierarchical_data()
        wb = Workbook()
        ws = wb.active
        ws.title = 'HierarchicalView'

        self._setup_headers(ws)
        self._populate_data(ws, df)
        self._add_data_validations(ws)
        self._autosize_columns(ws)

        ws.freeze_panes = 'G3'
        ws.autofilter.ref = f'A2:O{len(df)+2}'

        self._add_help_sheet(wb)

        if not outputpath:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            outputpath = f'structure_hierarchical_v4_{ts}.xlsx'
        wb.save(outputpath)
        return outputpath

    def _load_hierarchical_data(self) -> pd.DataFrame:
        rows: List[Dict] = []
        areasq = self.client.table('areas').select('*').eq('userid', self.userid)
        if self.filterarea:
            areasq = areasq.eq('name', self.filterarea)
        areas = areasq.order('sortorder').execute().data or []

        for area in areas:
            rows.append({
                'Type': 'Area', 'Level': 0, 'SortOrder': area.get('sortorder', 0),
                'Area': area.get('name', ''),
                'CategoryPath': area.get('name', ''),
                'Category': '', 'AttributeName': '', 'DataType': '', 'Unit': '',
                'IsRequired': '',
                'ValidationType': '',
                'DefaultValue': '', 'ValidationMin': '', 'ValidationMax': '',
                'Description': area.get('description', '')
            })
            self._load_categories_recursive(area['id'], area.get('name', ''), rows)

        df = pd.DataFrame(rows)
        if self.filtercategory and not df.empty:
            mask = df['CategoryPath'].str.contains(f' {self.filtercategory}', case=False, na=False, regex=False) | df['CategoryPath'].str.endswith(self.filtercategory, na=False)
            df = df[mask | (df['Type'] == 'Area')]
        return df

    def _load_categories_recursive(self, areaid: str, areaname: str, rows: List[Dict], parentid: Optional[str] = None, parentpath: str = '', level: int = 1):
        q = self.client.table('categories').select('*').eq('userid', self.userid).eq('areaid', areaid).eq('level', level)
        if parentid:
            q = q.eq('parentcategoryid', parentid)
        else:
            q = q.is_('parentcategoryid', 'null')
        cats = q.order('sortorder').execute().data or []

        for cat in cats:
            catpath = f"{parentpath} {cat['name']}" if parentpath else f"{areaname} {cat['name']}"
            rows.append({
                'Type': 'Category', 'Level': level, 'SortOrder': cat.get('sortorder', 0),
                'Area': areaname,
                'CategoryPath': catpath,
                'Category': cat.get('name', ''),
                'AttributeName': '', 'DataType': '', 'Unit': '',
                'IsRequired': '',
                'ValidationType': '',
                'DefaultValue': '', 'ValidationMin': '', 'ValidationMax': '',
                'Description': cat.get('description', '')
            })

            attrs = self.client.table('attributedefinitions').select('*').eq('userid', self.userid).eq('categoryid', cat['id']).order('sortorder').execute().data or []
            for attr in attrs:
                vr = attr.get('validationrules')
                if isinstance(vr, str):
                    try:
                        vr = json.loads(vr)
                    except Exception:
                        vr = {}
                if not isinstance(vr, dict):
                    vr = {}

                datatype = (attr.get('datatype') or 'text').strip()
                vtype = (vr.get('type') or '').strip()

                # Default: suggest for text. Exporter will write 'suggest' even if options are empty.
                if not vtype and datatype == 'text':
                    vtype = 'suggest'

                text_options = ''
                if datatype == 'text':
                    opt_list = vr.get('enum') or vr.get('suggest')
                    if isinstance(opt_list, list):
                        text_options = '|'.join([str(x) for x in opt_list if str(x).strip()])

                valmin = vr.get('min', '')
                valmax = vr.get('max', '')

                rows.append({
                    'Type': 'Attribute', 'Level': level + 1, 'SortOrder': attr.get('sortorder', 0),
                    'Area': areaname,
                    'CategoryPath': catpath,
                    'Category': cat.get('name', ''),
                    'AttributeName': attr.get('name', ''),
                    'DataType': datatype,
                    'Unit': attr.get('unit', ''),
                    'IsRequired': 'TRUE' if attr.get('isrequired', False) else 'FALSE',
                    'ValidationType': vtype,
                    'DefaultValue': attr.get('defaultvalue', ''),
                    'ValidationMin': text_options if datatype == 'text' else valmin,
                    'ValidationMax': '' if datatype == 'text' else valmax,
                    'Description': attr.get('description', ''),
                })

            if level < 10:
                self._load_categories_recursive(areaid, areaname, rows, cat['id'], catpath, level + 1)

    def _setup_headers(self, ws):
        headers = [
            'Type','Level','SortOrder','Area','CategoryPath','Category','AttributeName','DataType','Unit','IsRequired',
            'ValidationType','DefaultValue','ValidationMin','ValidationMax','Description'
        ]
        for colidx, header in enumerate(headers, start=1):
            cell = ws.cell(row=2, column=colidx, value=header)
            cell.font = self.BOLDFONT
            cell.fill = self.HEADERFILL
            cell.alignment = self.CENTERALIGN
            cell.border = self.THINBORDER

        colletters = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O']
        for i, col in enumerate(colletters, start=1):
            if col in self.HEADERCOMMENTS:
                c = ws.cell(row=2, column=i)
                comment = Comment(self.HEADERCOMMENTS[col], 'Events Tracker')
                comment.width = 380
                comment.height = 150
                c.comment = comment

    def _populate_data(self, ws, df: pd.DataFrame):
        for r, row in enumerate(df.itertuples(index=False), start=3):
            values = list(row)
            for c, val in enumerate(values, start=1):
                cell = ws.cell(row=r, column=c, value=val)
                cell.border = self.THINBORDER
                if c in (1,2,4):
                    cell.fill = self.PINKFILL
                    cell.alignment = self.CENTERALIGN if c != 4 else self.LEFTALIGN
                elif c in (3,5):
                    cell.fill = self.YELLOWFILL
                    cell.alignment = self.CENTERALIGN if c == 3 else self.LEFTALIGN
                else:
                    cell.fill = self.BLUEFILL
                    cell.alignment = self.LEFTALIGN if c in (6,7,12,15) else self.CENTERALIGN

            if ws.cell(r, 1).value == 'Area':
                ws.cell(r, 2, 0)
            else:
                levelf = f"=LEN(E{r})-LEN(SUBSTITUTE(E{r},\" \",\"\"))"
                ws.cell(r, 2).value = levelf
                ws.cell(r, 2).fill = self.PINKFILL
                ws.cell(r, 2).alignment = self.CENTERALIGN

            areaf = f"=TRIM(LEFT(E{r},IFERROR(FIND(\" \",E{r})-1,LEN(E{r}))))"
            ws.cell(r, 4).value = areaf
            ws.cell(r, 4).fill = self.PINKFILL
            ws.cell(r, 4).alignment = self.LEFTALIGN

    def _add_data_validations(self, ws):
        maxrow = max(ws.max_row, 100)

        typedv = DataValidation(type='list', formula1='Area,Category,Attribute', allow_blank=False, showDropDown=True)
        ws.add_data_validation(typedv)
        typedv.add(f'A3:A{maxrow}')

        datatypedv = DataValidation(type='list', formula1='number,text,datetime,boolean,link,image', allow_blank=True, showDropDown=True)
        ws.add_data_validation(datatypedv)
        datatypedv.add(f'H3:H{maxrow}')

        requireddv = DataValidation(type='list', formula1='TRUE,FALSE', allow_blank=True, showDropDown=True)
        ws.add_data_validation(requireddv)
        requireddv.add(f'J3:J{maxrow}')

        # Dropdown excludes suggest; suggest is the default.
        vtypedv = DataValidation(type='list', formula1='none,enum', allow_blank=True, showDropDown=True)
        ws.add_data_validation(vtypedv)
        vtypedv.add(f'K3:K{maxrow}')

    def _autosize_columns(self, ws):
        for col in ws.columns:
            col_letter = col[0].column_letter
            maxlen = 0
            for cell in col:
                if cell.value is None:
                    continue
                maxlen = max(maxlen, len(str(cell.value)))
            if col_letter in ('A','B','C','D'):
                ws.column_dimensions[col_letter].width = 10
            else:
                ws.column_dimensions[col_letter].width = min(max(10, maxlen + 2), 60)

    def _add_help_sheet(self, wb: Workbook):
        ws = wb.create_sheet('Help')
        title = 'EVENTS TRACKER - Structure Import/Export Guide (v4)'
        ws.cell(1, 1, title).font = Font(bold=True, size=14, color='FFFFFF')
        ws.cell(1, 1).fill = self.HEADERFILL

        lines = [
            '',
            'NEW IN v4',
            '- ValidationType column (K). Default for text is suggest (even if you do not provide options).',
            '- Dropdown in K offers only: none, enum. (Suggest is default.)',
            '- For text attributes, ValidationMin column (M) can hold TextOptions as pipe-separated list (Run|Hiking|Cycling).',
            '',
            'ValidationType meaning',
            '- suggest: free text allowed; if M has options they can be used as suggestions in UI.',
            '- enum: strict; only values from M are allowed (UI should use dropdown).',
            '- none: no validation/suggestions; free text.',
            '',
            'COLUMN REFERENCE',
            'A - Type',
            'B - Level (auto)',
            'C - SortOrder (key)',
            'D - Area (auto)',
            'E - CategoryPath (key)',
            'F - Category',
            'G - AttributeName',
            'H - DataType',
            'I - Unit',
            'J - IsRequired',
            'K - ValidationType (none/enum; suggest default)',
            'L - DefaultValue',
            'M - ValidationMin (number) OR TextOptions (text)',
            'N - ValidationMax (number)',
            'O - Description',
        ]
        for i, t in enumerate(lines, start=2):
            ws.cell(i, 1, t)
        ws.freeze_panes = 'A2'
        ws.column_dimensions['A'].width = 110
