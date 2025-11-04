"""
Events Tracker - Main Streamlit Application (WITH AUTHENTICATION)
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
from auth import AuthManager

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
    """Main application logic with authentication."""
    
    # Initialize Supabase
    try:
        supabase = init_supabase()
    except Exception as e:
        st.error(f"Failed to initialize Supabase: {e}")
        st.stop()
    
    # Initialize Auth Manager
    auth = AuthManager(supabase.client)
    
    # Check authentication
    if not auth.is_authenticated():
        # Show login page
        auth.show_login_page()
        return
    
    # User is authenticated - show main app
    st.title("📊 Events Tracker")
    st.markdown("*Flexible event tracking with customizable metadata structure*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Action",
        ["📤 Upload Template", "📥 Export Structure", "📄 Generate SQL", "ℹ️ Help"]
    )
    
    # Show user info and logout button
    auth.show_user_info_sidebar()
    
    # Test connection
    with st.sidebar:
        st.divider()
        with st.expander("🔌 Connection Status"):
            success, message = supabase.test_connection()
            if success:
                st.success(message)
            else:
                st.error(message)
    
    # Page routing (passing user_id to functions that need it)
    user_id = auth.get_user_id()
    
    if page == "📤 Upload Template":
        upload_template_page(supabase, user_id)
    elif page == "📥 Export Structure":
        export_structure_page(supabase, user_id)
    elif page == "📄 Generate SQL":
        generate_sql_page()
    elif page == "ℹ️ Help":
        help_page()


def upload_template_page(supabase: SupabaseManager, user_id: str):
    """Page for uploading and applying Excel templates."""
    
    st.header("Upload Template")
    st.markdown("""
    Upload an Excel template to configure your tracking structure. The system will:
    1. Validate the template
    2. Show you what will change
    3. Create a backup before applying
    4. Apply changes to your database
    """)
    
    st.info("ℹ️ **Note**: Changes are applied to YOUR data only (secured with RLS)")
    
    uploaded_file = st.file_uploader(
        "Choose Excel template",
        type=['xlsx'],
        help="Upload an Excel file with Areas, Categories, and Attributes sheets"
    )
    
    if uploaded_file:
        # Save temporarily
        temp_path = Path("temp_upload.xlsx")
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        # Parse Excel
        st.subheader("📋 Validation Results")
        parser = ExcelParser(str(temp_path))
        success, errors, warnings = parser.parse()
        # ADD THIS DEBUG LINE:
        st.write(f"DEBUG: Parser has {len(parser.attributes)} attributes after parsing")
        
        # Show stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Areas", len(parser.areas))
        with col2:
            st.metric("Categories", len(parser.categories))
        with col3:
            st.metric("Attributes", len(parser.attributes))
        
        if errors:
            st.error("❌ Validation failed!")
            for error in errors:
                st.error(f"• {error}")
        else:
            st.success("✅ Template is valid!")
            
            if warnings:
                st.warning("⚠️ Warnings:")
                for warning in warnings:
                    st.warning(f"• {warning}")
            
            # Get current structure from database (for this user only)
            current_areas, current_categories, current_attributes = supabase.get_current_structure(user_id)
            
            # Detect changes
            st.subheader("📊 Changes Preview")
            
            # Compare and show changes
            # ... (keep existing change detection logic but filter by user_id)
            
            st.info("💡 Review the changes above carefully before applying.")
            
            if st.button("🚀 Apply Changes", type="primary"):
                try:
                    # Create backup
                    backup_data = {
                        'areas': current_areas,
                        'categories': current_categories,
                        'attributes': current_attributes,
                        'timestamp': datetime.now().isoformat(),
                        'user_id': user_id
                    }
                    st.session_state.backup_data = backup_data
                    
                    # Apply changes (with user_id)
                    supabase.apply_template(parser.areas, parser.categories, parser.attributes, user_id)
                    
                    st.success("✅ Changes applied successfully!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Failed to apply changes: {e}")
        
        # Clean up
        if temp_path.exists():
            temp_path.unlink()


def export_structure_page(supabase: SupabaseManager, user_id: str):
    """Page for exporting current structure to Excel."""
    
    st.header("Export Structure")
    st.markdown("""
    Export your current tracking structure to an Excel template. You can then edit it and re-upload to make changes.
    """)
    
    st.info("ℹ️ **Note**: Only YOUR data will be exported (secured with RLS)")
    
    if st.button("📥 Export to Excel", type="primary"):
        try:
            # Get current structure (filtered by user_id)
            areas, categories, attributes = supabase.get_current_structure(user_id)
            
            # Export to Excel
            reverse = ReverseEngineer()
            excel_bytes = reverse.export_to_excel(areas, categories, attributes)
            
            # Show summary
            st.success("Exported successfully:")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Areas", len(areas))
            with col2:
                st.metric("Categories", len(categories))
            with col3:
                st.metric("Attributes", len(attributes))
            
            # Download button
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"structure_export_{timestamp}.xlsx"
            
            st.download_button(
                label="📥 Download Excel File",
                data=excel_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"❌ Export failed: {e}")


def generate_sql_page():
    """Page for generating SQL from Excel template."""
    
    st.header("Generate SQL")
    st.markdown("""
    Generate SQL schema from an Excel template.
    Use this to create a new database or understand the structure.
    """)
    
    st.warning("⚠️ **Note**: This generates schema WITHOUT authentication. Use only for initial setup!")
    
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
            5. Run the authentication setup SQL
            6. Sign up as a user in the app
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
        
        ### 2. Setup Database
        
        1. Download template: `templates/garmin_fitness_template.xlsx`
        2. Go to "Generate SQL" page
        3. Upload template → Download SQL
        4. Run SQL in Supabase Dashboard
        5. Run authentication setup SQL
        
        ### 3. Sign Up
        
        1. Return to app
        2. Click "Sign Up" tab
        3. Enter email and password
        4. Check email for confirmation
        5. Login!
        
        ### 4. Customize Structure
        
        1. Export your current structure
        2. Edit in Excel (add/remove/rename items)
        3. Upload modified template
        4. Review changes and apply
        
        ### 5. Track Events
        
        (Coming soon - Event entry interface)
        """)
    
    with st.expander("🔒 Security & Privacy"):
        st.markdown("""
        ### Row Level Security (RLS)
        
        - All your data is **private** and secured
        - You can only see and modify YOUR data
        - Other users cannot access your data
        - Implemented via PostgreSQL RLS policies
        
        ### Authentication
        
        - Powered by Supabase Auth
        - Email/password authentication
        - Email confirmation required
        - Secure token-based sessions
        """)
    
    with st.expander("📋 Excel Template Format"):
        st.markdown("""
        ### Required Sheets
        
        1. **Areas** - Top-level organization
           - uuid, name, icon, color, sort_order, description
        
        2. **Categories** - Hierarchical subcategories
           - uuid, area_uuid, parent_uuid, name, description, level, sort_order
        
        3. **Attributes** - What data to capture
           - uuid, category_uuid, name, data_type, unit, is_required, default_value, validation_rules, sort_order
        
        ### UUID Management
        
        - Every item has a UUID (unique identifier)
        - UUIDs allow renaming without breaking relationships
        - Generate new UUIDs with Python: `import uuid; str(uuid.uuid4())`
        - Never reuse UUIDs from deleted items
        """)


if __name__ == "__main__":
    main()
