"""
Events Tracker - Add Activity Module
=====================================
Created: 2025-12-13 15:00 UTC
Last Modified: 2025-12-13 15:00 UTC
Python: 3.11
Version: 1.0.0 - Initial mobile-optimized implementation

Description:
Mobile-first activity entry form with support for:
- Multiple training sessions per day (triathlete scenario)
- Hierarchical category selection with search
- Session grouping by start time
- Quick add workflow for repeated entries
- Parent category attributes (summary fields)

Features:
- 📱 Mobile-optimized touch targets (48px minimum)
- ⏰ Session time tracking (morning/noon/evening badges)
- 🔍 Searchable category dropdown
- 📊 Live session preview
- 💾 Save & Add Another workflow
- 🎯 Sticky date/time header

Dependencies: streamlit, datetime, supabase

Technical Notes:
- Uses session_start (TIMESTAMPTZ) for multi-session support
- Groups events by DATE(session_start) + hour for session separation
- Inherits attributes from parent categories
"""

import streamlit as st
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple
import json


# ============================================
# CONSTANTS & CONFIGURATION
# ============================================

# Time slot presets with icons
TIME_SLOTS = {
    "🌅 Morning": time(6, 30),
    "🌞 Midday": time(12, 0),
    "🌆 Afternoon": time(15, 30),
    "🌙 Evening": time(18, 30),
    "🦉 Night": time(21, 0),
}

# Session badge based on hour
def get_session_badge(hour: int) -> str:
    """Return emoji badge based on hour of day."""
    if 5 <= hour < 10:
        return "🌅"
    elif 10 <= hour < 14:
        return "🌞"
    elif 14 <= hour < 17:
        return "🌆"
    elif 17 <= hour < 21:
        return "🌙"
    else:
        return "🦉"


# ============================================
# DATA LOADING FUNCTIONS
# ============================================

def load_category_tree(client, user_id: str) -> List[Dict]:
    """
    Load full category tree with hierarchy paths.
    
    Returns list of categories with full_path for display:
    [{'id': uuid, 'name': 'Squats', 'full_path': 'Fitness > Strength > Legs > Squats', ...}]
    """
    try:
        # Load areas
        areas_resp = client.table('areas').select('id, name, sort_order') \
            .eq('user_id', user_id).order('sort_order').execute()
        areas = {a['id']: a['name'] for a in areas_resp.data}
        
        # Load all categories with parent info
        cats_resp = client.table('categories') \
            .select('id, name, area_id, parent_category_id, level, sort_order') \
            .eq('user_id', user_id).order('sort_order').execute()
        
        categories = cats_resp.data
        cat_dict = {c['id']: c for c in categories}
        
        # Build full paths
        result = []
        for cat in categories:
            path_parts = []
            
            # Add area name
            if cat['area_id'] in areas:
                path_parts.append(areas[cat['area_id']])
            
            # Build category path (traverse up to root)
            cat_path = []
            current = cat
            while current:
                cat_path.insert(0, current['name'])
                parent_id = current.get('parent_category_id')
                current = cat_dict.get(parent_id) if parent_id else None
            
            path_parts.extend(cat_path)
            
            result.append({
                'id': cat['id'],
                'name': cat['name'],
                'area_id': cat['area_id'],
                'area_name': areas.get(cat['area_id'], ''),
                'level': cat['level'],
                'full_path': ' > '.join(path_parts),
                'parent_category_id': cat.get('parent_category_id')
            })
        
        # Sort by full path for nice display
        result.sort(key=lambda x: x['full_path'])
        return result
        
    except Exception as e:
        st.error(f"Error loading categories: {e}")
        return []


def load_attributes_for_category(client, user_id: str, category_id: str) -> List[Dict]:
    """Load attribute definitions for a category."""
    try:
        resp = client.table('attribute_definitions') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('category_id', category_id) \
            .order('sort_order') \
            .execute()
        return resp.data
    except Exception as e:
        st.error(f"Error loading attributes: {e}")
        return []


def load_category_chain(client, user_id: str, category_id: str, cat_tree: List[Dict]) -> List[Dict]:
    """
    Get category and all its ancestors (for inherited attributes).
    Returns list from leaf to root: [Squats, Legs, Strength, Fitness]
    """
    cat_dict = {c['id']: c for c in cat_tree}
    chain = []
    
    current_id = category_id
    while current_id:
        if current_id in cat_dict:
            cat = cat_dict[current_id]
            chain.append(cat)
            current_id = cat.get('parent_category_id')
        else:
            break
    
    return chain


def load_todays_sessions(client, user_id: str, target_date: date) -> List[Dict]:
    """Load all sessions for a specific date grouped by start time."""
    try:
        # Query events for this date
        start_of_day = datetime.combine(target_date, time(0, 0))
        end_of_day = datetime.combine(target_date + timedelta(days=1), time(0, 0))
        
        resp = client.table('events') \
            .select('id, category_id, session_start, comment, categories(name)') \
            .eq('user_id', user_id) \
            .gte('session_start', start_of_day.isoformat()) \
            .lt('session_start', end_of_day.isoformat()) \
            .order('session_start') \
            .execute()
        
        if not resp.data:
            return []
        
        # Group by session_start hour
        sessions = {}
        for event in resp.data:
            if event.get('session_start'):
                session_time = datetime.fromisoformat(event['session_start'].replace('Z', '+00:00'))
                # Round to nearest hour for grouping
                session_key = session_time.replace(minute=0, second=0, microsecond=0)
                
                if session_key not in sessions:
                    sessions[session_key] = {
                        'time': session_time,
                        'badge': get_session_badge(session_time.hour),
                        'events': []
                    }
                
                sessions[session_key]['events'].append({
                    'id': event['id'],
                    'category_name': event.get('categories', {}).get('name', 'Unknown'),
                    'comment': event.get('comment', '')
                })
        
        # Convert to sorted list
        return sorted(sessions.values(), key=lambda x: x['time'])
        
    except Exception as e:
        st.error(f"Error loading sessions: {e}")
        return []


# ============================================
# SAVE FUNCTIONS
# ============================================

def save_activity_event(
    client, 
    user_id: str, 
    category_id: str, 
    session_start: datetime,
    comment: str,
    attributes: Dict[str, any]
) -> Tuple[bool, str]:
    """
    Save activity event with attributes.
    
    Returns: (success: bool, message: str)
    """
    try:
        # 1. Create event
        event_data = {
            'user_id': user_id,
            'category_id': category_id,
            'event_date': session_start.date().isoformat(),
            'session_start': session_start.isoformat(),
            'comment': comment if comment else None
        }
        
        event_resp = client.table('events').insert(event_data).execute()
        
        if not event_resp.data:
            return False, "Failed to create event"
        
        event_id = event_resp.data[0]['id']
        
        # 2. Save attributes (EAV pattern)
        if attributes:
            attr_records = []
            for attr_def_id, value in attributes.items():
                if value is None or value == '':
                    continue
                    
                record = {
                    'event_id': event_id,
                    'attribute_definition_id': attr_def_id,
                    'user_id': user_id
                }
                
                # Determine value type and set appropriate column
                if isinstance(value, bool):
                    record['value_boolean'] = value
                elif isinstance(value, (int, float)):
                    record['value_number'] = value
                elif isinstance(value, datetime):
                    record['value_datetime'] = value.isoformat()
                else:
                    record['value_text'] = str(value)
                
                attr_records.append(record)
            
            if attr_records:
                client.table('event_attributes').insert(attr_records).execute()
        
        return True, f"Activity saved! (Event ID: {event_id[:8]}...)"
        
    except Exception as e:
        return False, f"Error saving: {str(e)}"


# ============================================
# UI COMPONENTS
# ============================================

def render_mobile_header(selected_date: date, selected_time: time) -> Tuple[date, time]:
    """Render sticky header with date and time selection."""
    
    # Apply mobile-friendly CSS
    st.markdown("""
    <style>
    /* Mobile optimizations */
    .stButton > button {
        min-height: 48px !important;
        font-size: 16px !important;
    }
    .stSelectbox, .stTextInput, .stNumberInput {
        min-height: 48px !important;
    }
    div[data-testid="stNumberInput"] input {
        font-size: 18px !important;
        min-height: 48px !important;
    }
    /* Session card styling */
    .session-card {
        background: #f0f2f6;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    .session-badge {
        font-size: 24px;
        margin-right: 8px;
    }
    /* Quick time buttons */
    .time-preset-btn {
        padding: 8px 12px;
        margin: 4px;
        border-radius: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.subheader("🏋️ Add Activity")
    
    # Date and time in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        new_date = st.date_input(
            "📅 Date",
            value=selected_date,
            key="activity_date",
            help="Select activity date"
        )
    
    with col2:
        new_time = st.time_input(
            "⏰ Time",
            value=selected_time,
            key="activity_time",
            step=300,  # 5 minute increments
            help="Session start time"
        )
    
    # Quick time presets
    st.caption("Quick presets:")
    preset_cols = st.columns(len(TIME_SLOTS))
    for i, (label, preset_time) in enumerate(TIME_SLOTS.items()):
        with preset_cols[i]:
            if st.button(label.split()[0], key=f"preset_{i}", use_container_width=True):
                new_time = preset_time
                st.rerun()
    
    return new_date, new_time


def render_category_selector(cat_tree: List[Dict], current_selection: Optional[str] = None) -> Optional[Dict]:
    """Render searchable category dropdown."""
    
    if not cat_tree:
        st.warning("No categories found. Please create categories first.")
        return None
    
    # Build options list
    options = ["-- Select Category --"] + [c['full_path'] for c in cat_tree]
    
    # Find current index
    current_idx = 0
    if current_selection:
        for i, cat in enumerate(cat_tree):
            if cat['id'] == current_selection:
                current_idx = i + 1
                break
    
    selected_path = st.selectbox(
        "📂 Category",
        options=options,
        index=current_idx,
        key="category_selector",
        help="Search or select activity category"
    )
    
    if selected_path == "-- Select Category --":
        return None
    
    # Find selected category
    for cat in cat_tree:
        if cat['full_path'] == selected_path:
            return cat
    
    return None


def render_attribute_input(attr: Dict, key_prefix: str) -> any:
    """Render appropriate input widget based on attribute data type."""
    
    attr_id = attr['id']
    attr_name = attr['name']
    data_type = attr['data_type']
    unit = attr.get('unit', '')
    is_required = attr.get('is_required', False)
    default = attr.get('default_value')
    
    # Build label
    label = f"{attr_name}"
    if unit:
        label += f" ({unit})"
    if is_required:
        label += " *"
    
    key = f"{key_prefix}_{attr_id}"
    
    if data_type == 'number':
        # Parse default value
        default_num = 0.0
        if default:
            try:
                default_num = float(default)
            except:
                pass
        
        return st.number_input(
            label,
            value=default_num,
            step=1.0,
            key=key,
            help=attr.get('description', '')
        )
    
    elif data_type == 'text':
        return st.text_input(
            label,
            value=default or '',
            key=key,
            help=attr.get('description', '')
        )
    
    elif data_type == 'boolean':
        default_bool = default and default.lower() in ('true', '1', 'yes')
        return st.checkbox(
            label,
            value=default_bool,
            key=key,
            help=attr.get('description', '')
        )
    
    elif data_type == 'datetime':
        return st.date_input(
            label,
            value=date.today(),
            key=key,
            help=attr.get('description', '')
        )
    
    else:  # link, image, other
        return st.text_input(
            label,
            value=default or '',
            key=key,
            help=attr.get('description', '')
        )


def render_attribute_section(
    client, 
    user_id: str, 
    category: Dict, 
    key_prefix: str,
    expanded: bool = True,
    show_header: bool = True
) -> Dict[str, any]:
    """
    Render attribute inputs for a category.
    Returns dict of {attr_id: value}
    """
    attrs = load_attributes_for_category(client, user_id, category['id'])
    
    if not attrs:
        return {}
    
    values = {}
    
    if show_header:
        with st.expander(f"**{category['name']}** attributes", expanded=expanded):
            # Render in 2-column grid for mobile
            for i in range(0, len(attrs), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(attrs):
                        with col:
                            attr = attrs[i + j]
                            values[attr['id']] = render_attribute_input(attr, key_prefix)
    else:
        for i in range(0, len(attrs), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(attrs):
                    with col:
                        attr = attrs[i + j]
                        values[attr['id']] = render_attribute_input(attr, key_prefix)
    
    return values


def render_session_preview(sessions: List[Dict], current_category: Optional[str] = None):
    """Render today's session preview panel."""
    
    if not sessions:
        st.caption("📊 No activities recorded today yet")
        return
    
    total_events = sum(len(s['events']) for s in sessions)
    st.caption(f"📊 Today: {len(sessions)} session(s), {total_events} activities")
    
    for session in sessions:
        badge = session['badge']
        time_str = session['time'].strftime('%H:%M')
        event_count = len(session['events'])
        
        with st.container():
            st.markdown(f"""
            <div style="background:#f0f2f6; border-radius:8px; padding:8px; margin:4px 0;">
                <span style="font-size:20px;">{badge}</span>
                <strong>{time_str}</strong> 
                <span style="color:#666;">({event_count} activities)</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Show event names
            event_names = [e['category_name'] for e in session['events']]
            st.caption(", ".join(event_names[:5]) + ("..." if len(event_names) > 5 else ""))


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render_add_activity(client, user_id: str):
    """
    Main entry point for Add Activity page.
    
    Args:
        client: Supabase client
        user_id: Current user's UUID
    """
    
    # Initialize session state
    if 'activity_selected_date' not in st.session_state:
        st.session_state.activity_selected_date = date.today()
    if 'activity_selected_time' not in st.session_state:
        st.session_state.activity_selected_time = datetime.now().time().replace(second=0, microsecond=0)
    if 'activity_last_category' not in st.session_state:
        st.session_state.activity_last_category = None
    if 'activity_lock_datetime' not in st.session_state:
        st.session_state.activity_lock_datetime = False
    
    # Load category tree once
    cat_tree = load_category_tree(client, user_id)
    
    # ─────────────────────────────────────────
    # HEADER: Date & Time
    # ─────────────────────────────────────────
    selected_date, selected_time = render_mobile_header(
        st.session_state.activity_selected_date,
        st.session_state.activity_selected_time
    )
    
    # Lock checkbox
    lock_datetime = st.checkbox(
        "🔒 Lock date/time for session",
        value=st.session_state.activity_lock_datetime,
        help="Keep same date/time when adding multiple activities"
    )
    st.session_state.activity_lock_datetime = lock_datetime
    
    if not lock_datetime:
        st.session_state.activity_selected_date = selected_date
        st.session_state.activity_selected_time = selected_time
    
    st.markdown("---")
    
    # ─────────────────────────────────────────
    # CATEGORY SELECTION
    # ─────────────────────────────────────────
    selected_cat = render_category_selector(
        cat_tree, 
        st.session_state.activity_last_category
    )
    
    if not selected_cat:
        st.info("👆 Select a category to add activity")
        
        # Still show today's sessions
        st.markdown("---")
        sessions = load_todays_sessions(client, user_id, selected_date)
        render_session_preview(sessions)
        return
    
    # Remember selection
    st.session_state.activity_last_category = selected_cat['id']
    
    st.markdown("---")
    
    # ─────────────────────────────────────────
    # ATTRIBUTE INPUTS
    # ─────────────────────────────────────────
    
    # Get category chain (leaf to root)
    category_chain = load_category_chain(client, user_id, selected_cat['id'], cat_tree)
    
    all_attributes = {}
    
    # Render attributes for each level
    for i, cat in enumerate(category_chain):
        is_leaf = (i == 0)
        
        # Load attributes for this category
        attrs = load_attributes_for_category(client, user_id, cat['id'])
        
        if not attrs:
            continue
        
        # Leaf category expanded by default, parents collapsed
        expanded = is_leaf
        header_icon = "🎯" if is_leaf else "📁"
        
        with st.expander(
            f"{header_icon} {cat['name']} {'(selected)' if is_leaf else '(parent)'}", 
            expanded=expanded
        ):
            # Render in 2-column grid
            for j in range(0, len(attrs), 2):
                cols = st.columns(2)
                for k, col in enumerate(cols):
                    if j + k < len(attrs):
                        with col:
                            attr = attrs[j + k]
                            value = render_attribute_input(attr, f"attr_{cat['id']}")
                            all_attributes[attr['id']] = value
    
    # ─────────────────────────────────────────
    # COMMENT (Optional)
    # ─────────────────────────────────────────
    comment = st.text_area(
        "💬 Notes (optional)",
        height=68,
        key="activity_comment",
        placeholder="Any additional notes..."
    )
    
    st.markdown("---")
    
    # ─────────────────────────────────────────
    # TODAY'S SESSION PREVIEW
    # ─────────────────────────────────────────
    sessions = load_todays_sessions(client, user_id, selected_date)
    render_session_preview(sessions, selected_cat['name'])
    
    st.markdown("---")
    
    # ─────────────────────────────────────────
    # ACTION BUTTONS
    # ─────────────────────────────────────────
    
    col1, col2 = st.columns(2)
    
    with col1:
        save_and_add = st.button(
            "💾 Save & Add Another",
            use_container_width=True,
            type="secondary"
        )
    
    with col2:
        save_and_finish = st.button(
            "✓ Save & Finish",
            use_container_width=True,
            type="primary"
        )
    
    # Handle save actions
    if save_and_add or save_and_finish:
        # Combine date and time
        session_start = datetime.combine(
            st.session_state.activity_selected_date,
            st.session_state.activity_selected_time
        )
        
        success, message = save_activity_event(
            client=client,
            user_id=user_id,
            category_id=selected_cat['id'],
            session_start=session_start,
            comment=comment,
            attributes=all_attributes
        )
        
        if success:
            st.success(f"✅ {message}")
            
            if save_and_add:
                # Lock datetime for session continuity
                st.session_state.activity_lock_datetime = True
                # Clear form but keep category
                st.rerun()
            else:
                # Clear everything
                st.session_state.activity_last_category = None
                st.session_state.activity_lock_datetime = False
                st.balloons()
        else:
            st.error(f"❌ {message}")


# ============================================
# STANDALONE TEST
# ============================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Add Activity",
        page_icon="🏋️",
        layout="centered",  # Better for mobile
        initial_sidebar_state="collapsed"
    )
    
    st.title("Add Activity - Test Mode")
    st.warning("This is a test page. Run from main app for full functionality.")
