"""
Bulk Import Module - FLEXIBLE SEPARATOR SUPPORT
================================================
Created: 2025-11-13 10:50 UTC
Last Modified: 2025-11-13 10:50 UTC
Python: 3.11

FEATURES:
- Supports both "→" and ">" as category separators
- Better error messages with available categories
- Multiple date format support
- Detailed validation feedback
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import json
from io import BytesIO


def normalize_category_path(path: str) -> str:
    """
    Normalize category path by converting all separators to →
    
    Supports:
    - "Health → Sleep"
    - "Health > Sleep"
    - "Health>Sleep" (no spaces)
    - "Health->Sleep"
    """
    if not path:
        return ""
    
    # Replace various separators with standard arrow
    path = path.replace(' > ', ' → ')
    path = path.replace('>', ' → ')
    path = path.replace(' -> ', ' → ')
    path = path.replace('->', ' → ')
    
    # Clean up multiple arrows or spaces
    import re
    path = re.sub(r'\s*→\s*', ' → ', path)
    path = re.sub(r'\s+', ' ', path)
    
    return path.strip()


def get_structure_for_import(client, user_id: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Fetch complete structure needed for import"""
    try:
        areas_response = client.table('areas').select('*').eq('user_id', user_id).execute()
        areas = areas_response.data
        
        categories_response = client.table('categories').select('*').eq('user_id', user_id).execute()
        categories = categories_response.data
        
        attributes_response = client.table('attribute_definitions').select('*').eq('user_id', user_id).execute()
        attributes = attributes_response.data
        
        return areas, categories, attributes
    except Exception as e:
        st.error(f"Error fetching structure: {str(e)}")
        return [], [], []


def build_category_lookup(categories: List[Dict]) -> Dict[str, str]:
    """
    Build lookup from category path to category ID
    Supports BOTH → and > separators
    """
    cat_map = {cat['id']: cat for cat in categories}
    lookup = {}
    
    def get_full_path(cat_id: str, separator: str = ' → ') -> str:
        cat = cat_map.get(cat_id)
        if not cat:
            return ""
        
        if cat['parent_category_id'] and cat['parent_category_id'] in cat_map:
            parent_path = get_full_path(cat['parent_category_id'], separator)
            return f"{parent_path}{separator}{cat['name']}"
        else:
            return cat['name']
    
    # Create lookups with BOTH separators
    for cat_id, cat in cat_map.items():
        # Standard arrow separator
        path_arrow = get_full_path(cat_id, ' → ')
        lookup[path_arrow] = cat_id
        
        # Greater-than separator (for compatibility)
        path_gt = get_full_path(cat_id, ' > ')
        lookup[path_gt] = cat_id
        
        # Just the name (for simple matching)
        lookup[cat['name']] = cat_id
    
    return lookup


def build_attribute_map(attributes: List[Dict]) -> Dict[str, List[Dict]]:
    """Build map of category_id -> list of attributes"""
    attr_map = {}
    for attr in attributes:
        cat_id = attr['category_id']
        if cat_id not in attr_map:
            attr_map[cat_id] = []
        attr_map[cat_id].append(attr)
    return attr_map


def validate_import_file(df: pd.DataFrame, category_lookup: Dict, 
                        attribute_map: Dict) -> Tuple[bool, List[str], List[Dict]]:
    """Validate import file with flexible category matching"""
    errors = []
    validated_rows = []
    
    # Check required columns
    required_cols = ['Category', 'Date']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        errors.append(f"❌ Missing required columns: {', '.join(missing_cols)}")
        return False, errors, []
    
    # Show available categories
    unique_categories = {}
    for path, cat_id in category_lookup.items():
        if cat_id not in unique_categories:
            unique_categories[cat_id] = path
    
    st.info(f"🔍 Found {len(unique_categories)} categories in database")
    with st.expander("📋 Available Category Paths (click to expand)"):
        for path in sorted(unique_categories.values()):
            st.text(path)
    
    # Validate each row
    for idx, row in df.iterrows():
        row_num = idx + 2
        row_errors = []
        
        # Validate category
        category_path_raw = str(row['Category']).strip()
        if pd.isna(row['Category']) or not category_path_raw:
            row_errors.append(f"Row {row_num}: ❌ Missing category")
            errors.extend(row_errors)
            continue
        
        # Normalize the category path
        category_path = normalize_category_path(category_path_raw)
        
        # Try to find match
        category_id = None
        
        # Try exact match with normalized path
        if category_path in category_lookup:
            category_id = category_lookup[category_path]
        else:
            # Try original path
            if category_path_raw in category_lookup:
                category_id = category_lookup[category_path_raw]
            else:
                # Try fuzzy matching
                from difflib import get_close_matches
                close_matches = get_close_matches(
                    category_path, 
                    list(unique_categories.values()), 
                    n=3, 
                    cutoff=0.6
                )
                
                row_errors.append(f"Row {row_num}: ❌ Unknown category '{category_path_raw}'")
                if close_matches:
                    row_errors.append(f"           💡 Did you mean: {close_matches[0]}")
                    row_errors.append(f"           (Use either → or > as separator)")
                
                errors.extend(row_errors)
                continue
        
        # Validate date with multiple formats
        event_date = None
        date_formats = [
            '%Y-%m-%d',      # 2025-11-10
            '%d.%m.%Y',      # 10.11.2025
            '%d/%m/%Y',      # 10/11/2025
            '%m/%d/%Y',      # 11/10/2025
            '%Y/%m/%d',      # 2025/11/10
        ]
        
        date_str = str(row['Date']).strip()
        for fmt in date_formats:
            try:
                event_date = datetime.strptime(date_str, fmt).date()
                break
            except:
                continue
        
        # Try pandas datetime as fallback
        if not event_date:
            try:
                event_date = pd.to_datetime(row['Date']).date()
            except:
                pass
        
        if not event_date:
            row_errors.append(f"Row {row_num}: ❌ Invalid date '{date_str}'")
            row_errors.append(f"           💡 Use: YYYY-MM-DD or DD.MM.YYYY")
            errors.extend(row_errors)
            continue
        
        # Collect attribute values
        attributes = attribute_map.get(category_id, [])
        attr_values = {}
        
        # Show attribute comparison
        expected_attrs = {attr['name']: attr for attr in attributes}
        csv_columns = [col for col in df.columns if col not in ['Category', 'Date', 'Comment']]
        
        missing_attrs = set(expected_attrs.keys()) - set(csv_columns)
        extra_attrs = set(csv_columns) - set(expected_attrs.keys())
        
        if row_num == 2:  # Only show once for first data row
            if missing_attrs:
                st.warning(f"⚠️ Expected attributes not in CSV: {', '.join(missing_attrs)}")
            if extra_attrs:
                st.warning(f"⚠️ CSV columns not matching any attribute: {', '.join(extra_attrs)}")
        
        # Process attributes
        for attr in attributes:
            attr_name = attr['name']
            if attr_name not in df.columns:
                if attr.get('is_required', False):
                    row_errors.append(f"Row {row_num}: ❌ Required field '{attr_name}' missing")
                continue
            
            value = row[attr_name]
            
            # Skip if empty
            if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                if attr.get('is_required', False):
                    row_errors.append(f"Row {row_num}: ❌ Required field '{attr_name}' is empty")
                continue
            
            # Type conversion
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
                row_errors.append(f"Row {row_num}: ❌ Invalid '{attr_name}': {str(e)}")
        
        # Get comment
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
    """Import validated events to database"""
    success_count = 0
    fail_count = 0
    errors = []
    
    for row in validated_rows:
        try:
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
            
            if row['attributes']:
                attr_records = []
                for attr_def_id, value in row['attributes'].items():
                    record = {
                        'event_id': event_id,
                        'attribute_definition_id': attr_def_id,
                        'user_id': user_id
                    }
                    
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
    """Generate Excel template - uses > separator for compatibility"""
    cat_map = {cat['id']: cat for cat in categories}
    
    def get_full_path(cat_id: str) -> str:
        cat = cat_map.get(cat_id)
        if not cat:
            return ""
        if cat['parent_category_id'] and cat['parent_category_id'] in cat_map:
            parent_path = get_full_path(cat['parent_category_id'])
            return f"{parent_path} > {cat['name']}"  # Use > for Excel compatibility
        else:
            return cat['name']
    
    example_rows = []
    for cat in categories[:3]:
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
            else:
                row[attr['name']] = ''
        
        row['Comment'] = 'Optional'
        example_rows.append(row)
    
    df = pd.DataFrame(example_rows)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Events', index=False)
        
        instructions = pd.DataFrame({
            'Instructions': [
                'CATEGORY FORMAT:',
                '- Use either ">" or "→" as separator',
                '- Examples: "Health > Sleep" OR "Health → Sleep"',
                '- Both formats work!',
                '',
                'DATE FORMAT:',
                '- YYYY-MM-DD (e.g., 2025-11-10)',
                '- DD.MM.YYYY (e.g., 10.11.2025)',
                '- DD/MM/YYYY (e.g., 10/11/2025)',
                '',
                'ATTRIBUTES:',
                '- Column names must match exactly',
                '- Check attribute names in Structure Viewer',
                '',
                'STEPS:',
                '1. Fill Category (with > or → separator)',
                '2. Fill Date',
                '3. Fill attribute values',
                '4. Optional Comment',
                '5. Save and upload'
            ]
        })
        instructions.to_excel(writer, sheet_name='README', index=False)
    
    output.seek(0)
    return output


def render_bulk_import(client, user_id: str):
    """Main render function for bulk import page"""
    
    st.title("📤 Bulk Import Events")
    st.markdown("Upload Excel or CSV file to import multiple events")
    
    # Info box about separators
    st.info("💡 **Tip:** Use either `>` or `→` as category separator - both work!")
    
    with st.spinner("Loading structure..."):
        areas, categories, attributes = get_structure_for_import(client, user_id)
    
    if not categories:
        st.warning("No structure defined. Please upload a template first.")
        return
    
    category_lookup = build_category_lookup(categories)
    attribute_map = build_attribute_map(attributes)
    
    # Download template
    st.markdown("### 📥 Step 1: Download Template")
    template_file = generate_template(areas, categories, attributes)
    st.download_button(
        label="⬇️ Download Excel Template",
        data=template_file,
        file_name=f"events_import_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # Upload section
    st.markdown("### 📤 Step 2: Upload Your File")
    uploaded_file = st.file_uploader(
        "Choose Excel or CSV file",
        type=['xlsx', 'xls', 'csv']
    )
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File loaded: {len(df)} rows")
            
            with st.expander("📊 Preview Data", expanded=True):
                st.dataframe(df.head(), use_container_width=True)
            
            # Validate
            st.markdown("### 🔍 Step 3: Validation")
            is_valid, errors, validated_rows = validate_import_file(
                df, category_lookup, attribute_map
            )
            
            if errors:
                st.error(f"❌ Found {len(errors)} errors:")
                for error in errors[:20]:
                    st.write(error)
                if len(errors) > 20:
                    st.write(f"... and {len(errors) - 20} more")
                return
            
            st.success(f"✅ {len(validated_rows)} rows validated!")
            
            # Preview
            with st.expander("📋 Preview Import", expanded=True):
                if validated_rows:
                    preview = [{
                        'Row': r['row_number'],
                        'Category': r['category_path'],
                        'Date': r['event_date'],
                        'Attrs': len(r['attributes']),
                        'Comment': '✓' if r['comment'] else ''
                    } for r in validated_rows[:10]]
                    st.dataframe(pd.DataFrame(preview), use_container_width=True)
            
            # Import
            st.markdown("### ✅ Step 4: Import")
            st.warning(f"⚠️ Creating {len(validated_rows)} events")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🚀 Import Events", type="primary", use_container_width=True):
                    success, fail, errs = import_events(client, user_id, validated_rows)
                    
                    if fail == 0:
                        st.success(f"🎉 Imported {success} events!")
                        st.balloons()
                    else:
                        st.warning(f"⚠️ {success} success, {fail} failed")
                        if errs:
                            with st.expander("Errors"):
                                for e in errs:
                                    st.write(e)
        
        except Exception as e:
            st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    st.write("Import by streamlit_app.py")
