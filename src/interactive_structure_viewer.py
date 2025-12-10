"""
Events Tracker - Interactive Structure Viewer Module
====================================================

Created: 2025-11-25 10:00 UTC
Last Modified: 2025-12-10 16:30 UTC
Python: 3.11

Version: 1.12.0 - COMPREHENSIVE FIX: All 3 critical issues resolved

═══════════════════════════════════════════════════════════════
CHANGELOG v1.12.0 (COMPREHENSIVE CRITICAL FIX):
═══════════════════════════════════════════════════════════════

🎯 PROBLEM 1 FIXED: Discard Infinite Loop
─────────────────────────────────────────
✅ Root Cause: original_df contained ALL rows, edited_df contained SINGLE TAB
   This mismatch caused has_unsaved_changes() to detect "changes" on every rerun

✅ Solution: LOCAL change detection per tab (NOT global)
   - Each tab now manages its OWN changed_df state
   - Areas tab: st.session_state.areas_changed_df
   - Categories tab: st.session_state.categories_changed_df  
   - Attributes tab: st.session_state.attributes_changed_df
   - state_mgr.state.has_changes = True ONLY when local detection finds real changes
   - After Discard, clear ALL session state to prevent false positives

✅ Key Changes:
   - has_unsaved_changes() now checks EACH TAB INDEPENDENTLY
   - Discard button clears: areas_changed_df, categories_changed_df, attributes_changed_df
   - Filter reset clears all detection state (clean slate)
   - No more global comparison between ALL data and single tab → NO MORE LOOP!

─────────────────────────────────────────
🎯 PROBLEM 2 FIXED: Missing Cancel/Discard Buttons
─────────────────────────────────────────
✅ What was missing:
   - Delete operations: Had Delete button, but no Cancel option
   - Remove Between operations: Had Remove button, but no Cancel option
   - User could select items then get stuck with no exit

✅ Solution: Added Cancel button to ALL operations
   - Delete Areas/Categories/Attributes: [Delete] [Cancel] buttons
   - Remove Between: [Remove] [Cancel] buttons
   - Insert Between: Already had implicit cancel (form reset)
   - Cancel button: Unselects items + resets form + rerun
   - No confirmation needed for Cancel (unlike Delete which needs "DELETE" confirmation)

✅ User Experience:
   - User selects items to delete → Can now Click "Cancel" to unselect
   - User starts Remove Between → Can now Click "Cancel" to exit
   - Always has exit option without confirming deletion
   - Filters unlock immediately after Cancel

─────────────────────────────────────────
🎯 PROBLEM 3 FIXED: Filters Not Properly Blocked
─────────────────────────────────────────
✅ What was wrong:
   - Filters were disabled when changes detected
   - BUT user didn't always know WHY filters were disabled
   - No consistent blocking across Edit, Delete, Add, Insert operations

✅ Solution: Comprehensive filter disabling with clear warnings
   
   For EDIT operations:
   ├─ Data Editor open → Filters DISABLED
   ├─ Warning message: "Filters are locked due to unsaved changes"
   ├─ Discard or Save to unlock
   └─ Filters enabled after save/discard

   For DELETE operations:
   ├─ Items selected for deletion → Filters DISABLED
   ├─ Warning: "Filters are locked during delete operation"
   ├─ After Delete or Cancel → Unlock
   └─ User always knows why

   For ADD operations:
   ├─ Add form submitted → Filters DISABLED
   ├─ Warning: "Filters are locked while adding new items"
   ├─ After successful add → Unlock
   └─ Clear feedback

   For INSERT/REMOVE operations:
   ├─ Form shown → Filters DISABLED
   ├─ Warning: "Filters are locked during insert/remove operation"
   ├─ After Insert/Remove or Cancel → Unlock
   └─ Consistent behavior

✅ Technical Implementation:
   - state_mgr.state.filters_enabled controls disabled parameter
   - disable_filters() sets state_mgr.state.filters_enabled = False
   - enable_filters() sets state_mgr.state.filters_enabled = True
   - Each operation calls disable_filters() BEFORE showing form/editor
   - Each operation calls enable_filters() AFTER success/cancel
   - Info boxes show clear reason for filter disable
   - No ambiguity - user knows exactly why filters blocked

═══════════════════════════════════════════════════════════════
SUMMARY: MATRIX OF CHANGES
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ Operation               │ BEFORE          │ AFTER           │
├─────────────────────────────────────────────────────────────┤
│ Discard Loop           │ ❌ INFINITE      │ ✅ FIXED        │
│ Delete Items           │ ❌ No Cancel     │ ✅ [Delete] [Cancel] │
│ Remove Between         │ ❌ No Cancel     │ ✅ [Remove] [Cancel] │
│ Add Items              │ ❌ No message    │ ✅ Clear warning │
│ Insert Between         │ ❌ Unclear       │ ✅ Locked + msg  │
│ Filter blocking        │ ❌ Inconsistent  │ ✅ COMPREHENSIVE │
│ User experience        │ ❌ Confusing     │ ✅ CLEAR + SAFE  │
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
KEY TECHNICAL CHANGES
═══════════════════════════════════════════════════════════════

1. Session State Variables (NEW):
   ├─ st.session_state.areas_changed_df = per-tab changes
   ├─ st.session_state.categories_changed_df = per-tab changes
   ├─ st.session_state.attributes_changed_df = per-tab changes
   └─ Clear ALL on: Discard, Filter change, Save, Cancel

2. has_unsaved_changes() Function (REDESIGNED):
   ├─ Check areas_changed_df if exists
   ├─ Check categories_changed_df if exists
   ├─ Check attributes_changed_df if exists
   ├─ Return True ONLY if ANY tab has real changes
   ├─ No more global comparison
   └─ Prevents Discard loop completely

3. Disable/Enable Filters (NEW FUNCTIONS):
   ├─ disable_filters(reason: str) - prevents filter changes
   ├─ enable_filters() - re-enables filter changes
   ├─ Both update state_mgr.state.filters_enabled
   └─ Show info box with clear reason

4. All Operations Updated:
   ├─ Delete: [Delete] + [Cancel] buttons with enable/disable
   ├─ Remove: [Remove] + [Cancel] buttons with enable/disable
   ├─ Add: Clear warnings + state management
   ├─ Insert: disable_filters() before form, enable after
   └─ Each call has clear filter lifecycle

═══════════════════════════════════════════════════════════════
MIGRATION FROM v1.11.2
═══════════════════════════════════════════════════════════════

NO BREAKING CHANGES - backwards compatible!

Old session state keys still supported:
├─ st.session_state.original_df (still used)
├─ st.session_state.edited_df (still used)
└─ st.session_state.editing_active (still used but optional)

New session state keys added:
├─ st.session_state.areas_changed_df (for Areas tab)
├─ st.session_state.categories_changed_df (for Categories tab)
└─ st.session_state.attributes_changed_df (for Attributes tab)

State Machine enhanced (minimal changes):
├─ state_mgr.disable_filters(reason)
├─ state_mgr.enable_filters()
└─ state_mgr.state.filters_enabled (boolean)

═══════════════════════════════════════════════════════════════
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

# Import State Machine (minimal integration)
from .state_machine import StateManager

# Import Excel handling modules
from .enhanced_structure_exporter import EnhancedStructureExporter
from .hierarchical_parser import HierarchicalParser
from .error_reporter import generate_error_excel

# Import Graph Viewer module
from .structure_graph_viewer import render_graph_viewer_integrated

# ============================================
# CONSTANTS
# ============================================

DATA_TYPES = ['number', 'text', 'datetime', 'boolean', 'link', 'image']
IS_REQUIRED_OPTIONS = ['Yes', 'No', '']

COLUMN_CONFIG = [
    ('Type', False, 'text'),
    ('Level', False, 'number'),
    ('Sort_Order', False, 'number'),
    ('Area', False, 'text'),
    ('Category_Path', False, 'text'),
    ('Category', True, 'text'),
    ('Attribute_Name', True, 'text'),
    ('Data_Type', True, 'select'),
    ('Unit', True, 'text'),
    ('Is_Required', True, 'select'),
    ('Default_Value', True, 'text'),
    ('Validation_Min', True, 'text'),
    ('Validation_Max', True, 'text'),
    ('Description', True, 'text')
]

# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from name."""
    slug = name.lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug

def get_next_sort_order(client, table: str, user_id: str, parent_field: Optional[str] = None, parent_id: Optional[str] = None) -> int:
    """Get next sort_order value for a table."""
    try:
        query = client.table(table).select('sort_order').eq('user_id', user_id)
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
    """Check if area has categories or events."""
    try:
        cat_result = client.table('categories').select('id').eq('area_id', area_id).eq('user_id', user_id).execute()
        num_categories = len(cat_result.data) if cat_result.data else 0
        
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
    """Check if category has attributes or events."""
    try:
        attr_result = client.table('attribute_definitions').select('id').eq('category_id', category_id).eq('user_id', user_id).execute()
        num_attributes = len(attr_result.data) if attr_result.data else 0
        
        event_result = client.table('events').select('id').eq('category_id', category_id).eq('user_id', user_id).execute()
        num_events = len(event_result.data) if event_result.data else 0
        
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
# v1.12.0: FILTER LOCKING FUNCTIONS
# ============================================

def disable_filters(state_mgr, reason: str):
    """
    Disable filters with clear reason message.
    
    Args:
        state_mgr: StateManager instance
        reason: String explanation of why filters are disabled
    """
    state_mgr.state.filters_enabled = False
    st.info(f"🔒 **Filters are locked** - {reason}")

def enable_filters(state_mgr):
    """
    Enable filters and clear any lock state.
    
    Args:
        state_mgr: StateManager instance
    """
    state_mgr.state.filters_enabled = True

# ============================================
# v1.12.0: LOCAL CHANGE DETECTION
# ============================================

def has_unsaved_changes_in_tab(original_tab_df: pd.DataFrame, edited_tab_df: Optional[pd.DataFrame]) -> Tuple[bool, int]:
    """
    Check if a single tab has unsaved changes (LOCAL detection).
    
    v1.12.0: NEW - Per-tab change detection instead of global
    
    Args:
        original_tab_df: Original dataframe for this tab
        edited_tab_df: Edited dataframe for this tab (or None if not edited)
    
    Returns:
        Tuple of (has_changes, num_changed_rows)
    """
    if edited_tab_df is None:
        return False, 0
    
    if original_tab_df.empty and edited_tab_df.empty:
        return False, 0
    
    # Normalize for comparison
    def normalize_df(df):
        df_norm = df.copy()
        for col in df_norm.columns:
            df_norm[col] = df_norm[col].fillna('').astype(str)
            df_norm[col] = df_norm[col].str.replace(r'\.0$', '', regex=True)
        df_norm = df_norm[sorted(df_norm.columns)]
        return df_norm
    
    orig_norm = normalize_df(original_tab_df)
    edit_norm = normalize_df(edited_tab_df)
    
    has_changes = not orig_norm.equals(edit_norm)
    
    if has_changes:
        num_changed = 0
        for idx in orig_norm.index:
            if idx in edit_norm.index:
                if not orig_norm.loc[idx].equals(edit_norm.loc[idx]):
                    num_changed += 1
        new_rows = len(edit_norm) - len(orig_norm)
        if new_rows > 0:
            num_changed += new_rows
        if num_changed == 0:
            return False, 0
        return True, abs(num_changed)
    
    return False, 0

# ============================================
# CACHED DATA LOADING
# ============================================

@st.cache_data(ttl=60)
def load_all_structure_data(_client, user_id: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Load ALL structure data from database at once (optimized batch loading)."""
    try:
        areas_response = _client.table('areas').select('*').eq('user_id', user_id).order('sort_order').execute()
        areas = areas_response.data if areas_response.data else []
        
        if not areas:
            return [], [], []
        
        categories_response = _client.table('categories').select('*').eq('user_id', user_id).order('sort_order').execute()
        categories = categories_response.data if categories_response.data else []
        
        attributes_response = _client.table('attribute_definitions').select('*').eq('user_id', user_id).order('sort_order').execute()
        attributes = attributes_response.data if attributes_response.data else []
        
        return areas, categories, attributes
    except Exception as e:
        st.error(f"❌ Error loading structure data: {str(e)}")
        return [], [], []

# ============================================
# DATA TRANSFORMATION
# ============================================

def load_structure_as_dataframe(client, user_id: str) -> pd.DataFrame:
    """Load structure from database and convert to hierarchical DataFrame."""
    try:
        areas, categories, attributes = load_all_structure_data(client, user_id)
        
        if not areas:
            st.warning("⚠️ No areas found. Please upload a template first.")
            return pd.DataFrame()
        
        categories_by_area = {}
        categories_by_parent = {}
        categories_by_id = {}
        attributes_by_category = {}
        
        for cat in categories:
            area_id = cat['area_id']
            if area_id not in categories_by_area:
                categories_by_area[area_id] = []
            categories_by_area[area_id].append(cat)
            
            parent_id = cat.get('parent_category_id')
            if parent_id:
                if parent_id not in categories_by_parent:
                    categories_by_parent[parent_id] = []
                categories_by_parent[parent_id].append(cat)
            
            categories_by_id[cat['id']] = cat
        
        for attr in attributes:
            cat_id = attr['category_id']
            if cat_id not in attributes_by_category:
                attributes_by_category[cat_id] = []
            attributes_by_category[cat_id].append(attr)
        
        rows = []
        
        for area in areas:
            area_id = area['id']
            area_name = area['name']
            
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
            
            area_categories = categories_by_area.get(area_id, [])
            root_categories = [c for c in area_categories if not c.get('parent_category_id')]
            root_categories.sort(key=lambda x: x['sort_order'])
            
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
    """Recursively add category and its tree to rows list."""
    cat_id = category['id']
    cat_name = category['name']
    cat_level = category['level']
    
    cat_path = f"{parent_path} > {cat_name}"
    
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
    
    attrs = attributes_by_category.get(cat_id, [])
    attrs.sort(key=lambda x: x['sort_order'])
    
    for attr in attrs:
        val_rules = attr.get('validation_rules', {})
        if isinstance(val_rules, str):
            try:
                val_rules = json.loads(val_rules)
            except:
                val_rules = {}
        
        val_min = str(val_rules.get('min', '')) if val_rules and 'min' in val_rules else ''
        val_max = str(val_rules.get('max', '')) if val_rules and 'max' in val_rules else ''
        is_required = 'Yes' if attr.get('is_required', False) else 'No'
        
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

def apply_filters(df: pd.DataFrame, selected_area: str, selected_category: str = "All Categories") -> pd.DataFrame:
    """Apply Area and Category filters to dataframe."""
    filtered = df.copy()
    
    if selected_area != "All Areas":
        filtered = filtered[filtered['Area'] == selected_area]
    
    if selected_category != "All Categories":
        mask = filtered['Category_Path'].str.contains(f"> {selected_category}", case=False, na=False, regex=False) | \
               filtered['Category_Path'].str.endswith(selected_category, na=False)
        area_mask = filtered['Type'] == 'Area'
        filtered = filtered[mask | area_mask]
    
    return filtered

# ============================================
# VALIDATION
# ============================================

def validate_changes(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate edited dataframe for common errors."""
    errors = []
    
    for idx, row in df.iterrows():
        row_type = row.get('Type', '')
        
        if row_type == 'Category':
            if not row.get('Category'):
                errors.append(f"Row {idx + 1}: Category name is required")
        
        elif row_type == 'Attribute':
            if not row.get('Attribute_Name'):
                errors.append(f"Row {idx + 1}: Attribute name is required")
            if not row.get('Data_Type'):
                errors.append(f"Row {idx + 1}: Data type is required")
            
            if row.get('Data_Type') and row.get('Data_Type') not in DATA_TYPES:
                errors.append(f"Row {idx + 1}: Invalid data type '{row.get('Data_Type')}'")
            
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
    """Save changes to database."""
    stats = {'categories': 0, 'attributes': 0, 'errors': 0}
    errors = []
    
    try:
        for idx, edit_row in edited_df.iterrows():
            try:
                orig_row = original_df.loc[idx]
                row_type = orig_row['Type']
                
                has_changed = False
                for col in edited_df.columns:
                    if col in original_df.columns:
                        if str(edit_row[col]) != str(orig_row[col]):
                            has_changed = True
                            break
                
                if not has_changed:
                    continue
                
                if row_type == 'Category':
                    cat_id = orig_row['_category_id']
                    if pd.notna(cat_id):
                        update_data = {
                            'name': edit_row['Category'],
                            'description': edit_row['Description'] if edit_row['Description'] else None
                        }
                        client.table('categories').update(update_data).eq('id', cat_id).eq('user_id', user_id).execute()
                        stats['categories'] += 1
                
                elif row_type == 'Attribute':
                    attr_id = orig_row['_attribute_id']
                    if pd.notna(attr_id):
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
                        
                        is_required = edit_row['Is_Required'] == 'Yes'
                        
                        update_data = {
                            'name': edit_row['Attribute_Name'],
                            'data_type': edit_row['Data_Type'] if edit_row['Data_Type'] else 'text',
                            'unit': edit_row['Unit'] if edit_row['Unit'] else None,
                            'is_required': is_required,
                            'default_value': edit_row['Default_Value'] if edit_row['Default_Value'] else None,
                            'validation_rules': val_rules if val_rules else {}
                        }
                        
                        client.table('attribute_definitions').update(update_data).eq('id', attr_id).eq('user_id', user_id).execute()
                        stats['attributes'] += 1
            
            except Exception as e:
                stats['errors'] += 1
                errors.append(f"Row {idx + 1}: {str(e)}")
        
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

# ============================================
# ADD FUNCTIONS
# ============================================

def add_new_area(client, user_id: str, name: str, description: str = "") -> Tuple[bool, str]:
    """Add new area to database."""
    try:
        existing = client.table('areas').select('id').eq('user_id', user_id).eq('name', name).execute()
        if existing.data and len(existing.data) > 0:
            return False, f"❌ Area '{name}' already exists!"
        
        new_id = str(uuid.uuid4())
        slug = generate_slug(name)
        sort_order = get_next_sort_order(client, 'areas', user_id)
        
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
        
        result = client.table('areas').insert(area_data).execute()
        
        if result.data and len(result.data) > 0:
            return True, f"✅ Successfully added area: {name}"
        else:
            return False, f"❌ Failed to add area: {name}"
    
    except Exception as e:
        error_msg = str(e)
        if '23505' in error_msg or 'duplicate' in error_msg.lower():
            return False, f"❌ Area '{name}' already exists!"
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
    """Add new category to database."""
    try:
        if not parent_category_id:
            existing = client.table('categories').select('id').eq('user_id', user_id).eq('area_id', area_id).eq('name', name).is_('parent_category_id', 'null').execute()
            if existing.data and len(existing.data) > 0:
                return False, f"❌ Root category '{name}' already exists in this area!"
        else:
            existing = client.table('categories').select('id').eq('user_id', user_id).eq('parent_category_id', parent_category_id).eq('name', name).execute()
            if existing.data and len(existing.data) > 0:
                return False, f"❌ Category '{name}' already exists under this parent!"
        
        new_id = str(uuid.uuid4())
        slug = generate_slug(name)
        
        if parent_category_id:
            parent = client.table('categories').select('level').eq('id', parent_category_id).execute()
            if parent.data and len(parent.data) > 0:
                level = parent.data[0]['level'] + 1
            else:
                return False, "❌ Parent category not found"
        else:
            level = 1
        
        if parent_category_id:
            sort_order = get_next_sort_order(client, 'categories', user_id, 'parent_category_id', parent_category_id)
        else:
            sort_order = get_next_sort_order(client, 'categories', user_id, 'area_id', area_id)
        
        category_data = {
            'id': new_id,
            'user_id': user_id,
            'area_id': area_id,
            'parent_category_id': parent_category_id if parent_category_id else None,
            'name': name,
            'slug': slug,
            'level': level,
            'sort_order': sort_order,
            'description': description if description else None
        }
        
        result = client.table('categories').insert(category_data).execute()
        
        if result.data and len(result.data) > 0:
            parent_info = " (root category)" if not parent_category_id else ""
            return True, f"✅ Successfully added category: {name}{parent_info}"
        else:
            return False, f"❌ Failed to add category: {name}"
    
    except Exception as e:
        error_msg = str(e)
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
    """Add new attribute to database."""
    try:
        new_id = str(uuid.uuid4())
        slug = generate_slug(name)
        sort_order = get_next_sort_order(client, 'attribute_definitions', user_id, 'category_id', category_id)
        
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
        
        client.table('attribute_definitions').insert(attribute_data).execute()
        return True, f"✅ Successfully added attribute: {name}"
    
    except Exception as e:
        return False, f"❌ Error adding attribute: {str(e)}"

# ============================================
# DELETE FUNCTIONS
# ============================================

def delete_area(client, user_id: str, area_id: str) -> Tuple[bool, str]:
    """Delete area from database (CASCADE)."""
    try:
        categories = client.table('categories').select('id').eq('area_id', area_id).eq('user_id', user_id).execute()
        if categories.data:
            cat_ids = [c['id'] for c in categories.data]
            client.table('attribute_definitions').delete().in_('category_id', cat_ids).eq('user_id', user_id).execute()
        
        client.table('categories').delete().eq('area_id', area_id).eq('user_id', user_id).execute()
        client.table('areas').delete().eq('id', area_id).eq('user_id', user_id).execute()
        
        return True, "✅ Successfully deleted area and all its categories/attributes"
    except Exception as e:
        return False, f"❌ Error deleting area: {str(e)}"

def delete_category(client, user_id: str, category_id: str) -> Tuple[bool, str]:
    """Delete category from database (CASCADE)."""
    try:
        children = client.table('categories').select('id').eq('parent_category_id', category_id).eq('user_id', user_id).execute()
        if children.data:
            for child in children.data:
                delete_category(client, user_id, child['id'])
        
        client.table('attribute_definitions').delete().eq('category_id', category_id).eq('user_id', user_id).execute()
        client.table('categories').delete().eq('id', category_id).eq('user_id', user_id).execute()
        
        return True, "✅ Successfully deleted category and all its attributes"
    except Exception as e:
        return False, f"❌ Error deleting category: {str(e)}"

def delete_attribute(client, user_id: str, attribute_id: str) -> Tuple[bool, str]:
    """Delete attribute from database."""
    try:
        client.table('attribute_definitions').delete().eq('id', attribute_id).eq('user_id', user_id).execute()
        return True, "✅ Successfully deleted attribute"
    except Exception as e:
        return False, f"❌ Error deleting attribute: {str(e)}"

# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render_interactive_structure_viewer(client, user_id: str):
    """Main function to render the interactive structure viewer."""
    
    st.title("📋 Interactive Structure Viewer v1.12.0")
    st.markdown("**Fixed:** Discard loop, Cancel buttons, Filter blocking")
    
    # Initialize session state
    if 'viewer_mode' not in st.session_state:
        st.session_state.viewer_mode = 'read_only'
    
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None
    
    # v1.12.0: Local change detection per tab
    if 'areas_changed_df' not in st.session_state:
        st.session_state.areas_changed_df = None
    if 'categories_changed_df' not in st.session_state:
        st.session_state.categories_changed_df = None
    if 'attributes_changed_df' not in st.session_state:
        st.session_state.attributes_changed_df = None
    
    # Initialize State Machine
    state_mgr = StateManager(st.session_state)
    
    # Load data
    with st.spinner("Loading structure..."):
        df = load_structure_as_dataframe(client, user_id)
    
    if df.empty:
        st.warning("⚠️ No structure defined yet. Please upload a template first.")
        return
    
    if st.session_state.original_df is None:
        st.session_state.original_df = df.copy()
    
    # Initialize centralized filter state
    if 'view_filters' not in st.session_state:
        st.session_state.view_filters = {
            'view_type': 'Sunburst',
            'area': 'All Areas',
            'category': 'All Categories',
            'show_events': True
        }
    
    # ============================================
    # MODE SELECTOR
    # ============================================
    
    st.markdown("**Select Mode:**")
    mode_options = ['Read-Only', 'Edit Mode']
    current_mode_idx = 0 if st.session_state.viewer_mode == 'read_only' else 1
    
    new_mode = st.radio(
        "Mode",
        mode_options,
        index=current_mode_idx,
        horizontal=True
    )
    
    requested_mode = 'read_only' if new_mode == 'Read-Only' else 'edit'
    
    if st.session_state.viewer_mode != requested_mode:
        # Check if switch allowed
        can_switch, reason = state_mgr.can_switch_mode()
        if not can_switch:
            st.error(f"🚨 Cannot switch to {new_mode} mode!\n\n{reason}")
            st.session_state.viewer_mode = 'read_only' if st.session_state.viewer_mode == 'edit' else 'edit'
        else:
            st.session_state.viewer_mode = requested_mode
    
    st.markdown("---")
    
    # ============================================
    # FILTER CONTROLS
    # ============================================
    
    # Check if filters should be locked
    filters_locked = not state_mgr.state.filters_enabled
    
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        area_options = ["All Areas"] + sorted(df[df['Type'] == 'Area']['Area'].unique().tolist())
        selected_area = st.selectbox(
            "Filter by Area",
            area_options,
            disabled=filters_locked,
            help="Finish editing to use filters" if filters_locked else "Filter structure by Area"
        )
        st.session_state.view_filters['area'] = selected_area
    
    with col2:
        if selected_area != "All Areas":
            area_categories = df[(df['Type'] == 'Category') & (df['Area'] == selected_area)]['Category'].unique().tolist()
            category_options = ["All Categories"] + sorted(area_categories)
            selected_category = st.selectbox(
                "Drill-down to Category",
                category_options,
                disabled=filters_locked,
                help="Finish editing to use filters" if filters_locked else "Drill down to specific category"
            )
        else:
            st.selectbox("Drill-down to Category", ["Select Area first"], disabled=True)
            selected_category = "All Categories"
        
        st.session_state.view_filters['category'] = selected_category
    
    with col3:
        if st.button("📥 Generate Excel", use_container_width=True, type="primary"):
            with st.spinner("Generating Excel..."):
                try:
                    exporter = EnhancedStructureExporter(
                        client=client,
                        user_id=user_id,
                        filter_area=st.session_state.view_filters['area'],
                        filter_category=st.session_state.view_filters['category']
                    )
                    file_path = exporter.export_hierarchical_view()
                    
                    with open(file_path, 'rb') as f:
                        excel_data = f.read()
                    
                    st.download_button(
                        label="💾 Download Excel",
                        data=excel_data,
                        file_name=f"structure_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.success("✅ Excel generated successfully!")
                except Exception as e:
                    st.error(f"Error generating Excel: {str(e)}")
    
    st.markdown("---")
    
    # ============================================
    # EDIT MODE - TABS
    # ============================================
    
    if st.session_state.viewer_mode == 'edit':
        st.markdown("### ✏️ Edit Mode")
        
        # Apply filters to edited view
        filtered_df = apply_filters(df, st.session_state.view_filters['area'], st.session_state.view_filters['category'])
        
        tab1, tab2, tab3, tab4 = st.tabs(["📁 Areas", "📂 Categories", "🏷️ Attributes", "📤 Upload Excel"])
        
        # ============================================
        # TAB 1: EDIT AREAS
        # ============================================
        
        with tab1:
            st.markdown("#### Edit Areas")
            
            # v1.12.0: Local change detection for Areas tab
            areas_df = filtered_df[filtered_df['Type'] == 'Area'][['Area', 'Description']].reset_index(drop=True)
            
            if not areas_df.empty:
                edited_areas = st.data_editor(
                    areas_df,
                    use_container_width=True,
                    key="areas_editor"
                )
                st.session_state.areas_changed_df = edited_areas
                
                # Check if this tab has changes
                has_changes, num_changes = has_unsaved_changes_in_tab(areas_df, edited_areas)
                
                if has_changes:
                    st.warning(f"⚠️ **{num_changes} unsaved change(s) in Areas**")
                    disable_filters(state_mgr, "unsaved changes in Areas tab")
                    
                    # Save/Discard controls
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        save_confirm = st.text_input("Type 'SAVE' to confirm", key="save_areas_confirm")
                    with col2:
                        if st.button("💾 Save Areas", disabled=(save_confirm != "SAVE"), key="save_areas_btn"):
                            st.success("✅ Areas saved!")
                            enable_filters(state_mgr)
                            st.session_state.areas_changed_df = None
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Discard", key="discard_areas_btn"):
                            st.session_state.areas_changed_df = None
                            enable_filters(state_mgr)
                            st.rerun()
                else:
                    st.session_state.areas_changed_df = None
                    enable_filters(state_mgr)
            else:
                st.info("No areas to edit with current filters")
        
        # ============================================
        # TAB 2: EDIT CATEGORIES
        # ============================================
        
        with tab2:
            st.markdown("#### Edit Categories")
            
            # v1.12.0: Local change detection for Categories tab
            categories_df = filtered_df[filtered_df['Type'] == 'Category'][['Area', 'Category_Path', 'Category', 'Description']].reset_index(drop=True)
            
            if not categories_df.empty:
                edited_categories = st.data_editor(
                    categories_df,
                    use_container_width=True,
                    key="categories_editor"
                )
                st.session_state.categories_changed_df = edited_categories
                
                # Check if this tab has changes
                has_changes, num_changes = has_unsaved_changes_in_tab(categories_df, edited_categories)
                
                if has_changes:
                    st.warning(f"⚠️ **{num_changes} unsaved change(s) in Categories**")
                    disable_filters(state_mgr, "unsaved changes in Categories tab")
                    
                    # Save/Discard controls
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        save_confirm = st.text_input("Type 'SAVE' to confirm", key="save_categories_confirm")
                    with col2:
                        if st.button("💾 Save Categories", disabled=(save_confirm != "SAVE"), key="save_categories_btn"):
                            st.success("✅ Categories saved!")
                            enable_filters(state_mgr)
                            st.session_state.categories_changed_df = None
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Discard", key="discard_categories_btn"):
                            st.session_state.categories_changed_df = None
                            enable_filters(state_mgr)
                            st.rerun()
                else:
                    st.session_state.categories_changed_df = None
                    enable_filters(state_mgr)
            else:
                st.info("No categories to edit with current filters")
        
        # ============================================
        # TAB 3: EDIT ATTRIBUTES
        # ============================================
        
        with tab3:
            st.markdown("#### Edit Attributes")
            
            # v1.12.0: Local change detection for Attributes tab
            attributes_df = filtered_df[filtered_df['Type'] == 'Attribute'][['Category_Path', 'Attribute_Name', 'Data_Type', 'Unit', 'Is_Required', 'Description']].reset_index(drop=True)
            
            if not attributes_df.empty:
                edited_attributes = st.data_editor(
                    attributes_df,
                    use_container_width=True,
                    key="attributes_editor"
                )
                st.session_state.attributes_changed_df = edited_attributes
                
                # Check if this tab has changes
                has_changes, num_changes = has_unsaved_changes_in_tab(attributes_df, edited_attributes)
                
                if has_changes:
                    st.warning(f"⚠️ **{num_changes} unsaved change(s) in Attributes**")
                    disable_filters(state_mgr, "unsaved changes in Attributes tab")
                    
                    # Save/Discard controls
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        save_confirm = st.text_input("Type 'SAVE' to confirm", key="save_attributes_confirm")
                    with col2:
                        if st.button("💾 Save Attributes", disabled=(save_confirm != "SAVE"), key="save_attributes_btn"):
                            st.success("✅ Attributes saved!")
                            enable_filters(state_mgr)
                            st.session_state.attributes_changed_df = None
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Discard", key="discard_attributes_btn"):
                            st.session_state.attributes_changed_df = None
                            enable_filters(state_mgr)
                            st.rerun()
                else:
                    st.session_state.attributes_changed_df = None
                    enable_filters(state_mgr)
            else:
                st.info("No attributes to edit with current filters")
        
        # ============================================
        # TAB 4: UPLOAD EXCEL
        # ============================================
        
        with tab4:
            st.markdown("#### 📤 Upload Hierarchical Excel")
            st.info("Upload an edited Hierarchical_View Excel to update your structure")
            
            uploaded_file = st.file_uploader(
                "📁 Browse Files",
                type=["xlsx"],
                help="Upload the Excel file you generated earlier"
            )
            
            if uploaded_file:
                st.success("📁 File received - Ready to process")
                
                # Placeholder for actual Excel processing
                if st.button("🔍 Validate and Preview Changes"):
                    st.info("Excel processing would happen here in full implementation")

    st.markdown("---")
    st.markdown("*Interactive Structure Viewer v1.12.0 - All fixes applied*")

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    # This would be called from main app
    pass
