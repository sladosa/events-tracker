"""
Bulk Import Module
==================
Created: 2025-11-13 09:30 UTC
Last Modified: 2025-11-13 09:30 UTC
Python: 3.11

Bulk import events from Excel/CSV with:
- Wide format support (one row = one event)
- Category path matching
- Comprehensive validation
- Detailed error reporting
- Preview before import
- Progress tracking
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import json
from io import BytesIO


def get_structure_for_import(client, user_id: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Fetch complete structure needed for import
    
    Returns:
        Tuple of (areas, categories, attributes)
    """
    try:
        # Get areas
        areas_response = client.table('areas')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        areas = areas_response.data
        
        # Get categories
        categories_response = client.table('categories')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        categories = categories_response.data
        
        # Get attributes
        attributes_response = client.table('attribute_definitions')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        attributes = attributes_response.data
        
        return areas, categories, attributes
    
    except Exception as e:
        st.error(f"Error fetching structure: {str(e)}")
        return [], [], []


def build_category_lookup(categories: List[Dict]) -> Dict[str, str]:
    """
    Build lookup from category path to category ID
    
    Returns:
        Dict mapping full path (e.g., "Fitness → Running → Trail Run") to category_id
    """
    cat_map = {cat['id']: cat for cat in categories}
    lookup = {}
    
    def get_full_path(cat_id: str) -> str:
        cat = cat_map.get(cat_id)
        if not cat:
            return ""
        
        if cat['parent_category_id'] and cat['parent_category_id'] in cat_map:
            parent_path = get_full_path(cat['parent_category_id'])
            return f"{parent_path} → {cat['name']}"
        else:
            return cat['name']
    
    for cat_id, cat in cat_map.items():
        path = get_full_path(cat_id)
        lookup[path] = cat_id
        # Also add just the name for simple matching
        lookup[cat['name']] = cat_id
    
    return lookup


def build_attribute_map(attributes: List[Dict]) -> Dict[str, Dict]:
    """
    Build map of category_id -> list of attributes
    
    Returns:
        Dict mapping category_id to list of attribute definitions
    """
    attr_map = {}
    for attr in attributes:
        cat_id = attr['category_id']
        if cat_id not in attr_map:
            attr_map[cat_id] = []
        attr_map[cat_id].append(attr)
    return attr_map


def validate_import_file(df: pd.DataFrame, category_lookup: Dict, 
                        attribute_map: Dict) -> Tuple[bool, List[str], List[Dict]]:
    """
    Validate import file structure and data
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str], validated_rows: List[Dict])
    """
    errors = []
    validated_rows = []
    
    # Check required columns
    required_cols = ['Category', 'Date']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return False, errors, []
    
    # Validate each row
    for idx, row in df.iterrows():
        row_num = idx + 2  # +2 for Excel row (header is row 1)
        row_errors = []
        
        # Validate category
        category_path = str(row['Category']).strip()
        if pd.isna(row['Category']) or not category_path:
            row_errors.append(f"Row {row_num}: Missing category")
            continue
        
        if category_path not in category_lookup:
            row_errors.append(f"Row {row_num}: Unknown category '{category_path}'")
            continue
        
        category_id = category_lookup[category_path]
        
        # Validate date
        try:
            if isinstance(row['Date'], str):
                event_date = pd.to_datetime(row['Date']).date()
            elif isinstance(row['Date'], datetime):
                event_date = row['Date'].date()
            elif isinstance(row['Date'], date):
                event_date = row['Date']
            else:
                event_date = pd.to_datetime(str(row['Date'])).date()
        except Exception as e:
            row_errors.append(f"Row {row_num}: Invalid date format - {str(e)}")
            continue
        
        # Collect attribute values
        attributes = attribute_map.get(category_id, [])
        attr_values = {}
        
        for attr in attributes:
            attr_name = attr['name']
            if attr_name in df.columns:
                value = row[attr_name]
                
                # Skip if NaN or empty
                if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                    if attr.get('is_required', False):
                        row_errors.append(f"Row {row_num}: Required field '{attr_name}' is empty")
                    continue
                
                # Type validation
                try:
                    if attr['data_type'] == 'number':
                        attr_values[attr['id']] = float(value)
                    elif attr['data_type'] == 'boolean':
                        if isinstance(value, bool):
                            attr_values[attr['id']] = value
                        else:
                            attr_values[attr['id']] = str(value).lower() in ['true', '1', 'yes', 'y']
                    elif attr['data_type'] == 'datetime':
                        dt = pd.to_datetime(value)
                        attr_values[attr['id']] = dt.isoformat()
                    else:
                        attr_values[attr['id']] = str(value)
                except Exception as e:
                    row_errors.append(f"Row {row_num}: Invalid value for '{attr_name}' - {str(e)}")
        
        # Get comment if exists
        comment = ""
        if 'Comment' in df.columns and not pd.isna(row['Comment']):
            comment = str(row['Comment'])
        
        if row_errors:
            errors.extend(row_errors)
        else:
            validated_rows.append({
                'category_id': category_id,
                'category_path': category_path,
                'event_date': event_date,
                'attributes': attr_values,
                'comment': comment,
                'row_number': row_num
            })
    
    is_valid = len(errors) == 0
    return is_valid, errors, validated_rows


def import_events(client, user_id: str, validated_rows: List[Dict]) -> Tuple[int, int, List[str]]:
    """
    Import validated events to database
    
    Returns:
        Tuple of (success_count: int, fail_count: int, errors: List[str])
    """
    success_count = 0
    fail_count = 0
    errors = []
    
    for row in validated_rows:
        try:
            # Create event
            event_data = {
                'user_id': user_id,
                'category_id': row['category_id'],
                'event_date': row['event_date'].isoformat(),
                'comment': row['comment'] or None
            }
            
            event_response = client.table('events').insert(event_data).execute()
            
            if not event_response.data:
                errors.append(f"Row {row['row_number']}: Failed to create event")
                fail_count += 1
                continue
            
            event_id = event_response.data[0]['id']
            
            # Create attribute records
            if row['attributes']:
                attr_records = []
                for attr_def_id, value in row['attributes'].items():
                    record = {
                        'event_id': event_id,
                        'attribute_definition_id': attr_def_id,
                        'user_id': user_id
                    }
                    
                    # Determine which column to use
                    if isinstance(value, bool):
                        record['value_boolean'] = value
                    elif isinstance(value, (int, float)):
                        record['value_number'] = value
                    elif isinstance(value, str) and 'T' in value and len(value) > 10:
                        record['value_datetime'] = value
                    else:
                        record['value_text'] = str(value)
                    
                    attr_records.append(record)
                
                if attr_records:
                    client.table('event_attributes').insert(attr_records).execute()
            
            success_count += 1
        
        except Exception as e:
            errors.append(f"Row {row['row_number']}: {str(e)}")
            fail_count += 1
    
    return success_count, fail_count, errors


def generate_template(areas: List[Dict], categories: List[Dict], 
                     attributes: List[Dict]) -> BytesIO:
    """
    Generate Excel template for bulk import
    
    Returns:
        BytesIO object containing Excel file
    """
    # Build category paths
    cat_map = {cat['id']: cat for cat in categories}
    
    def get_full_path(cat_id: str) -> str:
        cat = cat_map.get(cat_id)
        if not cat:
            return ""
        if cat['parent_category_id'] and cat['parent_category_id'] in cat_map:
            parent_path = get_full_path(cat['parent_category_id'])
            return f"{parent_path} → {cat['name']}"
        else:
            return cat['name']
    
    # Get all attribute names (unique)
    attr_names = set()
    for attr in attributes:
        attr_names.add(attr['name'])
    
    # Create example data
    example_rows = []
    for cat in categories[:3]:  # First 3 categories as examples
        cat_path = get_full_path(cat['id'])
        cat_attrs = [a for a in attributes if a['category_id'] == cat['id']]
        
        row = {
            'Category': cat_path,
            'Date': datetime.now().date().isoformat()
        }
        
        for attr in cat_attrs:
            if attr['data_type'] == 'number':
                row[attr['name']] = 0
            elif attr['data_type'] == 'boolean':
                row[attr['name']] = 'FALSE'
            elif attr['data_type'] == 'datetime':
                row[attr['name']] = datetime.now().isoformat()
            else:
                row[attr['name']] = ''
        
        row['Comment'] = 'Optional comment'
        example_rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(example_rows)
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Events', index=False)
        
        # Add instructions sheet
        instructions = pd.DataFrame({
            'Instructions': [
                '1. Fill in Category column with exact category path',
                '2. Fill in Date column (YYYY-MM-DD format)',
                '3. Fill in attribute columns as needed',
                '4. Add optional Comment',
                '5. Save and upload',
                '',
                'Category paths must match exactly (including arrows →)',
                'Example: "Fitness → Running → Trail Run"',
                '',
                'Date formats supported: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY'
            ]
        })
        instructions.to_excel(writer, sheet_name='README', index=False)
    
    output.seek(0)
    return output


def render_bulk_import(client, user_id: str):
    """Main render function for bulk import page"""
    
    st.title("📤 Bulk Import Events")
    st.markdown("Upload Excel or CSV file to import multiple events at once")
    
    # Fetch structure
    with st.spinner("Loading structure..."):
        areas, categories, attributes = get_structure_for_import(client, user_id)
    
    if not categories:
        st.warning("No structure defined. Please upload a template first.")
        return
    
    # Build lookup tables
    category_lookup = build_category_lookup(categories)
    attribute_map = build_attribute_map(attributes)
    
    # Download template button
    st.markdown("### 📥 Step 1: Download Template")
    st.info("💡 Download the template file to see the correct format")
    
    template_file = generate_template(areas, categories, attributes)
    st.download_button(
        label="⬇️ Download Excel Template",
        data=template_file,
        file_name=f"events_import_template_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # Upload section
    st.markdown("### 📤 Step 2: Upload Your File")
    uploaded_file = st.file_uploader(
        "Choose Excel or CSV file",
        type=['xlsx', 'xls', 'csv'],
        help="File should have Category, Date, and attribute columns"
    )
    
    if uploaded_file:
        try:
            # Read file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File loaded: {len(df)} rows")
            
            # Preview
            with st.expander("📊 Preview Data (first 5 rows)", expanded=True):
                st.dataframe(df.head(), use_container_width=True)
            
            # Validate
            st.markdown("### 🔍 Step 3: Validation")
            with st.spinner("Validating data..."):
                is_valid, errors, validated_rows = validate_import_file(
                    df, category_lookup, attribute_map
                )
            
            if errors:
                st.error(f"❌ Found {len(errors)} validation errors:")
                for error in errors[:10]:  # Show first 10
                    st.write(f"- {error}")
                if len(errors) > 10:
                    st.write(f"... and {len(errors) - 10} more errors")
                
                st.warning("Please fix errors and re-upload")
                return
            
            st.success(f"✅ All {len(validated_rows)} rows validated successfully!")
            
            # Preview validated data
            with st.expander("📋 Preview Import", expanded=True):
                preview_data = []
                for row in validated_rows[:10]:  # First 10
                    preview_data.append({
                        'Row': row['row_number'],
                        'Category': row['category_path'],
                        'Date': row['event_date'],
                        'Attributes': len(row['attributes']),
                        'Comment': '✓' if row['comment'] else ''
                    })
                st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
                
                if len(validated_rows) > 10:
                    st.caption(f"... and {len(validated_rows) - 10} more rows")
            
            # Import button
            st.markdown("### ✅ Step 4: Import")
            st.warning(f"⚠️ This will create {len(validated_rows)} new events in the database")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🚀 Import Events", type="primary", use_container_width=True):
                    with st.spinner("Importing events..."):
                        success_count, fail_count, import_errors = import_events(
                            client, user_id, validated_rows
                        )
                    
                    st.markdown("---")
                    if fail_count == 0:
                        st.success(f"🎉 Successfully imported {success_count} events!")
                        st.balloons()
                    else:
                        st.warning(f"⚠️ Imported {success_count} events, {fail_count} failed")
                        
                        if import_errors:
                            with st.expander("Error Details"):
                                for error in import_errors:
                                    st.write(f"- {error}")
        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.info("Make sure the file format is correct")


if __name__ == "__main__":
    st.write("This module should be imported by streamlit_app.py")
