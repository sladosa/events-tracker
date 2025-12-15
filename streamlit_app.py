"""
Events Tracker - Main Application
==================================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-12-15 10:00 UTC
Python: 3.11
Version: 1.8.0 - Added Show Events, removed Add Event

Description:
Main Streamlit application with authentication and multiple pages.
Core modules: Interactive Structure Viewer (main hub), Add Activity,
Show Events, bulk import, view data export/import.

NEW in v1.8.0:
- 📋 Show Events page - view, edit, delete events with filters
- 🗑️ Removed Add Event page (obsolete - replaced by Add Activity)
- 🏋️ Add Activity v2.0.0 - filter-first design with shortcuts

CHANGELOG:
- v1.8.0: Show Events + Remove Add Event
- v1.7.0: Add Activity module (mobile-optimized)
- v1.6.1: Removed deprecated pages (View Structure, Download, Upload Template)

Modules:
- auth: User authentication
- interactive_structure_viewer: Excel-like editing interface (main hub)
- add_activity: Mobile-optimized activity entry with shortcuts
- show_events: View, edit, delete events
- bulk_import: Import multiple events from Excel/CSV
- view_data_export: Export events to Excel for editing
- view_data_import: Import edited Excel with change detection
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Import local modules
from src.auth import AuthManager
from src import supabase_client
from src.interactive_structure_viewer import render_interactive_structure_viewer
from src.add_activity import render_add_activity
from src.show_events import render_show_events
from src import bulk_import
from src import view_data_export
from src import view_data_import


# Page configuration
st.set_page_config(
    page_title="Events Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()


@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        st.error("⚠️ Missing Supabase credentials. Please check your secrets.")
        st.stop()
    
    return supabase_client.SupabaseManager(url, key)


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
    
    # Sidebar navigation
    st.sidebar.title("🗂️ Events Tracker")
    st.sidebar.markdown("---")
    
    # Navigation menu
    page = st.sidebar.radio(
        "Navigation",
        [
            "📋 Interactive Structure Viewer",
            "🏋️ Add Activity",
            "📊 Show Events",
            "📤 Bulk Import",
            "📥 View Data - Export",
            "📤 View Data - Import",
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
    
    # Route to appropriate page
    if page == "📋 Interactive Structure Viewer":
        render_interactive_structure_viewer(supabase.client, user_id)
    
    elif page == "🏋️ Add Activity":
        render_add_activity(supabase.client, user_id)
    
    elif page == "📊 Show Events":
        render_show_events(supabase.client, user_id)
    
    elif page == "📤 Bulk Import":
        bulk_import.render_bulk_import(supabase.client, user_id)
    
    elif page == "📥 View Data - Export":
        view_data_export.render_view_data_export(supabase.client, user_id)
    
    elif page == "📤 View Data - Import":
        view_data_import.render_view_data_import(supabase.client, user_id)
    
    elif page == "ℹ️ Help":
        render_help_page()


def render_help_page():
    """Render the help page with basic application concepts only"""
    st.title("ℹ️ Help & Documentation")
    
    st.markdown("""
    ## 📚 Events Tracker - Basic Concepts
    
    ### 🎯 What is Events Tracker?
    
    Events Tracker helps you organize and track events using a **hierarchical structure**:
    
    - **Areas** → Top-level organization (e.g., Health, Work, Finance)
    - **Categories** → Specific event types (e.g., Sleep, Exercise, Meetings)  
    - **Attributes** → Data fields you want to track (e.g., Duration, Amount, Quality)
    
    This flexible structure allows you to:
    - Track any type of event (health, work, finance, personal, etc.)
    - Define custom attributes for each category
    - Maintain relationships and hierarchies
    - Export and analyze your data
    
    ---
    
    ### 📊 Core Components
    
    **1. Structure Management**
    - Define your hierarchical structure (Areas → Categories → Attributes)
    - Edit structure directly or via Excel templates
    - Add/modify/delete items with validation
    
    **2. Event Entry**
    - **Add Activity**: Mobile-optimized activity entry with shortcuts
    - Bulk import from Excel/CSV
    - Link events to categories with automatic attribute capture
    
    **3. Data Management**
    - **Show Events**: View, edit, and delete your events
    - Export events to Excel for editing
    - Import edited data with change detection
    - Filter and search capabilities
    
    ---
    
    ### 🗺️ Application Navigation
    
    **Interactive Structure Viewer** 🌟
    - **Main hub** for structure management
    - Two modes: Read-Only (view/export) and Edit (modify/upload)
    - Detailed help available within the page
    
    **Add Activity** 🏋️
    - Mobile-optimized event entry
    - Filter by Area → Category drill-down
    - Save shortcuts for frequently used categories
    - Photo attachments support
    
    **Show Events** 📊
    - View all your events with filters
    - Edit event details and attributes
    - Delete events with confirmation
    - Pagination for large datasets
    
    **Bulk Import**
    - Import multiple events from Excel/CSV
    - Template download available
    - Preview and validation before import
    
    **View Data - Export/Import**
    - Export events to Excel for editing
    - Import with automatic change detection
    - Color-coded editable vs read-only fields
    
    ---
    
    ### 💡 Getting Started
    
    **New to Events Tracker?**
    
    1. **Define your structure** using Interactive Structure Viewer
       - Start with a few Areas (e.g., "Health", "Work")
       - Add Categories under each Area
       - Define Attributes for each Category
    
    2. **Add some events**
       - Use "Add Activity" for quick entry
       - Or use "Bulk Import" for multiple events
    
    3. **Review and manage your data**
       - Use "Show Events" to view and edit
       - Use "View Data - Export" for Excel export
    
    ---
    
    ### 🔧 Data Types
    
    When defining attributes, you can choose from:
    
    - **number** - Numeric values (e.g., duration, amount, quantity)
    - **text** - Free text (e.g., notes, descriptions)
    - **datetime** - Date and time values
    - **boolean** - Yes/No or True/False
    - **link** - URLs and web links
    - **image** - Image file paths or URLs
    
    ---
    
    ### 🎨 Color Coding Convention
    
    Throughout the application, you'll see color-coded columns:
    
    - 🟪 **PINK columns** = AUTO-CALCULATED (read-only)
      - System-generated values
      - Don't edit these manually
    
    - 🔵 **BLUE columns** = EDITABLE
      - Your data and properties
      - Safe to modify
    
    ---
    
    ### ⚠️ Important Notes
    
    **Data Safety:**
    - Always review changes before confirming
    - Download backups before major structural changes
    - Check validation messages carefully
    - Use CONFIRM dialogs for destructive operations
    
    **Best Practices:**
    - Start small - add complexity gradually
    - Use meaningful names for Areas, Categories, and Attributes
    - Add descriptions to document your structure
    - Test with sample data before bulk operations
    
    ---
    
    ### 🎉 Happy Tracking!
    
    Remember: Events Tracker is designed to be flexible. Start with basics and expand as you discover what works for your tracking needs.
    """)
    
    # Version info
    st.markdown("---")
    st.caption("Version: 1.8.0 | 2025-12-15 | Python: 3.11 | Streamlit: 1.28.0")


if __name__ == "__main__":
    main()
