"""
Event Entry Module
==================
Created: 2025-11-13 09:25 UTC
Last Modified: 2025-11-13 09:25 UTC
Python: 3.11

Single event entry form with:
- Dynamic category selection (hierarchical)
- Dynamic attribute inputs based on category
- Mobile-optimized layout
- Form validation
- "Sticky" last-used category for quick entry
"""

import streamlit as st
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
import json


def get_areas(client, user_id: str) -> List[Dict]:
    """Fetch all areas for user"""
    try:
        response = client.table('areas')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('sort_order')\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching areas: {str(e)}")
        return []


def get_categories_for_area(client, area_id: str, user_id: str) -> List[Dict]:
    """Fetch all categories for a specific area"""
    try:
        response = client.table('categories')\
            .select('*')\
            .eq('area_id', area_id)\
            .eq('user_id', user_id)\
            .order('level, sort_order')\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching categories: {str(e)}")
        return []


def get_attributes_for_category(client, category_id: str) -> List[Dict]:
    """Fetch all attributes for a specific category"""
    try:
        response = client.table('attribute_definitions')\
            .select('*')\
            .eq('category_id', category_id)\
            .order('sort_order')\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching attributes: {str(e)}")
        return []


def build_category_path_map(categories: List[Dict]) -> Dict[str, str]:
    """Build a map of category_id -> full hierarchical path name"""
    cat_map = {cat['id']: cat for cat in categories}
    path_map = {}
    
    def get_full_path(cat_id: str) -> str:
        cat = cat_map.get(cat_id)
        if not cat:
            return ""
        
        if cat['parent_category_id'] and cat['parent_category_id'] in cat_map:
            parent_path = get_full_path(cat['parent_category_id'])
            return f"{parent_path} → {cat['name']}"
        else:
            return cat['name']
    
    for cat_id in cat_map:
        path_map[cat_id] = get_full_path(cat_id)
    
    return path_map


def render_attribute_input(attr: Dict, key_prefix: str) -> Optional[any]:
    """
    Render appropriate input widget based on attribute data type
    
    Returns:
        The input value or None if not provided
    """
    attr_name = attr['name']
    data_type = attr['data_type']
    is_required = attr.get('is_required', False)
    default_value = attr.get('default_value')
    unit = attr.get('unit', '')
    
    # Build label
    label = f"{attr_name}"
    if unit:
        label += f" ({unit})"
    if is_required:
        label += " *"
    
    # Unique key for this input
    input_key = f"{key_prefix}_{attr['id']}"
    
    # Render based on data type
    if data_type == 'number':
        value = st.number_input(
            label,
            value=float(default_value) if default_value else 0.0,
            key=input_key,
            help=f"Type: Number{' (Required)' if is_required else ''}"
        )
        return value if value != 0.0 or is_required else None
    
    elif data_type == 'text':
        value = st.text_input(
            label,
            value=default_value or "",
            key=input_key,
            help=f"Type: Text{' (Required)' if is_required else ''}"
        )
        return value if value else None
    
    elif data_type == 'datetime':
        col1, col2 = st.columns(2)
        with col1:
            date_value = st.date_input(
                f"{label} - Date",
                value=date.today(),
                key=f"{input_key}_date"
            )
        with col2:
            time_value = st.time_input(
                f"{label} - Time",
                key=f"{input_key}_time"
            )
        
        if date_value and time_value:
            dt = datetime.combine(date_value, time_value)
            return dt.isoformat()
        return None
    
    elif data_type == 'boolean':
        value = st.checkbox(
            label,
            value=bool(default_value) if default_value else False,
            key=input_key,
            help=f"Type: Yes/No{' (Required)' if is_required else ''}"
        )
        return value
    
    elif data_type == 'link':
        value = st.text_input(
            label,
            value=default_value or "",
            key=input_key,
            placeholder="https://...",
            help=f"Type: URL{' (Required)' if is_required else ''}"
        )
        return value if value else None
    
    else:
        # Fallback to text
        value = st.text_input(
            label,
            value=default_value or "",
            key=input_key,
            help=f"Type: {data_type}{' (Required)' if is_required else ''}"
        )
        return value if value else None


def save_event(client, user_id: str, category_id: str, event_date: date,
               attributes: Dict[str, any], comment: str = "") -> Tuple[bool, str]:
    """
    Save event to database
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Create event record
        event_data = {
            'user_id': user_id,
            'category_id': category_id,
            'event_date': event_date.isoformat(),
            'comment': comment or None
        }
        
        event_response = client.table('events').insert(event_data).execute()
        
        if not event_response.data:
            return False, "Failed to create event"
        
        event_id = event_response.data[0]['id']
        
        # Save attributes
        if attributes:
            attr_records = []
            for attr_def_id, value in attributes.items():
                if value is None:
                    continue
                
                record = {
                    'event_id': event_id,
                    'attribute_definition_id': attr_def_id,
                    'user_id': user_id
                }
                
                # Determine which column to use based on value type
                if isinstance(value, bool):
                    record['value_boolean'] = value
                elif isinstance(value, (int, float)):
                    record['value_number'] = value
                elif isinstance(value, str):
                    # Check if it's a datetime string
                    if 'T' in value and len(value) > 10:
                        record['value_datetime'] = value
                    else:
                        record['value_text'] = value
                else:
                    record['value_json'] = json.dumps(value)
                
                attr_records.append(record)
            
            if attr_records:
                client.table('event_attributes').insert(attr_records).execute()
        
        return True, f"Event saved successfully! (ID: {event_id})"
    
    except Exception as e:
        return False, f"Failed to save event: {str(e)}"


def render_event_entry(client, user_id: str):
    """Main render function for event entry page"""
    
    st.title("➕ Add New Event")
    st.markdown("Quick entry form for recording events")
    
    # Initialize session state for "sticky" category
    if 'last_area_id' not in st.session_state:
        st.session_state.last_area_id = None
    if 'last_category_id' not in st.session_state:
        st.session_state.last_category_id = None
    
    # Fetch areas
    areas = get_areas(client, user_id)
    
    if not areas:
        st.warning("No structure defined. Please upload a template first.")
        return
    
    # Area selection
    st.markdown("### 📦 Select Area")
    area_options = {area['id']: f"{area.get('icon', '📦')} {area['name']}" for area in areas}
    
    # Pre-select last used area if available
    default_area_idx = 0
    if st.session_state.last_area_id in area_options:
        area_ids = list(area_options.keys())
        default_area_idx = area_ids.index(st.session_state.last_area_id)
    
    selected_area_id = st.selectbox(
        "Area",
        options=list(area_options.keys()),
        format_func=lambda x: area_options[x],
        index=default_area_idx,
        key="area_select"
    )
    
    # Update last used area
    st.session_state.last_area_id = selected_area_id
    
    # Fetch categories for selected area
    categories = get_categories_for_area(client, selected_area_id, user_id)
    
    if not categories:
        st.warning("No categories defined for this area.")
        return
    
    # Build category path map
    path_map = build_category_path_map(categories)
    
    # Category selection with hierarchical display
    st.markdown("### 📁 Select Category")
    category_options = {cat['id']: path_map[cat['id']] for cat in categories}
    
    # Pre-select last used category if available
    default_cat_idx = 0
    if st.session_state.last_category_id in category_options:
        cat_ids = list(category_options.keys())
        default_cat_idx = cat_ids.index(st.session_state.last_category_id)
    
    selected_category_id = st.selectbox(
        "Category",
        options=list(category_options.keys()),
        format_func=lambda x: category_options[x],
        index=default_cat_idx,
        key="category_select"
    )
    
    # Update last used category
    st.session_state.last_category_id = selected_category_id
    
    # Fetch attributes for selected category
    attributes = get_attributes_for_category(client, selected_category_id)
    
    # Event date
    st.markdown("### 📅 Event Date")
    event_date = st.date_input(
        "Date",
        value=date.today(),
        key="event_date"
    )
    
    # Attributes section
    if attributes:
        st.markdown("### 📝 Event Details")
        st.caption(f"Fill in the details for this {path_map[selected_category_id]} event")
        
        # Collect attribute values
        attribute_values = {}
        
        for attr in sorted(attributes, key=lambda x: x.get('sort_order', 0)):
            value = render_attribute_input(attr, "event_attr")
            if value is not None:
                attribute_values[attr['id']] = value
        
        # Check required fields
        required_attrs = [a for a in attributes if a.get('is_required', False)]
        missing_required = [a['name'] for a in required_attrs if a['id'] not in attribute_values]
        
        if missing_required:
            st.warning(f"⚠️ Required fields missing: {', '.join(missing_required)}")
    else:
        st.info("No attributes defined for this category")
        attribute_values = {}
    
    # Comment section
    st.markdown("### 💬 Additional Notes (Optional)")
    comment = st.text_area(
        "Comment",
        placeholder="Add any additional notes or context...",
        key="event_comment"
    )
    
    # Save button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("💾 Save Event", type="primary", use_container_width=True):
            # Validate required fields
            if attributes:
                required_attrs = [a for a in attributes if a.get('is_required', False)]
                missing_required = [a['name'] for a in required_attrs if a['id'] not in attribute_values]
                
                if missing_required:
                    st.error(f"❌ Please fill in required fields: {', '.join(missing_required)}")
                    return
            
            # Save event
            with st.spinner("Saving event..."):
                success, message = save_event(
                    client,
                    user_id,
                    selected_category_id,
                    event_date,
                    attribute_values,
                    comment
                )
            
            if success:
                st.success(message)
                st.balloons()
                
                # Option to add another
                if st.button("➕ Add Another Event"):
                    st.rerun()
            else:
                st.error(message)
    
    # Quick stats
    st.markdown("---")
    st.caption(f"💡 Tip: Your last selection ({path_map[selected_category_id]}) will be remembered for quick entry!")


if __name__ == "__main__":
    st.write("This module should be imported by streamlit_app.py")
