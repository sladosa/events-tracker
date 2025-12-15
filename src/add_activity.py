"""
Events Tracker - Add Activity Module
=====================================
Created: 2025-12-13 15:00 UTC
Last Modified: 2025-12-15 09:30 UTC
Python: 3.11
Version: 2.0.0 - Major UI/UX overhaul

Description:
Mobile-first activity entry form with:
- Filter-first design (Area → Category drill-down)
- Shortcuts for frequently used filter combinations
- Optimized layout for minimal scrolling
- Photo attachments via Supabase Storage

CHANGELOG v2.0.0:
- 🎯 NEW: Filter by Area + Drill-down to Category (ISV-style)
- 🎯 NEW: Shortcuts system (save/load filter combinations)
- 🎯 NEW: Shortcuts stored in activity_presets table
- 🔧 REMOVED: Quick time presets (simplify UI)
- 🔧 MOVED: Save buttons closer to top (less scrolling)
- 🔧 MOVED: Recent Activities to bottom (max 10)
- 🔧 IMPROVED: Time default is local time (HH:MM)
- 📱 IMPROVED: Mobile-optimized layout

Previous versions:
- v1.2.0: Photo attachments
- v1.1.0: Bug fixes (infinite loop, numeric attributes)

Dependencies: streamlit, datetime, supabase, uuid
"""

import streamlit as st
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple
import uuid


# ============================================
# CONSTANTS & CONFIGURATION
# ============================================

STORAGE_BUCKET = "activity-attachments"
MAX_FILE_SIZE_MB = 5
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]
MAX_RECENT_ACTIVITIES = 10


# ============================================
# STORAGE & ATTACHMENT FUNCTIONS
# ============================================

def upload_to_storage(client, user_id: str, file_data: bytes, filename: str) -> Tuple[bool, str, str]:
    """Upload file to Supabase Storage."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = filename.split('.')[-1].lower()
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_ext}"
        storage_path = f"{user_id}/{unique_filename}"
        
        client.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": f"image/{file_ext}"}
        )
        
        public_url = client.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
        return True, public_url, ""
        
    except Exception as e:
        return False, "", str(e)


def save_attachment(client, user_id: str, event_id: str, url: str, 
                   filename: str, size_bytes: int) -> Tuple[bool, str]:
    """Save attachment record to event_attachments table."""
    try:
        record = {
            'event_id': event_id,
            'user_id': user_id,
            'type': 'image',
            'url': url,
            'filename': filename,
            'size_bytes': size_bytes
        }
        client.table('event_attachments').insert(record).execute()
        return True, "Attachment saved"
    except Exception as e:
        return False, str(e)


def load_attachments_for_events(client, user_id: str, event_ids: List[str]) -> Dict[str, List[Dict]]:
    """Load attachments for multiple events."""
    if not event_ids:
        return {}
    
    try:
        resp = client.table('event_attachments') \
            .select('event_id, url, filename, type') \
            .eq('user_id', user_id) \
            .in_('event_id', event_ids) \
            .execute()
        
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
# SHORTCUT (PRESET) FUNCTIONS
# ============================================

def load_shortcuts(client, user_id: str) -> List[Dict]:
    """Load user's shortcuts sorted by usage."""
    try:
        resp = client.table('activity_presets') \
            .select('id, name, area_id, category_id, usage_count') \
            .eq('user_id', user_id) \
            .order('usage_count', desc=True) \
            .order('last_used', desc=True) \
            .limit(20) \
            .execute()
        return resp.data or []
    except Exception:
        return []


def save_shortcut(client, user_id: str, name: str, area_id: str, 
                  category_id: Optional[str]) -> Tuple[bool, str]:
    """Save a new shortcut."""
    try:
        record = {
            'user_id': user_id,
            'name': name,
            'area_id': area_id,
            'category_id': category_id,
            'usage_count': 0,
            'last_used': datetime.now().isoformat()
        }
        client.table('activity_presets').insert(record).execute()
        return True, f"Shortcut '{name}' saved!"
    except Exception as e:
        if 'unique' in str(e).lower():
            return False, f"Shortcut '{name}' already exists"
        return False, str(e)


def update_shortcut_usage(client, user_id: str, shortcut_id: str):
    """Increment usage counter for shortcut."""
    try:
        # Get current count
        resp = client.table('activity_presets') \
            .select('usage_count') \
            .eq('id', shortcut_id) \
            .eq('user_id', user_id) \
            .single() \
            .execute()
        
        if resp.data:
            new_count = (resp.data.get('usage_count') or 0) + 1
            client.table('activity_presets') \
                .update({
                    'usage_count': new_count,
                    'last_used': datetime.now().isoformat()
                }) \
                .eq('id', shortcut_id) \
                .eq('user_id', user_id) \
                .execute()
    except Exception:
        pass  # Silent fail - not critical


def delete_shortcut(client, user_id: str, shortcut_id: str) -> Tuple[bool, str]:
    """Delete a shortcut."""
    try:
        client.table('activity_presets') \
            .delete() \
            .eq('id', shortcut_id) \
            .eq('user_id', user_id) \
            .execute()
        return True, "Shortcut deleted"
    except Exception as e:
        return False, str(e)


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
        
        # Build full paths
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
        
        # Sort by path for nice display
        result.sort(key=lambda x: x['full_path'])
        return result
        
    except Exception:
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
        return resp.data or []
    except Exception:
        return []


def load_category_chain(client, user_id: str, category_id: str, 
                        categories: List[Dict]) -> List[Dict]:
    """Get category and all its ancestors for inherited attributes."""
    cat_dict = {c['id']: c for c in categories}
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


def load_recent_activities(client, user_id: str, target_date: date) -> Tuple[List[Dict], List[str]]:
    """Load recent activities for a specific date (max 10)."""
    try:
        resp = client.table('events') \
            .select('id, category_id, session_start, comment, categories(name)') \
            .eq('user_id', user_id) \
            .eq('event_date', target_date.isoformat()) \
            .order('session_start', desc=True) \
            .limit(MAX_RECENT_ACTIVITIES) \
            .execute()
        
        if not resp.data:
            return [], []
        
        events = []
        event_ids = []
        for event in resp.data:
            event_ids.append(event['id'])
            
            time_str = "??:??"
            if event.get('session_start'):
                try:
                    ss = event['session_start']
                    if isinstance(ss, str):
                        ss = ss.replace('Z', '+00:00').split('+')[0]
                        session_dt = datetime.fromisoformat(ss)
                        time_str = session_dt.strftime('%H:%M')
                except Exception:
                    pass
            
            cat_name = 'Unknown'
            if event.get('categories') and isinstance(event['categories'], dict):
                cat_name = event['categories'].get('name', 'Unknown')
            
            events.append({
                'id': event['id'],
                'time_str': time_str,
                'category_name': cat_name,
                'comment': event.get('comment') or ''
            })
        
        return events, event_ids
        
    except Exception:
        return [], []


# ============================================
# SAVE FUNCTIONS
# ============================================

def save_activity_event(client, user_id: str, category_id: str, 
                        session_start: datetime, comment: str,
                        attributes: Dict[str, any]) -> Tuple[bool, str, Optional[str]]:
    """Save activity event with attributes."""
    try:
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
        
        # Save attributes (EAV pattern)
        saved_count = 0
        if attributes:
            attr_records = []
            for attr_def_id, value in attributes.items():
                if value is None:
                    continue
                if isinstance(value, str) and value.strip() == '':
                    continue
                    
                record = {
                    'event_id': event_id,
                    'attribute_definition_id': attr_def_id,
                    'user_id': user_id
                }
                
                if isinstance(value, bool):
                    record['value_boolean'] = value
                elif isinstance(value, (int, float)):
                    record['value_number'] = float(value)
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


# ============================================
# UI COMPONENTS
# ============================================

def render_attribute_input(attr: Dict, key_prefix: str) -> any:
    """Render appropriate input widget based on attribute data type."""
    attr_id = attr['id']
    attr_name = attr['name']
    data_type = attr['data_type']
    unit = attr.get('unit', '')
    is_required = attr.get('is_required', False)
    default = attr.get('default_value')
    
    label = attr_name
    if unit:
        label += f" ({unit})"
    if is_required:
        label += " *"
    
    key = f"{key_prefix}_{attr_id}"
    
    if data_type == 'number':
        default_num = None
        if default:
            try:
                default_num = float(default)
            except:
                pass
        
        return st.number_input(
            label, value=default_num, step=1.0, format="%.2f",
            key=key, help=attr.get('description', '')
        )
    
    elif data_type == 'text':
        return st.text_input(
            label, value=default or '', key=key,
            help=attr.get('description', '')
        )
    
    elif data_type == 'boolean':
        default_bool = default and str(default).lower() in ('true', '1', 'yes')
        return st.checkbox(
            label, value=default_bool, key=key,
            help=attr.get('description', '')
        )
    
    elif data_type == 'datetime':
        return st.date_input(
            label, value=date.today(), key=key,
            help=attr.get('description', '')
        )
    
    else:
        return st.text_input(
            label, value=default or '', key=key,
            help=attr.get('description', '')
        )


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render_add_activity(client, user_id: str):
    """
    Main entry point for Add Activity page.
    
    v2.0.0: Complete UI overhaul with filters on top.
    """
    
    # Mobile CSS
    st.markdown("""
    <style>
    .stButton > button { min-height: 48px !important; font-size: 16px !important; }
    .stSelectbox, .stTextInput, .stNumberInput { min-height: 48px !important; }
    div[data-testid="stNumberInput"] input { font-size: 18px !important; min-height: 48px !important; }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'aa_area_id' not in st.session_state:
        st.session_state.aa_area_id = None
    if 'aa_category_id' not in st.session_state:
        st.session_state.aa_category_id = None
    if 'aa_save_success' not in st.session_state:
        st.session_state.aa_save_success = False
    if 'aa_save_message' not in st.session_state:
        st.session_state.aa_save_message = ""
    if 'aa_file_counter' not in st.session_state:
        st.session_state.aa_file_counter = 0
    
    # Show success message from previous save
    if st.session_state.aa_save_success:
        st.success(f"✅ {st.session_state.aa_save_message}")
        st.session_state.aa_save_success = False
        st.session_state.aa_save_message = ""
    
    st.subheader("🏋️ Add Activity")
    
    # Load data
    areas = load_areas(client, user_id)
    shortcuts = load_shortcuts(client, user_id)
    
    if not areas:
        st.warning("No areas defined. Please create structure first in Interactive Structure Viewer.")
        return
    
    # ─────────────────────────────────────────
    # ROW 1: SHORTCUTS
    # ─────────────────────────────────────────
    if shortcuts:
        shortcut_col, manage_col = st.columns([4, 1])
        
        with shortcut_col:
            shortcut_options = ["-- Quick Select --"] + [s['name'] for s in shortcuts]
            selected_shortcut = st.selectbox(
                "⚡ Shortcuts",
                shortcut_options,
                key="aa_shortcut_select",
                help="Select a saved shortcut to auto-fill filters"
            )
            
            if selected_shortcut != "-- Quick Select --":
                # Find and apply shortcut
                for sc in shortcuts:
                    if sc['name'] == selected_shortcut:
                        st.session_state.aa_area_id = sc['area_id']
                        st.session_state.aa_category_id = sc['category_id']
                        update_shortcut_usage(client, user_id, sc['id'])
                        break
        
        with manage_col:
            st.write("")  # Spacing
            if st.button("🗑️", key="manage_shortcuts", help="Delete shortcuts"):
                st.session_state.aa_show_shortcut_manager = True
    
    # Shortcut manager popup
    if st.session_state.get('aa_show_shortcut_manager', False):
        with st.expander("🗑️ Manage Shortcuts", expanded=True):
            for sc in shortcuts:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"{sc['name']} ({sc['usage_count']} uses)")
                with col2:
                    if st.button("❌", key=f"del_sc_{sc['id']}"):
                        success, _ = delete_shortcut(client, user_id, sc['id'])
                        if success:
                            st.rerun()
            
            if st.button("Close"):
                st.session_state.aa_show_shortcut_manager = False
                st.rerun()
    
    # ─────────────────────────────────────────
    # ROW 2: AREA + CATEGORY FILTERS
    # ─────────────────────────────────────────
    area_col, cat_col = st.columns(2)
    
    with area_col:
        area_options = {a['id']: f"{a.get('icon', '📦')} {a['name']}" for a in areas}
        area_ids = list(area_options.keys())
        
        # Find current index
        current_area_idx = 0
        if st.session_state.aa_area_id in area_ids:
            current_area_idx = area_ids.index(st.session_state.aa_area_id)
        
        selected_area_id = st.selectbox(
            "📦 Area",
            options=area_ids,
            format_func=lambda x: area_options[x],
            index=current_area_idx,
            key="aa_area_filter"
        )
        
        # Update state if changed
        if selected_area_id != st.session_state.aa_area_id:
            st.session_state.aa_area_id = selected_area_id
            st.session_state.aa_category_id = None  # Reset category
    
    # Load categories for selected area
    categories = []
    if st.session_state.aa_area_id:
        categories = load_categories_for_area(client, user_id, st.session_state.aa_area_id)
    
    with cat_col:
        if categories:
            cat_options = {c['id']: c['full_path'] for c in categories}
            cat_ids = list(cat_options.keys())
            
            # Find current index
            current_cat_idx = 0
            if st.session_state.aa_category_id in cat_ids:
                current_cat_idx = cat_ids.index(st.session_state.aa_category_id)
            
            selected_cat_id = st.selectbox(
                "📂 Category",
                options=cat_ids,
                format_func=lambda x: cat_options[x],
                index=current_cat_idx,
                key="aa_category_filter"
            )
            st.session_state.aa_category_id = selected_cat_id
        else:
            st.selectbox("📂 Category", ["Select area first"], disabled=True)
    
    # ─────────────────────────────────────────
    # ROW 3: SAVE SHORTCUT OPTION
    # ─────────────────────────────────────────
    if st.session_state.aa_category_id:
        with st.expander("💾 Save as Shortcut", expanded=False):
            new_shortcut_name = st.text_input(
                "Shortcut name",
                placeholder="e.g., Morning Run, Evening Gym",
                key="aa_new_shortcut_name"
            )
            if st.button("Save Shortcut", key="aa_save_shortcut"):
                if new_shortcut_name.strip():
                    success, msg = save_shortcut(
                        client, user_id, new_shortcut_name.strip(),
                        st.session_state.aa_area_id,
                        st.session_state.aa_category_id
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter a shortcut name")
    
    st.markdown("---")
    
    # ─────────────────────────────────────────
    # ROW 4: DATE & TIME
    # ─────────────────────────────────────────
    if 'aa_date' not in st.session_state:
        st.session_state.aa_date = date.today()
    if 'aa_time' not in st.session_state:
        st.session_state.aa_time = datetime.now().time().replace(second=0, microsecond=0)
    
    date_col, time_col = st.columns(2)
    
    with date_col:
        selected_date = st.date_input(
            "📅 Date",
            value=st.session_state.aa_date,
            key="aa_date_input"
        )
        st.session_state.aa_date = selected_date
    
    with time_col:
        selected_time = st.time_input(
            "⏰ Time",
            value=st.session_state.aa_time,
            step=300,  # 5 minute increments
            key="aa_time_input"
        )
        st.session_state.aa_time = selected_time
    
    # ─────────────────────────────────────────
    # ATTRIBUTES, PHOTO, COMMENT, BUTTONS
    # ─────────────────────────────────────────
    
    if not st.session_state.aa_category_id:
        st.info("👆 Select Area and Category to add activity")
        
        # Still show recent activities
        st.markdown("---")
        events, event_ids = load_recent_activities(client, user_id, selected_date)
        attachments = load_attachments_for_events(client, user_id, event_ids) if event_ids else {}
        render_recent_activities(events, attachments)
        return
    
    # Find selected category info
    selected_cat = None
    for c in categories:
        if c['id'] == st.session_state.aa_category_id:
            selected_cat = c
            break
    
    if not selected_cat:
        st.error("Category not found")
        return
    
    # Get category chain for inherited attributes
    category_chain = load_category_chain(client, user_id, selected_cat['id'], categories)
    
    all_attributes = {}
    
    # Render attributes for each level in chain
    for i, cat in enumerate(category_chain):
        is_leaf = (i == 0)
        attrs = load_attributes_for_category(client, user_id, cat['id'])
        
        if not attrs:
            continue
        
        header = f"🎯 {cat['name']}" if is_leaf else f"📁 {cat['name']} (parent)"
        with st.expander(header, expanded=is_leaf):
            for j in range(0, len(attrs), 2):
                cols = st.columns(2)
                for k, col in enumerate(cols):
                    if j + k < len(attrs):
                        with col:
                            attr = attrs[j + k]
                            value = render_attribute_input(attr, f"attr_{cat['id']}")
                            all_attributes[attr['id']] = value
    
    # Photo attachment
    uploaded_file = None
    with st.expander("📷 Add Photo (optional)", expanded=False):
        uploaded_file = st.file_uploader(
            "Upload image",
            type=ALLOWED_IMAGE_TYPES,
            help=f"Max {MAX_FILE_SIZE_MB}MB. Supported: JPG, PNG, WebP",
            key=f"aa_photo_{st.session_state.aa_file_counter}"
        )
        
        if uploaded_file:
            file_size = len(uploaded_file.getvalue())
            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f"❌ File too large! Max {MAX_FILE_SIZE_MB}MB")
                uploaded_file = None
            else:
                st.image(uploaded_file, caption=uploaded_file.name, width=200)
                st.caption(f"Size: {file_size / 1024:.1f} KB")
    
    # Comment
    comment = st.text_area(
        "💬 Notes (optional)",
        height=68,
        key="aa_comment",
        placeholder="Any additional notes..."
    )
    
    # ─────────────────────────────────────────
    # ACTION BUTTONS (prominent position)
    # ─────────────────────────────────────────
    st.markdown("---")
    
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
            attachment_msg = ""
            if uploaded_file:
                file_data = uploaded_file.getvalue()
                upload_ok, url, error = upload_to_storage(
                    client, user_id, file_data, uploaded_file.name
                )
                
                if upload_ok:
                    save_ok, _ = save_attachment(
                        client, user_id, event_id, url,
                        uploaded_file.name, len(file_data)
                    )
                    if save_ok:
                        attachment_msg = " + 📷 photo"
                else:
                    st.warning(f"⚠️ Photo upload failed: {error}")
            
            final_message = message + attachment_msg
            
            if save_and_add:
                st.session_state.aa_save_success = True
                st.session_state.aa_save_message = final_message
                st.session_state.aa_file_counter += 1
                st.session_state.aa_time = datetime.now().time().replace(second=0, microsecond=0)
                st.rerun()
            else:
                st.success(f"✅ {final_message}")
                st.session_state.aa_file_counter += 1
                st.balloons()
        else:
            st.error(f"❌ {message}")
    
    # ─────────────────────────────────────────
    # RECENT ACTIVITIES (at bottom, max 10)
    # ─────────────────────────────────────────
    st.markdown("---")
    events, event_ids = load_recent_activities(client, user_id, selected_date)
    attachments = load_attachments_for_events(client, user_id, event_ids) if event_ids else {}
    render_recent_activities(events, attachments)


def render_recent_activities(events: List[Dict], attachments: Dict[str, List[Dict]] = None):
    """Render recent activities panel (max 10)."""
    if not events:
        st.caption(f"📊 No activities recorded today yet")
        return
    
    if attachments is None:
        attachments = {}
    
    st.caption(f"📊 Today: {len(events)} activities (showing last {MAX_RECENT_ACTIVITIES})")
    
    for event in events:
        time_str = event.get('time_str', '??:??')
        cat_name = event.get('category_name', 'Unknown')
        comment = event.get('comment', '')
        event_id = event.get('id', '')
        
        has_attachment = event_id in attachments and len(attachments[event_id]) > 0
        photo_icon = " 📷" if has_attachment else ""
        
        display = f"**{time_str}** - {cat_name}{photo_icon}"
        if comment:
            display += f" _{comment[:30]}{'...' if len(comment) > 30 else ''}_"
        
        st.markdown(display)


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
