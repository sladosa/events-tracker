"""
Events Tracker - Unified Excel Events I/O Module
=================================================
Created: 2025-01-07 17:00 UTC
Last Modified: 2025-01-07 17:00 UTC
Python: 3.11
Version: 1.0.0

Description:
Unified Excel Export/Import for events with:
- Legend section (attribute definitions) at top
- Split line separator
- Event data section below
- Color coding: PINK (read-only) / BLUE (editable)
- Support for CREATE (empty event_id) and UPDATE (existing event_id)

Excel Format (per Master Plan V2):
┌─────────────────────────────────────────────────────────────────┐
│ TOP SECTION - Attribute Legend (scrollable if many)             │
├─────┬──────────────────┬────────────┬──────┬─────┬─────┬───────┤
│ Col │ Category_Path    │ Attribute  │ Type │ Def │ Min │ Max   │
├─────┴──────────────────┴────────────┴──────┴─────┴─────┴───────┤
│ ═══════════════════ SPLIT LINE ════════════════════════════════│
├─────────────────────────────────────────────────────────────────┤
│ BOTTOM SECTION - Event Data                                     │
├──────────┬────────────┬─────────┬──────────────┬───────┬───────┤
│ event_id │ event_date │ Area    │ Category_Path│comment│ attrs │
└──────────┴────────────┴─────────┴──────────────┴───────┴───────┘

Colors:
🟣 PINK = Read-only (event_id, Area, Category_Path for existing events)
🔵 BLUE = Editable (event_date, comment, attributes, new event rows)

Dependencies: openpyxl, pandas
"""

import io
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd


# ============================================
# CONSTANTS
# ============================================

# Colors
PINK_FILL = PatternFill(start_color="FFE6F0", end_color="FFE6F0", fill_type="solid")  # Read-only
BLUE_FILL = PatternFill(start_color="E6F2FF", end_color="E6F2FF", fill_type="solid")  # Editable
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
LEGEND_HEADER_FILL = PatternFill(start_color="7030A0", end_color="7030A0", fill_type="solid")  # Purple
SPLIT_FILL = PatternFill(start_color="808080", end_color="808080", fill_type="solid")  # Gray

HEADER_FONT = Font(color="FFFFFF", bold=True)
SPLIT_FONT = Font(color="FFFFFF", bold=True)

BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

# Fixed columns (before attributes)
FIXED_COLUMNS = ['event_id', 'event_date', 'Area', 'Category_Path', 'comment']
FIXED_COL_COUNT = len(FIXED_COLUMNS)

# Legend columns
LEGEND_COLUMNS = ['Col', 'Category_Path', 'Attribute', 'Type', 'Default', 'Min', 'Max', 'Unit']


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
    """
    Load categories as dict: category_id -> {name, full_path, area_id, area_name, ...}
    """
    try:
        resp = client.table('categories') \
            .select('id, name, parent_category_id, area_id, level, sort_order') \
            .eq('user_id', user_id) \
            .order('level') \
            .order('sort_order') \
            .execute()
        
        categories = resp.data or []
        cat_dict = {c['id']: c for c in categories}
        
        # Load areas for area_name
        areas = load_areas_dict(client, user_id)
        
        result = {}
        for cat in categories:
            # Build full path
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


def load_attribute_definitions_for_categories(
    client, 
    user_id: str, 
    category_ids: List[str]
) -> List[Dict]:
    """
    Load all attribute definitions for given categories.
    Returns list of dicts with category info included.
    """
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
    client,
    user_id: str,
    category_ids: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> List[Dict]:
    """
    Load events with their attributes for export.
    No pagination - loads all matching events.
    """
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


# ============================================
# EXCEL EXPORT
# ============================================

def create_events_excel(
    events: List[Dict],
    attribute_definitions: List[Dict],
    categories_dict: Dict[str, Dict]
) -> bytes:
    """
    Create Excel file with events in unified format.
    
    Args:
        events: List of event dicts with event_attributes
        attribute_definitions: List of attr def dicts
        categories_dict: Dict of category_id -> {name, full_path, area_name, ...}
    
    Returns:
        Excel file as bytes
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Events"
    
    # Build attribute info: attr_def_id -> {name, category_path, data_type, ...}
    attr_info = {}
    attr_columns = []  # Ordered list of attribute names for columns
    
    for attr_def in attribute_definitions:
        cat_id = attr_def.get('category_id')
        cat_info = categories_dict.get(cat_id, {})
        
        attr_info[attr_def['id']] = {
            'id': attr_def['id'],
            'name': attr_def['name'],
            'category_path': cat_info.get('full_path', 'Unknown'),
            'data_type': attr_def.get('data_type', 'text'),
            'unit': attr_def.get('unit', ''),
            'default_value': attr_def.get('default_value', ''),
            'validation_rules': attr_def.get('validation_rules', {})
        }
        
        # Use unique column name: attr_name (if unique) or category > attr_name
        attr_name = attr_def['name']
        if attr_name not in attr_columns:
            attr_columns.append(attr_name)
    
    # ─────────────────────────────────────────
    # SECTION 1: ATTRIBUTE LEGEND
    # ─────────────────────────────────────────
    
    # Legend header row
    row = 1
    for col_idx, col_name in enumerate(LEGEND_COLUMNS, start=1):
        cell = ws.cell(row=row, column=col_idx, value=col_name)
        cell.fill = LEGEND_HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER
    
    # Legend data rows
    row = 2
    col_letter_start = get_column_letter(FIXED_COL_COUNT + 1)  # First attribute column
    
    for idx, attr_name in enumerate(attr_columns):
        # Find the attr_def for this name
        attr_def = next((ad for ad in attribute_definitions if ad['name'] == attr_name), None)
        if not attr_def:
            continue
        
        info = attr_info.get(attr_def['id'], {})
        validation = info.get('validation_rules', {})
        
        col_letter = get_column_letter(FIXED_COL_COUNT + 1 + idx)
        
        legend_data = [
            col_letter,  # Col
            info.get('category_path', ''),  # Category_Path
            attr_name,  # Attribute
            info.get('data_type', 'text'),  # Type
            info.get('default_value', ''),  # Default
            validation.get('min', ''),  # Min
            validation.get('max', ''),  # Max
            info.get('unit', '')  # Unit
        ]
        
        for col_idx, value in enumerate(legend_data, start=1):
            cell = ws.cell(row=row, column=col_idx, value=value if value else '')
            cell.fill = PINK_FILL  # Legend is read-only
            cell.border = BORDER
            cell.alignment = Alignment(horizontal="left", vertical="center")
        
        row += 1
    
    # ─────────────────────────────────────────
    # SECTION 2: SPLIT LINE
    # ─────────────────────────────────────────
    
    split_row = row
    total_columns = FIXED_COL_COUNT + len(attr_columns)
    
    # Merge cells for split line
    ws.merge_cells(start_row=split_row, start_column=1, end_row=split_row, end_column=max(total_columns, len(LEGEND_COLUMNS)))
    split_cell = ws.cell(row=split_row, column=1, value="═══════════════════ EVENT DATA ═══════════════════")
    split_cell.fill = SPLIT_FILL
    split_cell.font = SPLIT_FONT
    split_cell.alignment = Alignment(horizontal="center", vertical="center")
    
    row += 1
    
    # ─────────────────────────────────────────
    # SECTION 3: EVENT DATA HEADER
    # ─────────────────────────────────────────
    
    data_header_row = row
    all_columns = FIXED_COLUMNS + attr_columns
    
    for col_idx, col_name in enumerate(all_columns, start=1):
        cell = ws.cell(row=row, column=col_idx, value=col_name)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER
    
    row += 1
    
    # ─────────────────────────────────────────
    # SECTION 4: EVENT DATA ROWS
    # ─────────────────────────────────────────
    
    for event in events:
        event_id = event.get('id', '')
        cat_id = event.get('category_id')
        cat_info = categories_dict.get(cat_id, {})
        
        # Build attribute values dict: attr_name -> value
        attr_values = {}
        for ea in event.get('event_attributes', []):
            attr_def_id = ea.get('attribute_definition_id')
            attr_inf = attr_info.get(attr_def_id, {})
            attr_name = attr_inf.get('name')
            
            if attr_name:
                # Get value based on type
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
            event_id,  # event_id (PINK for existing)
            event.get('event_date', ''),  # event_date (BLUE)
            cat_info.get('area_name', ''),  # Area (PINK)
            cat_info.get('full_path', ''),  # Category_Path (PINK)
            event.get('comment', '') or ''  # comment (BLUE)
        ]
        
        # Write fixed columns
        for col_idx, value in enumerate(fixed_data, start=1):
            cell = ws.cell(row=row, column=col_idx, value=value)
            cell.border = BORDER
            cell.alignment = Alignment(horizontal="left", vertical="center")
            
            # Color coding: event_id, Area, Category_Path = PINK; rest = BLUE
            if col_idx in [1, 3, 4]:  # event_id, Area, Category_Path
                cell.fill = PINK_FILL
            else:
                cell.fill = BLUE_FILL
        
        # Attribute columns (BLUE - editable)
        for col_idx, attr_name in enumerate(attr_columns, start=FIXED_COL_COUNT + 1):
            value = attr_values.get(attr_name, '')
            
            cell = ws.cell(row=row, column=col_idx, value=value if value is not None else '')
            cell.fill = BLUE_FILL
            cell.border = BORDER
            
            # Align numbers right
            if isinstance(value, (int, float)):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
        
        row += 1
    
    # ─────────────────────────────────────────
    # COLUMN WIDTHS
    # ─────────────────────────────────────────
    
    # event_id column: narrow (10)
    ws.column_dimensions['A'].width = 10
    
    # Other fixed columns
    ws.column_dimensions['B'].width = 12  # event_date
    ws.column_dimensions['C'].width = 15  # Area
    ws.column_dimensions['D'].width = 30  # Category_Path
    ws.column_dimensions['E'].width = 25  # comment
    
    # Attribute columns: auto-size
    for idx in range(len(attr_columns)):
        col_letter = get_column_letter(FIXED_COL_COUNT + 1 + idx)
        ws.column_dimensions[col_letter].width = 12
    
    # Legend columns width
    legend_widths = [6, 30, 15, 10, 10, 8, 8, 10]
    for idx, width in enumerate(legend_widths):
        col_letter = get_column_letter(idx + 1)
        # Only apply if not already wider
        current = ws.column_dimensions[col_letter].width or 0
        if current < width:
            ws.column_dimensions[col_letter].width = width
    
    # ─────────────────────────────────────────
    # FREEZE PANES (Split between legend and data)
    # ─────────────────────────────────────────
    
    # Freeze at data header row, after fixed columns
    ws.freeze_panes = f"F{data_header_row + 1}"
    
    # ─────────────────────────────────────────
    # HELP SHEET
    # ─────────────────────────────────────────
    
    ws_help = wb.create_sheet("Help")
    _create_help_sheet(ws_help)
    
    # Save to bytes
    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)
    
    return excel_buffer.getvalue()


def _create_help_sheet(ws):
    """Create Help sheet with instructions."""
    instructions = [
        ["EVENTS TRACKER - Excel Export/Import Help"],
        [""],
        ["FILE STRUCTURE:"],
        ["This Excel file has two sections:"],
        ["1. ATTRIBUTE LEGEND (top) - Shows which columns contain which attributes"],
        ["2. EVENT DATA (below split line) - Your actual events"],
        [""],
        ["COLOR CODING:"],
        ["🟣 PINK columns = READ-ONLY (do not edit)"],
        ["   - event_id: Identifies existing events"],
        ["   - Area: Determined by Category"],
        ["   - Category_Path: Cannot change category of existing event"],
        [""],
        ["🔵 BLUE columns = EDITABLE"],
        ["   - event_date: Date of event"],
        ["   - comment: Notes/comments"],
        ["   - Attribute columns: Your data values"],
        [""],
        ["HOW TO EDIT EXISTING EVENTS:"],
        ["1. Find the row with the event you want to edit"],
        ["2. Change values in BLUE columns only"],
        ["3. Save the file"],
        ["4. Import back in Show Events"],
        [""],
        ["HOW TO CREATE NEW EVENTS:"],
        ["1. Add a new row at the bottom"],
        ["2. Leave event_id EMPTY (this signals a new event)"],
        ["3. Fill in event_date (required)"],
        ["4. Fill in Area and Category_Path (must match existing structure)"],
        ["5. Fill in attribute values"],
        ["6. Save and import"],
        [""],
        ["ATTRIBUTE LEGEND EXPLAINED:"],
        ["- Col: Excel column letter for this attribute"],
        ["- Category_Path: Which category this attribute belongs to"],
        ["- Attribute: Name of the attribute"],
        ["- Type: number, text, datetime, boolean"],
        ["- Default: Default value if not specified"],
        ["- Min/Max: Validation rules for numbers"],
        ["- Unit: Unit of measurement (kg, km, etc.)"],
        [""],
        ["IMPORTANT NOTES:"],
        ["⚠️ DO NOT delete rows - use Delete in app instead"],
        ["⚠️ DO NOT change event_id values"],
        ["⚠️ Empty cells = no value (not zero!)"],
        ["⚠️ Attribute columns only apply to their categories"],
        [""],
        ["VALIDATION:"],
        ["- Import will validate all data before applying"],
        ["- You'll see a preview of changes before confirming"],
        ["- Invalid data will be highlighted with error messages"],
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
# EXCEL IMPORT
# ============================================

def parse_events_excel(file_bytes: bytes) -> Tuple[List[Dict], List[Dict], str]:
    """
    Parse Excel file and extract events for import.
    
    Returns:
        Tuple of (events_to_create, events_to_update, error_message)
        - events_to_create: List of new events (empty event_id)
        - events_to_update: List of existing events with changes
        - error_message: Error string if parsing failed, empty if OK
    """
    try:
        wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb.active
        
        # Find split row
        split_row = None
        for row_idx in range(1, ws.max_row + 1):
            cell_value = ws.cell(row=row_idx, column=1).value
            if cell_value and 'EVENT DATA' in str(cell_value):
                split_row = row_idx
                break
        
        if not split_row:
            return [], [], "Could not find EVENT DATA split line. Invalid file format."
        
        # Header row is right after split
        header_row = split_row + 1
        
        # Read headers
        headers = []
        for col_idx in range(1, ws.max_column + 1):
            val = ws.cell(row=header_row, column=col_idx).value
            if val:
                headers.append(str(val).strip())
            else:
                break
        
        if not headers or 'event_id' not in headers:
            return [], [], "Invalid header row. Must contain 'event_id' column."
        
        # Parse data rows
        events_to_create = []
        events_to_update = []
        
        for row_idx in range(header_row + 1, ws.max_row + 1):
            # Check if row is empty
            first_cell = ws.cell(row=row_idx, column=1).value
            second_cell = ws.cell(row=row_idx, column=2).value
            
            # Skip completely empty rows
            if first_cell is None and second_cell is None:
                continue
            
            row_data = {}
            for col_idx, header in enumerate(headers, start=1):
                value = ws.cell(row=row_idx, column=col_idx).value
                row_data[header] = value
            
            event_id = row_data.get('event_id')
            
            # Determine if CREATE or UPDATE
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
    """
    Validate import data and return validated events + errors.
    
    Returns:
        Tuple of (valid_creates, valid_updates, errors)
    """
    errors = []
    valid_creates = []
    valid_updates = []
    
    # Build category lookup by full_path
    cat_by_path = {info['full_path']: cat_id for cat_id, info in categories_dict.items()}
    
    # Build attr def lookup by category_id + name
    attr_by_cat_name = {}
    for attr_def in attribute_definitions:
        key = (attr_def['category_id'], attr_def['name'])
        attr_by_cat_name[key] = attr_def
    
    # Validate creates
    for idx, event in enumerate(events_to_create, start=1):
        event_errors = []
        
        # Required: event_date
        if not event.get('event_date'):
            event_errors.append(f"Row {idx}: event_date is required")
        
        # Required: Category_Path must exist
        cat_path = event.get('Category_Path', '')
        if not cat_path:
            event_errors.append(f"Row {idx}: Category_Path is required")
        elif cat_path not in cat_by_path:
            event_errors.append(f"Row {idx}: Category_Path '{cat_path}' not found")
        
        if event_errors:
            errors.extend(event_errors)
        else:
            # Add category_id
            event['_category_id'] = cat_by_path.get(cat_path)
            valid_creates.append(event)
    
    # Validate updates
    for idx, event in enumerate(events_to_update, start=1):
        event_errors = []
        
        # Required: event_id must be valid UUID format
        event_id = event.get('event_id')
        if not event_id:
            event_errors.append(f"Update row {idx}: event_id is required")
        
        # event_date required
        if not event.get('event_date'):
            event_errors.append(f"Update row {idx}: event_date is required")
        
        if event_errors:
            errors.extend(event_errors)
        else:
            valid_updates.append(event)
    
    return valid_creates, valid_updates, errors


def apply_import_changes(
    client,
    user_id: str,
    events_to_create: List[Dict],
    events_to_update: List[Dict],
    categories_dict: Dict[str, Dict],
    attribute_definitions: List[Dict]
) -> Tuple[int, int, List[str]]:
    """
    Apply import changes to database.
    
    Returns:
        Tuple of (created_count, updated_count, errors)
    """
    created = 0
    updated = 0
    errors = []
    
    # Build attr def lookup
    attr_by_cat_name = {}
    for attr_def in attribute_definitions:
        key = (attr_def['category_id'], attr_def['name'])
        attr_by_cat_name[key] = attr_def
    
    # Process creates
    for event_data in events_to_create:
        try:
            category_id = event_data.get('_category_id')
            
            # Parse event_date
            event_date = event_data.get('event_date')
            if isinstance(event_date, datetime):
                event_date = event_date.date().isoformat()
            elif isinstance(event_date, date):
                event_date = event_date.isoformat()
            else:
                event_date = str(event_date)
            
            # Create event
            new_event = {
                'user_id': user_id,
                'category_id': category_id,
                'event_date': event_date,
                'comment': event_data.get('comment', '') or None
            }
            
            result = client.table('events').insert(new_event).execute()
            event_id = result.data[0]['id']
            
            # Create attributes
            for key, value in event_data.items():
                if key in FIXED_COLUMNS or key.startswith('_'):
                    continue
                if value is None or value == '':
                    continue
                
                # Find attribute definition
                attr_def = attr_by_cat_name.get((category_id, key))
                if not attr_def:
                    continue
                
                # Create event_attribute
                attr_data = {
                    'event_id': event_id,
                    'attribute_definition_id': attr_def['id'],
                    'user_id': user_id
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
    
    # Process updates
    for event_data in events_to_update:
        try:
            event_id = event_data.get('event_id')
            
            # Parse event_date
            event_date = event_data.get('event_date')
            if isinstance(event_date, datetime):
                event_date = event_date.date().isoformat()
            elif isinstance(event_date, date):
                event_date = event_date.isoformat()
            else:
                event_date = str(event_date)
            
            # Update event basic info
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
            
            # Get existing event with category
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
            
            # Update/create attributes
            for key, value in event_data.items():
                if key in FIXED_COLUMNS or key.startswith('_'):
                    continue
                
                # Find attribute definition
                attr_def = attr_by_cat_name.get((category_id, key))
                if not attr_def:
                    continue
                
                attr_def_id = attr_def['id']
                data_type = attr_def.get('data_type', 'text')
                
                # Prepare value
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
                    # Update existing
                    client.table('event_attributes') \
                        .update(attr_update) \
                        .eq('id', existing_attrs[attr_def_id]) \
                        .eq('user_id', user_id) \
                        .execute()
                elif value is not None and value != '':
                    # Create new
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
    client,
    user_id: str,
    category_ids: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Tuple[bytes, int, str]:
    """
    High-level function to export events to Excel.
    
    Args:
        client: Supabase client
        user_id: User ID
        category_ids: Optional list of category IDs to filter
        date_from: Optional start date
        date_to: Optional end date
    
    Returns:
        Tuple of (excel_bytes, event_count, error_message)
    """
    try:
        # Load categories
        categories_dict = load_categories_dict(client, user_id)
        
        # Determine which categories to include
        if category_ids:
            relevant_categories = category_ids
        else:
            relevant_categories = list(categories_dict.keys())
        
        # Load attribute definitions for these categories
        attribute_definitions = load_attribute_definitions_for_categories(
            client, user_id, relevant_categories
        )
        
        # Load events
        events = load_events_for_export(
            client, user_id, 
            category_ids=category_ids,
            date_from=date_from,
            date_to=date_to
        )
        
        if not events:
            return b'', 0, "No events found matching filters"
        
        # Create Excel
        excel_bytes = create_events_excel(events, attribute_definitions, categories_dict)
        
        return excel_bytes, len(events), ""
        
    except Exception as e:
        return b'', 0, f"Export error: {str(e)}"


# ============================================
# HIGH-LEVEL IMPORT FUNCTION
# ============================================

def import_events_from_excel(
    client,
    user_id: str,
    file_bytes: bytes
) -> Tuple[int, int, List[str]]:
    """
    High-level function to import events from Excel.
    
    Returns:
        Tuple of (created_count, updated_count, errors)
    """
    # Parse file
    events_to_create, events_to_update, parse_error = parse_events_excel(file_bytes)
    
    if parse_error:
        return 0, 0, [parse_error]
    
    if not events_to_create and not events_to_update:
        return 0, 0, ["No events found in file"]
    
    # Load reference data
    categories_dict = load_categories_dict(client, user_id)
    
    # Get all category IDs
    all_category_ids = list(categories_dict.keys())
    attribute_definitions = load_attribute_definitions_for_categories(
        client, user_id, all_category_ids
    )
    
    # Validate
    valid_creates, valid_updates, validation_errors = validate_import_data(
        events_to_create, events_to_update, categories_dict, attribute_definitions
    )
    
    if validation_errors:
        return 0, 0, validation_errors
    
    # Apply changes
    created, updated, apply_errors = apply_import_changes(
        client, user_id, valid_creates, valid_updates, 
        categories_dict, attribute_definitions
    )
    
    return created, updated, apply_errors
