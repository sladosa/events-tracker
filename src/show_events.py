"""
Events Tracker - Show Events Module
====================================
Created: 2025-12-15 09:45 UTC
Last Modified: 2025-01-13 15:05 UTC
Python: 3.11
Version: 2.6.2 - UX Improvements

Description:
View, edit, and delete events with:
- Table view using st.dataframe with native row selection
- Filter by Area + Category drill-down + Date range + Sort order
- Toolbar actions (Edit/Delete/Export/Import) above table
- Downstream category filter (includes all sub-categories)
- Bulk delete with row selection
- Category_Path display (ISV-style)
- Attribute value formatting by type
- Excel Export/Import with unified format (Master Plan V2)

CHANGELOG v2.6.2:
- 🎯 IMPROVED: Parent-child sorting in UI
  - Events with same timestamp now properly grouped
  - Parent category (e.g., Cardio) ALWAYS appears above child (e.g., Running)
  - Added tertiary sort by category.level (ascending)
  - Much cleaner visual grouping of multi-level activities ✅

CHANGELOG v2.6.1:
- 🐛 FIXED: Export UI cleanup after actions
  - Clear export state after Edit/Delete/Import/Filter changes
  - Prevents stale "Export ready" messages from persisting
  - Added clear_export_state() helper function
- ✨ NEW: Sort order selection (Newest first ⬇️ / Oldest first ⬆️)
  - User can choose sort direction in filters
  - Sorts by event_date → session_start
  - Useful for viewing activity sessions chronologically

CHANGELOG v2.6.0:
- ✨ NEW: Bootstrap system integration
  - Auto-creates default structure if empty database
  - Eliminates empty database UX catch-22
  - Seamless first-time user experience

CHANGELOG v2.5.2:
- ✅ NEW: Display validation warnings from Excel import
- ✅ NEW: Check if legend columns exist in EVENT DATA
- ✅ NEW: Warning for orphan columns not in legend
- 🎯 IMPROVED: Better error handling for malformed Excel files

CHANGELOG v2.5.0:
- 📥 NEW: Export to Excel button - exports filtered events with attribute legend
- 📤 NEW: Import from Excel button - create/update events from Excel
- 📋 NEW: Unified Excel format with legend section + event data
- 🎨 NEW: Color-coded Excel (PINK=read-only, BLUE=editable)
- ✨ NEW: Support for CREATE (empty event_id) and UPDATE (existing event_id)

CHANGELOG v2.4.1:
- 🐛 CRITICAL FIX: Attributes now load correctly in table and edit view!
  - ROOT CAUSE: Multiline SELECT string broke PostgREST nested query parsing
  - Nested select with newlines/whitespace was silently failing
  - SOLUTION: Changed to single-line select string format
  - Both main query and single-event query fixed

CHANGELOG v2.4.0:
- 🎯 T2.2 FIX: Edit modal now shows ALL defined attributes (not just saved ones)
- ➕ NEW: Can add attribute values that weren't set when event was created
- 🗑️ T1 CLEANUP: Removed icon from Areas (simplified display)
- 🔧 NEW: create_event_attribute() function for inserting new attribute values

CHANGELOG v2.3.0:
- 🎯 NEW: Native row selection (st.dataframe selection_mode) - much more responsive!
- 🗑️ REMOVED: Checkbox column (replaced by row selection)
- 🗑️ REMOVED: Select All/Clear buttons (use Shift+Click for range selection)
- 🔧 FIX: Selection now clears when filter changes
- 📋 IMPROVED: Selection count always in sync with table

CHANGELOG v2.2.0:
- 🔧 FIX P1: Area/Category filter now done in SQL (not Python after pagination)
- 🔧 FIX P2: Added Select All/Clear buttons for better selection UX
- 🗑️ FIX P3: Removed View button (redundant with Edit)
- 🔧 FIX P4: Multi-event navigation now sorted by date (newest first)
- ⚠️ FIX P5: Warning for large datasets (>100 events)
- 📋 IMPROVED: Selection preserved across pages

CHANGELOG v2.1.0:
- 🎯 NEW: Toolbar with View/Edit/Delete above table (replaces per-row actions)
- 🌳 NEW: Downstream category filter (shows events from all sub-categories)
- 🗑️ REMOVED: Refresh button (actions auto-refresh)
- 🗑️ REMOVED: Per-row action buttons below table
- 🔄 IMPROVED: Single/multi-event navigation for View/Edit
- 📱 IMPROVED: Cleaner UI with less scrolling

CHANGELOG v2.0.0:
- 🎨 NEW: Table view with st.dataframe (replaces expanders)
- 📊 NEW: Category_Path column (full hierarchy path)
- 🎯 NEW: Attribute preview with smart formatting by type
- ☑️ NEW: Checkbox column for bulk operations
- 📑 NEW: Sortable by date (newest first default)

Dependencies: streamlit, datetime, supabase, pandas, excel_events_io
"""

import streamlit as st
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import time as time_module  # For sleep in bootstrap

# Import bootstrap function
from src.interactive_structure_viewer import create_bootstrap_structure

# Import Excel I/O module
from src.excel_events_io import (
    export_events_to_excel,
    import_events_from_excel,
    parse_events_excel_v2,  # Use V2 for legend-based mapping
    validate_import_data,
    apply_import_changes,
    load_categories_dict,
    load_attribute_definitions_for_categories
)


# ============================================
# CONSTANTS
# ============================================

EVENTS_PER_PAGE = 20


# ============================================
# HELPER FUNCTIONS
# ============================================

def clear_export_state():
    """
    Clear export state after actions.
    
    V2.5.3: Prevents stale export UI from remaining visible after
    Edit, Delete, Import, or Filter changes.
    """
    st.session_state.se_export_data = None
    st.session_state.se_export_filename = None
    st.session_state.se_export_count = None


# ============================================
# DATA LOADING FUNCTIONS
# ============================================

def load_areas(client, user_id: str) -> List[Dict]:
    """Load all areas for user."""
    try:
        resp = client.table('areas') \
            .select('id, name, sort_order') \
            .eq('user_id', user_id) \
            .order('sort_order') \
            .execute()
        return resp.data or []
    except Exception:
        return []


def load_all_categories_with_paths(client, user_id: str) -> Dict[str, Dict]:
    """
    Load all categories with full path information.
    Returns dict: category_id -> {name, full_path, area_id, level}
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
        
        result = {}
        for cat in categories:
            path_parts = []
            current = cat
            while current:
                path_parts.insert(0, current['name'])
                parent_id = current.get('parent_category_id')
                current = cat_dict.get(parent_id) if parent_id else None
            
            result[cat['id']] = {
                'name': cat['name'],
                'full_path': ' > '.join(path_parts),
                'area_id': cat.get('area_id'),
                'level': cat.get('level', 1)
            }
        
        return result
        
    except Exception:
        return {}


def load_categories_for_area(client, user_id: str, area_id: str) -> List[Dict]:
    """Load categories for a specific area with hierarchy info."""
    try:
        resp = client.table('categories') \
            .select('id, name, parent_category_id, level, sort_order') \
            .eq('user_id', user_id) \
            .eq('area_id', area_id) \
            .order('level') \
            .order('sort_order') \
            .execute()
        
        categories = resp.data or []
        cat_dict = {c['id']: c for c in categories}
        
        result = []
        for cat in categories:
            path_parts = []
            current = cat
            while current:
                path_parts.insert(0, current['name'])
                parent_id = current.get('parent_category_id')
                current = cat_dict.get(parent_id) if parent_id else None
            
            result.append({
                'id': cat['id'],
                'name': cat['name'],
                'level': cat['level'],
                'full_path': ' > '.join(path_parts),
                'parent_category_id': cat.get('parent_category_id')
            })
        
        result.sort(key=lambda x: x['full_path'])
        return result
        
    except Exception:
        return []


def get_downstream_category_ids(all_categories: Dict[str, Dict], category_id: str) -> List[str]:
    """
    Get all downstream category IDs (the category itself + all descendants).
    
    Args:
        all_categories: Dict from load_all_categories_with_paths (id -> {name, full_path, area_id})
        category_id: The parent category ID to start from
        
    Returns:
        List of category IDs including the parent and all descendants
    """
    if not category_id or category_id not in all_categories:
        return [category_id] if category_id else []
    
    # Get the path of selected category
    selected_path = all_categories[category_id].get('full_path', '')
    
    # Find all categories whose path starts with selected path
    result = []
    for cat_id, cat_info in all_categories.items():
        cat_path = cat_info.get('full_path', '')
        # Include if path starts with selected path (same or descendant)
        if cat_path == selected_path or cat_path.startswith(selected_path + ' > '):
            result.append(cat_id)
    
    return result


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


def load_events_with_attributes(
    client, 
    user_id: str, 
    area_id: Optional[str] = None,
    category_ids: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    offset: int = 0,
    limit: int = EVENTS_PER_PAGE,
    sort_order: str = 'desc'  # V2.5.3: 'desc' = newest first, 'asc' = oldest first
) -> Tuple[List[Dict], int]:
    """
    Load events with their attributes for table display.
    
    Args:
        area_id: Filter by area (converted to category_ids internally)
        category_ids: List of category IDs to filter (supports downstream filtering)
        sort_order: 'desc' for newest first (default), 'asc' for oldest first
    
    Returns:
        Tuple of (events list with attributes, total count)
    
    v2.5.3: Added sort_order parameter for flexible sorting
    v2.2.0: Fixed filtering - now done in SQL query, not Python (P1 fix)
    """
    try:
        # Resolve area_id to category_ids if needed
        effective_category_ids = category_ids
        if area_id and not category_ids:
            # Get all categories for this area
            effective_category_ids = get_category_ids_for_area(client, user_id, area_id)
            if not effective_category_ids:
                # No categories in this area = no events
                return [], 0
        
        # Build base query - include attributes in join
        # NOTE: Nested select must be on single line - multiline breaks PostgREST
        # V2.5.5: Added categories.level for proper parent-child sorting
        select_fields = 'id, category_id, event_date, session_start, comment, created_at, categories(id, name, area_id, level), event_attributes(id, value_text, value_number, value_datetime, value_boolean, attribute_definitions(id, name, data_type, unit, description))'
        
        query = client.table('events') \
            .select(select_fields, count='exact') \
            .eq('user_id', user_id)
        
        # Apply category filter IN SQL (not Python!) - P1 fix
        if effective_category_ids:
            query = query.in_('category_id', effective_category_ids)
        
        # Apply date filters
        if date_from:
            query = query.gte('event_date', date_from.isoformat())
        if date_to:
            query = query.lte('event_date', date_to.isoformat())
        
        # V2.5.3: Apply sort order based on parameter
        # V2.5.5: Added session_start secondary sort for timestamp grouping
        desc_order = (sort_order == 'desc')
        query = query.order('event_date', desc=desc_order) \
                     .order('session_start', desc=desc_order) \
                     .range(offset, offset + limit - 1)
        
        resp = query.execute()
        events = resp.data or []
        
        # V2.5.5: Sort by category.level (ascending) as tertiary sort
        # This ensures parent categories appear before child categories for same timestamp
        # Cannot do this in SQL ORDER BY because 'level' is in nested 'categories' relation
        events.sort(key=lambda e: (
            e.get('event_date', ''),
            e.get('session_start', ''),
            e.get('categories', {}).get('level', 999)  # Parent (level=1) before child (level=2)
        ), reverse=desc_order)
        
        resp = query.execute()
        events = resp.data or []
        
        # Get total count from response (count='exact' in select)
        total_count = resp.count if hasattr(resp, 'count') and resp.count is not None else len(events)
        
        return events, total_count
        
    except Exception as e:
        st.error(f"Error loading events: {e}")
        return [], 0


def load_event_attachments(client, user_id: str, event_id: str) -> List[Dict]:
    """Load attachments for a specific event."""
    try:
        resp = client.table('event_attachments') \
            .select('id, url, filename, type, size_bytes') \
            .eq('user_id', user_id) \
            .eq('event_id', event_id) \
            .execute()
        return resp.data or []
    except Exception:
        return []


def load_attribute_definitions(client, user_id: str, category_id: str) -> List[Dict]:
    """Load attribute definitions for a category."""
    try:
        resp = client.table('attribute_definitions') \
            .select('id, name, data_type, unit, is_required, description') \
            .eq('user_id', user_id) \
            .eq('category_id', category_id) \
            .order('sort_order') \
            .execute()
        return resp.data or []
    except Exception:
        return []


# ============================================
# UPDATE/DELETE FUNCTIONS
# ============================================

def update_event(client, user_id: str, event_id: str, updates: Dict) -> Tuple[bool, str]:
    """Update event record."""
    try:
        client.table('events') \
            .update(updates) \
            .eq('id', event_id) \
            .eq('user_id', user_id) \
            .execute()
        return True, "Event updated"
    except Exception as e:
        return False, str(e)


def update_event_attribute(client, user_id: str, attr_id: str, value: any, data_type: str) -> Tuple[bool, str]:
    """Update a single event attribute."""
    try:
        update_data = {
            'value_text': None,
            'value_number': None,
            'value_datetime': None,
            'value_boolean': None
        }
        
        if data_type == 'number' and value is not None:
            update_data['value_number'] = float(value)
        elif data_type == 'boolean':
            update_data['value_boolean'] = bool(value)
        elif data_type == 'datetime' and value:
            update_data['value_datetime'] = value if isinstance(value, str) else value.isoformat()
        elif value:
            update_data['value_text'] = str(value)
        
        client.table('event_attributes') \
            .update(update_data) \
            .eq('id', attr_id) \
            .eq('user_id', user_id) \
            .execute()
        
        return True, "Attribute updated"
    except Exception as e:
        return False, str(e)


def create_event_attribute(client, user_id: str, event_id: str, attr_def_id: str, 
                          value: any, data_type: str) -> Tuple[bool, str]:
    """Create a new event attribute."""
    try:
        insert_data = {
            'event_id': event_id,
            'attribute_definition_id': attr_def_id,
            'user_id': user_id,
            'value_text': None,
            'value_number': None,
            'value_datetime': None,
            'value_boolean': None
        }
        
        if data_type == 'number' and value is not None:
            insert_data['value_number'] = float(value)
        elif data_type == 'boolean':
            insert_data['value_boolean'] = bool(value)
        elif data_type == 'datetime' and value:
            insert_data['value_datetime'] = value if isinstance(value, str) else value.isoformat()
        elif value:
            insert_data['value_text'] = str(value)
        
        client.table('event_attributes').insert(insert_data).execute()
        
        return True, "Attribute created"
    except Exception as e:
        return False, str(e)


def delete_event(client, user_id: str, event_id: str) -> Tuple[bool, str]:
    """Delete event and all related records."""
    try:
        # Delete attachments from storage first
        attachments = load_event_attachments(client, user_id, event_id)
        for att in attachments:
            try:
                url = att.get('url', '')
                if 'activity-attachments' in url:
                    path = url.split('activity-attachments/')[-1]
                    client.storage.from_('activity-attachments').remove([path])
            except Exception:
                pass
        
        # Delete event (CASCADE handles event_attributes and event_attachments)
        client.table('events') \
            .delete() \
            .eq('id', event_id) \
            .eq('user_id', user_id) \
            .execute()
        
        return True, "Event deleted"
    except Exception as e:
        return False, str(e)


def delete_events_bulk(client, user_id: str, event_ids: List[str]) -> Tuple[int, int]:
    """
    Delete multiple events.
    Returns: (success_count, error_count)
    """
    success = 0
    errors = 0
    
    for event_id in event_ids:
        ok, _ = delete_event(client, user_id, event_id)
        if ok:
            success += 1
        else:
            errors += 1
    
    return success, errors


# ============================================
# FORMATTING FUNCTIONS
# ============================================

def format_time(session_start: str) -> str:
    """Format session_start to HH:MM."""
    if not session_start:
        return "--:--"
    try:
        ss = session_start.replace('Z', '+00:00').split('+')[0]
        dt = datetime.fromisoformat(ss)
        return dt.strftime('%H:%M')
    except Exception:
        return "--:--"


def get_attribute_value(attr: Dict) -> any:
    """Extract the actual value from an event attribute record."""
    if attr.get('value_number') is not None:
        return attr['value_number']
    if attr.get('value_boolean') is not None:
        return attr['value_boolean']
    if attr.get('value_datetime'):
        return attr['value_datetime']
    if attr.get('value_text'):
        return attr['value_text']
    return None


def format_attribute_value(attr: Dict) -> str:
    """
    Format attribute value based on data type for table display.
    
    Formats:
    - number: value unit (e.g., "12 kg")
    - text: first 20 chars
    - datetime: formatted date
    - boolean: Yes/No
    - link: "🔗 Link"
    - image: "📷 Image"
    """
    attr_def = attr.get('attribute_definitions', {})
    data_type = attr_def.get('data_type', 'text')
    unit = attr_def.get('unit', '')
    value = get_attribute_value(attr)
    
    if value is None:
        return "-"
    
    if data_type == 'number':
        try:
            num_val = float(value)
            if num_val == int(num_val):
                formatted = str(int(num_val))
            else:
                formatted = f"{num_val:.2f}"
            if unit:
                formatted += f" {unit}"
            return formatted
        except:
            return str(value)
    
    elif data_type == 'text':
        text = str(value)
        if len(text) > 20:
            return text[:20] + "..."
        return text
    
    elif data_type == 'datetime':
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value.replace('Z', '+00:00').split('+')[0])
                return dt.strftime('%Y-%m-%d %H:%M')
            return str(value)
        except:
            return str(value)
    
    elif data_type == 'boolean':
        return "Yes" if value else "No"
    
    elif data_type == 'link':
        return "🔗 Link"
    
    elif data_type == 'image':
        return "📷 Image"
    
    return str(value)[:20]


def format_attributes_preview(attributes: List[Dict]) -> str:
    """
    Create a condensed preview of all attributes for table display.
    """
    if not attributes:
        return "-"
    
    parts = []
    for attr in attributes[:3]:  # Show max 3 in preview
        attr_def = attr.get('attribute_definitions', {})
        name = attr_def.get('name', '?')
        formatted_value = format_attribute_value(attr)
        parts.append(f"{name}: {formatted_value}")
    
    result = " | ".join(parts)
    
    if len(attributes) > 3:
        result += f" (+{len(attributes) - 3} more)"
    
    return result


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render_show_events(client, user_id: str):
    """
    Main entry point for Show Events page.
    
    v2.2.0: Removed View modal, improved selection, fixed navigation
    """
    
    st.subheader("📋 View Events")
    
    # Initialize session state
    if 'se_area_id' not in st.session_state:
        st.session_state.se_area_id = None
    if 'se_category_id' not in st.session_state:
        st.session_state.se_category_id = None
    if 'se_page' not in st.session_state:
        st.session_state.se_page = 0
    if 'se_selected_events' not in st.session_state:
        st.session_state.se_selected_events = set()
    if 'se_edit_event' not in st.session_state:
        st.session_state.se_edit_event = None
    if 'se_edit_list' not in st.session_state:
        st.session_state.se_edit_list = []
    if 'se_edit_index' not in st.session_state:
        st.session_state.se_edit_index = 0
    if 'se_delete_confirm' not in st.session_state:
        st.session_state.se_delete_confirm = None
    if 'se_bulk_delete_confirm' not in st.session_state:
        st.session_state.se_bulk_delete_confirm = False
    if 'se_import_file' not in st.session_state:
        st.session_state.se_import_file = None
    if 'se_import_preview' not in st.session_state:
        st.session_state.se_import_preview = None
    if 'se_upload_counter' not in st.session_state:
        st.session_state.se_upload_counter = 0
    if 'se_export_data' not in st.session_state:
        st.session_state.se_export_data = None
    if 'se_export_filename' not in st.session_state:
        st.session_state.se_export_filename = None
    if 'se_export_count' not in st.session_state:
        st.session_state.se_export_count = None
    if 'se_import_result' not in st.session_state:
        st.session_state.se_import_result = None  # {'type': 'success'|'error'|'warning', 'message': str, 'details': list}
    if 'se_sort_order' not in st.session_state:
        st.session_state.se_sort_order = 'desc'  # V2.5.3: 'desc' = newest first, 'asc' = oldest first
    
    # Display import result messages (persists through rerun)
    if st.session_state.se_import_result:
        result = st.session_state.se_import_result
        if result['type'] == 'success':
            st.success(result['message'])
            if result.get('details'):
                with st.expander("📋 Details", expanded=False):
                    for detail in result['details']:
                        if detail.startswith('⚠️'):
                            st.warning(detail)
                        else:
                            st.info(detail)
        elif result['type'] == 'error':
            st.error(result['message'])
            if result.get('details'):
                for detail in result['details'][:5]:
                    st.error(f"• {detail}")
                if len(result['details']) > 5:
                    st.error(f"... and {len(result['details']) - 5} more errors")
        elif result['type'] == 'warning':
            st.warning(result['message'])
            if result.get('details'):
                for detail in result['details']:
                    st.info(f"• {detail}")
        
        # Clear result after displaying (one-time message)
        st.session_state.se_import_result = None
    
    
    # Load areas and categories
    areas = load_areas(client, user_id)
    all_categories = load_all_categories_with_paths(client, user_id)
    
    # v1.13.0: Bootstrap system - auto-create default structure if empty
    if not areas:
        st.info("🔧 First time here? Creating default structure for you...")
        
        success, message = create_bootstrap_structure(client, user_id)
        
        if success:
            st.success(message)
            st.info("🎉 You can now start using the app! Feel free to customize or delete the default structure.")
            # Brief pause to show messages, then reload
            time_module.sleep(1.5)
            st.rerun()
        else:
            st.error(message)
            st.warning("⚠️ Please try refreshing the page or contact support.")
            return
    
    # ─────────────────────────────────────────
    # FILTERS ROW
    # ─────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1.5])
    
    with col1:
        area_options = {"all": "All Areas"} | {a['id']: f"📦 {a['name']}" for a in areas}
        area_ids = list(area_options.keys())
        
        current_area_idx = 0
        if st.session_state.se_area_id and st.session_state.se_area_id in area_ids:
            current_area_idx = area_ids.index(st.session_state.se_area_id)
        
        selected_area = st.selectbox(
            "📦 Area",
            options=area_ids,
            format_func=lambda x: area_options[x],
            index=current_area_idx,
            key="se_area_filter"
        )
        
        if selected_area == "all":
            if st.session_state.se_area_id is not None:
                st.session_state.se_area_id = None
                st.session_state.se_category_id = None
                st.session_state.se_page = 0
                st.session_state.se_selected_events = set()  # Clear selection on filter change
                clear_export_state()  # V2.5.3: Clear export UI
        elif selected_area != st.session_state.se_area_id:
            st.session_state.se_area_id = selected_area
            st.session_state.se_category_id = None
            st.session_state.se_page = 0
            st.session_state.se_selected_events = set()  # Clear selection on filter change
            clear_export_state()  # V2.5.3: Clear export UI
    
    # Load categories for selected area
    categories = []
    if st.session_state.se_area_id:
        categories = load_categories_for_area(client, user_id, st.session_state.se_area_id)
    
    with col2:
        if categories:
            cat_options = {"all": "All Categories"} | {c['id']: c['full_path'] for c in categories}
            cat_ids = list(cat_options.keys())
            
            current_cat_idx = 0
            if st.session_state.se_category_id and st.session_state.se_category_id in cat_ids:
                current_cat_idx = cat_ids.index(st.session_state.se_category_id)
            
            selected_cat = st.selectbox(
                "📂 Category",
                options=cat_ids,
                format_func=lambda x: cat_options[x],
                index=current_cat_idx,
                key="se_category_filter"
            )
            
            if selected_cat == "all":
                if st.session_state.se_category_id is not None:
                    st.session_state.se_category_id = None
                    st.session_state.se_selected_events = set()  # Clear selection on filter change
                    clear_export_state()  # V2.5.3: Clear export UI
            elif selected_cat != st.session_state.se_category_id:
                st.session_state.se_category_id = selected_cat
                st.session_state.se_selected_events = set()  # Clear selection on filter change
                clear_export_state()  # V2.5.3: Clear export UI
        else:
            st.selectbox("📂 Category", ["Select area first"], disabled=True, key="se_cat_disabled")
    
    with col3:
        date_from = st.date_input(
            "📅 From",
            value=date.today() - timedelta(days=30),
            key="se_date_from"
        )
    
    with col4:
        date_to = st.date_input(
            "📅 To",
            value=date.today(),
            key="se_date_to"
        )
    
    with col5:
        # V2.5.3: Sort order selection
        sort_options = {
            'desc': '⬇️ Newest first',
            'asc': '⬆️ Oldest first'
        }
        selected_sort = st.selectbox(
            "🔄 Sort",
            options=['desc', 'asc'],
            format_func=lambda x: sort_options[x],
            index=0 if st.session_state.se_sort_order == 'desc' else 1,
            key="se_sort_filter"
        )
        if selected_sort != st.session_state.se_sort_order:
            st.session_state.se_sort_order = selected_sort
    
    st.markdown("---")
    
    # ─────────────────────────────────────────
    # LOAD AND DISPLAY EVENTS
    # ─────────────────────────────────────────
    
    offset = st.session_state.se_page * EVENTS_PER_PAGE
    
    # Get downstream category IDs if a category is selected
    category_ids = None
    if st.session_state.se_category_id:
        category_ids = get_downstream_category_ids(all_categories, st.session_state.se_category_id)
        if len(category_ids) > 1:
            st.info(f"📂 Showing events from **{len(category_ids)}** categories (including sub-categories)")
    
    events, total_count = load_events_with_attributes(
        client, user_id,
        area_id=st.session_state.se_area_id,
        category_ids=category_ids,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=EVENTS_PER_PAGE,
        sort_order=st.session_state.se_sort_order  # V2.5.3: User-selected sort order
    )
    
    if not events:
        st.info("No events found matching your filters.")
        return
    
    # P5: Warning for large datasets
    total_pages = max(1, (total_count + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE)
    
    if total_count > 100:
        st.warning(f"⚠️ Large dataset: {total_count} events. Consider narrowing your date range or using category filters for better performance.")
    
    # Stats
    st.caption(f"Showing {len(events)} of {total_count} events (Page {st.session_state.se_page + 1} of {total_pages})")
    
    # ─────────────────────────────────────────
    # EVENTS TABLE - v2.3.0: Using st.dataframe with row selection (much more responsive!)
    # ─────────────────────────────────────────
    
    # Build table data
    table_data = []
    event_id_map = {}  # Map row index to event_id
    
    for idx, event in enumerate(events):
        event_id = event['id']
        event_id_map[idx] = event_id
        
        cat_info = all_categories.get(event.get('category_id'), {})
        cat_path = cat_info.get('full_path', 'Unknown')
        
        # Format attributes preview
        attrs = event.get('event_attributes', [])
        attr_preview = format_attributes_preview(attrs)
        
        # Format notes preview
        comment = event.get('comment', '') or ''
        notes_preview = comment[:30] + '...' if len(comment) > 30 else comment
        
        table_data.append({
            'Date': event.get('event_date', ''),
            'Time': format_time(event.get('session_start', '')),
            'Category Path': cat_path,
            'Attributes': attr_preview,
            'Notes': notes_preview
        })
    
    # Create DataFrame
    df = pd.DataFrame(table_data)
    
    # Display with native row selection (much more responsive than data_editor checkboxes!)
    # Note: Selection is per-page only (use filters to narrow down results for bulk operations)
    # Tip: Use Shift+Click to select a range of rows
    selection = st.dataframe(
        df,
        column_config={
            'Date': st.column_config.TextColumn('Date', width="small"),
            'Time': st.column_config.TextColumn('Time', width="small"),
            'Category Path': st.column_config.TextColumn('Category Path', width="medium"),
            'Attributes': st.column_config.TextColumn('Attributes', width="large"),
            'Notes': st.column_config.TextColumn('Notes', width="medium")
        },
        hide_index=True,
        use_container_width=True,
        selection_mode="multi-row",
        on_select="rerun",
        key="events_table"
    )
    
    # Update selected events from row selection (current page only)
    selected_rows = selection.selection.rows if selection and hasattr(selection, 'selection') else []
    st.session_state.se_selected_events = {event_id_map[idx] for idx in selected_rows}
    
    # ─────────────────────────────────────────
    # TOOLBAR (Edit/Delete/Export/Import actions) - now below table for sync
    # ─────────────────────────────────────────
    selected_count = len(st.session_state.se_selected_events)
    
    toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4, toolbar_col5 = st.columns([1, 1, 1, 1, 3])
    
    with toolbar_col1:
        edit_disabled = selected_count == 0
        if st.button("✏️ Edit", use_container_width=True, disabled=edit_disabled,
                     help="Edit selected event(s)"):
            # Sort selected events by date (newest first)
            selected_events_info = [
                {'id': event['id'], 'date': event.get('event_date', ''), 'time': event.get('session_start', '')}
                for event in events if event['id'] in st.session_state.se_selected_events
            ]
            selected_events_info.sort(key=lambda x: (x['date'], x['time']), reverse=True)
            sorted_list = [e['id'] for e in selected_events_info]
            
            st.session_state.se_edit_event = sorted_list[0] if sorted_list else None
            st.session_state.se_edit_index = 0
            st.session_state.se_edit_list = sorted_list
            st.rerun()
    
    with toolbar_col2:
        delete_disabled = selected_count == 0
        if st.button(f"🗑️ Delete ({selected_count})" if selected_count > 0 else "🗑️ Delete", 
                     use_container_width=True, disabled=delete_disabled, type="secondary",
                     help="Delete selected event(s)"):
            if selected_count > 0:
                st.session_state.se_bulk_delete_confirm = True
                st.rerun()
    
    with toolbar_col3:
        # Export button - exports all filtered events (not just current page)
        if st.button("📥 Export", use_container_width=True, help="Export filtered events to Excel"):
            with st.spinner("Exporting..."):
                excel_bytes, event_count, error = export_events_to_excel(
                    client, user_id,
                    area_id=st.session_state.se_area_id,  # Pass area_id for filtering
                    category_ids=category_ids,
                    date_from=date_from,
                    date_to=date_to,
                    sort_order=st.session_state.se_sort_order  # V2.5.5: Pass user sort order
                )
                
                if error:
                    st.error(f"❌ {error}")
                else:
                    filename = f"events_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    st.session_state.se_export_data = excel_bytes
                    st.session_state.se_export_filename = filename
                    st.session_state.se_export_count = event_count
                    st.rerun()
    
    with toolbar_col4:
        if st.button("📤 Import", use_container_width=True, help="Import events from Excel"):
            st.session_state.se_import_file = True
            st.rerun()
    
    with toolbar_col5:
        if selected_count > 0:
            st.caption(f"📋 {selected_count} selected • Shift+Click for range")
        else:
            st.caption("💡 Click rows to select • Shift+Click for range")
    
    # Bulk delete confirmation
    if st.session_state.get('se_bulk_delete_confirm', False):
        st.warning(f"⚠️ Are you sure you want to delete {selected_count} events?")
        confirm_col1, confirm_col2, confirm_col3 = st.columns([1, 1, 4])
        with confirm_col1:
            if st.button("✓ Yes, Delete", type="primary"):
                success, errors = delete_events_bulk(
                    client, user_id, 
                    list(st.session_state.se_selected_events)
                )
                st.session_state.se_selected_events = set()
                st.session_state.se_bulk_delete_confirm = False
                if errors == 0:
                    st.success(f"✅ Deleted {success} events")
                else:
                    st.warning(f"Deleted {success}, failed {errors}")
                clear_export_state()  # V2.5.3: Clear export UI after delete
                st.rerun()
        with confirm_col2:
            if st.button("Cancel"):
                st.session_state.se_bulk_delete_confirm = False
                st.rerun()
    
    # ─────────────────────────────────────────
    # EXPORT DOWNLOAD (after Export button clicked)
    # ─────────────────────────────────────────
    if st.session_state.get('se_export_data'):
        st.success(f"✅ Export ready: {st.session_state.se_export_count} events")
        
        col1, col2, col3 = st.columns([2, 1, 3])
        with col1:
            st.download_button(
                label="📥 Download Excel",
                data=st.session_state.se_export_data,
                file_name=st.session_state.get('se_export_filename', 'events_export.xlsx'),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col2:
            if st.button("✕ Close", key="close_export"):
                st.session_state.se_export_data = None
                st.session_state.se_export_filename = None
                st.session_state.se_export_count = None
                st.rerun()
        
        st.info("💡 Edit BLUE columns in Excel, then use Import to apply changes")
    
    # ─────────────────────────────────────────
    # IMPORT WORKFLOW
    # ─────────────────────────────────────────
    if st.session_state.get('se_import_file'):
        st.markdown("---")
        st.markdown("### 📤 Import Events from Excel")
        
        # File uploader with dynamic key to allow re-upload
        upload_key = f"excel_import_{st.session_state.se_upload_counter}"
        uploaded_file = st.file_uploader(
            "Upload Excel file",
            type=['xlsx'],
            key=upload_key,
            help="Upload an Excel file exported from this app or in the same format"
        )
        
        if uploaded_file:
            file_bytes = uploaded_file.read()
            
            # Parse and validate
            with st.spinner("Parsing Excel file..."):
                events_to_create, events_to_update, legend_mapping, parse_error = parse_events_excel_v2(file_bytes)
            
            # Check for validation warnings or errors
            if parse_error and ("⚠️" in parse_error or "ℹ️" in parse_error):
                # Has validation warnings - show them but continue
                st.warning("📋 Validation Notes")
                for line in parse_error.split("\n"):
                    if line.strip():
                        if "⚠️" in line:
                            st.warning(line)
                        elif "ℹ️" in line:
                            st.info(line)
            elif parse_error:
                # Critical error - stop
                st.error(f"❌ {parse_error}")
                return
            
            # Show preview if parsing succeeded
            if events_to_create or events_to_update:
                # Show preview
                st.markdown("#### Preview")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("New Events", len(events_to_create), help="Events with empty event_id")
                with col2:
                    st.metric("Updates", len(events_to_update), help="Events with existing event_id")
                
                if events_to_create:
                    with st.expander(f"📝 New Events ({len(events_to_create)})", expanded=False):
                        preview_data = []
                        for e in events_to_create[:10]:
                            preview_data.append({
                                'Date': e.get('event_date', ''),
                                'Category': e.get('Category_Path', ''),
                                'Comment': str(e.get('comment', ''))[:30]
                            })
                        st.dataframe(pd.DataFrame(preview_data), hide_index=True, use_container_width=True)
                        if len(events_to_create) > 10:
                            st.caption(f"... and {len(events_to_create) - 10} more")
                
                if events_to_update:
                    with st.expander(f"✏️ Updates ({len(events_to_update)})", expanded=False):
                        preview_data = []
                        for e in events_to_update[:10]:
                            preview_data.append({
                                'Event ID': str(e.get('event_id', ''))[:8] + '...',
                                'Date': e.get('event_date', ''),
                                'Comment': str(e.get('comment', ''))[:30]
                            })
                        st.dataframe(pd.DataFrame(preview_data), hide_index=True, use_container_width=True)
                        if len(events_to_update) > 10:
                            st.caption(f"... and {len(events_to_update) - 10} more")
                
                # Action buttons
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])
                
                with btn_col1:
                    if st.button("✓ Apply Import", type="primary", use_container_width=True):
                        with st.spinner("Importing events..."):
                            created, updated, messages = import_events_from_excel(
                                client, user_id, file_bytes
                            )
                        
                        # Separate warnings from errors
                        errors = [m for m in messages if not m.startswith('⚠️') and not m.startswith('💡')]
                        warnings = [m for m in messages if m.startswith('⚠️') or m.startswith('💡')]
                        
                        # Store result in session state (survives st.rerun!)
                        if errors:
                            st.session_state.se_import_result = {
                                'type': 'error',
                                'message': "❌ Import failed with errors:",
                                'details': errors
                            }
                        elif warnings:
                            st.session_state.se_import_result = {
                                'type': 'success',
                                'message': f"✅ Import complete: {created} created, {updated} updated",
                                'details': warnings
                            }
                        else:
                            st.session_state.se_import_result = {
                                'type': 'success',
                                'message': f"✅ Import complete: {created} created, {updated} updated",
                                'details': []
                            }
                        
                        # Reset import state
                        st.session_state.se_import_file = None
                        st.session_state.se_upload_counter += 1
                        clear_export_state()  # V2.5.3: Clear export UI after import
                        st.rerun()
                
                with btn_col2:
                    if st.button("✕ Cancel", use_container_width=True):
                        st.session_state.se_import_file = None
                        st.session_state.se_upload_counter += 1
                        clear_export_state()  # V2.5.3: Clear export UI
                        st.rerun()
            else:
                # No events found in Excel
                st.warning("⚠️ No events found in Excel file. The file may be empty or in incorrect format.")
                if st.button("✕ Cancel", use_container_width=True):
                    st.session_state.se_import_file = None
                    st.session_state.se_upload_counter += 1
                    clear_export_state()  # V2.5.3: Clear export UI
                    st.rerun()
        else:
            # Cancel button when no file uploaded
            if st.button("✕ Cancel Import"):
                st.session_state.se_import_file = None
                st.rerun()
    
    # ─────────────────────────────────────────
    # EDIT EVENT MODAL (with multi-event navigation)
    # ─────────────────────────────────────────
    if st.session_state.se_edit_event:
        event_id = st.session_state.se_edit_event
        event = next((e for e in events if e['id'] == event_id), None)
        
        # Try to load from database if not in current page
        if not event:
            try:
                single_select = 'id, category_id, event_date, session_start, comment, event_attributes(id, value_text, value_number, value_datetime, value_boolean, attribute_definitions(id, name, data_type, unit, description))'
                resp = client.table('events') \
                    .select(single_select) \
                    .eq('id', event_id) \
                    .eq('user_id', user_id) \
                    .single() \
                    .execute()
                event = resp.data
            except:
                event = None
        
        if event:
            edit_list = st.session_state.get('se_edit_list', [event_id])
            edit_index = st.session_state.get('se_edit_index', 0)
            render_event_edit_modal(client, user_id, event, all_categories, edit_list, edit_index)
    
    # ─────────────────────────────────────────
    # PAGINATION
    # ─────────────────────────────────────────
    st.markdown("---")
    
    page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
    
    with page_col1:
        if st.session_state.se_page > 0:
            if st.button("◀ Previous", key="prev_page", use_container_width=True):
                st.session_state.se_page -= 1
                st.session_state.se_edit_event = None
                clear_export_state()  # V2.5.3: Clear export UI
                st.rerun()
    
    with page_col2:
        st.markdown(f"<center>Page {st.session_state.se_page + 1} of {total_pages}</center>", unsafe_allow_html=True)
    
    with page_col3:
        if st.session_state.se_page < total_pages - 1:
            if st.button("Next ▶", key="next_page", use_container_width=True):
                st.session_state.se_page += 1
                st.session_state.se_edit_event = None
                clear_export_state()  # V2.5.3: Clear export UI
                st.rerun()


def render_event_edit_modal(client, user_id: str, event: Dict, all_categories: Dict,
                           event_list: List[str] = None, current_index: int = 0):
    """Render event edit form in an expander with optional multi-event navigation."""
    
    event_id = event['id']
    cat_info = all_categories.get(event.get('category_id'), {})
    
    # Determine if we have multiple events to navigate
    has_navigation = event_list and len(event_list) > 1
    nav_info = f" ({current_index + 1}/{len(event_list)})" if has_navigation else ""
    
    with st.expander(f"✏️ Edit Event{nav_info}: {event.get('event_date', '')} - {cat_info.get('name', '')}", expanded=True):
        
        # Header row with Close and navigation
        if has_navigation:
            nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 3])
            with nav_col1:
                if current_index > 0:
                    if st.button("◀ Prev", key="edit_prev"):
                        st.session_state.se_edit_index = current_index - 1
                        st.session_state.se_edit_event = event_list[current_index - 1]
                        st.rerun()
            with nav_col2:
                if current_index < len(event_list) - 1:
                    if st.button("Next ▶", key="edit_next"):
                        st.session_state.se_edit_index = current_index + 1
                        st.session_state.se_edit_event = event_list[current_index + 1]
                        st.rerun()
            with nav_col3:
                if st.button("✕ Close", key="close_edit"):
                    st.session_state.se_edit_event = None
                    st.session_state.se_edit_list = []
                    st.session_state.se_edit_index = 0
                    clear_export_state()  # V2.5.3: Clear export UI
                    st.rerun()
        else:
            if st.button("✕ Close", key="close_edit"):
                st.session_state.se_edit_event = None
                clear_export_state()  # V2.5.3: Clear export UI
                st.rerun()
        
        st.markdown("---")
        
        # Basic info editing
        col1, col2 = st.columns(2)
        
        with col1:
            current_date = date.today()
            if event.get('event_date'):
                try:
                    current_date = date.fromisoformat(event['event_date'])
                except:
                    pass
            
            new_date = st.date_input(
                "📅 Date",
                value=current_date,
                key=f"edit_date_{event_id}"
            )
        
        with col2:
            current_time = time(0, 0)
            if event.get('session_start'):
                try:
                    ss = event['session_start'].replace('Z', '+00:00').split('+')[0]
                    dt = datetime.fromisoformat(ss)
                    current_time = dt.time()
                except:
                    pass
            
            new_time = st.time_input(
                "⏰ Time",
                value=current_time,
                key=f"edit_time_{event_id}"
            )
        
        # Comment
        new_comment = st.text_area(
            "💬 Notes",
            value=event.get('comment', '') or '',
            key=f"edit_comment_{event_id}"
        )
        
        # Save basic info
        if st.button("💾 Save Event Info", key=f"save_basic_{event_id}"):
            new_session_start = datetime.combine(new_date, new_time)
            updates = {
                'event_date': new_date.isoformat(),
                'session_start': new_session_start.isoformat(),
                'comment': new_comment if new_comment.strip() else None,
                'edited_at': datetime.now().isoformat()
            }
            
            success, msg = update_event(client, user_id, event_id, updates)
            if success:
                st.success("✅ Event updated!")
                clear_export_state()  # V2.5.3: Clear export UI after edit
                st.rerun()
            else:
                st.error(f"❌ {msg}")
        
        # ─────────────────────────────────────────
        # ATTRIBUTES EDITING (T2.2: Show ALL defined attributes)
        # ─────────────────────────────────────────
        category_id = event.get('category_id')
        
        # Load ALL attribute definitions for this category
        attr_definitions = load_attribute_definitions(client, user_id, category_id) if category_id else []
        
        # Build a map of existing event_attributes by attribute_definition_id
        existing_attrs = event.get('event_attributes', [])
        existing_attrs_map = {}
        for attr in existing_attrs:
            attr_def = attr.get('attribute_definitions', {})
            if attr_def:
                existing_attrs_map[attr_def.get('id')] = attr
        
        if attr_definitions:
            st.markdown("---")
            st.markdown("**🏷️ Attributes:**")
            
            # Display in 2-column grid
            for j in range(0, len(attr_definitions), 2):
                cols = st.columns(2)
                for k, col in enumerate(cols):
                    if j + k < len(attr_definitions):
                        attr_def = attr_definitions[j + k]
                        attr_def_id = attr_def['id']
                        name = attr_def.get('name', 'Unknown')
                        data_type = attr_def.get('data_type', 'text')
                        unit = attr_def.get('unit', '')
                        is_required = attr_def.get('is_required', False)
                        
                        # Check if we have an existing value
                        existing = existing_attrs_map.get(attr_def_id)
                        existing_attr_id = existing['id'] if existing else None
                        current_value = get_attribute_value(existing) if existing else None
                        
                        # Build label
                        label = name
                        if unit:
                            label += f" ({unit})"
                        if is_required:
                            label += " *"
                        
                        with col:
                            # Render input based on data type
                            input_key = f"edit_attr_{event_id}_{attr_def_id}"
                            
                            if data_type == 'number':
                                new_val = st.number_input(
                                    label,
                                    value=float(current_value) if current_value is not None else 0.0,
                                    key=input_key,
                                    help=attr_def.get('description', '')
                                )
                            elif data_type == 'boolean':
                                new_val = st.checkbox(
                                    label,
                                    value=bool(current_value) if current_value else False,
                                    key=input_key,
                                    help=attr_def.get('description', '')
                                )
                            elif data_type == 'datetime':
                                try:
                                    current_dt = date.fromisoformat(str(current_value)[:10]) if current_value else date.today()
                                except:
                                    current_dt = date.today()
                                new_val = st.date_input(
                                    label,
                                    value=current_dt,
                                    key=input_key,
                                    help=attr_def.get('description', '')
                                )
                            else:
                                new_val = st.text_input(
                                    label,
                                    value=str(current_value) if current_value else '',
                                    key=input_key,
                                    help=attr_def.get('description', '')
                                )
                            
                            # Save button for this attribute
                            btn_key = f"save_attr_btn_{event_id}_{attr_def_id}"
                            if st.button("💾 Save", key=btn_key, use_container_width=True):
                                if existing_attr_id:
                                    # Update existing
                                    success, msg = update_event_attribute(client, user_id, existing_attr_id, new_val, data_type)
                                else:
                                    # Create new
                                    success, msg = create_event_attribute(client, user_id, event_id, attr_def_id, new_val, data_type)
                                
                                if success:
                                    st.success("✅ Saved!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
        else:
            st.info("ℹ️ No attributes defined for this category")


# ============================================
# STANDALONE TEST
# ============================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Show Events",
        page_icon="📋",
        layout="wide"
    )
    
    st.title("Show Events - Test Mode")
    st.warning("This is a test page. Run from main app for full functionality.")
