"""
Events Tracker - Main Application (REFACTORED v2.0)
====================================================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-11-29 11:15 UTC
Python: 3.11
Version: 2.0.0 - REFACTORED

Description:
Main Streamlit application with authentication and multiple pages.
Integrates all modules with centralized utils for better maintainability.

CHANGES in v2.0:
- ✅ REMOVED: "📊 View Structure" page (replaced by Interactive Structure)
- ✅ REMOVED: "📥 Download Structure" page (integrated into Interactive Structure)
- ✅ REMOVED: "📤 Upload Template" page (integrated into Interactive Structure)
- ✅ NEW: Streamlined navigation (6 pages instead of 9)
- ✅ NEW: Contextual help on all pages
- ✅ NEW: Uses centralized utils modules
- ✅ UPDATED: Help page is concise overview only

Modules Used:
- auth: User authentication
- interactive_structure_viewer: Main structure management (Read-Only + Edit + Upload)
- event_entry: Add single events
- bulk_import: Import multiple events from Excel/CSV
- view_data_export: Export events to Excel for editing
- view_data_import: Import edited Excel with change detection

Removed Modules (no longer in navigation):
- structure_viewer: Replaced by interactive_structure_viewer
- reverse_engineer: Integrated into interactive_structure_viewer
- enhanced_structure_exporter: Used internally by utils.excel_operations
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Import local modules
from src.auth import AuthManager
from src import supabase_client
from src.interactive_structure_viewer import render_interactive_structure_viewer
from src import event_entry
from src import bulk_import
from src import view_data_export
from src import view_data_import

# Import utils for contextual help
from src.utils.ui_components import (
    show_contextual_help,
    HELP_ADD_EVENT,
    HELP_BULK_IMPORT,
    HELP_VIEW_DATA_EXPORT,
    HELP_VIEW_DATA_IMPORT
)


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Events Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()


# ============================================================================
# SUPABASE INITIALIZATION
# ============================================================================

@st.cache_resource
def init_supabase():
    """Initialize Supabase client (cached for performance)"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        st.error("⚠️ Missing Supabase credentials. Please check your .env file.")
        st.stop()
    
    return supabase_client.SupabaseManager(url, key)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application logic"""
    
    # Initialize Supabase
    supabase = init_supabase()
    
    # Initialize AuthManager
    auth_manager = AuthManager(supabase.client)
    
    # Check authentication
    if not auth_manager.is_authenticated():
        auth_manager.show_login_page()
        return
    
    # Get user info
    user_id = auth_manager.get_user_id()
    user_email = auth_manager.get_user_email()
    
    # ========================================
    # SIDEBAR NAVIGATION
    # ========================================
    
    st.sidebar.title("🗂️ Events Tracker")
    st.sidebar.markdown("---")
    
    # Streamlined navigation menu (6 pages)
    page = st.sidebar.radio(
        "Navigation",
        [
            "📋 Interactive Structure",
            "➕ Add Event",
            "📤 Bulk Import",
            "📊 View Data - Export",
            "📥 View Data - Import",
            "ℹ️ Help"
        ],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # User info and logout
    st.sidebar.markdown("### 👤 User")
    st.sidebar.text(f"📧 {user_email}")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        auth_manager.logout()
    
    # Connection status
    with st.sidebar.expander("🔌 Connection Status", expanded=False):
        success, message = supabase.test_connection()
        if success:
            st.success("✅ Connected to Supabase")
        else:
            st.error(f"❌ {message}")
    
    # Version info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.caption("Version: 2.0.0 (Refactored)")
    st.sidebar.caption("Last Updated: 2025-11-29")
    
    # Main content area styling
    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # ========================================
    # ROUTING TO PAGES
    # ========================================
    
    if page == "📋 Interactive Structure":
        # Main structure management page (Read-Only + Edit + Upload integrated)
        render_interactive_structure_viewer(supabase.client, user_id)
    
    elif page == "➕ Add Event":
        # Add single event with contextual help
        render_add_event_with_help(supabase.client, user_id)
    
    elif page == "📤 Bulk Import":
        # Bulk import events with contextual help
        render_bulk_import_with_help(supabase.client, user_id)
    
    elif page == "📊 View Data - Export":
        # Export events to Excel with contextual help
        render_view_data_export_with_help(supabase.client, user_id)
    
    elif page == "📥 View Data - Import":
        # Import edited Excel with contextual help
        render_view_data_import_with_help(supabase.client, user_id)
    
    elif page == "ℹ️ Help":
        # Concise help page (overview only)
        render_help_page()


# ============================================================================
# PAGE WRAPPERS WITH CONTEXTUAL HELP
# ============================================================================

def render_add_event_with_help(client, user_id: str):
    """Render Add Event page with contextual help"""
    # Show contextual help at top
    show_contextual_help("Add Event", HELP_ADD_EVENT)
    st.markdown("---")
    
    # Render original page
    event_entry.render_event_entry(client, user_id)


def render_bulk_import_with_help(client, user_id: str):
    """Render Bulk Import page with contextual help"""
    # Show contextual help at top
    show_contextual_help("Bulk Import", HELP_BULK_IMPORT)
    st.markdown("---")
    
    # Render original page
    bulk_import.render_bulk_import(client, user_id)


def render_view_data_export_with_help(client, user_id: str):
    """Render View Data Export page with contextual help"""
    # Show contextual help at top
    show_contextual_help("View Data - Export", HELP_VIEW_DATA_EXPORT)
    st.markdown("---")
    
    # Render original page
    view_data_export.render_view_data_export(client, user_id)


def render_view_data_import_with_help(client, user_id: str):
    """Render View Data Import page with contextual help"""
    # Show contextual help at top
    show_contextual_help("View Data - Import", HELP_VIEW_DATA_IMPORT)
    st.markdown("---")
    
    # Render original page
    view_data_import.render_view_data_import(client, user_id)


# ============================================================================
# HELP PAGE (CONCISE OVERVIEW ONLY)
# ============================================================================

def render_help_page():
    """
    Render concise help page - overview only.
    Detailed help available via contextual help on each page.
    """
    st.title("ℹ️ Help & Documentation")
    
    st.markdown("""
    ## 📚 Events Tracker Guide
    
    ### 🎯 What is Events Tracker?
    
    Events Tracker helps you organize and track events using a hierarchical structure:
    - **Areas** (e.g., Health, Work, Finance) - High-level grouping
    - **Categories** (e.g., Sleep, Exercise, Meetings) - Specific event types
    - **Attributes** (e.g., Duration, Amount, Quality) - Data points to track
    
    ---
    
    ### 📖 How to Use
    
    **Each page has its own contextual help** - click the **❓ Help** expander at the top of any page for specific guidance.
    
    ---
    
    ### 📋 Quick Start Guide
    
    #### 1. Set Up Your Structure
    Use **Interactive Structure** to define your tracking system:
    - **Read-Only Mode**: Browse, filter, and download your structure
    - **Edit Mode**: Add, modify, or delete areas, categories, and attributes
    - **Upload Template**: Bulk import structure changes from Excel
    
    #### 2. Add Events
    Choose your preferred method:
    - **Add Event**: Quick single-event entry with sticky mode for repeated entries
    - **Bulk Import**: Upload Excel/CSV with multiple events at once
    
    #### 3. Manage Your Data
    - **View Data - Export**: Download events to Excel (color-coded for easy editing)
    - **View Data - Import**: Upload edited Excel with automatic change detection
    
    ---
    
    ### 💡 Key Features by Page
    
    #### 📋 Interactive Structure
    **Your central hub for structure management**
    
    - **Read-Only Mode**:
      - Browse complete hierarchical structure
      - Filter by Area to focus on specific sections
      - Search Category Path to find specific categories
      - Download filtered structure to Excel
    
    - **Edit Mode**:
      - **Tab 1: Edit Areas** - Manage top-level groupings
      - **Tab 2: Edit Categories** - Build category hierarchy
      - **Tab 3: Edit Attributes** - Configure data fields
      - **Tab 4: Upload Template** - Bulk import structure from Excel
    
    #### ➕ Add Event
    **Quick single-event entry**
    
    - Select event date
    - Choose category from hierarchical dropdown
    - Fill attribute values (required fields marked with *)
    - Optional comment
    - Sticky mode for repeated entries in same category
    
    #### 📤 Bulk Import
    **Import multiple events at once**
    
    - Download Excel template for your category
    - Fill in event data (dates, attributes, comments)
    - Upload completed file
    - Review preview and validation
    - Confirm import
    
    #### 📊 View Data - Export
    **Download events to Excel for viewing/editing**
    
    - Apply filters (category, date range, attributes)
    - Export to Excel with color-coded columns:
      - 🟪 PINK = READ-ONLY (Event_ID, Category, Date)
      - 🔵 BLUE = EDITABLE (attribute values, comment)
    - Edit in Excel
    - Re-import via View Data - Import
    
    #### 📥 View Data - Import
    **Import edited event data with change detection**
    
    - Upload Excel file (from View Data - Export)
    - System automatically detects changes
    - Review detailed diff (old → new values)
    - Confirm to apply changes
    - Safety features prevent invalid changes
    
    ---
    
    ### ❓ Need More Help?
    
    - Click **❓ Help** at the top of any page for specific guidance
    - Check validation messages for data entry tips
    - Use Excel templates for correct formatting
    - Review color-coded columns in exported files
    
    ---
    
    ### 🎯 Best Practices
    
    **Structure Organization:**
    - Use Areas for broad categories (Health, Work, etc.)
    - Categories for specific event types (Sleep, Meetings, etc.)
    - Attributes for data points you want to track
    
    **Data Entry:**
    - Enable Sticky Mode in Add Event for repeated entries
    - Use Bulk Import for initial data load or multiple events
    - Use View Data Export/Import for editing large datasets
    
    **Data Safety:**
    - Always review changes before confirming
    - Download backups before major structural changes
    - Check validation messages carefully
    - Don't edit PINK columns in exported Excel files
    
    ---
    
    ### 🎉 Happy Tracking!
    
    Remember: Detailed help is available on every page via the **❓ Help** expander.
    """)
    
    # Version info
    st.markdown("---")
    st.caption("""
    **Version**: 2.0.0 (Refactored)  
    **Last Updated**: 2025-11-29  
    **Framework**: Streamlit 1.28.0 | Python 3.11  
    **Features**: Centralized Utils | Validation | Contextual Help
    """)


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
