"""
Events Tracker - Main Application
==================================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-11-13 10:20 UTC
Python: 3.11

Fully integrated with AuthManager class from src/auth.py
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Import local modules
from src.auth import AuthManager
from src import supabase_client
from src import structure_viewer
from src import event_entry
from src import bulk_import


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
            "📊 View Structure",
            "➕ Add Event",
            "📤 Bulk Import",
            "📥 Download Structure",
            "📤 Upload Template",
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
    if page == "📊 View Structure":
        structure_viewer.render_structure_viewer(supabase.client, user_id)
    
    elif page == "➕ Add Event":
        event_entry.render_event_entry(supabase.client, user_id)
    
    elif page == "📤 Bulk Import":
        bulk_import.render_bulk_import(supabase.client, user_id)
    
    elif page == "📥 Download Structure":
        render_download_page(supabase, user_id)
    
    elif page == "📤 Upload Template":
        render_upload_page(supabase, user_id)
    
    elif page == "ℹ️ Help":
        render_help_page()


def render_download_page(supabase, user_id: str):
    """Render the download structure page"""
    st.title("📥 Download Structure")
    st.markdown("Export your current structure to Excel")
    
    st.info("📝 Download functionality - to be integrated with existing logic")
    st.caption("This will use your existing download template code")


def render_upload_page(supabase, user_id: str):
    """Render the upload template page"""
    st.title("📤 Upload Template")
    st.markdown("Define or update your structure using Excel template")
    
    st.info("📝 Upload functionality - to be integrated with existing logic")
    st.caption("This will use your existing upload template code")


def render_help_page():
    """Render the help page"""
    st.title("ℹ️ Help & Documentation")
    
    st.markdown("""
    ## 📚 Events Tracker Guide
    
    ### Getting Started
    
    1. **Upload Template** - Define your structure (Areas → Categories → Attributes)
    2. **View Structure** - Browse your hierarchical organization
    3. **Add Events** - Record individual events
    4. **Bulk Import** - Upload multiple events from Excel/CSV
    
    ### Features
    
    #### 📊 View Structure
    - Browse hierarchical organization
    - Filter by area and level
    - Search categories and attributes
    - View metadata and statistics
    
    #### ➕ Add Event
    - Quick entry form for single events
    - Dynamic category selection
    - Automatic attribute inputs based on category
    - "Sticky" last-used category for efficiency
    - Mobile-optimized
    
    #### 📤 Bulk Import
    - Upload Excel or CSV files
    - Wide format (one row = one event)
    - Download template with examples
    - Comprehensive validation before import
    - Progress tracking
    
    ### Tips & Tricks
    
    💡 **Quick Entry**: The Add Event form remembers your last category selection  
    💡 **Bulk Import**: Download the template first to see correct format  
    💡 **Category Paths**: Use full hierarchical paths (e.g., "Fitness → Running → Trail Run")  
    💡 **Required Fields**: Marked with * in forms  
    
    ### Support
    
    For issues or questions, check the logs in Streamlit Cloud dashboard.
    """)
    
    # Version info
    st.markdown("---")
    st.caption("Version: 2025-11-13 10:20 UTC | Python: 3.11 | Streamlit: 1.28.0")


if __name__ == "__main__":
    main()
