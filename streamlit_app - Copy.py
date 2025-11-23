"""
Events Tracker - Main Application
==================================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-11-15 18:30 UTC
Python: 3.11

Description:
Main Streamlit application with authentication and multiple pages.
Integrates all modules: structure viewer, event entry, bulk import,
view data export/import, download/upload structure.

Modules:
- auth: User authentication
- structure_viewer: Browse hierarchical structure
- event_entry: Add single events
- bulk_import: Import multiple events from Excel/CSV
- view_data_export: Export events to Excel for editing
- view_data_import: Import edited Excel with change detection
- reverse_engineer: Download structure to Excel
- excel_parser_new: Upload and parse Excel template
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
from src import view_data_export
from src import view_data_import
from src.reverse_engineer import ReverseEngineer
from src import excel_parser_new


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
            "🔍 View Data - Export",
            "📥 View Data - Import",
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
    
    elif page == "🔍 View Data - Export":
        view_data_export.render_view_data_export(supabase.client, user_id)
    
    elif page == "📥 View Data - Import":
        view_data_import.render_view_data_import(supabase.client, user_id)
    
    elif page == "📥 Download Structure":
        render_download_page(supabase, user_id)
    
    elif page == "📤 Upload Template":
        render_upload_page(supabase, user_id)
    
    elif page == "ℹ️ Help":
        render_help_page()


def render_download_page(supabase, user_id: str):
    """Render the download structure page"""
    st.title("📥 Download Structure")
    st.markdown("Export your current structure to Excel template")
    
    st.info("💡 Download your areas, categories, and attributes as an Excel template that you can edit and re-upload.")
    
    st.markdown("---")
    
    # Initialize ReverseEngineer
    reverse_engineer = ReverseEngineer(supabase.client)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("📥 Download Structure", type="primary", use_container_width=True):
            with st.spinner("Generating Excel file..."):
                success, excel_bytes, message = reverse_engineer.export_to_bytes(user_id)
            
            if success:
                st.success(message)
                
                # Download button
                from datetime import datetime
                filename = f"structure_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                st.info("💡 **Next Steps:**\n1. Download the file\n2. Edit in Excel (add/remove/rename items)\n3. Go to 'Upload Template' to re-import")
            else:
                st.error(f"❌ {message}")


def render_upload_page(supabase, user_id: str):
    """Render the upload template page"""
    st.title("📤 Upload Template")
    st.markdown("Update your structure by uploading an edited Excel template")
    
    st.info("💡 Upload an Excel template to create or update your structure (Areas, Categories, Attributes).")
    
    st.markdown("---")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Excel Template",
        type=["xlsx"],
        help="Upload the Excel template you downloaded and edited"
    )
    
    if not uploaded_file:
        st.markdown("### 📋 Instructions")
        st.markdown("""
        1. **Download** current structure using 'Download Structure' page
        2. **Edit** in Excel:
           - Add/remove/rename Areas
           - Add/remove/rename Categories  
           - Add/remove/rename Attributes
           - Update properties (data types, units, etc.)
        3. **Upload** the edited file here
        4. **Review** detected changes
        5. **Confirm** to apply changes to database
        
        ⚠️ **Important:** Keep UUID columns unchanged for items you want to update
        """)
        return
    
    # Parse uploaded file
    with st.spinner("Parsing Excel template..."):
        try:
            parser = excel_parser_new.ExcelParser()
            success, result, message = parser.parse_template(uploaded_file)
            
            if not success:
                st.error(f"❌ {message}")
                return
            
            st.success("✅ Template parsed successfully!")
            
            # Show summary
            st.markdown("### 📊 Template Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Areas", len(result.get("areas", [])))
            with col2:
                st.metric("Categories", len(result.get("categories", [])))
            with col3:
                st.metric("Attributes", len(result.get("attributes", [])))
            
            # Preview data
            with st.expander("📄 Preview Template Data", expanded=False):
                if result.get("areas"):
                    st.markdown("**Areas:**")
                    st.dataframe(result["areas"], use_container_width=True)
                
                if result.get("categories"):
                    st.markdown("**Categories:**")
                    st.dataframe(result["categories"], use_container_width=True)
                
                if result.get("attributes"):
                    st.markdown("**Attributes:**")
                    st.dataframe(result["attributes"], use_container_width=True)
            
            st.markdown("---")
            
            # Apply button
            st.markdown("### ✅ Apply Changes")
            st.warning("⚠️ This will update your database structure")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                if st.button("🚀 Confirm & Apply", type="primary", use_container_width=True):
                    st.info("📝 Applying changes functionality - integration pending with rename detector and change applier")
                    st.caption("This will be completed in next iteration")
        
        except Exception as e:
            st.error(f"❌ Error parsing template: {str(e)}")


def render_help_page():
    """Render the help page"""
    st.title("ℹ️ Help & Documentation")
    
    st.markdown("""
    ## 📚 Events Tracker Guide
    
    ### 🎯 Overview
    Events Tracker helps you organize and track events using a hierarchical structure:
    - **Areas** (e.g., Health, Work, Finance)
    - **Categories** (e.g., Sleep, Exercise, Meetings)
    - **Attributes** (e.g., Duration, Amount, Quality)
    
    ---
    
    ### 📊 View Structure
    Browse your hierarchical structure in an interactive tree view:
    - Expand/collapse areas and categories
    - View all attributes with their properties
    - Search and filter
    - Navigate the structure
    
    ---
    
    ### 📝 Add Event
    Add single events with a user-friendly form:
    - Select category (hierarchical dropdown)
    - Pick date
    - Fill attribute values
    - Add optional comment
    - **Sticky mode**: Keep category selected for multiple entries
    
    ---
    
    ### 📤 Bulk Import
    Import multiple events from Excel/CSV:
    1. Download template
    2. Fill with your data
    3. Upload file
    4. Preview and validate
    5. Confirm import
    
    **Supported formats:**
    - Excel (.xlsx)
    - CSV (.csv)
    
    **Required columns:**
    - `event_date` (YYYY-MM-DD)
    - `category_path` (e.g., "Health > Sleep")
    - Attribute columns (e.g., `Duration`, `Quality`)
    
    ---
    
    ### 🔍 View Data - Export
    Export your events to Excel for viewing and editing:
    1. Apply filters (category, date range, attributes)
    2. Export to Excel
    3. Download file
    4. View/edit in Excel
    
    **Color coding:**
    - 🟪 **PINK columns** = READ-ONLY (Event_ID, Category_Path, Date)
    - 🔵 **BLUE columns** = EDITABLE (attribute values, comment)
    
    ---
    
    ### 📥 View Data - Import
    Import edited Excel file with change detection:
    1. Upload edited Excel file (from Export)
    2. System detects changes automatically
    3. Review detailed diff (old vs new values)
    4. Confirm to apply changes
    5. Changes applied to database
    
    **Safety features:**
    - Only changed values are updated
    - Unchanged data remains untouched
    - Full validation before applying
    - Error reporting
    
    ---
    
    ### 📥 Download Structure
    Export your structure to Excel template:
    - Download all areas, categories, and attributes
    - Edit in Excel (add/remove/rename)
    - Re-upload using 'Upload Template'
    
    ---
    
    ### 📤 Upload Template
    Update your structure by uploading Excel template:
    - Download current structure first
    - Edit in Excel (add/rename/delete areas, categories, attributes)
    - Upload modified template
    - Review changes
    - Confirm updates
    
    **Features:**
    - Rename detection (smart matching)
    - Hierarchical structure support
    - Validation before applying changes
    
    ---
    
    ### 💡 Tips & Best Practices
    
    **Structure Organization:**
    - Use Areas for high-level grouping (Health, Work, etc.)
    - Categories for specific event types (Sleep, Meetings, etc.)
    - Attributes for data points you want to track
    
    **Bulk Operations:**
    - Use Bulk Import for initial data load
    - Use View Data Export/Import for editing existing data
    - Download structure template before making structural changes
    
    **Data Entry:**
    - Enable Sticky Mode in Add Event for repeated entries in same category
    - Use Bulk Import for multiple events at once
    - Use View Data Export/Import to edit large datasets
    
    **Data Safety:**
    - Always review changes before confirming
    - Download backups before major structural changes
    - Check validation messages carefully
    
    ---
    
    ### ❓ Need More Help?
    
    If you encounter issues:
    1. Check validation messages carefully
    2. Review error details in expander sections
    3. Ensure Excel files follow required format
    4. Verify date formats (YYYY-MM-DD)
    
    ---
    
    ### 🎉 Happy Tracking!
    """)
    
    # Version info
    st.markdown("---")
    st.caption("Version: 2025-11-15 18:30 UTC | Python: 3.11 | Streamlit: 1.28.0")


if __name__ == "__main__":
    main()
