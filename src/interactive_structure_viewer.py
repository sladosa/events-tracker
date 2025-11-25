"""
Events Tracker - Interactive Structure Viewer Module
====================================================
Created: 2025-11-25 10:00 UTC
Last Modified: 2025-11-25 10:00 UTC
Python: 3.11

Description:
Interactive Excel-like table for direct structure editing without Excel files.
Uses st.data_editor with live database connection, validation, and batch save.

Features:
- Excel-like table matching Hierarchical_View export format
- Color-coded columns (Pink=auto-calc, Blue=editable)
- Read-Only and Edit modes with toggle
- Dropdown validations for Data_Type and Is_Required
- Search and filtering (Area, Category_Path)
- Live validation before save
- Batch save with ONE confirmation (type 'SAVE')
- Rollback/discard changes option

Dependencies: streamlit, pandas, supabase

Technical Details:
- Layout matches Download Structure - Hierarchical_View format
- Direct database connectivity (no Excel intermediary)
- Reduces editing time from 5 minutes to ~30 seconds
- Validates changes before committing to database
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import json
from datetime import datetime


# ============================================
# CONSTANTS
# ============================================

# Data type options for dropdown
DATA_TYPES = ['number', 'text', 'datetime', 'boolean', 'link', 'image']

# Is_Required options for dropdown
IS_REQUIRED_OPTIONS = ['Yes', 'No', '']

# Column definitions with editability flag
COLUMN_CONFIG = [
    ('Type', False, 'text'),           # Auto-calculated
    ('Level', False, 'number'),        # Auto-calculated
    ('Sort_Order', False, 'number'),   # Auto-calculated
    ('Area', False, 'text'),           # Auto-calculated
    ('Category_Path', False, 'text'),  # Auto-calculated (but can be edited to add new rows)
    ('Category', True, 'text'),        # Editable
    ('Attribute_Name', True, 'text'),  # Editable
    ('Data_Type', True, 'select'),     # Editable with dropdown
    ('Unit', True, 'text'),            # Editable
    ('Is_Required', True, 'select'),   # Editable with dropdown
    ('Default_Value', True, 'text'),   # Editable
    ('Validation_Min', True, 'text'),  # Editable
    ('Validation_Max', True, 'text'),  # Editable
    ('Description', True, 'text')      # Editable
]


# ============================================
# DATA LOADING
# ============================================

def load_structure_as_dataframe(client, user_id: str) -> pd.DataFrame:
    """
    Load structure from database in Hierarchical_View format.
    
    Args:
        client: Supabase client instance
        user_id: Current user's UUID
    
    Returns:
        DataFrame with columns matching Hierarchical_View export
    """
    rows = []
    
    try:
        # Load Areas
        areas_response = client.table('areas') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('sort_order') \
            .execute()
        
        areas = areas_response.data
        
        for area in areas:
            # Add Area row
            rows.append({
                'Type': 'Area',
                'Level': 0,
                'Sort_Order': area['sort_order'],
                'Area': area['name'],
                'Category_Path': area['name'],
                'Category': '',
                'Attribute_Name': '',
                'Data_Type': '',
                'Unit': '',
                'Is_Required': '',
                'Default_Value': '',
                'Validation_Min': '',
                'Validation_Max': '',
                'Description': area.get('description', ''),
                '_area_id': area['id'],  # Hidden metadata
                '_category_id': None,
                '_attribute_id': None
            })
            
            # Load Categories for this Area
            _load_categories_recursive(
                client, user_id, area['id'], area['name'], rows
            )
        
        return pd.DataFrame(rows)
    
    except Exception as e:
        st.error(f"❌ Error loading structure: {str(e)}")
        return pd.DataFrame()


def _load_categories_recursive(
    client, 
    user_id: str,
    area_id: str, 
    area_name: str,
    rows: List[Dict],
    parent_id: Optional[str] = None,
    parent_path: str = '',
    level: int = 1
):
    """
    Recursively load categories and their attributes.
    
    Args:
        client: Supabase client
        user_id: User UUID
        area_id: Area UUID
        area_name: Area name for building paths
        rows: List to append rows to
        parent_id: Parent category UUID (None for top-level)
        parent_path: Parent's full path
        level: Current hierarchy level
    """
    # Query categories at this level
    query = client.table('categories') \
        .select('*') \
        .eq('user_id', user_id) \
        .eq('area_id', area_id) \
        .eq('level', level)
    
    if parent_id:
        query = query.eq('parent_category_id', parent_id)
    else:
        query = query.is_('parent_category_id', 'null')
    
    categories_response = query.order('sort_order').execute()
    categories = categories_response.data
    
    for category in categories:
        # Build category path
        if parent_path:
            cat_path = f"{parent_path} > {category['name']}"
        else:
            cat_path = f"{area_name} > {category['name']}"
        
        # Add Category row
        rows.append({
            'Type': 'Category',
            'Level': level,
            'Sort_Order': category['sort_order'],
            'Area': area_name,
            'Category_Path': cat_path,
            'Category': category['name'],
            'Attribute_Name': '',
            'Data_Type': '',
            'Unit': '',
            'Is_Required': '',
            'Default_Value': '',
            'Validation_Min': '',
            'Validation_Max': '',
            'Description': category.get('description', ''),
            '_area_id': area_id,
            '_category_id': category['id'],
            '_attribute_id': None
        })
        
        # Load Attributes for this Category
        attributes_response = client.table('attribute_definitions') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('category_id', category['id']) \
            .order('sort_order') \
            .execute()
        
        attributes = attributes_response.data
        
        for attr in attributes:
            # Parse validation_rules JSONB
            val_rules = attr.get('validation_rules', {})
            if isinstance(val_rules, str):
                try:
                    val_rules = json.loads(val_rules)
                except:
                    val_rules = {}
            
            val_min = str(val_rules.get('min', '')) if val_rules and 'min' in val_rules else ''
            val_max = str(val_rules.get('max', '')) if val_rules and 'max' in val_rules else ''
            
            # Convert is_required to Yes/No
            is_required = 'Yes' if attr.get('is_required', False) else 'No'
            
            # Add Attribute row
            rows.append({
                'Type': 'Attribute',
                'Level': level + 1,
                'Sort_Order': attr['sort_order'],
                'Area': area_name,
                'Category_Path': cat_path,
                'Category': category['name'],
                'Attribute_Name': attr['name'],
                'Data_Type': attr['data_type'],
                'Unit': attr.get('unit', ''),
                'Is_Required': is_required,
                'Default_Value': attr.get('default_value', ''),
                'Validation_Min': val_min,
                'Validation_Max': val_max,
                'Description': attr.get('description', ''),
                '_area_id': area_id,
                '_category_id': category['id'],
                '_attribute_id': attr['id']
            })
        
        # Recursively load child categories
        _load_categories_recursive(
            client, user_id, area_id, area_name, rows,
            parent_id=category['id'],
            parent_path=cat_path,
            level=level + 1
        )


# ============================================
# FILTERING
# ============================================

def apply_filters(
    df: pd.DataFrame,
    selected_area: str,
    search_term: str
) -> pd.DataFrame:
    """
    Apply filters to dataframe.
    
    Args:
        df: Original dataframe
        selected_area: Selected area name or "All Areas"
        search_term: Search term for Category_Path
    
    Returns:
        Filtered dataframe
    """
    filtered = df.copy()
    
    # Filter by Area
    if selected_area != "All Areas":
        filtered = filtered[filtered['Area'] == selected_area]
    
    # Filter by search term in Category_Path
    if search_term:
        filtered = filtered[
            filtered['Category_Path'].str.contains(search_term, case=False, na=False)
        ]
    
    return filtered


# ============================================
# VALIDATION
# ============================================

def validate_changes(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate changes before saving to database.
    
    Args:
        df: DataFrame with potentially edited data
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    
    for idx, row in df.iterrows():
        row_num = idx + 1  # For error messages (1-indexed)
        
        # Validate Category rows
        if row['Type'] == 'Category':
            if not row['Category'] or pd.isna(row['Category']):
                errors.append(f"Row {row_num}: Category name is required")
        
        # Validate Attribute rows
        elif row['Type'] == 'Attribute':
            if not row['Attribute_Name'] or pd.isna(row['Attribute_Name']):
                errors.append(f"Row {row_num}: Attribute name is required")
            
            if not row['Data_Type'] or pd.isna(row['Data_Type']):
                errors.append(f"Row {row_num}: Data type is required")
            elif row['Data_Type'] not in DATA_TYPES:
                errors.append(f"Row {row_num}: Invalid data type '{row['Data_Type']}'")
            
            # Validate Is_Required
            if row['Is_Required'] and row['Is_Required'] not in ['Yes', 'No', '']:
                errors.append(f"Row {row_num}: Is_Required must be 'Yes', 'No', or empty")
            
            # Validate min/max for number type
            if row['Data_Type'] == 'number':
                if row['Validation_Min']:
                    try:
                        float(row['Validation_Min'])
                    except ValueError:
                        errors.append(f"Row {row_num}: Validation_Min must be a number")
                
                if row['Validation_Max']:
                    try:
                        float(row['Validation_Max'])
                    except ValueError:
                        errors.append(f"Row {row_num}: Validation_Max must be a number")
                
                # Check min <= max
                if row['Validation_Min'] and row['Validation_Max']:
                    try:
                        min_val = float(row['Validation_Min'])
                        max_val = float(row['Validation_Max'])
                        if min_val > max_val:
                            errors.append(f"Row {row_num}: Validation_Min must be <= Validation_Max")
                    except ValueError:
                        pass  # Already reported above
    
    return (len(errors) == 0, errors)


# ============================================
# DATABASE UPDATES
# ============================================

def save_changes_to_database(
    client,
    user_id: str,
    original_df: pd.DataFrame,
    edited_df: pd.DataFrame
) -> Tuple[bool, str, Dict[str, int]]:
    """
    Save edited changes back to database.
    Only updates rows that were actually changed.
    
    Args:
        client: Supabase client
        user_id: User UUID
        original_df: Original dataframe before editing
        edited_df: Edited dataframe
    
    Returns:
        Tuple of (success: bool, message: str, stats: Dict[str, int])
    """
    stats = {'categories': 0, 'attributes': 0}
    
    try:
        # Compare dataframes to find changes
        for idx in edited_df.index:
            if idx not in original_df.index:
                continue  # Skip new rows (not supported in this version)
            
            orig_row = original_df.loc[idx]
            edit_row = edited_df.loc[idx]
            
            # Check if row was modified
            editable_cols = ['Category', 'Attribute_Name', 'Data_Type', 'Unit', 
                           'Is_Required', 'Default_Value', 'Validation_Min', 
                           'Validation_Max', 'Description']
            
            is_modified = False
            for col in editable_cols:
                if str(orig_row[col]) != str(edit_row[col]):
                    is_modified = True
                    break
            
            if not is_modified:
                continue
            
            # Update Category
            if edit_row['Type'] == 'Category' and edit_row['_category_id']:
                update_data = {
                    'name': edit_row['Category'],
                    'description': edit_row['Description'] if edit_row['Description'] else None
                }
                
                client.table('categories') \
                    .update(update_data) \
                    .eq('id', edit_row['_category_id']) \
                    .eq('user_id', user_id) \
                    .execute()
                
                stats['categories'] += 1
            
            # Update Attribute
            elif edit_row['Type'] == 'Attribute' and edit_row['_attribute_id']:
                # Build validation_rules JSONB
                val_rules = {}
                if edit_row['Validation_Min']:
                    try:
                        val_rules['min'] = float(edit_row['Validation_Min'])
                    except ValueError:
                        val_rules['min'] = edit_row['Validation_Min']
                
                if edit_row['Validation_Max']:
                    try:
                        val_rules['max'] = float(edit_row['Validation_Max'])
                    except ValueError:
                        val_rules['max'] = edit_row['Validation_Max']
                
                # Convert Is_Required to boolean
                is_required = edit_row['Is_Required'] == 'Yes' if edit_row['Is_Required'] else False
                
                update_data = {
                    'name': edit_row['Attribute_Name'],
                    'data_type': edit_row['Data_Type'],
                    'unit': edit_row['Unit'] if edit_row['Unit'] else None,
                    'is_required': is_required,
                    'default_value': edit_row['Default_Value'] if edit_row['Default_Value'] else None,
                    'validation_rules': val_rules,
                    'description': edit_row['Description'] if edit_row['Description'] else None
                }
                
                client.table('attribute_definitions') \
                    .update(update_data) \
                    .eq('id', edit_row['_attribute_id']) \
                    .eq('user_id', user_id) \
                    .execute()
                
                stats['attributes'] += 1
        
        total_updates = stats['categories'] + stats['attributes']
        
        if total_updates == 0:
            return True, "No changes detected", stats
        else:
            return True, f"Successfully updated {total_updates} items", stats
    
    except Exception as e:
        return False, f"Error saving changes: {str(e)}", stats


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render_interactive_structure_viewer(client, user_id: str):
    """
    Main function to render the interactive structure viewer.
    
    Args:
        client: Supabase client instance
        user_id: Current user's UUID
    """
    st.title("📋 Interactive Structure Viewer")
    
    st.info("""
    **Excel-like editing interface** - Direct database connectivity
    - 🎨 **Color-coded columns**: Pink (auto-calculated) vs Blue (editable)
    - ✏️ **Direct editing**: No Excel download/upload needed
    - ✅ **Live validation**: Checks before saving
    - 💾 **Batch save**: Save all changes at once with confirmation
    - ⏪ **Rollback**: Discard changes without saving
    """)
    
    st.markdown("---")
    
    # Initialize session state
    if 'viewer_mode' not in st.session_state:
        st.session_state.viewer_mode = 'read_only'
    
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None
    
    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = None
    
    # Load data
    with st.spinner("Loading structure..."):
        df = load_structure_as_dataframe(client, user_id)
    
    if df.empty:
        st.warning("⚠️ No structure defined yet. Please upload a template first.")
        return
    
    # Store original dataframe
    if st.session_state.original_df is None:
        st.session_state.original_df = df.copy()
    
    # ============================================
    # CONTROLS
    # ============================================
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Mode toggle
        mode_options = ['Read-Only', 'Edit Mode']
        current_mode_idx = 0 if st.session_state.viewer_mode == 'read_only' else 1
        
        new_mode = st.radio(
            "Mode",
            mode_options,
            index=current_mode_idx,
            horizontal=True
        )
        
        # Update session state
        st.session_state.viewer_mode = 'read_only' if new_mode == 'Read-Only' else 'edit'
    
    with col2:
        # Filters
        area_options = ["All Areas"] + sorted(df[df['Type'] == 'Area']['Area'].unique().tolist())
        selected_area = st.selectbox("Filter by Area", area_options)
    
    with col3:
        # Refresh button
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.original_df = None
            st.session_state.edited_df = None
            st.rerun()
    
    # Search
    search_term = st.text_input("🔎 Search in Category Path", "")
    
    st.markdown("---")
    
    # Apply filters
    filtered_df = apply_filters(df, selected_area, search_term)
    
    # Remove metadata columns for display
    display_cols = [col for col in filtered_df.columns if not col.startswith('_')]
    display_df = filtered_df[display_cols].copy()
    
    # ============================================
    # DATA EDITOR
    # ============================================
    
    if st.session_state.viewer_mode == 'read_only':
        # Read-only mode - display as table
        st.markdown("### 📊 Structure (Read-Only)")
        st.markdown("_Switch to Edit Mode to make changes_")
        
        # Style the dataframe
        styled_df = display_df.style.apply(
            lambda x: [
                'background-color: #FFE6F0' if col in ['Type', 'Level', 'Sort_Order', 'Area', 'Category_Path']
                else 'background-color: #E6F2FF'
                for col in display_df.columns
            ],
            axis=1
        )
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=600
        )
    
    else:
        # Edit mode - use data_editor
        st.markdown("### ✏️ Structure (Edit Mode)")
        st.markdown("_Edit BLUE columns only. PINK columns are auto-calculated._")
        
        # Configure column properties
        column_config = {}
        
        for col_name, is_editable, col_type in COLUMN_CONFIG:
            if col_name not in display_df.columns:
                continue
            
            if col_type == 'select':
                if col_name == 'Data_Type':
                    column_config[col_name] = st.column_config.SelectboxColumn(
                        col_name,
                        options=DATA_TYPES,
                        required=True,
                        disabled=not is_editable
                    )
                elif col_name == 'Is_Required':
                    column_config[col_name] = st.column_config.SelectboxColumn(
                        col_name,
                        options=IS_REQUIRED_OPTIONS,
                        disabled=not is_editable
                    )
            elif col_type == 'number':
                column_config[col_name] = st.column_config.NumberColumn(
                    col_name,
                    disabled=not is_editable
                )
            else:  # text
                column_config[col_name] = st.column_config.TextColumn(
                    col_name,
                    disabled=not is_editable
                )
        
        # Render data editor
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            height=600,
            column_config=column_config,
            hide_index=True,
            num_rows="fixed"  # Don't allow adding/deleting rows in this version
        )
        
        # Store edited dataframe
        st.session_state.edited_df = edited_df
        
        # ============================================
        # SAVE CONTROLS
        # ============================================
        
        st.markdown("---")
        st.markdown("### 💾 Save Changes")
        
        # Check if there are changes
        has_changes = False
        if st.session_state.original_df is not None:
            # Compare display columns only
            orig_display = st.session_state.original_df[display_cols]
            has_changes = not orig_display.equals(edited_df)
        
        if not has_changes:
            st.info("ℹ️ No changes detected")
        else:
            st.warning("⚠️ **You have unsaved changes**")
            
            # Validate changes
            is_valid, errors = validate_changes(edited_df)
            
            if not is_valid:
                st.error("❌ **Validation Errors:**")
                for error in errors:
                    st.error(f"  • {error}")
            else:
                st.success("✅ All changes are valid")
            
            # Save controls
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                confirmation_text = st.text_input(
                    "Type 'SAVE' to confirm batch save",
                    key="save_confirmation"
                )
            
            with col2:
                if st.button("💾 Save Changes", disabled=not is_valid, use_container_width=True):
                    if confirmation_text == "SAVE":
                        with st.spinner("Saving changes..."):
                            # Merge edited data back with metadata
                            full_edited_df = filtered_df.copy()
                            full_edited_df[display_cols] = edited_df
                            
                            success, message, stats = save_changes_to_database(
                                client,
                                user_id,
                                st.session_state.original_df,
                                full_edited_df
                            )
                            
                            if success:
                                st.success(f"✅ {message}")
                                if stats['categories'] > 0 or stats['attributes'] > 0:
                                    st.info(
                                        f"Updated: {stats['categories']} categories, "
                                        f"{stats['attributes']} attributes"
                                    )
                                
                                # Reset session state
                                st.session_state.original_df = None
                                st.session_state.edited_df = None
                                
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    else:
                        st.error("❌ Please type 'SAVE' to confirm")
            
            with col3:
                if st.button("⏪ Discard Changes", use_container_width=True):
                    st.session_state.original_df = None
                    st.session_state.edited_df = None
                    st.rerun()
    
    # ============================================
    # STATISTICS
    # ============================================
    
    st.markdown("---")
    st.markdown("### 📊 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        area_count = len(df[df['Type'] == 'Area'])
        st.metric("Areas", area_count)
    
    with col2:
        category_count = len(df[df['Type'] == 'Category'])
        st.metric("Categories", category_count)
    
    with col3:
        attribute_count = len(df[df['Type'] == 'Attribute'])
        st.metric("Attributes", attribute_count)
    
    with col4:
        if not df.empty:
            max_level = int(df['Level'].max())
            st.metric("Max Depth", max_level)
        else:
            st.metric("Max Depth", 0)


# ============================================
# MODULE TEST
# ============================================

if __name__ == "__main__":
    st.write("⚠️ This module should be imported, not run directly.")
    st.write("Use: `from src.interactive_structure_viewer import render_interactive_structure_viewer`")
