"""
Events Tracker - Show Events Module
====================================
Created: 2025-12-15 09:45 UTC
Last Modified: 2025-12-17 15:00 UTC
Python: 3.11
Version: 2.3.0 - Native Row Selection

Description:
View, edit, and delete events with:
- Table view using st.dataframe with native row selection
- Filter by Area + Category drill-down + Date range
- Toolbar actions (Edit/Delete) above table
- Downstream category filter (includes all sub-categories)
- Bulk delete with row selection
- Category_Path display (ISV-style)
- Attribute value formatting by type

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

Dependencies: streamlit, datetime, supabase, pandas
"""

import streamlit as st
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd


# ============================================
# CONSTANTS
# ============================================

EVENTS_PER_PAGE = 20


# ============================================
# DATA LOADING FUNCTIONS
# ============================================

def load_areas(client, user_id: str) -> List[Dict]:
    """Load all areas for user."""
    try:
        resp = client.table('areas') \
            .select('id, name, icon, sort_order') \
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
    limit: int = EVENTS_PER_PAGE
) -> Tuple[List[Dict], int]:
    """
    Load events with their attributes for table display.
    
    Args:
        area_id: Filter by area (converted to category_ids internally)
        category_ids: List of category IDs to filter (supports downstream filtering)
    
    Returns:
        Tuple of (events list with attributes, total count)
    
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
        query = client.table('events') \
            .select('''
                id, category_id, event_date, session_start, comment, created_at,
                categories(id, name, area_id),
                event_attributes(
                    id, value_text, value_number, value_datetime, value_boolean,
                    attribute_definitions(id, name, data_type, unit, description)
                )
            ''', count='exact') \
            .eq('user_id', user_id)
        
        # Apply category filter IN SQL (not Python!) - P1 fix
        if effective_category_ids:
            query = query.in_('category_id', effective_category_ids)
        
        # Apply date filters
        if date_from:
            query = query.gte('event_date', date_from.isoformat())
        if date_to:
            query = query.lte('event_date', date_to.isoformat())
        
        # Execute query with pagination
        query = query.order('event_date', desc=True) \
                     .order('session_start', desc=True) \
                     .range(offset, offset + limit - 1)
        
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
    
    # Load areas and categories
    areas = load_areas(client, user_id)
    all_categories = load_all_categories_with_paths(client, user_id)
    
    if not areas:
        st.warning("No areas defined. Please create structure first.")
        return
    
    # ─────────────────────────────────────────
    # FILTERS ROW
    # ─────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        area_options = {"all": "All Areas"} | {a['id']: f"{a.get('icon', '📦')} {a['name']}" for a in areas}
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
        elif selected_area != st.session_state.se_area_id:
            st.session_state.se_area_id = selected_area
            st.session_state.se_category_id = None
            st.session_state.se_page = 0
            st.session_state.se_selected_events = set()  # Clear selection on filter change
    
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
            elif selected_cat != st.session_state.se_category_id:
                st.session_state.se_category_id = selected_cat
                st.session_state.se_selected_events = set()  # Clear selection on filter change
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
        limit=EVENTS_PER_PAGE
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
    # TOOLBAR (Edit/Delete actions) - now below table for sync
    # ─────────────────────────────────────────
    selected_count = len(st.session_state.se_selected_events)
    
    toolbar_col1, toolbar_col2, toolbar_col3 = st.columns([1, 1, 4])
    
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
        if selected_count > 0:
            st.caption(f"📋 {selected_count} selected • Click row to select • Shift+Click for range")
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
                st.rerun()
        with confirm_col2:
            if st.button("Cancel"):
                st.session_state.se_bulk_delete_confirm = False
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
                resp = client.table('events') \
                    .select('''
                        id, category_id, event_date, session_start, comment,
                        event_attributes(
                            id, value_text, value_number, value_datetime, value_boolean,
                            attribute_definitions(id, name, data_type, unit, description)
                        )
                    ''') \
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
                st.rerun()
    
    with page_col2:
        st.markdown(f"<center>Page {st.session_state.se_page + 1} of {total_pages}</center>", unsafe_allow_html=True)
    
    with page_col3:
        if st.session_state.se_page < total_pages - 1:
            if st.button("Next ▶", key="next_page", use_container_width=True):
                st.session_state.se_page += 1
                st.session_state.se_edit_event = None
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
                    st.rerun()
        else:
            if st.button("✕ Close", key="close_edit"):
                st.session_state.se_edit_event = None
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
                st.rerun()
            else:
                st.error(f"❌ {msg}")
        
        # Attributes editing
        attrs = event.get('event_attributes', [])
        if attrs:
            st.markdown("---")
            st.markdown("**🏷️ Edit Attributes:**")
            
            for attr in attrs:
                attr_id = attr['id']
                attr_def = attr.get('attribute_definitions', {})
                name = attr_def.get('name', 'Unknown')
                data_type = attr_def.get('data_type', 'text')
                unit = attr_def.get('unit', '')
                current_value = get_attribute_value(attr)
                
                label = name
                if unit:
                    label += f" ({unit})"
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if data_type == 'number':
                        new_val = st.number_input(
                            label,
                            value=float(current_value) if current_value is not None else 0.0,
                            key=f"edit_attr_{attr_id}"
                        )
                    elif data_type == 'boolean':
                        new_val = st.checkbox(
                            label,
                            value=bool(current_value),
                            key=f"edit_attr_{attr_id}"
                        )
                    elif data_type == 'datetime':
                        try:
                            current_dt = date.fromisoformat(str(current_value)[:10]) if current_value else date.today()
                        except:
                            current_dt = date.today()
                        new_val = st.date_input(
                            label,
                            value=current_dt,
                            key=f"edit_attr_{attr_id}"
                        )
                    else:
                        new_val = st.text_input(
                            label,
                            value=str(current_value) if current_value else '',
                            key=f"edit_attr_{attr_id}"
                        )
                
                with col2:
                    if st.button("💾", key=f"save_attr_{attr_id}", help="Save this attribute"):
                        success, msg = update_event_attribute(client, user_id, attr_id, new_val, data_type)
                        if success:
                            st.success("✅")
                        else:
                            st.error(f"❌ {msg}")


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
