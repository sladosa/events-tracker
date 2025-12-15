"""
Events Tracker - Show Events Module
====================================
Created: 2025-12-15 09:45 UTC
Last Modified: 2025-12-15 09:45 UTC
Python: 3.11
Version: 1.0.0 - Initial release

Description:
View, edit, and delete events with:
- Filter by Area + Category drill-down (same as Add Activity)
- Date range filter
- Pagination (20 events per page)
- Inline editing of event attributes
- Delete with confirmation
- Photo attachment preview

Features:
- 🔍 Filter by Area/Category/Date range
- ✏️ Edit event attributes inline
- 🗑️ Delete events with confirmation
- 📷 View attached photos
- 📊 Pagination for large datasets

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


def load_all_categories(client, user_id: str) -> Dict[str, str]:
    """Load all categories as id -> name mapping."""
    try:
        resp = client.table('categories') \
            .select('id, name') \
            .eq('user_id', user_id) \
            .execute()
        return {c['id']: c['name'] for c in (resp.data or [])}
    except Exception:
        return {}


def load_events(
    client, 
    user_id: str, 
    area_id: Optional[str] = None,
    category_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    offset: int = 0,
    limit: int = EVENTS_PER_PAGE
) -> Tuple[List[Dict], int]:
    """
    Load events with filters and pagination.
    
    Returns:
        Tuple of (events list, total count)
    """
    try:
        # Build base query
        query = client.table('events') \
            .select('id, category_id, event_date, session_start, comment, created_at, categories(id, name, area_id)') \
            .eq('user_id', user_id)
        
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
        
        # Filter by area/category in Python (Supabase doesn't support nested filters well)
        if area_id:
            events = [e for e in events if e.get('categories', {}).get('area_id') == area_id]
        if category_id:
            events = [e for e in events if e.get('category_id') == category_id]
        
        # Get total count (separate query)
        count_query = client.table('events') \
            .select('id', count='exact') \
            .eq('user_id', user_id)
        
        if date_from:
            count_query = count_query.gte('event_date', date_from.isoformat())
        if date_to:
            count_query = count_query.lte('event_date', date_to.isoformat())
        
        count_resp = count_query.execute()
        total_count = count_resp.count if hasattr(count_resp, 'count') and count_resp.count else len(events)
        
        return events, total_count
        
    except Exception as e:
        st.error(f"Error loading events: {e}")
        return [], 0


def load_event_attributes(client, user_id: str, event_id: str) -> List[Dict]:
    """Load attributes for a specific event."""
    try:
        resp = client.table('event_attributes') \
            .select('id, attribute_definition_id, value_text, value_number, value_datetime, value_boolean, attribute_definitions(name, data_type, unit)') \
            .eq('user_id', user_id) \
            .eq('event_id', event_id) \
            .execute()
        return resp.data or []
    except Exception:
        return []


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
            .select('id, name, data_type, unit, is_required') \
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
        update_data = {}
        
        # Clear all value columns first
        update_data['value_text'] = None
        update_data['value_number'] = None
        update_data['value_datetime'] = None
        update_data['value_boolean'] = None
        
        # Set appropriate column based on data type
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
    """Delete event and all related records (CASCADE handles attributes/attachments)."""
    try:
        # Delete attachments from storage first (if any)
        attachments = load_event_attachments(client, user_id, event_id)
        for att in attachments:
            try:
                # Extract path from URL
                url = att.get('url', '')
                if 'activity-attachments' in url:
                    # Get path after bucket name
                    path = url.split('activity-attachments/')[-1]
                    client.storage.from_('activity-attachments').remove([path])
            except Exception:
                pass  # Continue even if storage delete fails
        
        # Delete event (CASCADE will handle event_attributes and event_attachments)
        client.table('events') \
            .delete() \
            .eq('id', event_id) \
            .eq('user_id', user_id) \
            .execute()
        
        return True, "Event deleted"
    except Exception as e:
        return False, str(e)


# ============================================
# UI HELPER FUNCTIONS
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


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render_show_events(client, user_id: str):
    """
    Main entry point for Show Events page.
    """
    
    st.subheader("📋 View Events")
    
    # Initialize session state
    if 'se_area_id' not in st.session_state:
        st.session_state.se_area_id = None
    if 'se_category_id' not in st.session_state:
        st.session_state.se_category_id = None
    if 'se_page' not in st.session_state:
        st.session_state.se_page = 0
    if 'se_editing_event' not in st.session_state:
        st.session_state.se_editing_event = None
    if 'se_delete_confirm' not in st.session_state:
        st.session_state.se_delete_confirm = None
    
    # Load areas
    areas = load_areas(client, user_id)
    
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
            st.session_state.se_area_id = None
        elif selected_area != st.session_state.se_area_id:
            st.session_state.se_area_id = selected_area
            st.session_state.se_category_id = None
            st.session_state.se_page = 0
    
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
                st.session_state.se_category_id = None
            else:
                st.session_state.se_category_id = selected_cat
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
    
    events, total_count = load_events(
        client, user_id,
        area_id=st.session_state.se_area_id,
        category_id=st.session_state.se_category_id,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=EVENTS_PER_PAGE
    )
    
    # All categories for display
    all_cats = load_all_categories(client, user_id)
    
    if not events:
        st.info("No events found matching your filters.")
        return
    
    # Stats
    total_pages = (total_count + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE
    st.caption(f"Showing {len(events)} of {total_count} events (Page {st.session_state.se_page + 1} of {total_pages})")
    
    # ─────────────────────────────────────────
    # EVENTS LIST
    # ─────────────────────────────────────────
    
    for event in events:
        event_id = event['id']
        cat_name = all_cats.get(event['category_id'], 'Unknown')
        event_date = event.get('event_date', '')
        time_str = format_time(event.get('session_start', ''))
        comment = event.get('comment', '') or ''
        
        # Event header
        with st.expander(f"📌 {event_date} {time_str} - **{cat_name}**", expanded=(st.session_state.se_editing_event == event_id)):
            
            # Check if we're editing this event
            is_editing = (st.session_state.se_editing_event == event_id)
            
            if is_editing:
                render_event_edit_form(client, user_id, event, all_cats)
            else:
                render_event_details(client, user_id, event, all_cats)
            
            # Action buttons
            st.markdown("---")
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
            
            with btn_col1:
                if is_editing:
                    if st.button("✅ Done", key=f"done_{event_id}", type="primary"):
                        st.session_state.se_editing_event = None
                        st.rerun()
                else:
                    if st.button("✏️ Edit", key=f"edit_{event_id}"):
                        st.session_state.se_editing_event = event_id
                        st.rerun()
            
            with btn_col2:
                if st.session_state.se_delete_confirm == event_id:
                    if st.button("⚠️ CONFIRM DELETE", key=f"confirm_del_{event_id}", type="primary"):
                        success, msg = delete_event(client, user_id, event_id)
                        if success:
                            st.success("Event deleted!")
                            st.session_state.se_delete_confirm = None
                            st.rerun()
                        else:
                            st.error(f"Delete failed: {msg}")
                else:
                    if st.button("🗑️ Delete", key=f"delete_{event_id}"):
                        st.session_state.se_delete_confirm = event_id
                        st.rerun()
            
            with btn_col3:
                if st.session_state.se_delete_confirm == event_id:
                    if st.button("Cancel", key=f"cancel_del_{event_id}"):
                        st.session_state.se_delete_confirm = None
                        st.rerun()
    
    # ─────────────────────────────────────────
    # PAGINATION
    # ─────────────────────────────────────────
    st.markdown("---")
    
    page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
    
    with page_col1:
        if st.session_state.se_page > 0:
            if st.button("◀ Previous", key="prev_page"):
                st.session_state.se_page -= 1
                st.rerun()
    
    with page_col2:
        st.markdown(f"<center>Page {st.session_state.se_page + 1} of {total_pages}</center>", unsafe_allow_html=True)
    
    with page_col3:
        if st.session_state.se_page < total_pages - 1:
            if st.button("Next ▶", key="next_page"):
                st.session_state.se_page += 1
                st.rerun()


def render_event_details(client, user_id: str, event: Dict, all_cats: Dict):
    """Render event details in read-only mode."""
    event_id = event['id']
    
    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        st.text(f"Date: {event.get('event_date', 'N/A')}")
        st.text(f"Time: {format_time(event.get('session_start', ''))}")
    with col2:
        st.text(f"Category: {all_cats.get(event['category_id'], 'Unknown')}")
    
    # Comment
    if event.get('comment'):
        st.text(f"Notes: {event['comment']}")
    
    # Attributes
    attrs = load_event_attributes(client, user_id, event_id)
    if attrs:
        st.markdown("**Attributes:**")
        for attr in attrs:
            attr_def = attr.get('attribute_definitions', {})
            name = attr_def.get('name', 'Unknown')
            unit = attr_def.get('unit', '')
            value = get_attribute_value(attr)
            
            display_val = f"{value}"
            if unit:
                display_val += f" {unit}"
            
            st.text(f"  • {name}: {display_val}")
    
    # Attachments
    attachments = load_event_attachments(client, user_id, event_id)
    if attachments:
        st.markdown("**Attachments:**")
        for att in attachments:
            if att.get('type') == 'image':
                st.image(att['url'], caption=att.get('filename', 'Image'), width=200)
            else:
                st.markdown(f"[{att.get('filename', 'File')}]({att['url']})")


def render_event_edit_form(client, user_id: str, event: Dict, all_cats: Dict):
    """Render event edit form."""
    event_id = event['id']
    
    # Basic info editing
    col1, col2 = st.columns(2)
    
    with col1:
        # Parse current date
        current_date = date.today()
        if event.get('event_date'):
            try:
                current_date = date.fromisoformat(event['event_date'])
            except:
                pass
        
        new_date = st.date_input(
            "Date",
            value=current_date,
            key=f"edit_date_{event_id}"
        )
    
    with col2:
        # Parse current time
        current_time = time(0, 0)
        if event.get('session_start'):
            try:
                ss = event['session_start'].replace('Z', '+00:00').split('+')[0]
                dt = datetime.fromisoformat(ss)
                current_time = dt.time()
            except:
                pass
        
        new_time = st.time_input(
            "Time",
            value=current_time,
            key=f"edit_time_{event_id}"
        )
    
    # Comment
    new_comment = st.text_area(
        "Notes",
        value=event.get('comment', '') or '',
        key=f"edit_comment_{event_id}"
    )
    
    # Save basic info changes
    if st.button("💾 Save Changes", key=f"save_basic_{event_id}"):
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
        else:
            st.error(f"❌ Update failed: {msg}")
    
    # Attributes editing
    attrs = load_event_attributes(client, user_id, event_id)
    if attrs:
        st.markdown("**Edit Attributes:**")
        
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
    
    # Show attachments (read-only in edit mode)
    attachments = load_event_attachments(client, user_id, event_id)
    if attachments:
        st.markdown("**Attachments:**")
        for att in attachments:
            if att.get('type') == 'image':
                st.image(att['url'], caption=att.get('filename', 'Image'), width=150)


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
