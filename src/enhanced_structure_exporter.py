"""Enhanced Structure Exporter v4 - FIXED VERSION

FIXES APPLIED (2026-01-23):
- Fixed database naming convention: all table/column names now use snake_case
- Table: attributedefinitions → attribute_definitions  
- Columns: areaid → area_id, categoryid → category_id, sortorder → sort_order, etc.

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
    def __init__(self, client, user_id: str, filter_area: Optional[str] = None, filter_category: Optional[str] = None):
        self.client = client
        self.user_id = user_id
        self.filter_area = filter_area if filter_area != 'All Areas' else None
        self.filter_category = filter_category if filter_category != 'All Categories' else None

        self.PINK_FILL = PatternFill(start_color='FFE6F0', end_color='FFE6F0', fill_type='solid')
        self.BLUE_FILL = PatternFill(start_color='E6F2FF', end_color='E6F2FF', fill_type='solid')
        self.YELLOW_FILL = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
        self.HEADER_FILL = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        self.BOLD_FONT = Font(bold=True, color='FFFFFF')
        self.THIN_BORDER = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000'),
        )
        self.CENTER_ALIGN = Alignment(horizontal='center', vertical='center')
        self.LEFT_ALIGN = Alignment(horizontal='left', vertical='center')

        self.HEADER_COMMENTS = {
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

    def export_hierarchical_view(self, output_path: Optional[str] = None) -> str:
        df = self._load_hierarchical_data()
        wb = Workbook()
        ws = wb.active
        ws.title = 'HierarchicalView'

        self._setup_headers(ws)
        self._populate_data(ws, df)
        self._add_data_validations(ws)
        self._autosize_columns(ws)

        ws.freeze_panes = 'G3'
        ws.auto_filter.ref = f'A2:O{len(df)+2}'

        self._add_help_sheet(wb)

        if not output_path:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'structure_hierarchical_v4_{ts}.xlsx'
        wb.save(output_path)
        return output_path

    def _load_hierarchical_data(self) -> pd.DataFrame:
        """Load hierarchical structure from database using correct snake_case naming."""
        rows: List[Dict] = []
        
        # FIXED: use snake_case column names
        areas_q = self.client.table('areas').select('*').eq('user_id', self.user_id)
        if self.filter_area:
            areas_q = areas_q.eq('name', self.filter_area)
        areas = areas_q.order('sort_order').execute().data or []  # FIXED: sort_order

        for area in areas:
            rows.append({
                'Type': 'Area', 
                'Level': 0, 
                'SortOrder': area.get('sort_order', 0),  # FIXED
                'Area': area.get('name', ''),
                'CategoryPath': area.get('name', ''),
                'Category': '', 
                'AttributeName': '', 
                'DataType': '', 
                'Unit': '',
                'IsRequired': '',
                'ValidationType': '',
                'DefaultValue': '', 
                'ValidationMin': '', 
                'ValidationMax': '',
                'Description': area.get('description', '')
            })
            self._load_categories_recursive(area['id'], area.get('name', ''), rows)

        df = pd.DataFrame(rows)
        if self.filter_category and not df.empty:
            mask = df['CategoryPath'].str.contains(f' {self.filter_category}', case=False, na=False, regex=False) | df['CategoryPath'].str.endswith(self.filter_category, na=False)
            df = df[mask | (df['Type'] == 'Area')]
        return df

    def _load_categories_recursive(self, area_id: str, area_name: str, rows: List[Dict], 
                                    parent_id: Optional[str] = None, parent_path: str = '', level: int = 1):
        """Recursively load categories using correct snake_case naming."""
        # FIXED: use snake_case column names
        q = self.client.table('categories').select('*').eq('user_id', self.user_id).eq('area_id', area_id).eq('level', level)
        if parent_id:
            q = q.eq('parent_category_id', parent_id)  # FIXED
        else:
            q = q.is_('parent_category_id', 'null')  # FIXED
        cats = q.order('sort_order').execute().data or []  # FIXED

        for cat in cats:
            catpath = f"{parent_path} > {cat['name']}" if parent_path else f"{area_name} > {cat['name']}"
            rows.append({
                'Type': 'Category', 
                'Level': level, 
                'SortOrder': cat.get('sort_order', 0),  # FIXED
                'Area': area_name,
                'CategoryPath': catpath,
                'Category': cat.get('name', ''),
                'AttributeName': '', 
                'DataType': '', 
                'Unit': '',
                'IsRequired': '',
                'ValidationType': '',
                'DefaultValue': '', 
                'ValidationMin': '', 
                'ValidationMax': '',
                'Description': cat.get('description', '')
            })

            # FIXED: table name is attribute_definitions
            attrs = self.client.table('attribute_definitions').select('*').eq('user_id', self.user_id).eq('category_id', cat['id']).order('sort_order').execute().data or []
            
            for attr in attrs:
                # FIXED: column is validation_rules
                vr = attr.get('validation_rules')
                if isinstance(vr, str):
                    try:
                        vr = json.loads(vr)
                    except Exception:
                        vr = {}
                if not isinstance(vr, dict):
                    vr = {}

                # FIXED: column is data_type
                datatype = (attr.get('data_type') or 'text').strip()
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
                    'Type': 'Attribute', 
                    'Level': level + 1, 
                    'SortOrder': attr.get('sort_order', 0),  # FIXED
                    'Area': area_name,
                    'CategoryPath': catpath,
                    'Category': cat.get('name', ''),
                    'AttributeName': attr.get('name', ''),
                    'DataType': datatype,
                    'Unit': attr.get('unit', ''),
                    # FIXED: column is is_required
                    'IsRequired': 'TRUE' if attr.get('is_required', False) else 'FALSE',
                    'ValidationType': vtype,
                    # FIXED: column is default_value
                    'DefaultValue': attr.get('default_value', ''),
                    'ValidationMin': text_options if datatype == 'text' else valmin,
                    'ValidationMax': '' if datatype == 'text' else valmax,
                    'Description': attr.get('description', ''),
                })

            if level < 10:
                self._load_categories_recursive(area_id, area_name, rows, cat['id'], catpath, level + 1)

    def _setup_headers(self, ws):
        headers = [
            'Type', 'Level', 'SortOrder', 'Area', 'CategoryPath', 'Category', 'AttributeName', 
            'DataType', 'Unit', 'IsRequired', 'ValidationType', 'DefaultValue', 'ValidationMin', 
            'ValidationMax', 'Description'
        ]
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=2, column=col_idx, value=header)
            cell.font = self.BOLD_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = self.CENTER_ALIGN
            cell.border = self.THIN_BORDER

        col_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
        for i, col in enumerate(col_letters, start=1):
            if col in self.HEADER_COMMENTS:
                c = ws.cell(row=2, column=i)
                comment = Comment(self.HEADER_COMMENTS[col], 'Events Tracker')
                comment.width = 380
                comment.height = 150
                c.comment = comment

    def _populate_data(self, ws, df: pd.DataFrame):
        for r, row in enumerate(df.itertuples(index=False), start=3):
            values = list(row)
            for c, val in enumerate(values, start=1):
                cell = ws.cell(row=r, column=c, value=val)
                cell.border = self.THIN_BORDER
                if c in (1, 2, 4):
                    cell.fill = self.PINK_FILL
                    cell.alignment = self.CENTER_ALIGN if c != 4 else self.LEFT_ALIGN
                elif c in (3, 5):
                    cell.fill = self.YELLOW_FILL
                    cell.alignment = self.CENTER_ALIGN if c == 3 else self.LEFT_ALIGN
                else:
                    cell.fill = self.BLUE_FILL
                    cell.alignment = self.LEFT_ALIGN if c in (6, 7, 12, 15) else self.CENTER_ALIGN

            if ws.cell(r, 1).value == 'Area':
                ws.cell(r, 2, 0)
            else:
                level_formula = f"=LEN(E{r})-LEN(SUBSTITUTE(E{r},\" > \",\"\"))/3"
                ws.cell(r, 2).value = level_formula
                ws.cell(r, 2).fill = self.PINK_FILL
                ws.cell(r, 2).alignment = self.CENTER_ALIGN

            area_formula = f"=TRIM(LEFT(E{r},IFERROR(FIND(\" > \",E{r})-1,LEN(E{r}))))"
            ws.cell(r, 4).value = area_formula
            ws.cell(r, 4).fill = self.PINK_FILL
            ws.cell(r, 4).alignment = self.LEFT_ALIGN

    def _add_data_validations(self, ws):
        maxrow = max(ws.max_row, 100)

        type_dv = DataValidation(type='list', formula1='"Area,Category,Attribute"', allow_blank=False)
        ws.add_data_validation(type_dv)
        type_dv.add(f'A3:A{maxrow}')

        datatype_dv = DataValidation(type='list', formula1='"number,text,datetime,boolean,link,image"', allow_blank=True)
        ws.add_data_validation(datatype_dv)
        datatype_dv.add(f'H3:H{maxrow}')

        required_dv = DataValidation(type='list', formula1='"TRUE,FALSE"', allow_blank=True)
        ws.add_data_validation(required_dv)
        required_dv.add(f'J3:J{maxrow}')

        # Dropdown excludes suggest; suggest is the default.
        vtype_dv = DataValidation(type='list', formula1='"none,enum"', allow_blank=True)
        ws.add_data_validation(vtype_dv)
        vtype_dv.add(f'K3:K{maxrow}')

    def _autosize_columns(self, ws):
        for col in ws.columns:
            col_letter = col[0].column_letter
            maxlen = 0
            for cell in col:
                if cell.value is None:
                    continue
                maxlen = max(maxlen, len(str(cell.value)))
            if col_letter in ('A', 'B', 'C', 'D'):
                ws.column_dimensions[col_letter].width = 10
            else:
                ws.column_dimensions[col_letter].width = min(max(10, maxlen + 2), 60)

    def _add_help_sheet(self, wb: Workbook):
        ws = wb.create_sheet('Help')
        title = 'EVENTS TRACKER - Structure Import/Export Guide (v4 FIXED)'
        ws.cell(1, 1, title).font = Font(bold=True, size=14, color='FFFFFF')
        ws.cell(1, 1).fill = self.HEADER_FILL

        lines = [
            '',
            'FIXED VERSION (2026-01-23)',
            '- Database column names now use snake_case (sort_order, area_id, etc.)',
            '- CategoryPath now uses " > " as separator (with spaces)',
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
            'E - CategoryPath (key) - use " > " separator',
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
