"""
Events Tracker - Main Streamlit Application
Flexible event tracking system with customizable metadata structure
"""
import streamlit as st
import sys
from pathlib import Path
import json
import os
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from excel_parser import ExcelParser
from sql_generator import SQLGenerator
from supabase_client import SupabaseManager
from reverse_engineer import ReverseEngineer

# Page config
st.set_page_config(
    page_title="Events Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'backup_data' not in st.session_state:
    st.session_state.backup_data = None
if 'parsed_excel' not in st.session_state:
    st.session_state.parsed_excel = None
if 'changes_preview' not in st.session_state:
    st.session_state.changes_preview = None


def init_supabase():
    """Initialize Supabase client from secrets or env."""
    try:
        # Try Streamlit secrets first
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except:
        # Fall back to environment variables
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        st.error("""
        ⚠️ Supabase credentials not found!
        
        Please configure either:
        1. Streamlit secrets (.streamlit/secrets.toml)
        2. Environment variables (.env file)
        
        Required variables:
        - SUPABASE_URL
        - SUPABASE_KEY
        """)
        st.stop()
    
    return SupabaseManager(url, key)


def main():
    """Main application logic."""
    
    st.title("📊 Events Tracker")
    st.markdown("*Flexible event tracking with customizable metadata structure*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Action",
        ["📤 Upload Template", "📥 Export Structure", "📄 Generate SQL", "ℹ️ Help"]
    )
    
    # Initialize Supabase
    try:
        supabase = init_supabase()
        
        # Test connection
        with st.sidebar:
            st.divider()
            with st.expander("🔌 Connection Status"):
                success, message = supabase.test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
    except Exception as e:
        st.error(f"Failed to initialize Supabase: {e}")
        st.stop()
    
    # Page routing
    if page == "📤 Upload Template":
        upload_template_page(supabase)
    elif page == "📥 Export Structure":
        export_structure_page(supabase)
    elif page == "📄 Generate SQL":
        generate_sql_page()
    elif page == "ℹ️ Help":
        help_page()


def upload_template_page(supabase: SupabaseManager):
    """Page for uploading and applying Excel templates."""
    
    st.header("Upload Template")
    st.markdown("""
    Upload an Excel template to configure your tracking structure.
    The system will:
    1. Validate the template
    2. Show you what will change
    3. Create a backup before applying
    4. Apply changes to your database
    """)
    
    # User ID input (temporary until auth is implemented)
    st.warning("⚠️ User authentication not yet implemented. Using test user ID.")
    user_id = st.text_input(
        "User ID (UUID)", 
        value="00000000-0000-0000-0000-000000000000",
        help="Enter your user UUID (get from Supabase Auth)"
    )
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose Excel template",
        type=['xlsx'],
        help="Upload an Excel file with Areas, Categories, and Attributes sheets"
    )
    
    if uploaded_file:
        # Save uploaded file temporarily
        temp_path = Path("temp_upload.xlsx")
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        # Parse Excel
        with st.spinner("Parsing and validating template..."):
            parser = ExcelParser(str(temp_path))
            success, errors, warnings = parser.parse()
        
        # Show validation results
        st.subheader("Validation Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Areas", parser.get_summary()['areas_count'])
        with col2:
            st.metric("Categories", parser.get_summary()['categories_count'])
        with col3:
            st.metric("Attributes", parser.get_summary()['attributes_count'])
        
        if errors:
            st.error("❌ Validation failed!")
            for error in errors:
                st.error(f"• {error}")
        else:
            st.success("✅ Validation passed!")
        
        if warnings:
            st.warning("⚠️ Warnings:")
            for warning in warnings:
                st.warning(f"• {warning}")
        
        # Show preview
        if not errors:
            st.subheader("Template Preview")
            
            tab1, tab2, tab3 = st.tabs(["Areas", "Categories", "Attributes"])
            
            with tab1:
                areas_display = [
                    {
                        'Name': a.name,
                        'Icon': a.icon,
                        'Description': a.description,
                        'Sort': a.sort_order
                    }
                    for a in parser.areas
                ]
                st.dataframe(areas_display, use_container_width=True)
            
            with tab2:
                categories_display = [
                    {
                        'Name': c.name,
                        'Area': next((a.name for a in parser.areas if a.uuid == c.area_uuid), 'Unknown'),
                        'Level': c.level,
                        'Description': c.description,
                        'Sort': c.sort_order
                    }
                    for c in parser.categories
                ]
                st.dataframe(categories_display, use_container_width=True)
            
            with tab3:
                attributes_display = [
                    {
                        'Name': attr.name,
                        'Category': next((c.name for c in parser.categories if c.uuid == attr.category_uuid), 'Unknown'),
                        'Type': attr.data_type,
                        'Unit': attr.unit,
                        'Required': attr.is_required
                    }
                    for attr in parser.attributes
                ]
                st.dataframe(attributes_display, use_container_width=True)
            
            # Detect changes
            st.subheader("Change Detection")
            
            with st.spinner("Detecting changes..."):
                try:
                    current_backup = supabase.backup_metadata(user_id)
                    changes = supabase.detect_changes(
                        current_backup,
                        parser.areas,
                        parser.categories,
                        parser.attributes
                    )
                    
                    st.session_state.backup_data = current_backup
                    st.session_state.parsed_excel = parser
                    st.session_state.changes_preview = changes
                    
                    # Display changes
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("To Add", 
                                 len(changes['areas']['add']) + 
                                 len(changes['categories']['add']) + 
                                 len(changes['attributes']['add']))
                    
                    with col2:
                        st.metric("To Update",
                                 len(changes['areas']['update']) +
                                 len(changes['categories']['update']) +
                                 len(changes['attributes']['update']))
                    
                    with col3:
                        deletions = (len(changes['areas']['delete']) +
                                   len(changes['categories']['delete']) +
                                   len(changes['attributes']['delete']))
                        st.metric("To Delete", deletions)
                    
                    # Show detailed changes
                    if any(changes['areas']['delete'] + changes['categories']['delete']):
                        st.warning("⚠️ **Deletion Warning**")
                        
                        if changes['categories']['delete']:
                            # Count affected events
                            cat_ids = [
                                c.uuid for c in parser.categories
                                if c.name in changes['categories']['delete']
                            ]
                            affected_events = supabase.count_affected_events(cat_ids)
                            
                            if affected_events > 0:
                                st.error(f"""
                                **{affected_events} events will be CASCADE DELETED!**
                                
                                Categories to be deleted:
                                {', '.join(changes['categories']['delete'])}
                                
                                A backup will be created before deletion.
                                """)
                    
                    with st.expander("View Detailed Changes"):
                        st.json(changes)
                    
                    # Apply changes button
                    st.divider()
                    st.subheader("Apply Changes")
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown("""
                        **What will happen:**
                        1. Create backup of current structure
                        2. Apply new/updated records (UPSERT)
                        3. Delete removed records (CASCADE)
                        4. Save backup file for rollback
                        """)
                    
                    with col2:
                        if st.button("🚀 Apply Changes", type="primary", use_container_width=True):
                            apply_changes(supabase, user_id, parser, current_backup)
                
                except Exception as e:
                    st.error(f"Error detecting changes: {e}")
        
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


def apply_changes(supabase: SupabaseManager, user_id: str, 
                 parser: ExcelParser, backup_data: dict):
    """Apply changes to Supabase database."""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Save backup file
        status_text.text("Saving backup...")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = backup_dir / backup_filename
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        progress_bar.progress(25)
        
        # Step 2: Apply upserts
        status_text.text("Applying updates...")
        success, message = supabase.apply_changes(
            user_id,
            parser.areas,
            parser.categories,
            parser.attributes
        )
        
        if not success:
            st.error(f"Failed to apply changes: {message}")
            return
        
        progress_bar.progress(50)
        
        # Step 3: Delete removed items
        status_text.text("Removing deleted items...")
        success, message = supabase.delete_removed_items(
            backup_data,
            parser.areas,
            parser.categories,
            parser.attributes
        )
        
        if not success:
            st.error(f"Failed to delete items: {message}")
            return
        
        progress_bar.progress(100)
        status_text.text("Complete!")
        
        # Success message
        st.success(f"""
        ✅ **Changes Applied Successfully!**
        
        Backup saved: `{backup_path}`
        
        Summary:
        - {len(parser.areas)} Areas
        - {len(parser.categories)} Categories  
        - {len(parser.attributes)} Attributes
        """)
        
    except Exception as e:
        st.error(f"Error applying changes: {e}")


def export_structure_page(supabase: SupabaseManager):
    """Page for exporting current structure to Excel."""
    
    st.header("Export Structure")
    st.markdown("""
    Export your current tracking structure to an Excel template.
    You can then edit it and re-upload to make changes.
    """)
    
    user_id = st.text_input(
        "User ID (UUID)",
        value="00000000-0000-0000-0000-000000000000",
        help="Enter your user UUID"
    )
    
    if st.button("📥 Export to Excel", type="primary"):
        with st.spinner("Exporting structure..."):
            try:
                reverse_eng = ReverseEngineer(supabase.client)
                
                # Generate filename
                filename = reverse_eng.create_backup_filename(user_id)
                output_path = Path("exports") / filename
                output_path.parent.mkdir(exist_ok=True)
                
                # Export
                success, message = reverse_eng.export_to_excel(
                    user_id,
                    str(output_path)
                )
                
                if success:
                    st.success(message)
                    
                    # Provide download
                    with open(output_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ Download Excel File",
                            data=f,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error(message)
                    
            except Exception as e:
                st.error(f"Export failed: {e}")


def generate_sql_page():
    """Page for generating SQL from Excel template."""
    
    st.header("Generate SQL")
    st.markdown("""
    Generate SQL schema from an Excel template.
    Use this to create a new database or understand the structure.
    """)
    
    uploaded_file = st.file_uploader(
        "Choose Excel template",
        type=['xlsx'],
        key="sql_gen_upload"
    )
    
    if uploaded_file:
        # Save temporarily
        temp_path = Path("temp_sql_gen.xlsx")
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        # Parse
        parser = ExcelParser(str(temp_path))
        success, errors, warnings = parser.parse()
        
        if errors:
            st.error("Template has validation errors. Fix them first.")
            for error in errors:
                st.error(f"• {error}")
        else:
            # Generate SQL
            generator = SQLGenerator(
                parser.areas,
                parser.categories,
                parser.attributes
            )
            
            sql = generator.generate_full_schema()
            
            st.subheader("Generated SQL")
            st.code(sql, language='sql')
            
            # Download button
            st.download_button(
                label="⬇️ Download SQL File",
                data=sql,
                file_name="events_tracker_schema.sql",
                mime="text/plain"
            )
            
            st.info("""
            **How to use this SQL:**
            
            1. Copy the SQL or download the file
            2. Go to Supabase Dashboard → SQL Editor
            3. Paste and run the SQL
            4. Verify tables were created in Table Editor
            """)
        
        # Clean up
        if temp_path.exists():
            temp_path.unlink()


def help_page():
    """Help and documentation page."""
    
    st.header("Help & Documentation")
    
    with st.expander("📖 Quick Start Guide", expanded=True):
        st.markdown("""
        ### 1. Setup Supabase Project
        
        1. Go to [supabase.com](https://supabase.com)
        2. Create new project: `events-tracker`
        3. Note your Project URL and anon key
        4. Add to `.streamlit/secrets.toml`:
           ```toml
           SUPABASE_URL = "https://xxx.supabase.co"
           SUPABASE_KEY = "your-anon-key"
           ```
        
        ### 2. Generate and Apply SQL
        
        1. Download template: `templates/garmin_fitness_template.xlsx`
        2. Go to "Generate SQL" page
        3. Upload template → Download SQL
        4. Run SQL in Supabase Dashboard
        
        ### 3. Customize Structure
        
        1. Export your current structure
        2. Edit in Excel (add/remove/rename items)
        3. Upload modified template
        4. Review changes and apply
        
        ### 4. Track Events
        
        (Coming soon - Event entry interface)
        """)
    
    with st.expander("📋 Excel Template Format"):
        st.markdown("""
        ### Required Sheets
        
        **Areas Sheet:**
        - `uuid`: Unique identifier (UUID v4)
        - `name`: Display name
        - `icon`: Emoji or icon
        - `color`: Hex color code
        - `sort_order`: Display order (integer)
        - `description`: Optional description
        
        **Categories Sheet:**
        - `uuid`: Unique identifier
        - `area_uuid`: References Area uuid
        - `parent_uuid`: Parent category (optional)
        - `name`: Display name
        - `description`: Optional description
        - `level`: Hierarchy level (1-10)
        - `sort_order`: Display order
        
        **Attributes Sheet:**
        - `uuid`: Unique identifier
        - `category_uuid`: References Category uuid
        - `name`: Attribute name
        - `data_type`: `number`, `text`, `datetime`, `boolean`, `link`, `image`
        - `unit`: Unit of measurement (optional)
        - `is_required`: TRUE/FALSE
        - `default_value`: Default value (optional)
        - `validation_rules`: JSON rules, e.g. `{"min": 0, "max": 100}`
        - `sort_order`: Display order
        """)
    
    with st.expander("🔒 Row Level Security (RLS)"):
        st.markdown("""
        All tables have RLS enabled. Users can only:
        
        - **View** their own data
        - **Create** records under their user_id
        - **Update** their own records
        - **Delete** their own records
        
        CASCADE deletion ensures:
        - Deleting an Area → deletes Categories → deletes Events
        - Deleting a Category → deletes Events
        - Deleting an Attribute → doesn't affect Events (just removes definition)
        """)
    
    with st.expander("💾 Backups"):
        st.markdown("""
        Before applying changes, the system:
        
        1. **Creates JSON backup** in `backups/` folder
        2. **Shows preview** of what will change
        3. **Warns about deletions** with event counts
        4. **Applies changes** only after confirmation
        
        To restore a backup:
        1. Find backup file in `backups/`
        2. Export to Excel format (manual step)
        3. Re-upload as template
        """)


if __name__ == "__main__":
    main()
