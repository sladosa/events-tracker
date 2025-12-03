"""
Events Tracker - Interactive Structure Viewer Module
====================================================
Created: 2025-11-25 10:00 UTC
Last Modified: 2025-12-03 11:15 UTC
Python: 3.11
Version: 1.7.0 - Filtered Excel Export

Description:
Interactive Excel-like table for direct structure editing without Excel files.
Uses st.data_editor with live database connection, validation, and batch save.
Integrated Excel export/import workflow for offline structure editing.

Features:
- **INTEGRATED HELP**: Collapsible help section at page top with comprehensive guide
- **EXCEL EXPORT**: Generate Enhanced Excel in Read-Only mode (respects active filters)
- **EXCEL IMPORT**: Upload Hierarchical Excel in Edit Mode (new 4th tab)
- **THREE SEPARATE EDITORS**: Areas, Categories, and Attributes in tabs
- **FILTERS**: Area filter in Tab 2, Area + Category cascade filter in Tab 3
- **ADD**: Add new Areas, Categories, and Attributes
- **DELETE**: Delete Areas, Categories, and Attributes with cascade warnings
- **SMART FORMS**: Two-step form - select Data Type first, then relevant fields appear
- Each editor shows only relevant columns for that entity type
- Read-Only mode: Shows ALL rows + Excel Export button (respects filters)
- Edit Mode: 4 tabs - Areas, Categories, Attributes, Upload Excel
- Dropdown validations for Data_Type and Is_Required
- Search and filtering (Area, Category_Path)
- Live validation before save
- Batch save with ONE confirmation (type 'SAVE')
- Rollback/discard changes option
- OPTIMIZED: Batch data loading with caching (60s TTL)
- IMPROVED: Unsaved changes warnings on filter/refresh

Dependencies: streamlit, pandas, supabase, enhanced_structure_exporter, hierarchical_parser, error_reporter

Technical Details:
- Layout matches Download Structure - Hierarchical_View format
- Direct database connectivity (no Excel intermediary for editing)
- Integrated Excel export/import for offline work
- Reduces editing time: ~30 seconds (direct edit) or full Excel workflow
- Validates changes before committing to database
- Uses @st.cache_data for 10x faster loading
- Tab-based interface for clarity and simplicity
- UUID generation for new entities
- Slug auto-generation from names
- CASCADE delete warnings
- Dynamic form generation based on Data Type

CHANGELOG v1.7.0 (Filtered Excel Export):
- ✨ NEW: Generate Excel respects active filters (Area + Search)
- 🎯 FEATURE: Export filtered structure for sharing specific Area themes
- 📦 USE CASE: Create starter templates for new users by exporting single Areas
- 🔧 IMPROVED: Success message shows which filters were applied
- 📝 TECHNICAL: EnhancedStructureExporter now accepts filter_area and filter_search params

CHANGELOG v1.6.1 (Production Release):
- 🗑️ REMOVED: Refresh button from Edit Mode (user feedback - not needed)
- 🎯 CLEAN: Edit Mode col3 now empty (intentional - refresh via browser or navigation)
- 📝 NOTE: Read-Only mode keeps Generate Excel button (primary action)

CHANGELOG v1.6.0:
- ✨ NEW: Collapsible Help section at page top with comprehensive guide
- ✨ NEW: Generate Enhanced Excel button in Read-Only mode (replaces Refresh)
- ✨ NEW: Upload Hierarchical Excel tab in Edit Mode (4th tab)
- 🔧 IMPROVED: Complete Excel workflow integrated into single page
- 🔧 IMPROVED: Better UX with contextual buttons (Excel export only in Read-Only)
- 📚 DOCUMENTATION: Detailed help for both direct editing and Excel workflows
- 🎯 GOAL: Single hub for all structure management operations
- ⚡ IMPORTS: Added enhanced_structure_exporter, hierarchical_parser, error_reporter

CHANGELOG v1.5.9:
- ✅ MAJOR FIX: Two-step form approach - select Data Type OUTSIDE form first
- 🎯 SOLUTION: Data Type selector triggers form re-render with relevant fields
- ✨ NEW UX: Step 1: Select Data Type → Step 2: Fill relevant fields
- 🔧 FIXED: Fields now actually hide/show when Data Type changes (user feedback!)
- 💡 IMPROVED: Helper text shows which fields are hidden and why
- Field visibility rules (unchanged):
  - Unit: ONLY 'number' type
  - Default Value: All EXCEPT 'link' and 'image'
  - Validation Min/Max: ONLY 'number' and 'datetime'
- Technical: Data Type selectbox outside st.form() allows dynamic field rendering

CHANGELOG v1.5.8:
- 🐛 FIXED: Reverted to show/hide approach instead of disabled fields
- 🔧 IMPROVED: Unit field now shows ONLY for 'number' type (user feedback)
- 🔧 IMPROVED: Default Value hidden for 'link' and 'image' types
- 🔧 IMPROVED: Validation Min/Max show only for 'number' and 'datetime' types
- 💡 IMPROVED: Helper caption shows which fields are hidden and why
- Field visibility rules:
  - Unit: ONLY 'number' type
  - Default Value: All EXCEPT 'link' and 'image'
  - Validation Min/Max: ONLY 'number' and 'datetime'
- ⚠️ NOTE: Table editing still allows all columns - validation needed (future fix)

CHANGELOG v1.5.7:
- 🐛 FIXED: Smart field masking now works correctly - uses DISABLED fields instead of hiding
- 🔧 IMPROVED: Non-applicable fields shown as disabled (greyed out) with help text
- 🔧 IMPROVED: Added caption explaining disabled field behavior
- ✅ VERIFIED: Disabled fields don't allow input and pass empty values to database
- Field behavior by Data Type:
  - 'link' & 'image': Unit, Default Value, Validation Min/Max → DISABLED
  - 'text' & 'boolean': Validation Min/Max → DISABLED
  - 'number' & 'datetime': All fields → ENABLED

CHANGELOG v1.5.6:
- 🐛 FIXED: Add Attribute form now always visible, even when no attributes exist (Bug #11 - CRITICAL)
- 🐛 FIXED: Filter by Area in Edit Attributes now queries database directly (Bug #12)
- ✨ NEW FEATURE: Smart field masking based on Data Type
  - 'link' and 'image' types: Hide Unit, Default Value, Validation fields
  - 'text' and 'boolean' types: Hide Validation Min/Max
  - 'number' and 'datetime' types: Show all fields
- 🔧 IMPROVED: Better UX with info messages for hidden fields
- 🔧 IMPROVED: Consistent behavior across all tabs (forms always accessible)

CHANGELOG v1.5.5:
- 🐛 FIXED: Add Category form now always visible, even when no categories exist (Bug #8)
- 🐛 FIXED: Filter by Category in Edit Attributes shows ALL categories from filtered Area (Bug #9)
- ✅ VERIFIED: Add Attribute respects filters correctly (Bug #10 was already fixed in v1.5.4)
- 🔧 IMPROVED: Better info messages when no categories/attributes found
- 🔧 IMPROVED: Add Category accessible even with empty filtered areas

CHANGELOG v1.5.4:
- 🐛 FIXED: Filter by Area dropdown in Edit Categories now queries database directly (Bug #6)
- 🐛 FIXED: Add Attribute form respects Area and Category filters (Bug #7)
- 🔧 IMPROVED: Add Attribute shows filter context with info box
- 🔧 IMPROVED: Category selection locked when single option available

CHANGELOG v1.5.3:
- 🐛 CRITICAL FIX: Form double submit prevention with unique keys
- 🐛 FIXED: Add Area form now uses unique key per submit (Bug #3)
- 🐛 FIXED: Add Category form now uses unique key per submit (Bug #4 - prevents duplicate inserts)
- 🐛 FIXED: Add Attribute form now uses unique key per submit
- 🐛 FIXED: Form fields clear properly after successful add (Bug #5)
- 🔧 IMPROVED: Form counter in session state increments after success
- 🔧 IMPROVED: Each form gets fresh state after rerun
- ✨ NEW: Form submission counters (area_form_counter, category_form_counter, attribute_form_counter)
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import json
from datetime import datetime
import uuid
import re
import os
import tempfile

# Import Excel handling modules
from .enhanced_structure_exporter import EnhancedStructureExporter
from .hierarchical_parser import HierarchicalParser
from .error_reporter import generate_error_excel


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
# HELPER FUNCTIONS
# ============================================

def generate_slug(name: str) -> str:
    """
    Generate URL-friendly slug from name.
    
    Args:
        name: Original name
    
    Returns:
        Slugified name (lowercase, no spaces, no special chars)
    """
    # Convert to lowercase
    slug = name.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove special characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


def get_next_sort_order(client, table: str, user_id: str, parent_field: Optional[str] = None, parent_id: Optional[str] = None) -> int:
    """
    Get next sort_order value for a table.
    
    Args:
        client: Supabase client
        table: Table name ('areas', 'categories', 'attribute_definitions')
        user_id: Current user's UUID
        parent_field: Optional parent field name ('area_id', 'category_id')
        parent_id: Optional parent ID
    
    Returns:
        Next sort_order value (max + 1)
    """
    try:
        query = client.table(table).select('sort_order').eq('user_id', user_id)
        
        # Add parent filter if specified
        if parent_field and parent_id:
            query = query.eq(parent_field, parent_id)
        
        result = query.execute()
        
        if result.data:
            max_sort = max([row['sort_order'] for row in result.data])
            return max_sort + 1
        else:
            return 1
    
    except Exception as e:
        st.error(f"Error getting next sort_order: {str(e)}")
        return 1


def check_area_has_dependencies(client, area_id: str, user_id: str) -> Tuple[bool, str]:
    """
    Check if area has categories or events.
    
    Args:
        client: Supabase client
        area_id: Area UUID
        user_id: User UUID
    
    Returns:
        Tuple of (has_dependencies, warning_message)
    """
    try:
        # Check categories
        cat_result = client.table('categories').select('id').eq('area_id', area_id).eq('user_id', user_id).execute()
        num_categories = len(cat_result.data) if cat_result.data else 0
        
        # Check events (through categories)
        if num_categories > 0:
            cat_ids = [c['id'] for c in cat_result.data]
            event_result = client.table('events').select('id').in_('category_id', cat_ids).eq('user_id', user_id).execute()
            num_events = len(event_result.data) if event_result.data else 0
        else:
            num_events = 0
        
        if num_categories > 0 or num_events > 0:
            msg = f"⚠️ **WARNING:** This area has {num_categories} categories"
            if num_events > 0:
                msg += f" and {num_events} events"
            msg += ". Deleting it will CASCADE DELETE all of them!"
            return True, msg
        
        return False, ""
    
    except Exception as e:
        return False, f"Error checking dependencies: {str(e)}"


def check_category_has_dependencies(client, category_id: str, user_id: str) -> Tuple[bool, str]:
    """
    Check if category has attributes or events.
    
    Args:
        client: Supabase client
        category_id: Category UUID
        user_id: User UUID
    
    Returns:
        Tuple of (has_dependencies, warning_message)
    """
    try:
        # Check attributes
        attr_result = client.table('attribute_definitions').select('id').eq('category_id', category_id).eq('user_id', user_id).execute()
        num_attributes = len(attr_result.data) if attr_result.data else 0
        
        # Check events
        event_result = client.table('events').select('id').eq('category_id', category_id).eq('user_id', user_id).execute()
        num_events = len(event_result.data) if event_result.data else 0
        
        # Check child categories
        child_result = client.table('categories').select('id').eq('parent_category_id', category_id).eq('user_id', user_id).execute()
        num_children = len(child_result.data) if child_result.data else 0
        
        if num_attributes > 0 or num_events > 0 or num_children > 0:
            msg = f"⚠️ **WARNING:** This category has"
            parts = []
            if num_children > 0:
                parts.append(f"{num_children} child categories")
            if num_attributes > 0:
                parts.append(f"{num_attributes} attributes")
            if num_events > 0:
                parts.append(f"{num_events} events")
            msg += " " + ", ".join(parts) + ". Deleting it will CASCADE DELETE all of them!"
            return True, msg
        
        return False, ""
    
    except Exception as e:
        return False, f"Error checking dependencies: {str(e)}"


# ============================================
# CACHED DATA LOADING
# ============================================

@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_all_structure_data(_client, user_id: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Load ALL structure data from database at once (optimized batch loading).
    
    Args:
        _client: Supabase client (underscore prefix to avoid hashing)
        user_id: Current user's UUID
    
    Returns:
        Tuple of (areas, categories, attributes) as lists of dicts
    """
    try:
        # Load ALL areas at once
        areas_response = _client.table('areas') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('sort_order') \
            .execute()
        
        areas = areas_response.data if areas_response.data else []
        
        if not areas:
            return [], [], []
        
        # Load ALL categories at once
        categories_response = _client.table('categories') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('sort_order') \
            .execute()
        
        categories = categories_response.data if categories_response.data else []
        
        # Load ALL attributes at once
        attributes_response = _client.table('attribute_definitions') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('sort_order') \
            .execute()
        
        attributes = attributes_response.data if attributes_response.data else []
        
        return areas, categories, attributes
    
    except Exception as e:
        st.error(f"❌ Error loading structure data: {str(e)}")
        return [], [], []


# ============================================
# DATA TRANSFORMATION
# ============================================

def load_structure_as_dataframe(client, user_id: str) -> pd.DataFrame:
    """
    Load structure from database and convert to hierarchical DataFrame.
    Uses cached batch loading for 10x performance improvement.
    
    Args:
        client: Supabase client instance
        user_id: Current user's UUID
    
    Returns:
        DataFrame with hierarchical structure including metadata columns (_area_id, _category_id, _attribute_id)
    """
    try:
        # Load ALL data at once (cached)
        areas, categories, attributes = load_all_structure_data(client, user_id)
        
        if not areas:
            st.warning("⚠️ No areas found. Please upload a template first.")
            return pd.DataFrame()
        
        # Build lookup maps for O(1) access
        categories_by_area = {}
        categories_by_parent = {}
        categories_by_id = {}
        attributes_by_category = {}
        
        # Map categories by area_id
        for cat in categories:
            area_id = cat['area_id']
            if area_id not in categories_by_area:
                categories_by_area[area_id] = []
            categories_by_area[area_id].append(cat)
            
            # Map categories by parent_id
            parent_id = cat.get('parent_category_id')
            if parent_id:
                if parent_id not in categories_by_parent:
                    categories_by_parent[parent_id] = []
                categories_by_parent[parent_id].append(cat)
            
            # Map categories by id
            categories_by_id[cat['id']] = cat
        
        # Map attributes by category_id
        for attr in attributes:
            cat_id = attr['category_id']
            if cat_id not in attributes_by_category:
                attributes_by_category[cat_id] = []
            attributes_by_category[cat_id].append(attr)
        
        # Build hierarchical structure
        rows = []
        
        for area in areas:
            area_id = area['id']
            area_name = area['name']
            
            # Add Area row
            rows.append({
                'Type': 'Area',
                'Level': 0,
                'Sort_Order': area['sort_order'],
                'Area': area_name,
                'Category_Path': area_name,
                'Category': '',
                'Attribute_Name': '',
                'Data_Type': '',
                'Unit': '',
                'Is_Required': '',
                'Default_Value': '',
                'Validation_Min': '',
                'Validation_Max': '',
                'Description': area.get('description', ''),
                '_area_id': area_id,
                '_category_id': None,
                '_attribute_id': None
            })
            
            # Process categories for this area
            area_categories = categories_by_area.get(area_id, [])
            root_categories = [c for c in area_categories if not c.get('parent_category_id')]
            
            # Sort root categories by sort_order
            root_categories.sort(key=lambda x: x['sort_order'])
            
            # Process each root category tree
            for root_cat in root_categories:
                _add_category_tree(
                    root_cat, 
                    area_name, 
                    area_name, 
                    rows,
                    categories_by_parent,
                    attributes_by_category,
                    categories_by_id
                )
        
        return pd.DataFrame(rows)
    
    except Exception as e:
        st.error(f"❌ Error loading structure: {str(e)}")
        return pd.DataFrame()


def _add_category_tree(
    category: Dict,
    area_name: str,
    parent_path: str,
    rows: List[Dict],
    categories_by_parent: Dict,
    attributes_by_category: Dict,
    categories_by_id: Dict
):
    """
    Recursively add category and its tree to rows list.
    All data is already loaded in memory - no DB queries!
    
    Args:
        category: Category dict
        area_name: Area name
        parent_path: Parent's category path
        rows: List to append rows to
        categories_by_parent: Map of parent_id -> list of child categories
        attributes_by_category: Map of category_id -> list of attributes
        categories_by_id: Map of category_id -> category dict
    """
    cat_id = category['id']
    cat_name = category['name']
    cat_level = category['level']
    
    # Build category path
    cat_path = f"{parent_path} > {cat_name}"
    
    # Add Category row
    rows.append({
        'Type': 'Category',
        'Level': cat_level,
        'Sort_Order': category['sort_order'],
        'Area': area_name,
        'Category_Path': cat_path,
        'Category': cat_name,
        'Attribute_Name': '',  
        'Data_Type': '',
        'Unit': '',
        'Is_Required': '',
        'Default_Value': '',
        'Validation_Min': '',
        'Validation_Max': '',
        'Description': category.get('description', ''),
        '_area_id': category['area_id'],
        '_category_id': cat_id,
        '_attribute_id': None
    })
    
    # Add attributes for this category
    attrs = attributes_by_category.get(cat_id, [])
    attrs.sort(key=lambda x: x['sort_order'])
    
    for attr in attrs:
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
            'Level': cat_level + 1,
            'Sort_Order': attr['sort_order'],
            'Area': area_name,
            'Category_Path': cat_path,
            'Category': cat_name,
            'Attribute_Name': attr['name'],
            'Data_Type': attr['data_type'],
            'Unit': attr.get('unit', ''),
            'Is_Required': is_required,
            'Default_Value': attr.get('default_value', ''),
            'Validation_Min': val_min,
            'Validation_Max': val_max,
            'Description': attr.get('description', ''),
            '_area_id': category['area_id'],
            '_category_id': cat_id,
            '_attribute_id': attr['id']
        })
    
    # Recursively add child categories
    child_categories = categories_by_parent.get(cat_id, [])
    child_categories.sort(key=lambda x: x['sort_order'])
    
    for child_cat in child_categories:
        _add_category_tree(
            child_cat,
            area_name,
            cat_path,
            rows,
            categories_by_parent,
            attributes_by_category,
            categories_by_id
        )


# ============================================
# FILTERING
# ============================================

def apply_filters(df: pd.DataFrame, selected_area: str, search_term: str) -> pd.DataFrame:
    """
    Apply Area and search filters to dataframe.
    
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
    Validate edited dataframe for common errors.
    
    Args:
        df: Edited dataframe
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    for idx, row in df.iterrows():
        row_type = row.get('Type', '')
        
        # Validate Category rows
        if row_type == 'Category':
            if not row.get('Category'):
                errors.append(f"Row {idx + 1}: Category name is required")
        
        # Validate Attribute rows
        elif row_type == 'Attribute':
            if not row.get('Attribute_Name'):
                errors.append(f"Row {idx + 1}: Attribute name is required")
            
            if not row.get('Data_Type'):
                errors.append(f"Row {idx + 1}: Data type is required")
            
            # Validate Data_Type values
            if row.get('Data_Type') and row.get('Data_Type') not in DATA_TYPES:
                errors.append(f"Row {idx + 1}: Invalid data type '{row.get('Data_Type')}'")
            
            # Validate Is_Required values
            if row.get('Is_Required') and row.get('Is_Required') not in IS_REQUIRED_OPTIONS:
                errors.append(f"Row {idx + 1}: Is_Required must be 'Yes', 'No', or empty")
    
    is_valid = len(errors) == 0
    return is_valid, errors


# ============================================
# SAVE TO DATABASE
# ============================================

def save_changes_to_database(
    client,
    user_id: str,
    original_df: pd.DataFrame,
    edited_df: pd.DataFrame
) -> Tuple[bool, str, Dict[str, int]]:
    """
    Save changes to database.
    Compares original_df and edited_df to identify changes.
    
    Args:
        client: Supabase client
        user_id: Current user's UUID
        original_df: Original dataframe with metadata columns
        edited_df: Edited dataframe (may not have all metadata columns)
    
    Returns:
        Tuple of (success, message, stats_dict)
    """
    stats = {
        'categories': 0,
        'attributes': 0,
        'errors': 0
    }
    errors = []
    
    try:
        # Iterate through rows and detect changes
        for idx, edit_row in edited_df.iterrows():
            try:
                # Find corresponding row in original_df
                orig_row = original_df.loc[idx]
                
                row_type = orig_row['Type']
                
                # Check if row has changed
                has_changed = False
                for col in edited_df.columns:
                    if col in original_df.columns:
                        if str(edit_row[col]) != str(orig_row[col]):
                            has_changed = True
                            break
                
                if not has_changed:
                    continue
                
                # CATEGORY UPDATE
                if row_type == 'Category':
                    cat_id = orig_row['_category_id']
                    if pd.notna(cat_id):
                        # Prepare update data
                        update_data = {
                            'name': edit_row['Category'],
                            'description': edit_row['Description'] if edit_row['Description'] else None
                        }
                        
                        client.table('categories') \
                            .update(update_data) \
                            .eq('id', cat_id) \
                            .eq('user_id', user_id) \
                            .execute()
                        
                        stats['categories'] += 1
                
                # ATTRIBUTE UPDATE
                elif row_type == 'Attribute':
                    attr_id = orig_row['_attribute_id']
                    if pd.notna(attr_id):
                        # Parse validation rules
                        val_rules = {}
                        if edit_row['Validation_Min']:
                            try:
                                val_rules['min'] = float(edit_row['Validation_Min'])
                            except:
                                val_rules['min'] = edit_row['Validation_Min']
                        
                        if edit_row['Validation_Max']:
                            try:
                                val_rules['max'] = float(edit_row['Validation_Max'])
                            except:
                                val_rules['max'] = edit_row['Validation_Max']
                        
                        # Convert Is_Required to boolean
                        is_required = edit_row['Is_Required'] == 'Yes'
                        
                        # Prepare update data
                        update_data = {
                            'name': edit_row['Attribute_Name'],
                            'data_type': edit_row['Data_Type'] if edit_row['Data_Type'] else 'text',
                            'unit': edit_row['Unit'] if edit_row['Unit'] else None,
                            'is_required': is_required,
                            'default_value': edit_row['Default_Value'] if edit_row['Default_Value'] else None,
                            'validation_rules': val_rules if val_rules else {},
                            'description': edit_row['Description'] if edit_row['Description'] else None
                        }
                        
                        client.table('attribute_definitions') \
                            .update(update_data) \
                            .eq('id', attr_id) \
                            .eq('user_id', user_id) \
                            .execute()
                        
                        stats['attributes'] += 1
            
            except Exception as e:
                stats['errors'] += 1
                errors.append(f"Row {idx + 1}: {str(e)}")
                # Continue processing other rows
        
        total_updates = stats['categories'] + stats['attributes']
        
        if stats['errors'] > 0:
            error_msg = f"Completed with {stats['errors']} errors. Check details below."
            return False, error_msg, stats
        elif total_updates == 0:
            return True, "No changes detected", stats
        else:
            return True, f"Successfully updated {total_updates} items", stats
    
    except Exception as e:
        return False, f"Error saving changes: {str(e)}", stats


def _save_category_changes(
    client,
    user_id: str,
    original_cat_df: pd.DataFrame,
    edited_cat_df: pd.DataFrame,
    full_df: pd.DataFrame
) -> Tuple[bool, Dict[str, int]]:
    """
    Save category changes to database.
    
    Args:
        client: Supabase client
        user_id: User ID
        original_cat_df: Original category dataframe (display columns only)
        edited_cat_df: Edited category dataframe (display columns only)
        full_df: Full dataframe with metadata columns (_category_id, etc.)
    
    Returns:
        Tuple of (success, stats_dict)
    """
    stats = {'categories': 0, 'errors': 0}
    
    try:
        # Find rows that have changed
        cat_cols = ['Category', 'Description']
        
        for idx, edited_row in edited_cat_df.iterrows():
            # Check if this row has changed
            orig_row = original_cat_df.loc[idx]
            has_changed = False
            
            for col in cat_cols:
                if col in edited_cat_df.columns and col in original_cat_df.columns:
                    if str(edited_row[col]) != str(orig_row[col]):
                        has_changed = True
                        break
            
            if not has_changed:
                continue
            
            # Get category_id from full_df (which has metadata)
            # Find matching row by index
            full_row = full_df.loc[idx]
            cat_id = full_row['_category_id']
            
            if pd.notna(cat_id):
                # Prepare update data
                update_data = {
                    'name': edited_row['Category'],
                    'description': edited_row['Description'] if edited_row['Description'] else None
                }
                
                client.table('categories') \
                    .update(update_data) \
                    .eq('id', cat_id) \
                    .eq('user_id', user_id) \
                    .execute()
                
                stats['categories'] += 1
        
        return True, stats
    
    except Exception as e:
        st.error(f"Error saving category changes: {str(e)}")
        stats['errors'] += 1
        return False, stats


# ============================================
# ADD FUNCTIONS
# ============================================

def add_new_area(client, user_id: str, name: str, description: str = "") -> Tuple[bool, str]:
    """
    Add new area to database.
    
    Args:
        client: Supabase client
        user_id: User ID
        name: Area name
        description: Area description
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Check if area with this name already exists (BEFORE generating UUID)
        existing = client.table('areas').select('id').eq('user_id', user_id).eq('name', name).execute()
        if existing.data and len(existing.data) > 0:
            return False, f"❌ Area '{name}' already exists! Please choose a different name or delete the existing area first."
        
        # Generate UUID and slug
        new_id = str(uuid.uuid4())
        slug = generate_slug(name)
        
        # Get next sort_order
        sort_order = get_next_sort_order(client, 'areas', user_id)
        
        # Prepare data
        area_data = {
            'id': new_id,
            'user_id': user_id,
            'name': name,
            'slug': slug,
            'sort_order': sort_order,
            'description': description if description else None,
            'icon': None,
            'color': None,
            'template_id': None
        }
        
        # Insert
        result = client.table('areas').insert(area_data).execute()
        
        # Verify insert was successful
        if result.data and len(result.data) > 0:
            return True, f"✅ Successfully added area: {name}"
        else:
            return False, f"❌ Failed to add area: {name}"
    
    except Exception as e:
        error_msg = str(e)
        # Handle duplicate key constraint
        if '23505' in error_msg or 'duplicate' in error_msg.lower():
            return False, f"❌ Area '{name}' already exists! Please choose a different name."
        # Handle unique constraint
        if 'unique constraint' in error_msg.lower():
            return False, f"❌ Area '{name}' already exists (unique constraint violation)."
        return False, f"❌ Error adding area: {error_msg}"


def add_new_category(
    client, 
    user_id: str, 
    area_id: str,
    name: str,
    description: str = "",
    parent_category_id: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Add new category to database.
    
    Args:
        client: Supabase client
        user_id: User ID
        area_id: Area UUID
        name: Category name
        description: Category description
        parent_category_id: Optional parent category UUID
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Check if category with this name already exists in this area (for root categories)
        if not parent_category_id:
            # For root categories: check unique constraint (name + area_id + parent=NULL)
            existing = client.table('categories').select('id').eq('user_id', user_id).eq('area_id', area_id).eq('name', name).is_('parent_category_id', 'null').execute()
            if existing.data and len(existing.data) > 0:
                return False, f"❌ Root category '{name}' already exists in this area! Please choose a different name."
        else:
            # For child categories: check if name exists under same parent
            existing = client.table('categories').select('id').eq('user_id', user_id).eq('parent_category_id', parent_category_id).eq('name', name).execute()
            if existing.data and len(existing.data) > 0:
                return False, f"❌ Category '{name}' already exists under this parent! Please choose a different name."
        
        # Generate UUID and slug
        new_id = str(uuid.uuid4())
        slug = generate_slug(name)
        
        # Determine level
        if parent_category_id:
            # Get parent level
            parent = client.table('categories').select('level').eq('id', parent_category_id).execute()
            if parent.data and len(parent.data) > 0:
                level = parent.data[0]['level'] + 1
            else:
                return False, "❌ Parent category not found"
        else:
            level = 1  # Root category
        
        # Get next sort_order
        if parent_category_id:
            # Sort within parent
            sort_order = get_next_sort_order(client, 'categories', user_id, 'parent_category_id', parent_category_id)
        else:
            # Sort within area for root categories
            sort_order = get_next_sort_order(client, 'categories', user_id, 'area_id', area_id)
        
        # Prepare data
        category_data = {
            'id': new_id,
            'user_id': user_id,
            'area_id': area_id,
            'parent_category_id': parent_category_id if parent_category_id else None,  # Explicitly set to None
            'name': name,
            'slug': slug,
            'level': level,
            'sort_order': sort_order,
            'description': description if description else None
        }
        
        # Insert ONCE
        result = client.table('categories').insert(category_data).execute()
        
        # Verify insert was successful
        if result.data and len(result.data) > 0:
            parent_info = " (root category)" if not parent_category_id else ""
            return True, f"✅ Successfully added category: {name}{parent_info}"
        else:
            return False, f"❌ Failed to add category: {name}"
    
    except Exception as e:
        error_msg = str(e)
        # Handle duplicate key constraints
        if '23505' in error_msg or 'duplicate' in error_msg.lower() or 'unique constraint' in error_msg.lower():
            if 'idx_categories_root_unique' in error_msg:
                return False, f"❌ Root category '{name}' already exists in this area!"
            else:
                return False, f"❌ Category '{name}' already exists!"
        return False, f"❌ Error adding category: {error_msg}"


def add_new_attribute(
    client,
    user_id: str,
    category_id: str,
    name: str,
    data_type: str,
    unit: str = "",
    is_required: bool = False,
    default_value: str = "",
    validation_min: str = "",
    validation_max: str = "",
    description: str = ""
) -> Tuple[bool, str]:
    """
    Add new attribute to database.
    
    Args:
        client: Supabase client
        user_id: User ID
        category_id: Category UUID
        name: Attribute name
        data_type: Data type
        unit: Unit
        is_required: Is required flag
        default_value: Default value
        validation_min: Validation min value
        validation_max: Validation max value
        description: Description
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Generate UUID and slug
        new_id = str(uuid.uuid4())
        slug = generate_slug(name)
        
        # Get next sort_order
        sort_order = get_next_sort_order(client, 'attribute_definitions', user_id, 'category_id', category_id)
        
        # Parse validation rules
        val_rules = {}
        if validation_min:
            try:
                val_rules['min'] = float(validation_min)
            except:
                val_rules['min'] = validation_min
        
        if validation_max:
            try:
                val_rules['max'] = float(validation_max)
            except:
                val_rules['max'] = validation_max
        
        # Prepare data
        attribute_data = {
            'id': new_id,
            'user_id': user_id,
            'category_id': category_id,
            'name': name,
            'slug': slug,
            'data_type': data_type,
            'unit': unit if unit else None,
            'is_required': is_required,
            'default_value': default_value if default_value else None,
            'validation_rules': val_rules if val_rules else {},
            'description': description if description else None,
            'sort_order': sort_order
        }
        
        # Insert
        client.table('attribute_definitions').insert(attribute_data).execute()
        
        return True, f"✅ Successfully added attribute: {name}"
    
    except Exception as e:
        return False, f"❌ Error adding attribute: {str(e)}"


# ============================================
# DELETE FUNCTIONS
# ============================================

def delete_area(client, user_id: str, area_id: str) -> Tuple[bool, str]:
    """
    Delete area from database (CASCADE deletes categories and attributes).
    
    Args:
        client: Supabase client
        user_id: User ID
        area_id: Area UUID
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # First delete all attributes for categories in this area
        categories = client.table('categories').select('id').eq('area_id', area_id).eq('user_id', user_id).execute()
        if categories.data:
            cat_ids = [c['id'] for c in categories.data]
            client.table('attribute_definitions').delete().in_('category_id', cat_ids).eq('user_id', user_id).execute()
        
        # Then delete all categories in this area
        client.table('categories').delete().eq('area_id', area_id).eq('user_id', user_id).execute()
        
        # Finally delete the area
        client.table('areas').delete().eq('id', area_id).eq('user_id', user_id).execute()
        
        return True, "✅ Successfully deleted area and all its categories/attributes"
    
    except Exception as e:
        return False, f"❌ Error deleting area: {str(e)}"


def delete_category(client, user_id: str, category_id: str) -> Tuple[bool, str]:
    """
    Delete category from database (CASCADE deletes attributes).
    
    Args:
        client: Supabase client
        user_id: User ID
        category_id: Category UUID
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # First delete all child categories recursively
        children = client.table('categories').select('id').eq('parent_category_id', category_id).eq('user_id', user_id).execute()
        if children.data:
            for child in children.data:
                delete_category(client, user_id, child['id'])
        
        # Delete all attributes for this category
        client.table('attribute_definitions').delete().eq('category_id', category_id).eq('user_id', user_id).execute()
        
        # Delete the category
        client.table('categories').delete().eq('id', category_id).eq('user_id', user_id).execute()
        
        return True, "✅ Successfully deleted category and all its attributes"
    
    except Exception as e:
        return False, f"❌ Error deleting category: {str(e)}"


def delete_attribute(client, user_id: str, attribute_id: str) -> Tuple[bool, str]:
    """
    Delete attribute from database.
    
    Args:
        client: Supabase client
        user_id: User ID
        attribute_id: Attribute UUID
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Delete the attribute
        client.table('attribute_definitions').delete().eq('id', attribute_id).eq('user_id', user_id).execute()
        
        return True, "✅ Successfully deleted attribute"
    
    except Exception as e:
        return False, f"❌ Error deleting attribute: {str(e)}"


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
    
    # ============================================
    # COLLAPSIBLE HELP SECTION
    # ============================================
    with st.expander("ℹ️ Help - How to Use Interactive Structure Viewer", expanded=False):
        st.markdown("""
        ### 🎯 Two Ways to Work with Your Structure
        
        #### **Method 1: Direct Editing (Edit Mode)**
        **Best for:** Quick changes, adding/editing individual items
        
        - Switch to **Edit Mode** using the toggle below
        - Choose what to edit in tabs: Areas, Categories, or Attributes
        - Make changes directly in the table (like Excel)
        - Add new items using the forms
        - Delete items with cascade warnings
        - Save all changes with one confirmation
        
        **Features:**
        - 🎨 Color-coded columns: Pink (auto) vs Blue (editable)
        - ✅ Live validation before saving
        - ⏪ Rollback option to discard changes
        
        ---
        
        #### **Method 2: Excel Upload (Edit Mode → Upload Tab)**
        **Best for:** Bulk changes, offline editing, complex restructuring
        
        1. **Download:** Generate Enhanced Excel in Read-Only mode
        2. **Edit:** Make changes in Excel (add rows, edit blue columns)
        3. **Upload:** Go to Edit Mode → Upload Hierarchical Excel tab
        4. **Review:** System shows detected changes
        5. **Confirm:** Apply changes to database
        
        **Excel Features:**
        - 📥 Drop-down validations
        - 🔢 Auto-formulas for Level, Area, Sort_Order
        - 📊 Row/Column grouping
        - 🎨 Color coding (Pink = auto, Blue = editable)
        
        ---
        
        ### 📥 Generate Enhanced Excel (Read-Only Mode)
        Export your structure to Excel with professional features:
        - All current structure data
        - Color-coded editable vs auto-calculated columns
        - Drop-down validations for Data Type, Is Required
        - Formulas for automatic calculations
        - Grouping for better organization
        
        **What you can edit in Excel:**
        - Category names
        - Attribute names, data types, units
        - Validation rules (min/max)
        - Descriptions
        - Add new rows for Areas, Categories, Attributes
        
        **What NOT to edit (auto-calculated):**
        - Type, Level, Sort_Order
        - Area extraction
        - Category Path structure
        
        ---
        
        ### 📤 Upload Hierarchical Excel (Edit Mode)
        Upload edited Excel to update your structure:
        
        **Adding New Items:**
        - **New Area:** Type=`Area`, Category_Path=`<AreaName>`
        - **New Category:** Type=`Category`, Category_Path=`<Area> > <Category>`
        - **New Attribute:** Type=`Attribute`, fill Attribute_Name, Data_Type
        
        **Safety Features:**
        - Change detection (shows what changed)
        - Validation before applying
        - Error highlighting in Excel
        - Confirmation required
        
        ---
        
        ### 💡 Tips
        - **Quick edits?** Use Edit Mode direct editing
        - **Bulk changes?** Use Excel Download → Edit → Upload
        - **Review first:** Always check changes before confirming
        - **Backup:** Download Excel before major changes
        """)
    
    st.info("""
    **Quick Overview:**
    - 📖 **Read-Only Mode**: View structure, Generate Enhanced Excel
    - ✏️ **Edit Mode**: Direct editing OR Upload Excel (4 tabs)
    - 🆕 **v1.5.9**: Two-step attribute form with smart field masking
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
        # Filters - warn if unsaved changes
        def check_unsaved_changes_warning():
            """Check for unsaved changes and display warning if needed"""
            if st.session_state.viewer_mode == 'edit' and st.session_state.original_df is not None:
                if st.session_state.edited_df is not None:
                    display_cols = [col for col in st.session_state.original_df.columns if not col.startswith('_')]
                    orig_display = st.session_state.original_df[display_cols]
                    has_changes = not orig_display.equals(st.session_state.edited_df)
                    
                    if has_changes:
                        st.warning("⚠️ Unsaved changes! Changing filters will discard them.")
                        return True
            return False
        
        area_options = ["All Areas"] + sorted(df[df['Type'] == 'Area']['Area'].unique().tolist())
        selected_area = st.selectbox("Filter by Area", area_options, key="area_filter")
        
        # Show warning if there are unsaved changes
        if selected_area != "All Areas":
            check_unsaved_changes_warning()
    
    with col3:
        # Conditional button based on mode
        if st.session_state.viewer_mode == 'read_only':
            # Generate Enhanced Excel button in Read-Only mode
            if st.button("📥 Generate Excel", use_container_width=True, type="primary"):
                with st.spinner("Generating enhanced Excel file..."):
                    try:
                        # Use EnhancedStructureExporter with current filters
                        exporter = EnhancedStructureExporter(
                            client=client,
                            user_id=user_id,
                            filter_area=selected_area,
                            filter_search=search_term
                        )
                        
                        file_path = exporter.export_hierarchical_view()
                        
                        # Read file for download
                        with open(file_path, 'rb') as f:
                            excel_data = f.read()
                        
                        # Show filter info if filters are applied
                        filter_info = []
                        if selected_area != "All Areas":
                            filter_info.append(f"Area: {selected_area}")
                        if search_term:
                            filter_info.append(f"Search: '{search_term}'")
                        
                        if filter_info:
                            st.success(f"✅ Enhanced Excel generated with filters: {', '.join(filter_info)}")
                        else:
                            st.success("✅ Enhanced Excel generated (all data)")
                        
                        # Download button
                        st.download_button(
                            label="⬇️ Download Excel",
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
                        with st.expander("🔍 View Error Details"):
                            st.exception(e)
        else:
            # Edit mode - no button needed
            # User can use browser refresh or navigate away and back
            st.empty()
    
    # Search - warn about unsaved changes
    search_term = st.text_input("🔎 Search in Category Path", "", key="search_filter")
    
    # Check for unsaved changes when search is used
    if search_term and st.session_state.viewer_mode == 'edit':
        if st.session_state.original_df is not None and st.session_state.edited_df is not None:
            display_cols = [col for col in st.session_state.original_df.columns if not col.startswith('_')]
            orig_display = st.session_state.original_df[display_cols]
            has_changes = not orig_display.equals(st.session_state.edited_df)
            
            if has_changes:
                st.warning("⚠️ Filtering with unsaved changes. Save or discard changes first to avoid confusion.")
    
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
        # Edit mode - use tabbed interface with 3 editors
        st.markdown("### ✏️ Structure (Edit Mode) - Choose What to Edit")
        
        # Create tabs for different entity types
        tab1, tab2, tab3, tab4 = st.tabs([
            "📦 Edit Areas", 
            "📁 Edit Categories", 
            "🏷️ Edit Attributes",
            "📤 Upload Hierarchical Excel"
        ])
        
        # ============================================
        # TAB 1: EDIT AREAS
        # ============================================
        with tab1:
            st.markdown("#### 📦 Edit Areas")
            st.info("Edit area names and descriptions. Add new areas or delete existing ones.")
            
            # Filter to show ONLY Area rows - USE filtered_df (has metadata)
            area_mask = filtered_df['Type'] == 'Area'
            area_full_df = filtered_df[area_mask].copy()
            
            if area_full_df.empty:
                st.warning("⚠️ No areas found.")
            else:
                st.markdown(f"**Viewing {len(area_full_df)} areas**")
                
                # Select relevant columns for Areas (display only)
                area_cols = ['Type', 'Sort_Order', 'Area', 'Description']
                area_display = area_full_df[area_cols].copy()
                
                # Add checkbox column for deletion
                area_display.insert(0, '🗑️', False)
                
                # Configure columns for Area editing
                area_column_config = {
                    '🗑️': st.column_config.CheckboxColumn('Delete?', help="Check to mark for deletion"),
                    'Type': st.column_config.TextColumn('Type', disabled=True, help="Row type (locked)"),
                    'Sort_Order': st.column_config.NumberColumn('Sort_Order', disabled=True, help="Display order (locked)"),
                    'Area': st.column_config.TextColumn('Area', help="Area name - editable", disabled=False),
                    'Description': st.column_config.TextColumn('Description', help="Area description - editable", disabled=False)
                }
                
                # Render area editor
                edited_area_df = st.data_editor(
                    area_display,
                    use_container_width=True,
                    height=300,
                    column_config=area_column_config,
                    hide_index=True,
                    num_rows="fixed"
                )
                
                # Check if any areas are marked for deletion
                areas_to_delete = edited_area_df[edited_area_df['🗑️'] == True]
                
                if not areas_to_delete.empty:
                    st.error(f"⚠️ **{len(areas_to_delete)} area(s) marked for deletion!**")
                    
                    # Show warnings for each area
                    for idx in areas_to_delete.index:
                        area_id = area_full_df.loc[idx, '_area_id']
                        has_deps, warning = check_area_has_dependencies(client, area_id, user_id)
                        if has_deps:
                            st.warning(warning)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        del_confirm = st.text_input("Type 'DELETE' to confirm deletion", key="delete_area_confirm")
                    with col2:
                        if st.button("❌ Delete Marked", key="delete_areas_btn", disabled=(del_confirm != "DELETE")):
                            with st.spinner("Deleting areas..."):
                                deleted_count = 0
                                for idx in areas_to_delete.index:
                                    area_id = area_full_df.loc[idx, '_area_id']
                                    success, msg = delete_area(client, user_id, area_id)
                                    if success:
                                        deleted_count += 1
                                    else:
                                        st.error(msg)
                                
                                if deleted_count > 0:
                                    st.success(f"✅ Deleted {deleted_count} area(s)")
                                    st.cache_data.clear()
                                    st.session_state.original_df = None
                                    st.rerun()
                
                st.markdown("---")
                
                # Add new area form
                with st.expander("➕ Add New Area", expanded=False):
                    # Initialize form submission counter in session state
                    if 'area_form_counter' not in st.session_state:
                        st.session_state.area_form_counter = 0
                    
                    # Use unique key with counter to force form reset after successful submit
                    with st.form(f"add_area_form_{st.session_state.area_form_counter}"):
                        new_area_name = st.text_input("Area Name *", placeholder="e.g., Fitness, Nutrition, Health")
                        new_area_desc = st.text_area("Description", placeholder="Optional description...")
                        
                        submitted = st.form_submit_button("➕ Add Area", use_container_width=True)
                        
                        if submitted:
                            if not new_area_name:
                                st.error("❌ Area name is required!")
                            else:
                                with st.spinner("Adding area..."):
                                    success, msg = add_new_area(client, user_id, new_area_name, new_area_desc)
                                    if success:
                                        st.success(msg)
                                        # Increment counter to create NEW form (prevents double submit)
                                        st.session_state.area_form_counter += 1
                                        # Clear cache
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        # Rerun to refresh
                                        st.rerun()
                                    else:
                                        st.error(msg)
        
        # ============================================
        # TAB 2: EDIT CATEGORIES
        # ============================================
        with tab2:
            st.markdown("#### 📁 Edit Categories")
            st.info("Edit category names and descriptions. Add new categories or delete existing ones.")
            
            # Filter to show ONLY Category rows - USE filtered_df (has metadata)
            category_mask = filtered_df['Type'] == 'Category'
            category_full_df = filtered_df[category_mask].copy()
            
            # Always show filter and Add Category form, even if no categories exist
            st.markdown("---")
            col_filter = st.columns([1, 3])
            
            with col_filter[0]:
                # Get ALL areas directly from database (not just those with categories)
                # This ensures new areas appear immediately after adding
                all_areas_response = client.table('areas').select('name').eq('user_id', user_id).order('name').execute()
                all_areas_list = [area['name'] for area in all_areas_response.data] if all_areas_response.data else []
                available_areas = ["All Areas"] + sorted(all_areas_list)
                
                selected_area_cat = st.selectbox(
                    "Filter by Area",
                    available_areas,
                    key="area_filter_categories"
                )
            
            # Apply area filter
            if selected_area_cat != "All Areas" and not category_full_df.empty:
                category_full_df = category_full_df[category_full_df['Area'] == selected_area_cat]
            
            # Show categories if they exist
            if category_full_df.empty:
                if selected_area_cat != "All Areas":
                    st.info(f"ℹ️ No categories found for Area: {selected_area_cat}. Add your first category below.")
                else:
                    st.info("ℹ️ No categories found. Add your first category below.")
            else:
                    st.markdown(f"**Viewing {len(category_full_df)} categories**")
                    
                    # Select relevant columns for Categories (display only)
                    cat_cols = ['Type', 'Level', 'Sort_Order', 'Area', 'Category_Path', 'Category', 'Description']
                    cat_display = category_full_df[cat_cols].copy()
                    
                    # Add checkbox column for deletion
                    cat_display.insert(0, '🗑️', False)
                    
                    # Configure columns for Category editing
                    cat_column_config = {
                        '🗑️': st.column_config.CheckboxColumn('Delete?', help="Check to mark for deletion"),
                        'Type': st.column_config.TextColumn('Type', disabled=True),
                        'Level': st.column_config.NumberColumn('Level', disabled=True),
                        'Sort_Order': st.column_config.NumberColumn('Sort_Order', disabled=True),
                        'Area': st.column_config.TextColumn('Area', disabled=True),
                        'Category_Path': st.column_config.TextColumn('Category_Path', disabled=True, help="Full hierarchical path"),
                        'Category': st.column_config.TextColumn('Category', help="Category name - editable", disabled=False),
                        'Description': st.column_config.TextColumn('Description', help="Category description - editable", disabled=False)
                    }
                    
                    # Render category editor
                    edited_cat_df = st.data_editor(
                        cat_display,
                        use_container_width=True,
                        height=300,
                        column_config=cat_column_config,
                        hide_index=True,
                        num_rows="fixed"
                    )
                    
                    # Check if any categories are marked for deletion
                    cats_to_delete = edited_cat_df[edited_cat_df['🗑️'] == True]
                    
                    if not cats_to_delete.empty:
                        st.error(f"⚠️ **{len(cats_to_delete)} category(ies) marked for deletion!**")
                        
                        # Show warnings for each category
                        for idx in cats_to_delete.index:
                            cat_id = category_full_df.loc[idx, '_category_id']
                            has_deps, warning = check_category_has_dependencies(client, cat_id, user_id)
                            if has_deps:
                                st.warning(warning)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            del_confirm = st.text_input("Type 'DELETE' to confirm deletion", key="delete_cat_confirm")
                        with col2:
                            if st.button("❌ Delete Marked", key="delete_cats_btn", disabled=(del_confirm != "DELETE")):
                                with st.spinner("Deleting categories..."):
                                    deleted_count = 0
                                    for idx in cats_to_delete.index:
                                        cat_id = category_full_df.loc[idx, '_category_id']
                                        success, msg = delete_category(client, user_id, cat_id)
                                        if success:
                                            deleted_count += 1
                                        else:
                                            st.error(msg)
                                    
                                    if deleted_count > 0:
                                        st.success(f"✅ Deleted {deleted_count} category(ies)")
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        st.rerun()
                    
                    # Check for edit changes (non-delete)
                    edited_cat_df_no_del = edited_cat_df.drop(columns=['🗑️'])
                    cat_display_no_del = cat_display.drop(columns=['🗑️'])
                    has_cat_changes = not cat_display_no_del.equals(edited_cat_df_no_del)
                    
                    if has_cat_changes:
                        st.warning("⚠️ You have unsaved edit changes")
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            confirm = st.text_input("Type 'SAVE' to confirm", key="save_cat_confirm")
                        with col2:
                            if st.button("💾 Save Changes", key="save_categories", disabled=(confirm != "SAVE")):
                                with st.spinner("Saving category changes..."):
                                    # Save category changes
                                    success, stats = _save_category_changes(
                                        client, user_id, cat_display_no_del, edited_cat_df_no_del, filtered_df
                                    )
                                    
                                    if success:
                                        st.success(f"✅ Successfully updated {stats['categories']} categories!")
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        st.session_state.edited_df = None
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to save changes. {stats['errors']} errors occurred.")
            
            # Add Category form - ALWAYS visible, regardless of whether categories exist
            st.markdown("---")
            
            # Add new category form
            with st.expander("➕ Add New Category", expanded=False):
                # Initialize form submission counter in session state
                if 'category_form_counter' not in st.session_state:
                    st.session_state.category_form_counter = 0
                
                # Get areas for selection
                areas_response = client.table('areas').select('id, name').eq('user_id', user_id).execute()
                areas_dict = {a['name']: a['id'] for a in areas_response.data} if areas_response.data else {}
                
                # Use unique key with counter to force form reset after successful submit
                with st.form(f"add_category_form_{st.session_state.category_form_counter}"):
                    # If Area filter is active, pre-populate and disable Area selection
                    if selected_area_cat != "All Areas":
                        st.info(f"ℹ️ Adding category to filtered area: **{selected_area_cat}**")
                        # Display as disabled text input (can't change)
                        st.text_input("Select Area *", value=selected_area_cat, disabled=True)
                        new_cat_area = selected_area_cat
                    else:
                        # Show full dropdown if no filter
                        new_cat_area = st.selectbox("Select Area *", list(areas_dict.keys()))
                    
                    new_cat_name = st.text_input("Category Name *", placeholder="e.g., Cardio, Strength Training")
                    new_cat_desc = st.text_area("Description", placeholder="Optional description...")
                    
                    # Parent category selection (optional)
                    if new_cat_area:
                        area_id_for_cats = areas_dict[new_cat_area]
                        # Get ONLY categories from the selected area
                        cats_in_area = client.table('categories').select('id, name').eq('area_id', area_id_for_cats).eq('user_id', user_id).execute()
                        parent_options = ["None (Root Category)"] + [c['name'] for c in (cats_in_area.data if cats_in_area.data else [])]
                        parent_cats_dict = {c['name']: c['id'] for c in (cats_in_area.data if cats_in_area.data else [])}
                        
                        if len(parent_options) > 1:
                            new_cat_parent = st.selectbox("Parent Category", parent_options, help=f"Select parent category from '{new_cat_area}' area")
                        else:
                            st.info(f"ℹ️ No existing categories in '{new_cat_area}' - this will be a root category")
                            new_cat_parent = "None (Root Category)"
                    else:
                        new_cat_parent = "None (Root Category)"
                    
                    submitted = st.form_submit_button("➕ Add Category", use_container_width=True)
                    
                    if submitted:
                        if not new_cat_name:
                            st.error("❌ Category name is required!")
                        elif not new_cat_area:
                            st.error("❌ Please select an area!")
                        else:
                            # Resolve parent_id
                            if new_cat_parent == "None (Root Category)":
                                parent_id = None
                            else:
                                parent_id = parent_cats_dict.get(new_cat_parent)
                                # Verify parent_id is valid
                                if not parent_id:
                                    st.error(f"❌ Parent category '{new_cat_parent}' not found in dropdown data!")
                                    st.stop()
                            
                            with st.spinner("Adding category..."):
                                success, msg = add_new_category(
                                    client, user_id, areas_dict[new_cat_area],
                                    new_cat_name, new_cat_desc, parent_id
                                )
                                if success:
                                    st.success(msg)
                                    # Increment counter to create NEW form (prevents double submit)
                                    st.session_state.category_form_counter += 1
                                    # Clear cache and reload data
                                    st.cache_data.clear()
                                    st.session_state.original_df = None
                                    # IMPORTANT: rerun to refresh everything and clear form
                                    st.rerun()
                                else:
                                    st.error(msg)
        
        # ============================================
        # TAB 3: EDIT ATTRIBUTES
        # ============================================
        with tab3:
            st.markdown("#### 🏷️ Edit Attributes")
            st.info("Edit attribute definitions. Add new attributes or delete existing ones.")
            
            # Filter to show ONLY Attribute rows - USE filtered_df (has metadata)
            attribute_mask = filtered_df['Type'] == 'Attribute'
            attribute_full_df = filtered_df[attribute_mask].copy()
            
            # Always show filters and Add Attribute form, even if no attributes exist
            st.markdown("---")
            col_filter1, col_filter2 = st.columns(2)
            
            with col_filter1:
                # Get ALL areas directly from database (not just those with attributes)
                # This ensures new areas appear immediately after adding (Bug #12 fix)
                all_areas_response = client.table('areas').select('name').eq('user_id', user_id).order('name').execute()
                all_areas_list = [area['name'] for area in all_areas_response.data] if all_areas_response.data else []
                available_areas_attr = ["All Areas"] + sorted(all_areas_list)
                
                selected_area_attr = st.selectbox(
                    "Filter by Area",
                    available_areas_attr,
                    key="area_filter_attributes"
                )
            
            # Apply area filter first
            if selected_area_attr != "All Areas" and not attribute_full_df.empty:
                attribute_full_df = attribute_full_df[attribute_full_df['Area'] == selected_area_attr]
            
            with col_filter2:
                # Get ALL categories from filtered area (not just those with attributes)
                available_cats = ["All Categories"]
                
                if selected_area_attr != "All Areas":
                    # Query database for ALL categories in the selected area
                    area_cats_response = client.table('categories').select('name, areas(name)').eq('user_id', user_id).execute()
                    if area_cats_response.data:
                        # Filter to selected area and get category names
                        area_cat_names = [
                            cat['name'] for cat in area_cats_response.data 
                            if cat.get('areas') and cat['areas']['name'] == selected_area_attr
                        ]
                        available_cats += sorted(area_cat_names)
                else:
                    # Show categories from ALL areas that have attributes
                    if not attribute_full_df.empty:
                        available_cats += sorted(attribute_full_df['Category'].unique().tolist())
                
                selected_category = st.selectbox(
                    "Filter by Category",
                    available_cats,
                    key="category_filter_attributes"
                )
            
            # Apply category filter
            if selected_category != "All Categories" and not attribute_full_df.empty:
                attribute_full_df = attribute_full_df[attribute_full_df['Category'] == selected_category]
            
            # Show attributes if they exist
            if attribute_full_df.empty:
                if selected_area_attr != "All Areas" or selected_category != "All Categories":
                    st.info(f"ℹ️ No attributes found for the selected filters. Add your first attribute below.")
                else:
                    st.info("ℹ️ No attributes found. Add your first attribute below.")
            else:
                    st.markdown(f"**Viewing {len(attribute_full_df)} attributes**")
                    
                    # Select relevant columns for Attributes (display only)
                    attr_cols = ['Type', 'Level', 'Sort_Order', 'Area', 'Category_Path', 'Category',
                                'Attribute_Name', 'Data_Type', 'Unit', 'Is_Required', 
                                'Default_Value', 'Validation_Min', 'Validation_Max', 'Description']
                    
                    attr_display = attribute_full_df[attr_cols].copy()
                    
                    # Add checkbox column for deletion
                    attr_display.insert(0, '🗑️', False)
                    
                    # Configure columns for Attribute editing
                    attr_column_config = {
                        '🗑️': st.column_config.CheckboxColumn('Delete?', help="Check to mark for deletion"),
                        'Type': st.column_config.TextColumn('Type', disabled=True),
                        'Level': st.column_config.NumberColumn('Level', disabled=True),
                        'Sort_Order': st.column_config.NumberColumn('Sort_Order', disabled=True),
                        'Area': st.column_config.TextColumn('Area', disabled=True),
                        'Category_Path': st.column_config.TextColumn('Category_Path', disabled=True),
                        'Category': st.column_config.TextColumn('Category', disabled=True),
                        'Attribute_Name': st.column_config.TextColumn('Attribute_Name', help="Attribute name - editable", disabled=False),
                        'Data_Type': st.column_config.SelectboxColumn('Data_Type', options=DATA_TYPES, help="Select data type", disabled=False),
                        'Unit': st.column_config.TextColumn('Unit', help="Measurement unit", disabled=False),
                        'Is_Required': st.column_config.SelectboxColumn('Is_Required', options=IS_REQUIRED_OPTIONS, help="Required field?", disabled=False),
                        'Default_Value': st.column_config.TextColumn('Default_Value', help="Default value", disabled=False),
                        'Validation_Min': st.column_config.TextColumn('Validation_Min', help="Minimum value", disabled=False),
                        'Validation_Max': st.column_config.TextColumn('Validation_Max', help="Maximum value", disabled=False),
                        'Description': st.column_config.TextColumn('Description', help="Attribute description", disabled=False)
                    }
                    
                    # Render attribute editor
                    edited_attr_df = st.data_editor(
                        attr_display,
                        use_container_width=True,
                        height=300,
                        column_config=attr_column_config,
                        hide_index=True,
                        num_rows="fixed"
                    )
                    
                    # Check if any attributes are marked for deletion
                    attrs_to_delete = edited_attr_df[edited_attr_df['🗑️'] == True]
                    
                    if not attrs_to_delete.empty:
                        st.error(f"⚠️ **{len(attrs_to_delete)} attribute(s) marked for deletion!**")
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            del_confirm = st.text_input("Type 'DELETE' to confirm deletion", key="delete_attr_confirm")
                        with col2:
                            if st.button("❌ Delete Marked", key="delete_attrs_btn", disabled=(del_confirm != "DELETE")):
                                with st.spinner("Deleting attributes..."):
                                    deleted_count = 0
                                    for idx in attrs_to_delete.index:
                                        attr_id = attribute_full_df.loc[idx, '_attribute_id']
                                        success, msg = delete_attribute(client, user_id, attr_id)
                                        if success:
                                            deleted_count += 1
                                        else:
                                            st.error(msg)
                                    
                                    if deleted_count > 0:
                                        st.success(f"✅ Deleted {deleted_count} attribute(s)")
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        st.rerun()
                    
                    # Store edited dataframe
                    st.session_state.edited_df = edited_attr_df.drop(columns=['🗑️'])
                    
                    # Check for edit changes (non-delete)
                    edited_attr_df_no_del = edited_attr_df.drop(columns=['🗑️'])
                    attr_display_no_del = attr_display.drop(columns=['🗑️'])
                    has_attr_changes = not attr_display_no_del.equals(edited_attr_df_no_del)
                    
                    if not has_attr_changes:
                        st.info("ℹ️ No edit changes detected")
                    else:
                        st.warning("⚠️ **You have unsaved edit changes**")
                        
                        # Validate changes
                        is_valid, errors = validate_changes(edited_attr_df_no_del)
                        
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
                                key="save_attr_confirmation"
                            )
                        
                        with col2:
                            if st.button("💾 Save Changes", disabled=not is_valid, use_container_width=True, key="save_attributes"):
                                if confirmation_text == "SAVE":
                                    with st.spinner("Saving changes..."):
                                        # Use attribute_full_df which has metadata columns (_attribute_id)
                                        full_edited_df = st.session_state.original_df.copy()
                                        
                                        # Update only the attribute rows that were edited
                                        for idx, edited_row in edited_attr_df_no_del.iterrows():
                                            # Find matching row in original df by metadata IDs
                                            attr_id = attribute_full_df.loc[idx, '_attribute_id']
                                            mask = (full_edited_df['_attribute_id'] == attr_id)
                                            if mask.any():
                                                # Update editable columns
                                                for col in attr_cols:
                                                    if col in edited_attr_df_no_del.columns:
                                                        full_edited_df.loc[mask, col] = edited_row[col]
                                        
                                        success, message, stats = save_changes_to_database(
                                            client,
                                            user_id,
                                            st.session_state.original_df,
                                            full_edited_df
                                        )
                                        
                                        if success:
                                            st.success(f"✅ {message}")
                                            if stats.get('attributes', 0) > 0:
                                                st.info(f"Updated: {stats['attributes']} attributes")
                                            
                                            # Show errors if any
                                            if stats.get('errors', 0) > 0:
                                                st.warning(f"⚠️ {stats['errors']} rows had errors (skipped)")
                                            
                                            # Clear cache and reset session state
                                            st.cache_data.clear()
                                            st.session_state.original_df = None
                                            st.session_state.edited_df = None
                                            
                                            st.balloons()
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {message}")
                                            if stats.get('errors', 0) > 0:
                                                st.error(f"Failed to update {stats['errors']} rows")
                                else:
                                    st.error("❌ Please type 'SAVE' to confirm")
                        
                        with col3:
                            if st.button("⏪ Discard Changes", use_container_width=True, key="discard_attributes"):
                                st.session_state.edited_df = None
                                st.rerun()
            
            # Add Attribute form - ALWAYS visible, regardless of whether attributes exist
            st.markdown("---")
            with st.expander("➕ Add New Attribute", expanded=False):
                st.caption("💡 Two-step process: (1) Select Data Type first → (2) Form shows only relevant fields for that type")
                
                # Initialize form submission counter in session state
                if 'attribute_form_counter' not in st.session_state:
                    st.session_state.attribute_form_counter = 0
                
                # Get current filters from session state
                current_area_filter = st.session_state.get('area_filter_attributes', 'All Areas')
                current_category_filter = st.session_state.get('category_filter_attributes', 'All Categories')
                
                # Get categories for selection
                cats_response = client.table('categories').select('id, name, area_id, areas(name)').eq('user_id', user_id).execute()
                
                # Filter categories based on active filters
                filtered_cats = []
                if cats_response.data:
                    for cat in cats_response.data:
                        area_name = cat['areas']['name'] if cat.get('areas') else 'Unknown'
                        
                        # Apply Area filter if active
                        if current_area_filter != "All Areas":
                            if area_name != current_area_filter:
                                continue  # Skip categories not from filtered area
                        
                        # Apply Category filter if active
                        if current_category_filter != "All Categories":
                            if cat['name'] != current_category_filter:
                                continue  # Skip categories not matching filter
                        
                        filtered_cats.append(cat)
                
                # Build category options from filtered list
                cat_options = {}
                for cat in filtered_cats:
                    area_name = cat['areas']['name'] if cat.get('areas') else 'Unknown'
                    display_name = f"{area_name} > {cat['name']}"
                    cat_options[display_name] = cat['id']
                
                # Show info if filters are active
                if current_area_filter != "All Areas" or current_category_filter != "All Categories":
                    filter_parts = []
                    if current_area_filter != "All Areas":
                        filter_parts.append(f"**Area:** {current_area_filter}")
                    if current_category_filter != "All Categories":
                        filter_parts.append(f"**Category:** {current_category_filter}")
                    
                    st.info(f"ℹ️ Adding attribute to filtered: {' > '.join(filter_parts)}")
                
                # TWO-STEP APPROACH: Select Data Type first (outside form), then show relevant form
                st.markdown("**Step 1:** Select Data Type")
                
                # Initialize selected_data_type in session state if not exists
                if 'selected_data_type' not in st.session_state:
                    st.session_state.selected_data_type = 'number'
                
                # Data Type selector OUTSIDE the form (allows dynamic form generation)
                selected_data_type = st.selectbox(
                    "Data Type *",
                    DATA_TYPES,
                    key="attr_data_type_selector",
                    help="Select data type first - form fields will adapt automatically"
                )
                
                # Update session state
                st.session_state.selected_data_type = selected_data_type
                
                st.markdown("**Step 2:** Fill in attribute details")
                
                # Determine which fields to show based on selected type
                show_unit = selected_data_type == 'number'
                show_default = selected_data_type not in ['link', 'image']
                show_validation = selected_data_type in ['number', 'datetime']
                
                # Show helper text about field visibility
                field_notes = []
                if not show_unit:
                    field_notes.append("Unit field hidden (only for 'number' type)")
                if not show_default:
                    field_notes.append("Default Value hidden (not for 'link'/'image')")
                if not show_validation:
                    field_notes.append("Validation fields hidden (only for 'number'/'datetime')")
                
                if field_notes:
                    st.caption(f"💡 {', '.join(field_notes)}")
                
                # Use unique key with counter to force form reset after successful submit
                with st.form(f"add_attribute_form_{st.session_state.attribute_form_counter}"):
                    # Category selection - locked if only one option
                    if len(cat_options) == 0:
                        st.warning("⚠️ No categories available for the current filter. Please adjust filters or create categories first.")
                        new_attr_category = None
                    elif len(cat_options) == 1:
                        # Only one option - show as locked/disabled
                        category_name = list(cat_options.keys())[0]
                        st.text_input("Select Category *", value=category_name, disabled=True, 
                                    help="Locked to filtered category")
                        new_attr_category = category_name
                    else:
                        # Multiple options - show dropdown
                        new_attr_category = st.selectbox("Select Category *", list(cat_options.keys()))
                    
                    new_attr_name = st.text_input("Attribute Name *", placeholder="e.g., Duration, Distance, Weight")
                    
                    # Show ONLY relevant fields based on selected data type
                    col1, col2 = st.columns(2)
                    with col1:
                        if show_unit:
                            new_attr_unit = st.text_input("Unit", placeholder="e.g., km, kg, minutes")
                        else:
                            new_attr_unit = ""
                        
                        new_attr_required = st.selectbox("Is Required?", ["No", "Yes"])
                    
                    with col2:
                        if show_default:
                            new_attr_default = st.text_input("Default Value", placeholder="Optional")
                        else:
                            new_attr_default = ""
                        
                        if show_validation:
                            new_attr_val_min = st.text_input("Validation Min", placeholder="Optional")
                        else:
                            new_attr_val_min = ""
                    
                    if show_validation:
                        new_attr_val_max = st.text_input("Validation Max", placeholder="Optional")
                    else:
                        new_attr_val_max = ""
                    
                    new_attr_desc = st.text_area("Description", placeholder="Optional description...")
                    
                    submitted = st.form_submit_button("➕ Add Attribute", use_container_width=True)
                    
                    if submitted:
                        if not new_attr_name:
                            st.error("❌ Attribute name is required!")
                        elif not new_attr_category:
                            st.error("❌ Please select a category!")
                        elif len(cat_options) == 0:
                            st.error("❌ No categories available. Please adjust filters.")
                        else:
                            is_req = new_attr_required == "Yes"
                            
                            with st.spinner("Adding attribute..."):
                                # Use selected_data_type from outside the form
                                success, msg = add_new_attribute(
                                    client, user_id, cat_options[new_attr_category],
                                    new_attr_name, st.session_state.selected_data_type,
                                    new_attr_unit, is_req, new_attr_default,
                                    new_attr_val_min, new_attr_val_max, new_attr_desc
                                )
                                if success:
                                    st.success(msg)
                                    # Increment counter to create NEW form (prevents double submit)
                                    st.session_state.attribute_form_counter += 1
                                    # Clear cache
                                    st.cache_data.clear()
                                    st.session_state.original_df = None
                                    # Rerun
                                    st.rerun()
                                else:
                                    st.error(msg)
        
        # ============================================
        # TAB 4: UPLOAD HIERARCHICAL EXCEL
        # ============================================
        with tab4:
            st.markdown("#### 📤 Upload Hierarchical Excel")
            st.info("""
            **Update your structure by uploading an edited Hierarchical_View Excel**
            - ✅ **Add new rows** for Areas, Categories, Attributes
            - ✅ **Edit BLUE columns** in existing rows (editable fields)
            - ✅ **Create hierarchies** using Category_Path
            - ✅ **Update properties** like descriptions, data types, validation rules
            """)
            
            st.markdown("---")
            
            # File uploader
            uploaded_file = st.file_uploader(
                "📁 Browse Files - Upload Hierarchical_View Excel",
                type=["xlsx"],
                help="Upload the Excel file you generated in Read-Only mode",
                key="isv_upload_excel"
            )
            
            if not uploaded_file:
                st.markdown("### 📋 How to Use Upload")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    **Step 1: Generate Excel**
                    - Go to **Read-Only Mode**
                    - Click **Generate Enhanced Excel**
                    - Download the file
                    
                    **Step 2: Edit in Excel**
                    - **Add rows** at bottom for new items
                    - **Edit BLUE columns** (editable)
                    - **Don't edit PINK columns** (auto-calculated)
                    
                    **Step 3: Upload**
                    - Come back here
                    - Upload edited file above
                    - Review detected changes
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
                    
                    **New Attribute:**
                    - Type: `Attribute`
                    - Category_Path: `<full path>`
                    - Attribute_Name: `<Name>`
                    - Data_Type: `number`, `text`, etc.
                    """)
                
                st.markdown("---")
                
                st.markdown("""
                ### ✏️ Editable Fields (BLUE columns)
                - **Category**, **Attribute_Name**
                - **Data_Type**: number, text, datetime, boolean, link, image
                - **Unit**, **Is_Required**, **Default_Value**
                - **Validation_Min**, **Validation_Max**
                - **Description**
                
                ### 🚫 Read-Only Fields (PINK columns)
                - **Type**, **Level**, **Sort_Order**
                - **Area**, **Category_Path** (path structure)
                
                ⚠️ **Important:** Don't change PINK columns - they're auto-calculated!
                """)
            
            else:
                # Save uploaded file to temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    # Parse and validate
                    with st.spinner("📖 Parsing Excel file..."):
                        parser = HierarchicalParser(
                            client=client,
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
                        
                        if st.button("📥 Generate Error Report Excel", type="primary", key="isv_error_report"):
                            with st.spinner("Generating error report..."):
                                try:
                                    # Generate error Excel
                                    error_excel_path = generate_error_excel(tmp_path, changes.validation_errors)
                                    
                                    # Read the file for download
                                    with open(error_excel_path, 'rb') as f:
                                        error_excel_data = f.read()
                                    
                                    st.success("✅ Error report generated!")
                                    
                                    # Download button
                                    st.download_button(
                                        label="⬇️ Download Error Report Excel",
                                        data=error_excel_data,
                                        file_name=os.path.basename(error_excel_path),
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        help="Excel file with highlighted errors and comments",
                                        key="isv_download_error_report"
                                    )
                                    
                                    # Cleanup
                                    if os.path.exists(error_excel_path):
                                        os.remove(error_excel_path)
                                
                                except Exception as e:
                                    st.error(f"❌ Error generating error report: {str(e)}")
                                    with st.expander("🔍 View Error Details"):
                                        st.exception(e)
                    
                    # Show validation warnings if any
                    elif changes.validation_warnings:
                        st.warning("⚠️ Validation Warnings")
                        
                        with st.expander("🔍 View Warnings", expanded=False):
                            for warning in changes.validation_warnings:
                                st.warning(f"**Row {warning.row}, Column '{warning.column}':** {warning.message}")
                    
                    # If no changes detected
                    if not changes.has_changes():
                        st.info("ℹ️ No changes detected in the uploaded file.")
                        st.markdown("The file matches your current structure exactly.")
                    
                    elif not changes.validation_errors:
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
                        change_tabs = st.tabs([
                            f"➕ New ({len(changes.new_areas) + len(changes.new_categories) + len(changes.new_attributes)})",
                            f"✏️ Updated ({len(changes.updated_areas) + len(changes.updated_categories) + len(changes.updated_attributes)})"
                        ])
                        
                        # Tab 1: New items
                        with change_tabs[0]:
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
                        with change_tabs[1]:
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
                                help="Type CONFIRM in all caps to enable the Apply button",
                                key="isv_confirm_text"
                            )
                        
                        with col2:
                            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                            apply_button = st.button(
                                "🚀 Apply Changes",
                                type="primary",
                                disabled=(confirm_text != "CONFIRM"),
                                use_container_width=True,
                                key="isv_apply_button"
                            )
                        
                        if apply_button and confirm_text == "CONFIRM":
                            with st.spinner("💾 Applying changes to database..."):
                                success, message = parser.apply_changes()
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.balloons()
                                    
                                    st.info("🔄 Changes applied successfully! Refresh to see updates.")
                                    
                                    # Clear cache to reload fresh data
                                    if st.button("🔄 Refresh Now", type="primary", key="isv_refresh_after_upload"):
                                        st.cache_data.clear()
                                        st.session_state.original_df = None
                                        st.session_state.edited_df = None
                                        st.rerun()
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
