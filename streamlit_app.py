"""
Events Tracker - Main Application
==================================
Created: 2025-11-13 10:20 UTC
Last Modified: 2025-11-25 10:00 UTC
Python: 3.11

Description:
Main Streamlit application with authentication and multiple pages.
Integrates all modules: structure viewer, interactive structure viewer,
event entry, bulk import, view data export/import, download/upload structure.

Modules:
- auth: User authentication
- structure_viewer: Browse hierarchical structure (tree view)
- interactive_structure_viewer: Excel-like editing interface (NEW)
- event_entry: Add single events
- bulk_import: Import multiple events from Excel/CSV
- view_data_export: Export events to Excel for editing
- view_data_import: Import edited Excel with change detection
- reverse_engineer: Download structure to Excel
- enhanced_structure_exporter: Enhanced Excel export with validation
- hierarchical_parser: Parse and update structure from Hierarchical_View Excel
"""

import streamlit as st
import os
import tempfile
from dotenv import load_dotenv

# Import local modules
from src.auth import AuthManager
from src import supabase_client
from src import structure_viewer
from src.interactive_structure_viewer import render_interactive_structure_viewer
from src import event_entry
from src import bulk_import
from src import view_data_export
from src import view_data_import
from src.reverse_engineer import ReverseEngineer
from src.enhanced_structure_exporter import EnhancedStructureExporter
from src.hierarchical_parser import HierarchicalParser
from src import excel_parser_new
from src.error_reporter import generate_error_excel


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
            "📋 Interactive Structure Viewer",
            "➕ Add Event",
            "📤 Bulk Import",
            "📊 View Data - Export",
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
    
    elif page == "📋 Interactive Structure Viewer":
        render_interactive_structure_viewer(supabase.client, user_id)
    
    elif page == "➕ Add Event":
        event_entry.render_event_entry(supabase.client, user_id)
    
    elif page == "📤 Bulk Import":
        bulk_import.render_bulk_import(supabase.client, user_id)
    
    elif page == "📊 View Data - Export":
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
    """Download structure to Excel with enhanced features."""
    st.title("📥 Download Structure")
    
    st.info("""
    **Enhanced Excel Export Features:**
    - 🎨 **Color-coded columns**: PINK (auto-calculated) vs BLUE (editable)
    - ✅ **Drop-down validation**: Type, Data_Type, Is_Required
    - 🔢 **Auto-formulas**: Level, Area, Sort_Order calculated automatically
    - 📊 **Row grouping**: Collapse/expand by Area and Category
    - 📋 **Column grouping**: Hide/show attribute details
    - 🔍 **Validation fields**: Min/Max values for number attributes
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 What you can edit:")
        st.markdown("""
        **BLUE columns** (editable):
        - Category name
        - Attribute Name, Data Type, Unit
        - Is Required, Default Value
        - Validation Min/Max
        - Description
        
        **PINK columns** (auto-calculated):
        - Type, Level, Area
        - Category Path
        - Sort Order
        """)
    
    with col2:
        st.markdown("### 🎯 Best for:")
        st.markdown("""
        - Reviewing structure
        - Adding descriptions
        - Setting validation rules
        - Bulk editing attributes
        - Documentation
        """)
    
    st.markdown("---")
    
    if st.button("📥 Generate Enhanced Excel", type="primary"):
        with st.spinner("Generating enhanced Excel file..."):
            try:
                # Use EnhancedStructureExporter
                exporter = EnhancedStructureExporter(
                    client=supabase.client,
                    user_id=user_id
                )
                
                file_path = exporter.export_hierarchical_view()
                
                # Read file for download
                with open(file_path, 'rb') as f:
                    excel_data = f.read()
                
                st.success("✅ Enhanced Excel file generated successfully!")
                
                # Download button
                st.download_button(
                    label="⬇️ Download Hierarchical View Excel",
                    data=excel_data,
                    file_name=os.path.basename(file_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Enhanced Excel with validation, formulas, and grouping"
                )
                
                # Cleanup temp file
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            except Exception as e:
                st.error(f"❌ Error generating Excel: {str(e)}")
                st.exception(e)


def render_upload_page(supabase, user_id: str):
    """
    Render the upload template page with full parsing and update functionality.
    """
    st.title("📤 Upload Template")
    st.markdown("Update your structure by uploading an edited Hierarchical_View Excel")
    
    st.info("""
    **What you can do:**
    - ✅ **Add new rows** for Areas, Categories, Attributes
    - ✅ **Edit BLUE columns** in existing rows (editable fields)
    - ✅ **Create hierarchies** using Category_Path (e.g., "Health > Sleep > Quality")
    - ✅ **Update properties** like descriptions, data types, validation rules
    """)
    
    st.markdown("---")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Hierarchical_View Excel",
        type=["xlsx"],
        help="Upload the Excel file you downloaded from 'Download Structure'"
    )
    
    if not uploaded_file:
        st.markdown("### 📋 How to Use")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Step 1: Download**
            - Go to "📥 Download Structure"
            - Generate and download Excel
            
            **Step 2: Edit in Excel**
            - **Add rows** at bottom for new items
            - **Edit BLUE columns** (editable)
            - **Don't edit PINK columns** (auto-calculated)
            
            **Step 3: Upload**
            - Come back here
            - Upload edited file
            - Review changes
            - Confirm to apply
            """)
        
        with col2:
            st.markdown("""
            **Adding New Items:**
            
            **New Area:**
            - Type: `Area`
            - Category_Path: `<AreaName>`
            - Example: `Fitness`
            
            **New Category:**
            - Type: `Category`
            - Category_Path: `<Area> > <Category>`
            - Category: `<CategoryName>`
            - Example: `Fitness > Cardio`
            
            **New Subcategory:**
            - Type: `Category`
            - Category_Path: `<Area> > <Cat> > <SubCat>`
            - Category: `<SubCategoryName>`
            - Example: `Fitness > Cardio > Running`
            
            **New Attribute:**
            - Type: `Attribute`
            - Category_Path: `<full path to category>`
            - Attribute_Name: `<AttributeName>`
            - Data_Type: `number`, `text`, etc.
            - Example: `Fitness > Cardio > Running` + `Distance`
            """)
        
        st.markdown("---")
        
        st.markdown("""
        ### ✏️ Editable Fields (BLUE columns)
        
        - **Category** - Category name
        - **Attribute_Name** - Attribute name  
        - **Data_Type** - number, text, datetime, boolean, link, image
        - **Unit** - Unit of measurement (e.g., 'km', 'hours')
        - **Is_Required** - TRUE or FALSE
        - **Default_Value** - Default value for new events
        - **Validation_Min** - Minimum value (for numbers)
        - **Validation_Max** - Maximum value (for numbers)
        - **Description** - Notes and documentation
        
        ### 🚫 Read-Only Fields (PINK columns)
        
        - **Type** - Auto-detected from row content
        - **Level** - Auto-calculated from Category_Path
        - **Sort_Order** - Auto-assigned
        - **Area** - Extracted from Category_Path
        - **Category_Path** - Full hierarchical path
        
        ⚠️ **Important:** Don't change PINK columns - they're auto-calculated!
        """)
        
        return
    
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        # Parse and validate
        with st.spinner("📖 Parsing Excel file..."):
            parser = HierarchicalParser(
                client=supabase.client,
                user_id=user_id,
                excel_path=tmp_path
            )
            
            changes = parser.parse_and_validate()
        
        # Show validation errors if any
        if changes.validation_errors:
            st.error("❌ Validation Errors Found")
            
            with st.expander("🔍 View Validation Errors", expanded=True):
                for error in changes.validation_errors:
                    if error.row > 0:
                        st.error(f"**Row {error.row}, Column '{error.column}':** {error.message}")
                    else:
                        st.error(f"**{error.column}:** {error.message}")
            
            st.warning("⚠️ Please fix the errors above and re-upload the file.")
            
            # Generate error Excel with highlighted cells
            st.markdown("---")
            st.markdown("### 📥 Download Error Report")
            st.info("""
            **Download an Excel file with errors highlighted:**
            - 🟡 **Yellow cells** = Cells with validation errors
            - 💬 **Comments** = Hover over yellow cells to see error details
            - ✏️ **Fix errors** in Excel and re-upload
            """)
            
            if st.button("📥 Generate Error Report Excel", type="primary"):
                with st.spinner("Generating error report..."):
                    try:
                        # Generate error Excel
                        error_excel_path = generate_error_excel(tmp_path, changes.validation_errors)
                        
                        # Read the file for download
                        with open(error_excel_path, 'rb') as f:
                            error_excel_data = f.read()
                        
                        st.success("✅ Error report generated successfully!")
                        
                        # Download button
                        st.download_button(
                            label="⬇️ Download Error Report Excel",
                            data=error_excel_data,
                            file_name=os.path.basename(error_excel_path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="Excel file with highlighted errors and comments"
                        )
                        
                        # Cleanup
                        if os.path.exists(error_excel_path):
                            os.remove(error_excel_path)
                    
                    except Exception as e:
                        st.error(f"❌ Error generating error report: {str(e)}")
                        with st.expander("🔍 View Error Details"):
                            st.exception(e)
            
            return
        
        # Show validation warnings if any
        if changes.validation_warnings:
            st.warning("⚠️ Validation Warnings")
            
            with st.expander("🔍 View Warnings", expanded=False):
                for warning in changes.validation_warnings:
                    st.warning(f"**Row {warning.row}, Column '{warning.column}':** {warning.message}")
        
        # If no changes detected
        if not changes.has_changes():
            st.info("ℹ️ No changes detected in the uploaded file.")
            st.markdown("The file matches your current structure exactly.")
            return
        
        # Show detected changes
        st.success("✅ File parsed successfully!")
        st.markdown("### 📊 Detected Changes")
        
        # Summary metrics
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("New Areas", len(changes.new_areas))
        with col2:
            st.metric("New Categories", len(changes.new_categories))
        with col3:
            st.metric("New Attributes", len(changes.new_attributes))
        with col4:
            st.metric("Updated Areas", len(changes.updated_areas))
        with col5:
            st.metric("Updated Categories", len(changes.updated_categories))
        with col6:
            st.metric("Updated Attributes", len(changes.updated_attributes))
        
        st.markdown("---")
        
        # Detailed changes
        tabs = st.tabs([
            f"➕ New ({len(changes.new_areas) + len(changes.new_categories) + len(changes.new_attributes)})",
            f"✏️ Updated ({len(changes.updated_areas) + len(changes.updated_categories) + len(changes.updated_attributes)})"
        ])
        
        # Tab 1: New items
        with tabs[0]:
            if changes.new_areas:
                st.markdown("#### 🆕 New Areas")
                for area in changes.new_areas:
                    with st.expander(f"📁 {area['name']} (Row {area['excel_row']})"):
                        st.json({
                            'name': area['name'],
                            'icon': area['icon'],
                            'color': area['color'],
                            'sort_order': area['sort_order'],
                            'description': area['description']
                        })
            
            if changes.new_categories:
                st.markdown("#### 🆕 New Categories")
                for cat in changes.new_categories:
                    with st.expander(f"📂 {cat['path']} (Row {cat['excel_row']})"):
                        st.json({
                            'name': cat['name'],
                            'path': cat['path'],
                            'level': cat['level'],
                            'sort_order': cat['sort_order'],
                            'description': cat['description']
                        })
            
            if changes.new_attributes:
                st.markdown("#### 🆕 New Attributes")
                for attr in changes.new_attributes:
                    with st.expander(f"🏷️ {attr['category_path']} → {attr['name']} (Row {attr['excel_row']})"):
                        st.json({
                            'name': attr['name'],
                            'category_path': attr['category_path'],
                            'data_type': attr['data_type'],
                            'unit': attr['unit'],
                            'is_required': attr['is_required'],
                            'default_value': attr['default_value'],
                            'validation_rules': attr['validation_rules'],
                            'description': attr['description']
                        })
            
            if not changes.new_areas and not changes.new_categories and not changes.new_attributes:
                st.info("No new items to add")
        
        # Tab 2: Updated items
        with tabs[1]:
            if changes.updated_areas:
                st.markdown("#### ✏️ Updated Areas")
                for area in changes.updated_areas:
                    with st.expander(f"📁 {area['name']} (Row {area['excel_row']})"):
                        st.markdown("**Changes:**")
                        for key, value in area['updates'].items():
                            st.markdown(f"- **{key}:** `{value}`")
            
            if changes.updated_categories:
                st.markdown("#### ✏️ Updated Categories")
                for cat in changes.updated_categories:
                    with st.expander(f"📂 {cat['path']} (Row {cat['excel_row']})"):
                        st.markdown("**Changes:**")
                        for key, value in cat['updates'].items():
                            st.markdown(f"- **{key}:** `{value}`")
            
            if changes.updated_attributes:
                st.markdown("#### ✏️ Updated Attributes")
                for attr in changes.updated_attributes:
                    with st.expander(f"🏷️ {attr['category_path']} → {attr['name']} (Row {attr['excel_row']})"):
                        st.markdown("**Changes:**")
                        for key, value in attr['updates'].items():
                            st.markdown(f"- **{key}:** `{value}`")
            
            if not changes.updated_areas and not changes.updated_categories and not changes.updated_attributes:
                st.info("No updates to existing items")
        
        st.markdown("---")
        
        # Confirmation
        st.markdown("### ✅ Confirm Changes")
        st.warning("⚠️ **Important:** Once you confirm, these changes will be applied to your database immediately.")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            confirm_text = st.text_input(
                "Type 'CONFIRM' to apply changes:",
                placeholder="CONFIRM",
                help="Type CONFIRM in all caps to enable the Apply button"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            apply_button = st.button(
                "🚀 Apply Changes",
                type="primary",
                disabled=(confirm_text != "CONFIRM"),
                use_container_width=True
            )
        
        if apply_button and confirm_text == "CONFIRM":
            with st.spinner("💾 Applying changes to database..."):
                success, message = parser.apply_changes()
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                    
                    st.info("🔄 Changes applied successfully! Refresh the page to see updates.")
                    
                    # Add a button to view structure
                    if st.button("📊 View Updated Structure"):
                        st.switch_page("pages/1_📊_View_Structure.py")
                else:
                    st.error(f"❌ {message}")
                    st.warning("Please check the errors and try again.")
    
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        with st.expander("🔍 View Error Details"):
            st.exception(e)
    
    finally:
        # Cleanup temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


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
    
    ### 📊 View Data - Export
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
    
    ### 📥 Download Structure (Enhanced)
    Export your structure to Excel template with advanced features:
    - **Color-coded columns**: PINK (auto) vs BLUE (editable)
    - **Drop-down validations** for data types, required fields
    - **Auto-formulas** for Level, Area extraction
    - **Row grouping**: Collapsible Areas and Categories
    - **Column grouping**: Hide/show attribute details
    - **Validation fields**: Min/Max for number attributes
    
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
    st.caption("Version: 2025-11-23 16:00 UTC | Python: 3.11 | Streamlit: 1.28.0")


if __name__ == "__main__":
    main()
