"""
UI Components Utility Module
=============================
Created: 2025-11-29 10:45 UTC
Last Modified: 2025-11-29 10:45 UTC
Python: 3.11

Description:
Reusable Streamlit UI components for Events Tracker.
Provides consistent UI elements across all pages.

Features:
- Contextual help sections
- Standardized buttons and forms
- Consistent messaging
- Common UI patterns

Dependencies: streamlit

Usage:
    from src.utils.ui_components import show_contextual_help
    
    show_contextual_help("Page Name", "Help content here...")
"""

import streamlit as st
from typing import Optional, List, Dict, Any


# ============================================================================
# HELP COMPONENTS
# ============================================================================

def show_contextual_help(page_name: str, help_content: str):
    """
    Display contextual help section at page top.
    
    Args:
        page_name: Name of the page/section
        help_content: Markdown-formatted help text
        
    Example:
        show_contextual_help(
            "Interactive Structure Viewer",
            '''
            ### How to use
            - Step 1: Select mode
            - Step 2: Filter data
            '''
        )
    """
    with st.expander(f"❓ Help - {page_name}", expanded=False):
        st.markdown(help_content)
        st.markdown("---")
        st.markdown("[📚 View Full Documentation](../ℹ️_Help)")


# ============================================================================
# HELP CONTENT TEMPLATES
# ============================================================================

HELP_INTERACTIVE_STRUCTURE = """
### 📋 Interactive Structure Viewer

**Read-Only Mode:**
- View your complete hierarchical structure
- Filter by Area to focus on specific sections
- Search Category Path to find specific categories
- Download filtered structure to Excel

**Edit Mode:**
- Tab 1: Edit Areas - Add, modify, or delete areas
- Tab 2: Edit Categories - Manage category hierarchy
- Tab 3: Edit Attributes - Configure attribute definitions
- Tab 4: Upload Template - Bulk import structure from Excel

**Tips:**
- Use filters to narrow down large structures
- Download creates Excel with only filtered data
- Edit mode tabs are independent - changes save per tab
- Upload Template detects additions, updates, and deletions
"""

HELP_ADD_EVENT = """
### ➕ Add Event

**How to add a single event:**
1. Select event date
2. Choose category from hierarchical dropdown
3. Fill in required attribute values
4. Add optional comment
5. Click Save Event

**Sticky Mode:**
- Enable to keep category selected after saving
- Useful for entering multiple events in same category
- Date resets to today, but category stays selected

**Tips:**
- Required attributes are marked with asterisk (*)
- Validation happens before saving
- Use Bulk Import for adding many events at once
"""

HELP_BULK_IMPORT = """
### 📤 Bulk Import Events

**Steps:**
1. Download Excel template for your category
2. Fill in event data (dates, attribute values)
3. Upload completed file
4. Review preview and validation
5. Confirm import

**Template Format:**
- `event_date`: YYYY-MM-DD format (required)
- `category_path`: Full path like "Training > Cardio" (required)
- Attribute columns: Match attribute names exactly
- `comment`: Optional text

**Tips:**
- Use Excel auto-fill for repetitive data
- Validate dates before uploading
- Check attribute names match exactly
- Preview shows any errors before import
"""

HELP_VIEW_DATA_EXPORT = """
### 📊 View Data - Export

**How to export your events:**
1. Apply filters (category, date range, specific attributes)
2. Click Export to Excel
3. Download generated file
4. View/edit in Excel

**Excel Color Coding:**
- 🟪 PINK columns = READ-ONLY (Event_ID, Category_Path, Date)
- 🔵 BLUE columns = EDITABLE (attribute values, comment)

**Tips:**
- Use filters to export only relevant data
- Edit values in BLUE columns only
- Import edited file via "View Data - Import"
- Don't change PINK columns or file structure
"""

HELP_VIEW_DATA_IMPORT = """
### 📥 View Data - Import

**How to import edited event data:**
1. Upload Excel file (from View Data Export)
2. System detects changes automatically
3. Review detailed diff (old → new values)
4. Confirm to apply changes
5. Changes saved to database

**Safety Features:**
- Only changed values are updated
- Unchanged data remains untouched
- Full validation before applying
- Error reporting for invalid data

**Tips:**
- Only edit BLUE columns in Excel
- Keep file structure intact
- Review diff carefully before confirming
- System prevents invalid changes
"""


# ============================================================================
# MESSAGE COMPONENTS
# ============================================================================

def show_success(message: str, balloons: bool = False):
    """
    Display success message with optional celebration.
    
    Args:
        message: Success message text
        balloons: Show balloons animation
        
    Example:
        show_success("Event saved successfully!", balloons=True)
    """
    st.success(f"✅ {message}")
    if balloons:
        st.balloons()


def show_error(message: str, details: Optional[str] = None):
    """
    Display error message with optional details.
    
    Args:
        message: Error message text
        details: Optional detailed error info
        
    Example:
        show_error("Failed to save", details=str(exception))
    """
    st.error(f"❌ {message}")
    
    if details:
        with st.expander("🔍 View Error Details"):
            st.code(details)


def show_warning(message: str):
    """
    Display warning message.
    
    Args:
        message: Warning message text
        
    Example:
        show_warning("This action cannot be undone")
    """
    st.warning(f"⚠️ {message}")


def show_info(message: str):
    """
    Display info message.
    
    Args:
        message: Info message text
        
    Example:
        show_info("Fill in all required fields")
    """
    st.info(f"ℹ️ {message}")


# ============================================================================
# CONFIRMATION COMPONENTS
# ============================================================================

def confirm_action(
    action_name: str,
    warning_message: Optional[str] = None,
    confirmation_text: str = "CONFIRM"
) -> bool:
    """
    Display confirmation dialog for destructive actions.
    
    Args:
        action_name: Name of action (e.g., "Delete Area")
        warning_message: Optional warning text
        confirmation_text: Text user must type to confirm
        
    Returns:
        True if confirmed, False otherwise
        
    Example:
        if confirm_action("Delete Area", "This will delete 5 categories!"):
            delete_area(area_id)
    """
    st.markdown(f"### ⚠️ Confirm {action_name}")
    
    if warning_message:
        st.warning(warning_message)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_input(
            f"Type '{confirmation_text}' to confirm:",
            placeholder=confirmation_text,
            key=f"confirm_{action_name.replace(' ', '_')}"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        confirmed = st.button(
            f"✓ {action_name}",
            type="primary",
            disabled=(user_input != confirmation_text),
            use_container_width=True
        )
    
    return confirmed and user_input == confirmation_text


# ============================================================================
# FILTER COMPONENTS
# ============================================================================

def create_area_filter(
    areas: List[Dict[str, Any]],
    key: str = "area_filter",
    include_all: bool = True
) -> Optional[str]:
    """
    Create standardized area filter dropdown.
    
    Args:
        areas: List of area dicts with 'id' and 'name'
        key: Streamlit widget key
        include_all: Include "All Areas" option
        
    Returns:
        Selected area ID or None if "All Areas"
        
    Example:
        areas = fetch_areas(client, user_id)
        selected_area_id = create_area_filter(areas)
    """
    options = []
    option_ids = []
    
    if include_all:
        options.append("All Areas")
        option_ids.append(None)
    
    for area in areas:
        options.append(area['name'])
        option_ids.append(area['id'])
    
    selected_idx = st.selectbox(
        "Filter by Area",
        range(len(options)),
        format_func=lambda i: options[i],
        key=key
    )
    
    return option_ids[selected_idx]


def create_category_filter(
    categories: List[Dict[str, Any]],
    key: str = "category_filter",
    include_all: bool = True
) -> Optional[str]:
    """
    Create standardized category filter dropdown.
    
    Args:
        categories: List of category dicts with 'id' and 'name'
        key: Streamlit widget key
        include_all: Include "All Categories" option
        
    Returns:
        Selected category ID or None if "All Categories"
        
    Example:
        cats = fetch_categories(client, user_id, area_id)
        selected_cat_id = create_category_filter(cats)
    """
    options = []
    option_ids = []
    
    if include_all:
        options.append("All Categories")
        option_ids.append(None)
    
    for cat in categories:
        # Build category path for display
        path = cat.get('name', 'Unknown')
        options.append(path)
        option_ids.append(cat['id'])
    
    selected_idx = st.selectbox(
        "Filter by Category",
        range(len(options)),
        format_func=lambda i: options[i],
        key=key
    )
    
    return option_ids[selected_idx]


# ============================================================================
# FORM COMPONENTS
# ============================================================================

def create_data_type_selector(
    key: str = "data_type",
    default: str = "number"
) -> str:
    """
    Create standardized data type selector.
    
    Args:
        key: Streamlit widget key
        default: Default data type
        
    Returns:
        Selected data type
        
    Example:
        data_type = create_data_type_selector()
    """
    data_types = ['number', 'text', 'datetime', 'boolean', 'link', 'image']
    
    return st.selectbox(
        "Data Type",
        options=data_types,
        index=data_types.index(default) if default in data_types else 0,
        key=key,
        help="Choose the type of data this attribute will store"
    )


def create_yes_no_selector(
    label: str,
    key: str,
    default: bool = False
) -> bool:
    """
    Create standardized Yes/No selector.
    
    Args:
        label: Field label
        key: Streamlit widget key
        default: Default value (True = Yes, False = No)
        
    Returns:
        True if Yes, False if No
        
    Example:
        is_required = create_yes_no_selector("Is Required?", "is_req")
    """
    options = ["No", "Yes"]
    default_idx = 1 if default else 0
    
    selected = st.selectbox(
        label,
        options=options,
        index=default_idx,
        key=key
    )
    
    return selected == "Yes"


# ============================================================================
# DISPLAY COMPONENTS
# ============================================================================

def display_validation_errors(errors: List[str]):
    """
    Display list of validation errors.
    
    Args:
        errors: List of error messages
        
    Example:
        errors = validate_data(df)
        if errors:
            display_validation_errors(errors)
    """
    if not errors:
        return
    
    st.error(f"❌ Found {len(errors)} validation error(s):")
    
    for idx, error in enumerate(errors, 1):
        st.markdown(f"{idx}. {error}")


def display_change_summary(changes: Dict[str, int]):
    """
    Display summary of changes to be applied.
    
    Args:
        changes: Dict with change counts (e.g., {'added': 5, 'updated': 3})
        
    Example:
        changes = {'new_areas': 2, 'updated_categories': 3}
        display_change_summary(changes)
    """
    if not changes:
        st.info("No changes detected")
        return
    
    st.markdown("### 📊 Change Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_items = sum(v for k, v in changes.items() if 'new' in k.lower())
        st.metric("New Items", new_items)
    
    with col2:
        updated_items = sum(v for k, v in changes.items() if 'update' in k.lower())
        st.metric("Updated Items", updated_items)
    
    with col3:
        deleted_items = sum(v for k, v in changes.items() if 'delete' in k.lower())
        st.metric("Deleted Items", deleted_items)


# ============================================================================
# LOADING COMPONENTS
# ============================================================================

def show_loading_spinner(message: str = "Loading..."):
    """
    Context manager for loading spinner.
    
    Args:
        message: Loading message to display
        
    Example:
        with show_loading_spinner("Fetching data..."):
            data = fetch_data()
    """
    return st.spinner(message)
