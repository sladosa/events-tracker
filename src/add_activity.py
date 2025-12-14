"""
Events Tracker - Add Activity Module
=====================================
Created: 2025-12-13 15:00 UTC
Last Modified: 2025-12-14 13:00 UTC
Python: 3.11
Version: 1.2.0 - Added photo attachment support

Description:
Mobile-first activity entry form with support for:
- Multiple training sessions per day (triathlete scenario)
- Hierarchical category selection with search
- Session grouping by start time
- Quick add workflow for repeated entries
- Parent category attributes (summary fields)
- Photo attachments via Supabase Storage

CHANGELOG v1.2.0:
- ✨ NEW: Photo attachment support
  - Upload images (jpg, png, webp) up to 5MB
  - Stored in Supabase Storage bucket "activity-attachments"
  - Linked to events via event_attachments table
  - Thumbnails shown in session preview
- 🔧 IMPROVED: Session preview shows attachment indicator (📷)

CHANGELOG v1.1.0:
- 🐛 FIXED: Infinite loop when saving
- 🐛 FIXED: Numeric attributes not saving
- 🐛 FIXED: Session preview blocking
- 🔧 REMOVED: Lock datetime toggle
- 🔧 REMOVED: Session badges from preview

Features:
- 📱 Mobile-optimized touch targets (48px minimum)
- 🔍 Searchable category dropdown
- 📊 Live session preview with thumbnails
- 💾 Save & Add Another workflow
- 📷 Photo attachments

Dependencies: streamlit, datetime, supabase, uuid
"""

import streamlit as st
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple
import uuid


# ============================================
# CONSTANTS & CONFIGURATION
# ============================================

# Time slot presets (icons removed to avoid rendering issues)
TIME_SLOTS = {
    "Morning (6:30)": time(6, 30),
    "Midday (12:00)": time(12, 0),
    "Afternoon (15:30)": time(15, 30),
    "Evening (18:30)": time(18, 30),
    "Night (21:00)": time(21, 0),
}

# Storage configuration
STORAGE_BUCKET = "activity-attachments"
MAX_FILE_SIZE_MB = 5
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]


# ============================================
# STORAGE & ATTACHMENT FUNCTIONS
# ============================================

def upload_to_storage(client, user_id: str, file_data: bytes, filename: str) -> Tuple[bool, str, str]:
    """
    Upload file to Supabase Storage.
    
    Args:
        client: Supabase client
        user_id: Current user's UUID
        file_data: File bytes
        filename: Original filename
        
    Returns:
        Tuple of (success: bool, url: str, error_message: str)
    """
    try:
        # Generate unique path: user_id/timestamp_filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = filename.split('.')[-1].lower()
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_ext}"
        storage_path = f"{user_id}/{unique_filename}"
        
        # Upload to storage
        result = client.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": f"image/{file_ext}"}
        )
        
        # Get public URL
        public_url = client.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
        
        return True, public_url, ""
        
    except Exception as e:
        return False, "", str(e)


def save_attachment(
    client,
    user_id: str,
    event_id: str,
    url: str,
    filename: str,
    size_bytes: int,
    attachment_type: str = "image"
) -> Tuple[bool, str]:
    """
    Save attachment record to event_attachments table.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        record = {
            'event_id': event_id,
            'user_id': user_id,
            'type': attachment_type,
            'url': url,
            'filename': filename,
            'size_bytes': size_bytes
        }
        
        client.table('event_attachments').insert(record).execute()
        return True, "Attachment saved"
        
    except Exception as e:
        return False, str(e)


def load_attachments_for_events(client, user_id: str, event_ids: List[str]) -> Dict[str, List[Dict]]:
    """
    Load attachments for multiple events.
    
    Returns:
        Dict mapping event_id to list of attachments
    """
    if not event_ids:
        return {}
    
    try:
        resp = client.table('event_attachments') \
            .select('event_id, url, filename, type') \
            .eq('user_id', user_id) \
            .in_('event_id', event_ids) \
            .execute()
        
        # Group by event_id
        result = {}
        for att in resp.data:
            eid = att['event_id']
            if eid not in result:
                result[eid] = []
            result[eid].append(att)
        
        return result
        
    except Exception:
        return {}


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


def load_todays_sessions(client, user_id: str, target_date: date) -> Tuple[List[Dict], List[str]]:
    """
    Load all sessions for a specific date.
    
    v1.2.0: Returns event_ids for attachment lookup.
    
    Returns:
        Tuple of (events list, event_ids list)
    """
    try:
        # Query events for this date
        resp = client.table('events') \
            .select('id, category_id, session_start, event_date, comment, categories(name)') \
            .eq('user_id', user_id) \
            .eq('event_date', target_date.isoformat()) \
            .order('session_start', desc=False) \
            .execute()
        
        if not resp.data:
            return [], []
        
        # Simple list of events (no complex grouping)
        events = []
        event_ids = []
        for event in resp.data:
            event_ids.append(event['id'])
            
            # Safe datetime parsing
            time_str = "??:??"
            if event.get('session_start'):
                try:
                    # Handle various datetime formats
                    ss = event['session_start']
                    if isinstance(ss, str):
                        # Remove timezone suffix for parsing
                        ss = ss.replace('Z', '+00:00')
                        if '+' in ss:
                            ss = ss.split('+')[0]
                        session_dt = datetime.fromisoformat(ss)
                        time_str = session_dt.strftime('%H:%M')
                except Exception:
                    time_str = "??:??"
            
            events.append({
                'id': event['id'],
                'time_str': time_str,
                'category_name': event.get('categories', {}).get('name', 'Unknown') if event.get('categories') else 'Unknown',
                'comment': event.get('comment', '') or ''
            })
        
        return events, event_ids
        
    except Exception as e:
        st.error(f"Error loading sessions: {e}")
        return [], []


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
) -> Tuple[bool, str, Optional[str]]:
    """
    Save activity event with attributes.
    
    v1.2.0: Now returns event_id for attachment linking.
    
    Returns: (success: bool, message: str, event_id: Optional[str])
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
            return False, "Failed to create event", None
        
        event_id = event_resp.data[0]['id']
        
        # 2. Save attributes (EAV pattern)
        saved_count = 0
        if attributes:
            attr_records = []
            for attr_def_id, value in attributes.items():
                # Skip only None and empty string, NOT 0 or 0.0
                if value is None:
                    continue
                if isinstance(value, str) and value.strip() == '':
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
                    record['value_number'] = float(value)  # Ensure float
                elif isinstance(value, datetime):
                    record['value_datetime'] = value.isoformat()
                elif isinstance(value, date):
                    record['value_datetime'] = datetime.combine(value, time(0, 0)).isoformat()
                else:
                    record['value_text'] = str(value)
                
                attr_records.append(record)
            
            if attr_records:
                client.table('event_attributes').insert(attr_records).execute()
                saved_count = len(attr_records)
        
        return True, f"Activity saved! ({saved_count} attributes)", event_id
        
    except Exception as e:
        return False, f"Error saving: {str(e)}", None
        return False, f"Error saving: {str(e)}"


# ============================================
# UI COMPONENTS
# ============================================

def render_mobile_header() -> Tuple[date, time]:
    """
    Render header with date and time selection.
    
    v1.1.0: Simplified - removed lock toggle, always allows editing.
    Quick presets now use session state properly.
    """
    
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
    </style>
    """, unsafe_allow_html=True)
    
    st.subheader("🏋️ Add Activity")
    
    # Initialize session state for date/time
    if 'activity_date' not in st.session_state:
        st.session_state.activity_date = date.today()
    if 'activity_time' not in st.session_state:
        st.session_state.activity_time = datetime.now().time().replace(second=0, microsecond=0)
    
    # Date and time in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        new_date = st.date_input(
            "📅 Date",
            value=st.session_state.activity_date,
            key="activity_date_input",
            help="Select activity date"
        )
        st.session_state.activity_date = new_date
    
    with col2:
        new_time = st.time_input(
            "⏰ Time",
            value=st.session_state.activity_time,
            key="activity_time_input",
            step=300,  # 5 minute increments
            help="Session start time"
        )
        st.session_state.activity_time = new_time
    
    # Quick time presets - v1.1.0: Use form to avoid rerun issues
    st.caption("Quick presets:")
    preset_cols = st.columns(5)
    for i, (label, preset_time) in enumerate(TIME_SLOTS.items()):
        with preset_cols[i]:
            # Short label for button
            short_label = label.split('(')[0].strip()[:4]
            if st.button(short_label, key=f"preset_{i}", use_container_width=True):
                st.session_state.activity_time = preset_time
                st.rerun()
    
    return st.session_state.activity_date, st.session_state.activity_time


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
        default_num = None  # Use None to show empty field
        if default:
            try:
                default_num = float(default)
            except:
                pass
        
        return st.number_input(
            label,
            value=default_num,
            step=1.0,
            format="%.2f",
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
        default_bool = default and str(default).lower() in ('true', '1', 'yes')
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


def render_session_preview(events: List[Dict], attachments: Dict[str, List[Dict]] = None):
    """
    Render today's session preview panel.
    
    v1.2.0: Shows 📷 indicator for events with attachments.
    
    Args:
        events: List of event dicts
        attachments: Dict mapping event_id to list of attachments
    """
    
    if not events:
        st.caption("📊 No activities recorded today yet")
        return
    
    if attachments is None:
        attachments = {}
    
    st.caption(f"📊 Today: {len(events)} activities")
    
    # Simple table-like display
    for event in events:
        time_str = event.get('time_str', '??:??')
        cat_name = event.get('category_name', 'Unknown')
        comment = event.get('comment', '')
        event_id = event.get('id', '')
        
        # Check for attachments
        has_attachment = event_id in attachments and len(attachments[event_id]) > 0
        photo_icon = " 📷" if has_attachment else ""
        
        # One-line display
        display = f"**{time_str}** - {cat_name}{photo_icon}"
        if comment:
            display += f" _{comment[:30]}{'...' if len(comment) > 30 else ''}_"
        
        st.markdown(display)


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render_add_activity(client, user_id: str):
    """
    Main entry point for Add Activity page.
    
    v1.2.0: Added photo attachment support.
    
    Args:
        client: Supabase client
        user_id: Current user's UUID
    """
    
    # Initialize session state
    if 'activity_last_category' not in st.session_state:
        st.session_state.activity_last_category = None
    if 'activity_save_success' not in st.session_state:
        st.session_state.activity_save_success = False
    if 'activity_save_message' not in st.session_state:
        st.session_state.activity_save_message = ""
    if 'activity_file_counter' not in st.session_state:
        st.session_state.activity_file_counter = 0
    
    # Check for success message from previous save
    if st.session_state.activity_save_success:
        st.success(f"✅ {st.session_state.activity_save_message}")
        st.session_state.activity_save_success = False
        st.session_state.activity_save_message = ""
    
    # Load category tree once
    cat_tree = load_category_tree(client, user_id)
    
    # ─────────────────────────────────────────
    # HEADER: Date & Time
    # ─────────────────────────────────────────
    selected_date, selected_time = render_mobile_header()
    
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
        events, event_ids = load_todays_sessions(client, user_id, selected_date)
        attachments = load_attachments_for_events(client, user_id, event_ids) if event_ids else {}
        render_session_preview(events, attachments)
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
    # PHOTO ATTACHMENT (Optional)
    # ─────────────────────────────────────────
    with st.expander("📷 Add Photo (optional)", expanded=False):
        uploaded_file = st.file_uploader(
            "Upload image",
            type=ALLOWED_IMAGE_TYPES,
            help=f"Max {MAX_FILE_SIZE_MB}MB. Supported: JPG, PNG, WebP",
            key=f"activity_photo_{st.session_state.activity_file_counter}"
        )
        
        if uploaded_file:
            # Validate file size
            file_size = len(uploaded_file.getvalue())
            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f"❌ File too large! Max {MAX_FILE_SIZE_MB}MB")
                uploaded_file = None
            else:
                # Show preview
                st.image(uploaded_file, caption=uploaded_file.name, width=200)
                st.caption(f"Size: {file_size / 1024:.1f} KB")
    
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
    events, event_ids = load_todays_sessions(client, user_id, selected_date)
    attachments = load_attachments_for_events(client, user_id, event_ids) if event_ids else {}
    render_session_preview(events, attachments)
    
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
        session_start = datetime.combine(selected_date, selected_time)
        
        success, message, event_id = save_activity_event(
            client=client,
            user_id=user_id,
            category_id=selected_cat['id'],
            session_start=session_start,
            comment=comment,
            attributes=all_attributes
        )
        
        if success and event_id:
            # Handle photo attachment if present
            attachment_msg = ""
            if uploaded_file:
                file_data = uploaded_file.getvalue()
                upload_ok, url, error = upload_to_storage(
                    client, user_id, file_data, uploaded_file.name
                )
                
                if upload_ok:
                    save_ok, _ = save_attachment(
                        client, user_id, event_id, url,
                        uploaded_file.name, len(file_data), "image"
                    )
                    if save_ok:
                        attachment_msg = " + 📷 photo"
                else:
                    st.warning(f"⚠️ Photo upload failed: {error}")
            
            final_message = message + attachment_msg
            
            if save_and_add:
                # Set success message for next render
                st.session_state.activity_save_success = True
                st.session_state.activity_save_message = final_message
                # Increment file counter to reset uploader
                st.session_state.activity_file_counter += 1
                # Keep category, reset time to now
                st.session_state.activity_time = datetime.now().time().replace(second=0, microsecond=0)
                st.rerun()
            else:
                # Save & Finish - show success and clear
                st.success(f"✅ {final_message}")
                st.session_state.activity_last_category = None
                st.session_state.activity_file_counter += 1
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
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    st.title("Add Activity - Test Mode")
    st.warning("This is a test page. Run from main app for full functionality.")
