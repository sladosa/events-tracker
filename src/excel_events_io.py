"""
Events Tracker - Unified Excel Events I/O Module V2
====================================================
Created: 2025-01-07 17:00 UTC
Last Modified: 2025-01-07 19:30 UTC
Python: 3.11
Version: 2.0.0

Description:
Unified Excel Export/Import for events with enhanced formatting:
- ATTRIBUTE LEGEND section with title, Area column, row grouping by category
- Column grouping for Default/Min/Max/Unit (collapsible)
- EVENT DATA section with title and SUBTOTAL formulas
- Yellow highlighting for non-relevant attributes per row
- AutoFilter on Area, Category_Path, event_date
- Proper freeze panes position
- Color coding: PINK (read-only) / BLUE (editable) / YELLOW (non-relevant)

Excel Format V2:
┌─────────────────────────────────────────────────────────────────┐
│ A1: ATTRIBUTE LEGEND (bold title)                               │
├─────┬──────┬──────────────┬───────────┬──────┬─────┬─────┬─────┤
│ Col │ Area │ Category_Path│ Attribute │ Type │ Def │ Min │ Max │ ← grouped
├─────┴──────┴──────────────┴───────────┴──────┴─────┴─────┴─────┤
│ (rows grouped by category, collapsed by default)                │
├─────────────────────────────────────────────────────────────────┤
│ (empty row)                                                     │
├─────────────────────────────────────────────────────────────────┤
│ EVENT DATA:    Summ (if relevant) ->    [SUBTOTAL formulas]     │
├──────────┬──────┬──────────────┬────────────┬─────────┬─────────┤
│ event_id │ Area │ Category_Path│ event_date │ comment │ attrs.. │
├──────────┼──────┼──────────────┼────────────┼─────────┼─────────┤
│ 🟣uuid   │ 🟣   │ 🟣           │ 🔵date     │ 🔵      │ 🔵/🟡   │
└──────────┴──────┴──────────────┴────────────┴─────────┴─────────┘

Colors:
🟣 PINK = Read-only (event_id, Area, Category_Path)
🔵 BLUE = Editable (event_date, comment, relevant attributes)
🟡 YELLOW = Non-relevant attribute for this event's category

Dependencies: openpyxl, pandas, json
"""

import io
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any, Set
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


# ============================================
# CONSTANTS
# ============================================

# Colors
PINK_FILL = PatternFill(start_color="FFE6F0", end_color="FFE6F0", fill_type="solid")
BLUE_FILL = PatternFill(start_color="E6F2FF", end_color="E6F2FF", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
LEGEND_HEADER_FILL = PatternFill(start_color="7030A0", end_color="7030A0", fill_type="solid")
TITLE_FILL = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")

HEADER_FONT = Font(color="FFFFFF", bold=True)
TITLE_FONT = Font(bold=True, size=12)
NORMAL_FONT = Font()

BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

OUTER_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

# Fixed columns for EVENT DATA (before attributes)
FIXED_COLUMNS = ['event_id', 'Area', 'Category_Path', 'event_date', 'comment']
FIXED_COL_COUNT = len(FIXED_COLUMNS)
PADDING_COLS = 4  # Empty columns after comment for grouping padding

# Legend columns
LEGEND_COLUMNS = ['Col', 'Area', 'Category_Path', 'Attribute', 'Type', 'Default', 'Min', 'Max', 'Unit']


# ============================================
# DATA LOADING HELPERS
# ============================================

def load_areas_dict(client, user_id: str) -> Dict[str, Dict]:
    """Load areas as dict: area_id -> {name, ...}"""
    try:
        resp = client.table('areas') \
            .select('id, name, sort_order') \
            .eq('user_id', user_id) \
            .order('sort_order') \
            .execute()
        return {a['id']: a for a in (resp.data or [])}
    except Exception:
        return {}


def load_categories_dict(client, user_id: str) -> Dict[str, Dict]:
    """Load categories as dict: category_id -> {name, full_path, area_id, area_name, ...}"""
    try:
        resp = client.table('categories') \
            .select('id, name, parent_category_id, area_id, level, sort_order') \
            .eq('user_id', user_id) \
            .order('level') \
            .order('sort_order') \
            .execute()
        
        categories = resp.data or []
        cat_dict = {c['id']: c for c in categories}
        areas = load_areas_dict(client, user_id)
        
        result = {}
        for cat in categories:
            path_parts = []
            current = cat
            while current:
                path_parts.insert(0, current['name'])
                parent_id = current.get('parent_category_id')
                current = cat_dict.get(parent_id) if parent_id else None
            
            area_id = cat.get('area_id')
            area_info = areas.get(area_id, {})
            
            result[cat['id']] = {
                'id': cat['id'],
                'name': cat['name'],
                'full_path': ' > '.join(path_parts),
                'area_id': area_id,
                'area_name': area_info.get('name', 'Unknown'),
                'level': cat.get('level', 1)
            }
        
        return result
    except Exception:
        return {}


def get_category_ids_for_area(client, user_id: str, area_id: str) -> List[str]:
    """Get all category IDs belonging to an area."""
    try:
        resp = client.table('categories') \
            .select('id') \
            .eq('user_id', user_id) \
            .eq('area_id', area_id) \
            .execute()
        return [c['id'] for c in (resp.data or [])]
    except Exception:
        return []


def load_attribute_definitions_for_categories(
    client, user_id: str, category_ids: List[str]
) -> List[Dict]:
    """Load all attribute definitions for given categories."""
    if not category_ids:
        return []
    
    try:
        resp = client.table('attribute_definitions') \
            .select('id, category_id, name, data_type, unit, is_required, default_value, validation_rules, sort_order') \
            .eq('user_id', user_id) \
            .in_('category_id', category_ids) \
            .order('category_id') \
            .order('sort_order') \
            .execute()
        return resp.data or []
    except Exception:
        return []


def load_events_for_export(
    client, user_id: str,
    category_ids: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> List[Dict]:
    """Load events with their attributes for export."""
    try:
        select_fields = 'id, category_id, event_date, comment, event_attributes(id, attribute_definition_id, value_text, value_number, value_datetime, value_boolean)'
        
        query = client.table('events') \
            .select(select_fields) \
            .eq('user_id', user_id)
        
        if category_ids:
            query = query.in_('category_id', category_ids)
        
        if date_from:
            query = query.gte('event_date', date_from.isoformat())
        if date_to:
            query = query.lte('event_date', date_to.isoformat())
        
        query = query.order('event_date', desc=True)
        
        resp = query.execute()
        return resp.data or []
    except Exception:
        return []


def parse_validation_rules(rules) -> Dict:
    """Safely parse validation_rules which can be dict, JSON string, or None."""
    if isinstance(rules, dict):
        return rules
    if isinstance(rules, str):
        try:
            return json.loads(rules)
        except:
            return {}
    return {}


# ============================================
# EXCEL EXPORT V2
# ============================================

def create_events_excel_v2(
    events: List[Dict],
    attribute_definitions: List[Dict],
    categories_dict: Dict[str, Dict]
) -> bytes:
    """Create Excel file with enhanced V2 format."""
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Events"
    
    # Build attribute info and determine columns
    attr_info = {}  # attr_def_id -> {name, category_path, area_name, data_type, ...}
    attr_columns = []  # Ordered list of attribute names
    attr_by_category = {}  # category_id -> set of attr_def_ids
    
    for attr_def in attribute_definitions:
        cat_id = attr_def.get('category_id')
        cat_info = categories_dict.get(cat_id, {})
        validation = parse_validation_rules(attr_def.get('validation_rules'))
        
        attr_info[attr_def['id']] = {
            'id': attr_def['id'],
            'name': attr_def['name'],
            'category_id': cat_id,
            'category_path': cat_info.get('full_path', 'Unknown'),
            'area_name': cat_info.get('area_name', 'Unknown'),
            'data_type': attr_def.get('data_type', 'text'),
            'unit': attr_def.get('unit', ''),
            'default_value': attr_def.get('default_value', ''),
            'min': validation.get('min', ''),
            'max': validation.get('max', '')
        }
        
        attr_name = attr_def['name']
        if attr_name not in attr_columns:
            attr_columns.append(attr_name)
        
        if cat_id not in attr_by_category:
            attr_by_category[cat_id] = set()
        attr_by_category[cat_id].add(attr_def['id'])
    
    # Build category -> attr_names mapping for yellow highlighting
    cat_to_attr_names = {}
    for cat_id, attr_ids in attr_by_category.items():
        cat_to_attr_names[cat_id] = {attr_info[aid]['name'] for aid in attr_ids}
    
    # ─────────────────────────────────────────
    # SECTION 1: ATTRIBUTE LEGEND
    # ─────────────────────────────────────────
    
    row = 1
    
    # Title row
    ws.cell(row=row, column=1, value="ATTRIBUTE LEGEND:").font = TITLE_FONT
    row += 1
    
    # Header row
    legend_header_row = row
    for col_idx, col_name in enumerate(LEGEND_COLUMNS, start=1):
        cell = ws.cell(row=row, column=col_idx, value=col_name)
        cell.fill = LEGEND_HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER
    row += 1
    
    # Legend data rows (grouped by category)
    legend_start_row = row
    current_category = None
    group_start_row = None
    attr_col_start = FIXED_COL_COUNT + PADDING_COLS + 1
    
    for idx, attr_name in enumerate(attr_columns):
        attr_def = next((ad for ad in attribute_definitions if ad['name'] == attr_name), None)
        if not attr_def:
            continue
        
        info = attr_info.get(attr_def['id'], {})
        col_letter = get_column_letter(attr_col_start + idx)
        
        # Check if category changed (for row grouping)
        cat_path = info.get('category_path', '')
        if current_category != cat_path:
            # End previous group
            if group_start_row and row > group_start_row + 1:
                ws.row_dimensions.group(group_start_row, row - 1, hidden=True, outline_level=1)
            current_category = cat_path
            group_start_row = row
        
        legend_data = [
            col_letter,
            info.get('area_name', ''),
            cat_path,
            attr_name,
            info.get('data_type', 'text'),
            info.get('default_value', ''),
            info.get('min', ''),
            info.get('max', ''),
            info.get('unit', '')
        ]
        
        for col_idx, value in enumerate(legend_data, start=1):
            cell = ws.cell(row=row, column=col_idx, value=value if value else '')
            cell.fill = PINK_FILL
            cell.border = BORDER
            cell.alignment = Alignment(horizontal="left", vertical="center")
        
        row += 1
    
    # Close last group
    if group_start_row and row > group_start_row + 1:
        ws.row_dimensions.group(group_start_row, row - 1, hidden=True, outline_level=1)
    
    legend_end_row = row - 1
    
    # Column grouping for Default, Min, Max, Unit (columns 6-9)
    ws.column_dimensions.group('F', 'I', hidden=False, outline_level=1)
    
    # ─────────────────────────────────────────
    # EMPTY ROW
    # ─────────────────────────────────────────
    row += 1
    
    # ─────────────────────────────────────────
    # SECTION 2: EVENT DATA
    # ─────────────────────────────────────────
    
    # Title row with SUBTOTAL placeholders
    event_title_row = row
    ws.cell(row=row, column=1, value="EVENT DATA:").font = TITLE_FONT
    ws.cell(row=row, column=3, value="Summ (if relevant) ->").alignment = Alignment(horizontal="right")
    
    # SUBTOTAL formulas will be added after we know the data range
    row += 1
    
    # Header row
    event_header_row = row
    all_columns = FIXED_COLUMNS + [''] * PADDING_COLS + attr_columns
    
    for col_idx, col_name in enumerate(all_columns, start=1):
        cell = ws.cell(row=row, column=col_idx, value=col_name)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER
    
    row += 1
    event_data_start_row = row
    
    # ─────────────────────────────────────────
    # EVENT DATA ROWS
    # ─────────────────────────────────────────
    
    for event in events:
        event_id = event.get('id', '')
        cat_id = event.get('category_id')
        cat_info = categories_dict.get(cat_id, {})
        
        # Get set of relevant attribute names for this event's category
        relevant_attrs = cat_to_attr_names.get(cat_id, set())
        
        # Build attribute values dict
        attr_values = {}
        for ea in event.get('event_attributes', []):
            attr_def_id = ea.get('attribute_definition_id')
            attr_inf = attr_info.get(attr_def_id, {})
            attr_name = attr_inf.get('name')
            
            if attr_name:
                value = None
                if ea.get('value_number') is not None:
                    value = ea['value_number']
                elif ea.get('value_boolean') is not None:
                    value = ea['value_boolean']
                elif ea.get('value_datetime'):
                    value = ea['value_datetime']
                elif ea.get('value_text'):
                    value = ea['value_text']
                attr_values[attr_name] = value
        
        # Fixed columns
        fixed_data = [
            event_id,
            cat_info.get('area_name', ''),
            cat_info.get('full_path', ''),
            event.get('event_date', ''),
            event.get('comment', '') or ''
        ]
        
        # Write fixed columns
        for col_idx, value in enumerate(fixed_data, start=1):
            cell = ws.cell(row=row, column=col_idx, value=value)
            cell.border = BORDER
            cell.alignment = Alignment(horizontal="left", vertical="center")
            
            # Color: event_id, Area, Category_Path = PINK; event_date, comment = BLUE
            if col_idx <= 3:
                cell.fill = PINK_FILL
            else:
                cell.fill = BLUE_FILL
        
        # Padding columns (empty, outer border only for comment block)
        for padding_idx in range(PADDING_COLS):
            col_idx = FIXED_COL_COUNT + 1 + padding_idx
            cell = ws.cell(row=row, column=col_idx, value='')
            cell.fill = BLUE_FILL
            # Only outer borders for the comment+padding block
            if padding_idx == PADDING_COLS - 1:
                cell.border = Border(right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        
        # Attribute columns
        for attr_idx, attr_name in enumerate(attr_columns):
            col_idx = attr_col_start + attr_idx
            value = attr_values.get(attr_name, '')
            
            cell = ws.cell(row=row, column=col_idx, value=value if value is not None else '')
            cell.border = BORDER
            
            # Color: YELLOW if not relevant, BLUE if relevant
            if attr_name in relevant_attrs:
                cell.fill = BLUE_FILL
            else:
                cell.fill = YELLOW_FILL
            
            if isinstance(value, (int, float)):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
        
        row += 1
    
    event_data_end_row = row - 1
    
    # ─────────────────────────────────────────
    # SUBTOTAL FORMULAS
    # ─────────────────────────────────────────
    
    for attr_idx, attr_name in enumerate(attr_columns):
        # Find attr_def to check if it's a number type
        attr_def = next((ad for ad in attribute_definitions if ad['name'] == attr_name), None)
        if attr_def and attr_def.get('data_type') == 'number':
            col_idx = attr_col_start + attr_idx
            col_letter = get_column_letter(col_idx)
            
            # SUBTOTAL(9, range) = SUM that respects filters
            formula = f"=SUBTOTAL(9,{col_letter}{event_data_start_row}:{col_letter}{event_data_end_row})"
            cell = ws.cell(row=event_title_row, column=col_idx, value=formula)
            cell.alignment = Alignment(horizontal="right")
    
    # ─────────────────────────────────────────
    # AUTOFILTER
    # ─────────────────────────────────────────
    
    # AutoFilter on header row, columns A through last column
    last_col = len(all_columns)
    ws.auto_filter.ref = f"A{event_header_row}:{get_column_letter(last_col)}{event_data_end_row}"
    
    # ─────────────────────────────────────────
    # FREEZE PANES
    # ─────────────────────────────────────────
    
    # Freeze below header row, after event_date column (E = column 5)
    ws.freeze_panes = f"E{event_data_start_row}"
    
    # ─────────────────────────────────────────
    # COLUMN WIDTHS
    # ─────────────────────────────────────────
    
    ws.column_dimensions['A'].width = 10  # event_id (narrow)
    ws.column_dimensions['B'].width = 12  # Area
    ws.column_dimensions['C'].width = 30  # Category_Path
    ws.column_dimensions['D'].width = 12  # event_date
    ws.column_dimensions['E'].width = 30  # comment
    
    # Padding columns
    for i in range(PADDING_COLS):
        ws.column_dimensions[get_column_letter(FIXED_COL_COUNT + 1 + i)].width = 3
    
    # Attribute columns
    for idx in range(len(attr_columns)):
        col_letter = get_column_letter(attr_col_start + idx)
        ws.column_dimensions[col_letter].width = 12
    
    # Legend columns widths
    legend_widths = {'A': 6, 'B': 12, 'C': 30, 'D': 15, 'E': 10, 'F': 10, 'G': 8, 'H': 8, 'I': 10}
    for col, width in legend_widths.items():
        current = ws.column_dimensions[col].width or 0
        if current < width:
            ws.column_dimensions[col].width = width
    
    # ─────────────────────────────────────────
    # HELP SHEET
    # ─────────────────────────────────────────
    
    ws_help = wb.create_sheet("Help")
    _create_help_sheet_v2(ws_help)
    
    # Save
    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)
    
    return excel_buffer.getvalue()


def _create_help_sheet_v2(ws):
    """Create Help sheet with V2 instructions."""
    instructions = [
        ["EVENTS TRACKER - Excel Export/Import Help V2"],
        [""],
        ["FILE STRUCTURE:"],
        ["This Excel file has two main sections:"],
        [""],
        ["1. ATTRIBUTE LEGEND (top)"],
        ["   - Shows all attributes with their properties"],
        ["   - Rows are grouped by category (click +/- to expand/collapse)"],
        ["   - Columns Default/Min/Max/Unit can be collapsed (click +/-)"],
        ["   - Col column shows which Excel column contains this attribute"],
        [""],
        ["2. EVENT DATA (below)"],
        ["   - Your actual events"],
        ["   - Has AutoFilter enabled - click column headers to filter"],
        ["   - Title row shows SUMs for numeric columns (respects filters)"],
        [""],
        ["COLOR CODING:"],
        [""],
        ["🟣 PINK = READ-ONLY (do not edit)"],
        ["   - event_id: Identifies existing events"],
        ["   - Area: Determined by Category"],
        ["   - Category_Path: Cannot change category of existing event"],
        [""],
        ["🔵 BLUE = EDITABLE"],
        ["   - event_date: Date of event (YYYY-MM-DD)"],
        ["   - comment: Notes/comments"],
        ["   - Attribute columns relevant for this event's category"],
        [""],
        ["🟡 YELLOW = NOT RELEVANT"],
        ["   - Attribute belongs to a different category"],
        ["   - Values here will be ignored on import"],
        ["   - Helps you see which columns matter for each event"],
        [""],
        ["HOW TO EDIT EXISTING EVENTS:"],
        ["1. Find the row with the event you want to edit"],
        ["2. Change values in BLUE columns only"],
        ["3. Save the file"],
        ["4. Import back in Show Events"],
        [""],
        ["HOW TO CREATE NEW EVENTS:"],
        ["1. Add a new row at the bottom of EVENT DATA"],
        ["2. Leave event_id EMPTY (this signals a new event)"],
        ["3. Fill in Area and Category_Path (must match existing structure)"],
        ["4. Fill in event_date (required, format: YYYY-MM-DD)"],
        ["5. Fill in attribute values (only relevant columns)"],
        ["6. Save and import"],
        [""],
        ["TIPS:"],
        ["- Use AutoFilter to show only specific categories or dates"],
        ["- Collapse ATTRIBUTE LEGEND groups to see more EVENT DATA"],
        ["- SUM row updates automatically when you filter"],
        ["- Yellow cells can be left empty - they're not for this category"],
        [""],
        ["IMPORTANT NOTES:"],
        ["⚠️ DO NOT delete rows - use Delete in app instead"],
        ["⚠️ DO NOT change event_id values"],
        ["⚠️ Empty cells = no value (not zero!)"],
    ]
    
    for row_idx, row_data in enumerate(instructions, start=1):
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            if row_idx == 1:
                cell.font = Font(bold=True, size=14)
            elif value and value.endswith(':') and not value.startswith(' '):
                cell.font = Font(bold=True, size=11)
    
    ws.column_dimensions['A'].width = 70


# ============================================
# EXCEL IMPORT (unchanged from V1)
# ============================================

def parse_events_excel(file_bytes: bytes) -> Tuple[List[Dict], List[Dict], str]:
    """Parse Excel file and extract events for import."""
    try:
        wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb.active
        
        # Find EVENT DATA section
        event_data_row = None
        for row_idx in range(1, min(ws.max_row + 1, 200)):
            cell_value = ws.cell(row=row_idx, column=1).value
            if cell_value and 'EVENT DATA' in str(cell_value):
                event_data_row = row_idx
                break
        
        if not event_data_row:
            return [], [], "Could not find EVENT DATA section. Invalid file format."
        
        # Header row is next row after EVENT DATA title
        header_row = event_data_row + 1
        
        # Read headers
        headers = []
        for col_idx in range(1, ws.max_column + 1):
            val = ws.cell(row=header_row, column=col_idx).value
            if val and str(val).strip():
                headers.append(str(val).strip())
            elif not val:
                headers.append(f'_empty_{col_idx}')  # Placeholder for empty columns
        
        if 'event_id' not in headers:
            return [], [], "Invalid header row. Must contain 'event_id' column."
        
        # Parse data rows
        events_to_create = []
        events_to_update = []
        
        for row_idx in range(header_row + 1, ws.max_row + 1):
            first_cell = ws.cell(row=row_idx, column=1).value
            
            # Check for Area in column 2 to detect data rows
            area_cell = ws.cell(row=row_idx, column=2).value
            if not area_cell:
                continue
            
            row_data = {}
            for col_idx, header in enumerate(headers, start=1):
                if header.startswith('_empty_'):
                    continue
                value = ws.cell(row=row_idx, column=col_idx).value
                row_data[header] = value
            
            event_id = row_data.get('event_id')
            
            if event_id is None or str(event_id).strip() == '':
                events_to_create.append(row_data)
            else:
                events_to_update.append(row_data)
        
        return events_to_create, events_to_update, ""
        
    except Exception as e:
        return [], [], f"Error parsing Excel file: {str(e)}"


def validate_import_data(
    events_to_create: List[Dict],
    events_to_update: List[Dict],
    categories_dict: Dict[str, Dict],
    attribute_definitions: List[Dict]
) -> Tuple[List[Dict], List[Dict], List[str]]:
    """Validate import data and return validated events + errors."""
    errors = []
    valid_creates = []
    valid_updates = []
    
    cat_by_path = {info['full_path']: cat_id for cat_id, info in categories_dict.items()}
    
    attr_by_cat_name = {}
    for attr_def in attribute_definitions:
        key = (attr_def['category_id'], attr_def['name'])
        attr_by_cat_name[key] = attr_def
    
    for idx, event in enumerate(events_to_create, start=1):
        event_errors = []
        
        if not event.get('event_date'):
            event_errors.append(f"Row {idx}: event_date is required")
        
        cat_path = event.get('Category_Path', '')
        if not cat_path:
            event_errors.append(f"Row {idx}: Category_Path is required")
        elif cat_path not in cat_by_path:
            event_errors.append(f"Row {idx}: Category_Path '{cat_path}' not found")
        
        if event_errors:
            errors.extend(event_errors)
        else:
            event['_category_id'] = cat_by_path.get(cat_path)
            valid_creates.append(event)
    
    for idx, event in enumerate(events_to_update, start=1):
        event_errors = []
        
        event_id = event.get('event_id')
        if not event_id:
            event_errors.append(f"Update row {idx}: event_id is required")
        
        if not event.get('event_date'):
            event_errors.append(f"Update row {idx}: event_date is required")
        
        if event_errors:
            errors.extend(event_errors)
        else:
            valid_updates.append(event)
    
    return valid_creates, valid_updates, errors


def apply_import_changes(
    client, user_id: str,
    events_to_create: List[Dict],
    events_to_update: List[Dict],
    categories_dict: Dict[str, Dict],
    attribute_definitions: List[Dict]
) -> Tuple[int, int, List[str]]:
    """Apply import changes to database."""
    created = 0
    updated = 0
    errors = []
    
    attr_by_cat_name = {}
    for attr_def in attribute_definitions:
        key = (attr_def['category_id'], attr_def['name'])
        attr_by_cat_name[key] = attr_def
    
    for event_data in events_to_create:
        try:
            category_id = event_data.get('_category_id')
            
            event_date = event_data.get('event_date')
            if isinstance(event_date, datetime):
                event_date = event_date.date().isoformat()
            elif isinstance(event_date, date):
                event_date = event_date.isoformat()
            else:
                event_date = str(event_date)
            
            new_event = {
                'user_id': user_id,
                'category_id': category_id,
                'event_date': event_date,
                'comment': event_data.get('comment', '') or None
            }
            
            result = client.table('events').insert(new_event).execute()
            event_id = result.data[0]['id']
            
            for key, value in event_data.items():
                if key in FIXED_COLUMNS or key.startswith('_') or not value:
                    continue
                
                attr_def = attr_by_cat_name.get((category_id, key))
                if not attr_def:
                    continue
                
                attr_data = {
                    'event_id': event_id,
                    'attribute_definition_id': attr_def['id'],
                    'user_id': user_id,
                    'value_text': None,
                    'value_number': None,
                    'value_datetime': None,
                    'value_boolean': None
                }
                
                data_type = attr_def.get('data_type', 'text')
                if data_type == 'number':
                    attr_data['value_number'] = float(value) if value else None
                elif data_type == 'boolean':
                    attr_data['value_boolean'] = bool(value)
                elif data_type == 'datetime':
                    attr_data['value_datetime'] = str(value)
                else:
                    attr_data['value_text'] = str(value)
                
                client.table('event_attributes').insert(attr_data).execute()
            
            created += 1
            
        except Exception as e:
            errors.append(f"Error creating event: {str(e)}")
    
    for event_data in events_to_update:
        try:
            event_id = event_data.get('event_id')
            
            event_date = event_data.get('event_date')
            if isinstance(event_date, datetime):
                event_date = event_date.date().isoformat()
            elif isinstance(event_date, date):
                event_date = event_date.isoformat()
            else:
                event_date = str(event_date)
            
            updates = {
                'event_date': event_date,
                'comment': event_data.get('comment', '') or None,
                'edited_at': datetime.now().isoformat()
            }
            
            client.table('events') \
                .update(updates) \
                .eq('id', event_id) \
                .eq('user_id', user_id) \
                .execute()
            
            select_fields = 'id, category_id, event_attributes(id, attribute_definition_id)'
            existing = client.table('events') \
                .select(select_fields) \
                .eq('id', event_id) \
                .eq('user_id', user_id) \
                .single() \
                .execute()
            
            if not existing.data:
                errors.append(f"Event {event_id} not found")
                continue
            
            category_id = existing.data.get('category_id')
            existing_attrs = {
                ea['attribute_definition_id']: ea['id']
                for ea in existing.data.get('event_attributes', [])
            }
            
            for key, value in event_data.items():
                if key in FIXED_COLUMNS or key.startswith('_'):
                    continue
                
                attr_def = attr_by_cat_name.get((category_id, key))
                if not attr_def:
                    continue
                
                attr_def_id = attr_def['id']
                data_type = attr_def.get('data_type', 'text')
                
                attr_update = {
                    'value_text': None,
                    'value_number': None,
                    'value_datetime': None,
                    'value_boolean': None
                }
                
                if value is not None and value != '':
                    if data_type == 'number':
                        attr_update['value_number'] = float(value)
                    elif data_type == 'boolean':
                        attr_update['value_boolean'] = bool(value)
                    elif data_type == 'datetime':
                        attr_update['value_datetime'] = str(value)
                    else:
                        attr_update['value_text'] = str(value)
                
                if attr_def_id in existing_attrs:
                    client.table('event_attributes') \
                        .update(attr_update) \
                        .eq('id', existing_attrs[attr_def_id]) \
                        .eq('user_id', user_id) \
                        .execute()
                elif value is not None and value != '':
                    attr_update['event_id'] = event_id
                    attr_update['attribute_definition_id'] = attr_def_id
                    attr_update['user_id'] = user_id
                    client.table('event_attributes').insert(attr_update).execute()
            
            updated += 1
            
        except Exception as e:
            errors.append(f"Error updating event {event_data.get('event_id')}: {str(e)}")
    
    return created, updated, errors


# ============================================
# HIGH-LEVEL EXPORT FUNCTION
# ============================================

def export_events_to_excel(
    client, user_id: str,
    area_id: Optional[str] = None,
    category_ids: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Tuple[bytes, int, str]:
    """High-level function to export events to Excel V2 format."""
    try:
        categories_dict = load_categories_dict(client, user_id)
        
        # Determine effective category_ids
        effective_category_ids = category_ids
        
        if not effective_category_ids and area_id:
            # Get all categories for this area
            effective_category_ids = get_category_ids_for_area(client, user_id, area_id)
            if not effective_category_ids:
                return b'', 0, "No categories found for selected area"
        
        if not effective_category_ids:
            # No filter - get all categories
            effective_category_ids = list(categories_dict.keys())
        
        attribute_definitions = load_attribute_definitions_for_categories(
            client, user_id, effective_category_ids
        )
        
        events = load_events_for_export(
            client, user_id,
            category_ids=effective_category_ids,
            date_from=date_from,
            date_to=date_to
        )
        
        if not events:
            return b'', 0, "No events found matching filters"
        
        excel_bytes = create_events_excel_v2(events, attribute_definitions, categories_dict)
        
        return excel_bytes, len(events), ""
        
    except Exception as e:
        return b'', 0, f"Export error: {str(e)}"


# ============================================
# HIGH-LEVEL IMPORT FUNCTION
# ============================================

def import_events_from_excel(
    client, user_id: str, file_bytes: bytes
) -> Tuple[int, int, List[str]]:
    """High-level function to import events from Excel."""
    events_to_create, events_to_update, parse_error = parse_events_excel(file_bytes)
    
    if parse_error:
        return 0, 0, [parse_error]
    
    if not events_to_create and not events_to_update:
        return 0, 0, ["No events found in file"]
    
    categories_dict = load_categories_dict(client, user_id)
    all_category_ids = list(categories_dict.keys())
    attribute_definitions = load_attribute_definitions_for_categories(
        client, user_id, all_category_ids
    )
    
    valid_creates, valid_updates, validation_errors = validate_import_data(
        events_to_create, events_to_update, categories_dict, attribute_definitions
    )
    
    if validation_errors:
        return 0, 0, validation_errors
    
    created, updated, apply_errors = apply_import_changes(
        client, user_id, valid_creates, valid_updates,
        categories_dict, attribute_definitions
    )
    
    return created, updated, apply_errors
