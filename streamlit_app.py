"""
Events Tracker - Main Streamlit Application 20251107-1400
Flexible event tracking with NAME-BASED templates and automatic rename detection
"""
import streamlit as st
import sys
from pathlib import Path
import json
import os
from datetime import datetime
import io

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

# FIXED: Use explicit src. prefix to avoid conflicts with system packages
from src.excel_validators import validate_template
from src.excel_parser_new import ExcelTemplateParser, load_from_database
from src.rename_detector import RenameDetector
from src.supabase_client import SupabaseManager
from src.auth import AuthManager

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
if 'validation_result' not in st.session_state:
    st.session_state.validation_result = None
if 'operations' not in st.session_state:
    st.session_state.operations = None


def init_supabase():
    """Initialize Supabase client from secrets or env."""
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except:
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
        auth.show_login_page()
        return
    
    # User is authenticated - show main app
    st.title("📊 Events Tracker")
    st.markdown("*Name-based templates with automatic rename detection*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Action",
        ["📤 Upload Template", "📥 Download Structure", "ℹ️ Help"]
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
    
    # Page routing
    user_id = auth.get_user_id()
    
    if page == "📤 Upload Template":
        upload_template_page(supabase, user_id)
    elif page == "📥 Download Structure":
        download_structure_page(supabase, user_id)
    elif page == "ℹ️ Help":
        help_page()


def upload_template_page(supabase: SupabaseManager, user_id: str):
    """Page for uploading name-based templates with rename detection."""
    
    st.header("📤 Upload Template")
    st.markdown("""
    Upload an Excel template using **names as identifiers** (no UUID management needed!). 
    The system will:
    1. ✅ Validate the template for errors
    2. 🔍 Detect renamed objects automatically
    3. 📊 Show you what will change
    4. 🚀 Apply changes atomically
    """)
    
    st.info("💡 **New**: Just use names! System handles UUID mapping automatically.")
    
    uploaded_file = st.file_uploader(
        "Choose Excel template",
        type=['xlsx'],
        help="Upload template with Areas, Categories, and Attributes sheets"
    )
    
    if uploaded_file:
        # Save temporarily
        temp_path = Path("temp_upload.xlsx")
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        # ==========================================
        # STEP 1: VALIDATION
        # ==========================================
        st.subheader("📋 Step 1: Validation")
        
        with st.spinner("Validating template..."):
            is_valid, report, error_file = validate_template(str(temp_path))
        
        if not is_valid:
            st.error("❌ Validation failed!")
            st.text(report)
            
            if error_file:
                with open(error_file, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download Template with Errors Highlighted",
                        data=f.read(),
                        file_name="template_with_errors.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            if temp_path.exists():
                temp_path.unlink()
            return
        
        st.success("✅ Validation passed!")
        
        # ==========================================
        # STEP 2: PARSE EXCEL
        # ==========================================
        st.subheader("📖 Step 2: Parsing Template")
        
        with st.spinner("Reading Excel file..."):
            parser = ExcelTemplateParser(str(temp_path))
            new_areas, new_categories, new_attributes = parser.parse()
            summary = parser.get_summary()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Areas", summary['areas_count'])
        with col2:
            st.metric("Categories", summary['categories_count'])
        with col3:
            st.metric("Attributes", summary['attributes_count'])
        
        # ==========================================
        # STEP 3: LOAD FROM DATABASE
        # ==========================================
        st.subheader("📥 Step 3: Loading Existing Data")
        
        with st.spinner("Loading from database..."):
            old_areas, old_categories, old_attributes = load_from_database(
                supabase.client, user_id
            )
        
        st.info(f"Found {len(old_areas)} areas, {len(old_categories)} categories, "
                f"{len(old_attributes)} attributes in database")
        
        # ==========================================
        # STEP 4: RENAME DETECTION
        # ==========================================
        st.subheader("🔍 Step 4: Detecting Changes")
        
        with st.spinner("Analyzing changes..."):
            # Process Areas
            area_detector = RenameDetector(confidence_threshold=0.65)
            area_matches = area_detector.match_objects(old_areas, new_areas)
            area_operations = area_detector.generate_operations()
            
            # Process Categories
            cat_detector = RenameDetector(confidence_threshold=0.65)
            cat_matches = cat_detector.match_objects(old_categories, new_categories)
            cat_operations = cat_detector.generate_operations()
            
            # Process Attributes
            attr_detector = RenameDetector(confidence_threshold=0.65)
            attr_matches = attr_detector.match_objects(old_attributes, new_attributes)
            attr_operations = attr_detector.generate_operations()
            
            # Combine all operations
            all_operations = area_operations + cat_operations + attr_operations
            st.session_state.operations = all_operations
        
        # ==========================================
        # STEP 5: DISPLAY CHANGES
        # ==========================================
        st.subheader("📊 Step 5: Changes Preview")
        
        # Categorize operations
        renames = [op for op in all_operations 
                   if op['operation'] == 'UPDATE' and 'new_name' in op]
        inserts = [op for op in all_operations if op['operation'] == 'INSERT']
        deletes = [op for op in all_operations if op['operation'] == 'DELETE']
        updates = [op for op in all_operations 
                   if op['operation'] == 'UPDATE' and 'changes' in op]
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔄 Renames", len(renames))
        with col2:
            st.metric("➕ New Objects", len(inserts))
        with col3:
            st.metric("🗑️ Deletions", len(deletes))
        with col4:
            st.metric("✏️ Updates", len(updates))
        
        # Detailed view in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔄 Renames", "➕ New", "🗑️ Deletions", "✏️ Updates"])
        
        with tab1:
            if renames:
                st.markdown("**Detected Renames:**")
                for op in renames:
                    confidence = op.get('confidence', 1.0)
                    
                    # Color based on confidence
                    if confidence > 0.85:
                        emoji = "🟢"
                        conf_color = "green"
                    elif confidence > 0.70:
                        emoji = "🟡"
                        conf_color = "orange"
                    else:
                        emoji = "🟠"
                        conf_color = "red"
                    
                    table = op['table_name'].replace('_', ' ').title()
                    old_name = op.get('old_name', 'Unknown')
                    new_name = op['new_name']
                    
                    st.markdown(
                        f"{emoji} **[{table}]** `{old_name}` → `{new_name}` "
                        f"<span style='color:{conf_color}'>(confidence: {confidence:.0%})</span>",
                        unsafe_allow_html=True
                    )
                    
                    # Show warning for low confidence
                    if confidence < 0.70:
                        st.warning(
                            f"⚠️ Low confidence! Please verify this is actually a rename "
                            f"of '{old_name}' and not a new object."
                        )
                        with st.expander("View matching signals"):
                            st.json(op.get('signals', {}))
            else:
                st.info("No renames detected")
        
        with tab2:
            if inserts:
                st.markdown(f"**{len(inserts)} new objects will be created:**")
                for op in inserts:
                    table = op['table_name'].replace('_', ' ').title()
                    name = op['name']
                    
                    if op['table_name'] == 'categories':
                        area = op.get('area_name', '')
                        parent = op.get('parent_name', '')
                        context = f" in {area}" + (f" > {parent}" if parent else "")
                    elif op['table_name'] == 'attribute_definitions':
                        category = op.get('category_name', '')
                        context = f" for {category}"
                    else:
                        context = ""
                    
                    st.markdown(f"• **[{table}]** {name}{context}")
            else:
                st.info("No new objects to create")
        
        with tab3:
            if deletes:
                st.warning(f"⚠️ **{len(deletes)} objects will be deleted:**")
                for op in deletes:
                    table = op['table_name'].replace('_', ' ').title()
                    name = op['name']
                    st.markdown(f"• **[{table}]** {name}")
                
                if any(op['table_name'] == 'categories' for op in deletes):
                    st.error(
                        "⚠️ **WARNING**: Deleting categories may fail if they have events. "
                        "Events must be reassigned or deleted first."
                    )
            else:
                st.info("No objects will be deleted")
        
        with tab4:
            if updates:
                st.markdown(f"**{len(updates)} objects will have attribute changes:**")
                for op in updates:
                    table = op['table_name'].replace('_', ' ').title()
                    changes = op.get('changes', {})
                    st.markdown(f"**[{table}]**")
                    for key, (old_val, new_val) in changes.items():
                        st.markdown(f"  • {key}: `{old_val}` → `{new_val}`")
            else:
                st.info("No attribute updates")
        
        # ==========================================
        # STEP 6: CONFIRMATION & APPLY
        # ==========================================
        st.divider()
        
        if len(all_operations) == 0:
            st.success("✅ No changes detected - your template matches the database!")
        else:
            st.warning("⚠️ **Review changes carefully before applying!**")
            
            if st.checkbox("I have reviewed the changes and want to proceed"):
                if st.button("🚀 Apply Changes", type="primary"):
                    
                    # Create backup info
                    backup_info = {
                        'timestamp': datetime.now().isoformat(),
                        'user_id': user_id,
                        'operation_count': len(all_operations)
                    }
                    st.session_state.backup_data = backup_info
                    
                    # Apply changes via stored procedure
                    with st.spinner("Applying changes to database..."):
                        try:
                            result = supabase.client.rpc(
                                'update_template_from_excel',
                                {
                                    'p_user_id': user_id,
                                    'p_template_data': all_operations
                                }
                            ).execute()
                            
                            if result.data.get('success'):
                                st.success("✅ Changes applied successfully!")
                                
                                # Show summary
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Inserted", result.data.get('inserted', 0))
                                with col2:
                                    st.metric("Updated", result.data.get('updated', 0))
                                with col3:
                                    st.metric("Renamed", result.data.get('renamed', 0))
                                with col4:
                                    st.metric("Deleted", result.data.get('deleted', 0))
                                
                                st.balloons()
                                
                                # Clear session state
                                st.session_state.operations = None
                                
                            else:
                                st.error(f"❌ Error: {result.data.get('error')}")
                                st.error(f"Details: {result.data.get('error_detail')}")
                        
                        except Exception as e:
                            st.error(f"❌ Failed to apply changes: {str(e)}")
                            st.error("Check Supabase logs for more details")
        
        # Clean up
        if temp_path.exists():
            temp_path.unlink()


def download_structure_page(supabase: SupabaseManager, user_id: str):
    """Page for downloading current structure as name-based template."""
    
    st.header("📥 Download Current Structure")
    st.markdown("""
    Download your current structure as an **Excel template** that you can:
    - ✏️ Edit names (renames detected automatically on re-upload)
    - ➕ Add new areas, categories, or attributes
    - 🗑️ Delete items (remove rows)
    - 📤 Upload back to apply changes
    """)
    
    st.info("💡 **No UUID management needed** - just work with names!")
    
    if st.button("📥 Generate Template", type="primary"):
        with st.spinner("Generating Excel template..."):
            try:
                # Load from database
                areas, categories, attributes = load_from_database(
                    supabase.client, user_id
                )
                
                if not areas and not categories and not attributes:
                    st.warning("⚠️ No data found. Upload a template first!")
                    return
                
                # Convert to DataFrames
                import pandas as pd
                
                df_areas = pd.DataFrame([
                    {
                        'area_id': obj.uuid,
                        'area_name': obj.name,
                        'icon': obj.attributes.get('icon', ''),
                        'color': obj.attributes.get('color', ''),
                        'sort_order': obj.attributes.get('sort_order', 0),
                        'description': obj.attributes.get('description', '')
                    }
                    for obj in areas
                ])
                
                df_categories = pd.DataFrame([
                    {
                        'category_id': obj.uuid,
                        'area_name': obj.area_name,
                        'parent_category': obj.parent_name or '',
                        'category_name': obj.name,
                        'level': obj.level,
                        'sort_order': obj.attributes.get('sort_order', 0),
                        'description': obj.attributes.get('description', '')
                    }
                    for obj in categories
                ])
                
                df_attributes = pd.DataFrame([
                    {
                        'attribute_id': obj.uuid,
                        'category_name': obj.category_name,
                        'attribute_name': obj.name,
                        'data_type': obj.attributes.get('data_type'),
                        'unit': obj.attributes.get('unit', ''),
                        'is_required': obj.attributes.get('is_required', False),
                        'default_value': obj.attributes.get('default_value', ''),
                        'validation_rules': obj.attributes.get('validation_rules', '{}'),
                        'sort_order': obj.attributes.get('sort_order', 0)
                    }
                    for obj in attributes
                ])
                
                # Write to Excel in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_areas.to_excel(writer, sheet_name='Areas', index=False)
                    df_categories.to_excel(writer, sheet_name='Categories', index=False)
                    df_attributes.to_excel(writer, sheet_name='Attributes', index=False)
                
                excel_bytes = output.getvalue()
                
                # Show summary
                st.success("✅ Template generated!")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Areas", len(df_areas))
                with col2:
                    st.metric("Categories", len(df_categories))
                with col3:
                    st.metric("Attributes", len(df_attributes))
                
                # Download button
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"template_{timestamp}.xlsx"
                
                st.download_button(
                    label="⬇️ Download Excel Template",
                    data=excel_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.info("""
                **How to use this template:**
                
                1. Open in Excel
                2. Edit names, add/remove rows
                3. Save and upload via "Upload Template"
                4. System will detect renames automatically!
                
                **Note:** Keep the `*_id` columns - they help detect renames. 
                Leave them empty for new items.
                """)
                
            except Exception as e:
                st.error(f"❌ Failed to generate template: {str(e)}")


def help_page():
    """Help and documentation page."""
    
    st.header("ℹ️ Help & Documentation")
    
    with st.expander("🚀 What's New - Name-Based Templates", expanded=True):
        st.markdown("""
        ### No More UUID Management! 🎉
        
        **Old Way (UUID-based):**
        - ❌ Manually generate UUIDs for each item
        - ❌ Complex to rename (had to keep UUID, change name)
        - ❌ Easy to break relationships
        
        **New Way (Name-based):**
        - ✅ Just use names - system handles UUIDs automatically
        - ✅ Rename by simply changing the name
        - ✅ Automatic rename detection
        - ✅ Relationships preserved
        
        ### How Rename Detection Works
        
        System uses multiple signals:
        - Position in file (20%)
        - Name similarity (40%)
        - Parent matching (20%)
        - Sibling context (10%)
        - Other attributes (10%)
        
        = **Confidence Score** (0-100%)
        
        - 🟢 High (>85%): Auto-accepted
        - 🟡 Medium (70-85%): Shows for review
        - 🟠 Low (<70%): Treated as new object
        """)
    
    with st.expander("📋 Excel Template Format"):
        st.markdown("""
        ### Areas Sheet
        
        | Column | Required | Description |
        |--------|----------|-------------|
        | area_id | Optional | Leave empty for new, keep for renames |
        | area_name | ✅ Yes | **Unique name** |
        | icon | No | Emoji or icon |
        | color | No | Hex color code |
        | sort_order | Yes | Display order |
        | description | No | Text description |
        
        ### Categories Sheet
        
        | Column | Required | Description |
        |--------|----------|-------------|
        | category_id | Optional | Leave empty for new |
        | area_name | ✅ Yes | Reference to parent area |
        | parent_category | No | Parent category name (empty for root) |
        | category_name | ✅ Yes | **Unique within parent** |
        | level | ✅ Yes | 1-10 (depth in hierarchy) |
        | sort_order | Yes | Display order |
        | description | No | Text description |
        
        ### Attributes Sheet
        
        | Column | Required | Description |
        |--------|----------|-------------|
        | attribute_id | Optional | Leave empty for new |
        | category_name | ✅ Yes | Which category this belongs to |
        | attribute_name | ✅ Yes | **Unique within category** |
        | data_type | ✅ Yes | number, text, datetime, boolean, link, image |
        | unit | No | e.g., "km", "kg", "hours" |
        | is_required | No | TRUE/FALSE |
        | default_value | No | Default value |
        | validation_rules | No | JSON rules |
        | sort_order | Yes | Display order |
        
        ### Uniqueness Rules
        
        - ✅ Area names must be unique
        - ✅ Category names must be unique within their parent
        - ✅ Attribute names must be unique within their category
        - ❌ Different parents CAN have categories with same name
        """)
    
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        ### Common Issues
        
        **Q: Validation failed with "duplicate name"**
        - Check that names are unique within their scope
        - Download the error-highlighted template to see exact issues
        
        **Q: Low confidence rename detected**
        - Review the signals in the expander
        - If it's not a rename, leave `*_id` column empty
        - If it IS a rename, keep the UUID from previous download
        
        **Q: Can't delete category - has events**
        - Categories with events cannot be deleted
        - Reassign events to another category first
        - Or delete events via Supabase dashboard
        
        **Q: Template shows more changes than expected**
        - Download current structure first
        - Make small incremental changes
        - Test with renames first, then additions/deletions
        """)
    
    with st.expander("🔒 Security & Privacy"):
        st.markdown("""
        ### Row Level Security (RLS)
        
        - ✅ All your data is private
        - ✅ Only you can see/modify your data
        - ✅ Other users cannot access your structure
        - ✅ Enforced at PostgreSQL level
        
        ### Audit Trail
        
        - All name changes are logged
        - Check `name_change_history` table in Supabase
        - See who changed what and when
        """)


if __name__ == "__main__":
    main()
