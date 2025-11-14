"""
Bulk Import Module - SMART VERSION
===================================
Created: 2025-11-13 11:20 UTC
Last Modified: 2025-11-13 11:20 UTC
Python: 3.11

FEATURES:
- AUTO-DETECTS flat vs hierarchical categories
- Shows ACTUAL category names from database
- Works with both structures
- Duplicate detection
- Mixed categories support
- Excel direct input
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import json
from io import BytesIO


def get_structure_for_import(client, user_id: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Fetch complete structure"""
    try:
        areas_response = client.table('areas').select('*').eq('user_id', user_id).execute()
        categories_response = client.table('categories').select('*').eq('user_id', user_id).execute()
        attributes_response = client.table('attribute_definitions').select('*').eq('user_id', user_id).execute()
        
        return areas_response.data, categories_response.data, attributes_response.data
    except Exception as e:
        st.error(f"Error fetching structure: {str(e)}")
        return [], [], []


def build_category_lookup(categories: List[Dict]) -> Tuple[Dict[str, str], bool]:
    """
    Build lookup and detect if structure is hierarchical or flat
    
    Returns:
        Tuple of (lookup_dict, is_hierarchical)
    """
    cat_map = {cat['id']: cat for cat in categories}
    lookup = {}
    has_hierarchy = False
    
    def get_full_path(cat_id: str) -> str:
        """Build path - will be just name if flat"""
        cat = cat_map.get(cat_id)
        if not cat:
            return ""
        
        if cat['parent_category_id'] and cat['parent_category_id'] in cat_map:
            has_hierarchy = True
            parent_path = get_full_path(cat['parent_category_id'])
            return f"{parent_path} > {cat['name']}"
        return cat['name']
    
    # Build lookup
    for cat_id, cat in cat_map.items():
        # Check if this category has parent
        if cat.get('parent_category_id'):
            has_hierarchy = True
        
        # Build full path
        path = get_full_path(cat_id)
        lookup[path] = cat_id
        
        # Also add just name as fallback
        lookup[cat['name']] = cat_id
    
    return lookup, has_hierarchy


def build_attribute_map(attributes: List[Dict]) -> Dict[str, List[Dict]]:
    """Build map of category_id -> attributes"""
    attr_map = {}
    for attr in attributes:
        cat_id = attr['category_id']
        if cat_id not in attr_map:
            attr_map[cat_id] = []
        attr_map[cat_id].append(attr)
    return attr_map


def check_for_duplicates(client, user_id: str, validated_rows: List[Dict]) -> Dict[str, List[str]]:
    """Check for existing events with same category + date"""
    duplicates = {}
    
    try:
        checks = set()
        for row in validated_rows:
            checks.add((row['category_id'], row['event_date'].isoformat()))
        
        for cat_id, event_date in checks:
            response = client.table('events')\
                .select('id')\
                .eq('user_id', user_id)\
                .eq('category_id', cat_id)\
                .eq('event_date', event_date)\
                .execute()
            
            if response.data:
                key = f"{cat_id}|{event_date}"
                duplicates[key] = [e['id'] for e in response.data]
    except Exception as e:
        st.warning(f"Could not check duplicates: {str(e)}")
    
    return duplicates


def validate_import_file(df: pd.DataFrame, category_lookup: Dict, 
                        attribute_map: Dict, is_hierarchical: bool) -> Tuple[bool, List[str], List[Dict]]:
    """Validate import file"""
    errors = []
    validated_rows = []
    
    # Check required columns
    if 'Category' not in df.columns or 'Date' not in df.columns:
        errors.append("❌ Missing required columns: Category and/or Date")
        return False, errors, []
    
    # Show available categories with clear indication
    structure_type = "HIERARCHICAL (use > separator)" if is_hierarchical else "FLAT (no separator)"
    st.info(f"🔍 Database structure: **{structure_type}**")
    st.info(f"📋 Found {len(category_lookup)} category paths")
    
    with st.expander("📋 Available Category Names (click to expand) - COPY THESE EXACTLY!", expanded=True):
        unique_cats = {}
        for path, cat_id in category_lookup.items():
            if cat_id not in unique_cats:
                unique_cats[cat_id] = path
        
        st.markdown("**Use these EXACT names in your Category column:**")
        for path in sorted(unique_cats.values()):
            st.code(path)
        
        if is_hierarchical:
            st.warning("⚠️ Your structure is HIERARCHICAL - use format: 'Parent > Child'")
        else:
            st.success("✓ Your structure is FLAT - use simple names (no > separator)")
    
    # Validate rows
    for idx, row in df.iterrows():
        row_num = idx + 2
        row_errors = []
        
        # Category
        category_str = str(row['Category']).strip()
        if pd.isna(row['Category']) or not category_str:
            row_errors.append(f"Row {row_num}: ❌ Missing category")
            errors.extend(row_errors)
            continue
        
        # Try exact match
        if category_str not in category_lookup:
            row_errors.append(f"Row {row_num}: ❌ Unknown category '{category_str}'")
            
            # Find similar
            from difflib import get_close_matches
            matches = get_close_matches(category_str, category_lookup.keys(), n=3, cutoff=0.5)
            if matches:
                row_errors.append(f"           💡 Did you mean: '{matches[0]}'?")
            
            errors.extend(row_errors)
            continue
        
        category_id = category_lookup[category_str]
        
        # Date
        event_date = None
        date_formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y']
        
        date_str = str(row['Date']).strip()
        for fmt in date_formats:
            try:
                event_date = datetime.strptime(date_str, fmt).date()
                break
            except:
                continue
        
        if not event_date:
            try:
                event_date = pd.to_datetime(row['Date']).date()
            except:
                pass
        
        if not event_date:
            row_errors.append(f"Row {row_num}: ❌ Invalid date '{date_str}'")
            errors.extend(row_errors)
            continue
        
        # Attributes
        expected_attrs = attribute_map.get(category_id, [])
        attr_values = {}
        
        for attr in expected_attrs:
            attr_name = attr['name']
            
            if attr_name not in df.columns:
                if attr.get('is_required', False):
                    row_errors.append(f"Row {row_num}: ❌ Required '{attr_name}' missing")
                continue
            
            value = row[attr_name]
            
            if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                if attr.get('is_required', False):
                    row_errors.append(f"Row {row_num}: ❌ Required '{attr_name}' empty")
                continue
            
            # Type conversion
            try:
                if attr['data_type'] == 'number':
                    attr_values[attr['id']] = float(value)
                elif attr['data_type'] == 'boolean':
                    attr_values[attr['id']] = str(value).lower() in ['true', '1', 'yes', 'y'] if not isinstance(value, bool) else value
                elif attr['data_type'] == 'datetime':
                    attr_values[attr['id']] = pd.to_datetime(value).isoformat()
                else:
                    attr_values[attr['id']] = str(value)
            except Exception as e:
                row_errors.append(f"Row {row_num}: ❌ Invalid '{attr_name}': {str(e)}")
        
        # Comment
        comment = ""
        if 'Comment' in df.columns and not pd.isna(row['Comment']):
            comment = str(row['Comment'])
        
        if row_errors:
            errors.extend(row_errors)
        else:
            validated_rows.append({
                'category_id': category_id,
                'category_path': category_str,
                'event_date': event_date,
                'attributes': attr_values,
                'comment': comment,
                'row_number': row_num
            })
    
    is_valid = len(errors) == 0
    return is_valid, errors, validated_rows


def import_events(client, user_id: str, validated_rows: List[Dict], 
                 skip_duplicates: bool = False) -> Tuple[int, int, int, List[str]]:
    """Import events"""
    success_count = 0
    fail_count = 0
    skipped_count = 0
    errors = []
    
    duplicates = {}
    if skip_duplicates:
        duplicates = check_for_duplicates(client, user_id, validated_rows)
    
    for row in validated_rows:
        try:
            dup_key = f"{row['category_id']}|{row['event_date'].isoformat()}"
            if skip_duplicates and dup_key in duplicates:
                skipped_count += 1
                continue
            
            event_data = {
                'user_id': user_id,
                'category_id': row['category_id'],
                'event_date': row['event_date'].isoformat(),
                'comment': row['comment'] or None
            }
            
            event_response = client.table('events').insert(event_data).execute()
            
            if not event_response.data:
                errors.append(f"Row {row['row_number']}: Failed")
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
                    elif isinstance(value, str) and 'T' in value:
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
    
    return success_count, fail_count, skipped_count, errors


def generate_template(areas: List[Dict], categories: List[Dict], 
                     attributes: List[Dict], is_hierarchical: bool) -> BytesIO:
    """Generate template based on actual structure"""
    
    cat_map = {cat['id']: cat for cat in categories}
    
    def get_full_path(cat_id: str) -> str:
        cat = cat_map.get(cat_id)
        if not cat:
            return ""
        
        if is_hierarchical and cat.get('parent_category_id') and cat['parent_category_id'] in cat_map:
            parent_path = get_full_path(cat['parent_category_id'])
            return f"{parent_path} > {cat['name']}"
        return cat['name']
    
    # Get all attributes
    all_attrs = set(attr['name'] for attr in attributes)
    
    # Create examples
    example_rows = []
    for cat in categories[:5]:
        cat_path = get_full_path(cat['id'])
        cat_attrs = [a for a in attributes if a['category_id'] == cat['id']]
        
        row = {'Category': cat_path, 'Date': datetime.now().date().isoformat()}
        
        for attr in cat_attrs:
            row[attr['name']] = 0 if attr['data_type'] == 'number' else ''
        
        for attr_name in all_attrs:
            if attr_name not in row:
                row[attr_name] = ''
        
        row['Comment'] = ''
        example_rows.append(row)
    
    df = pd.DataFrame(example_rows)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Events', index=False)
        
        instructions = pd.DataFrame({
            'INSTRUCTIONS': [
                '',
                f'DATABASE STRUCTURE: {"HIERARCHICAL" if is_hierarchical else "FLAT"}',
                '',
                'CATEGORY FORMAT:',
                f'- {"Use > separator (e.g., Health > Sleep)" if is_hierarchical else "Use simple names (e.g., Sleep)"}',
                '- Copy exact names from Structure Viewer or Available Category Paths',
                '',
                'DATE FORMAT:',
                '- YYYY-MM-DD (recommended)',
                '- DD.MM.YYYY, DD/MM/YYYY also work',
                '',
                'ATTRIBUTES:',
                '- Fill only applicable columns',
                '- Leave non-applicable columns empty',
                '',
                'MIXED CATEGORIES:',
                '- You can mix different categories in same file',
                '- Each row can be different category type',
                '',
                'DUPLICATES:',
                '- Enable "Skip duplicates" to avoid same category+date',
                ''
            ]
        })
        instructions.to_excel(writer, sheet_name='README', index=False)
    
    output.seek(0)
    return output


def render_bulk_import(client, user_id: str):
    """Main render function"""
    
    st.title("📤 Bulk Import Events")
    st.markdown("Import multiple events from Excel or CSV")
    
    with st.spinner("Loading structure..."):
        areas, categories, attributes = get_structure_for_import(client, user_id)
    
    if not categories:
        st.warning("No structure defined")
        return
    
    category_lookup, is_hierarchical = build_category_lookup(categories)
    attribute_map = build_attribute_map(attributes)
    
    # Step 1: Download
    st.markdown("### 📥 Step 1: Download Template")
    template = generate_template(areas, categories, attributes, is_hierarchical)
    st.download_button(
        "⬇️ Download Excel Template",
        data=template,
        file_name=f"bulk_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # Step 2: Upload
    st.markdown("### 📤 Step 2: Upload File")
    uploaded = st.file_uploader("Choose Excel or CSV", type=['xlsx', 'xls', 'csv'])
    
    if uploaded:
        try:
            df = pd.read_csv(uploaded) if uploaded.name.endswith('.csv') else pd.read_excel(uploaded)
            st.success(f"✅ Loaded {len(df)} rows")
            
            with st.expander("📊 Preview", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)
            
            # Step 3: Validate
            st.markdown("### 🔍 Step 3: Validation")
            is_valid, errors, validated = validate_import_file(df, category_lookup, attribute_map, is_hierarchical)
            
            if errors:
                st.error(f"❌ Found {len(errors)} errors:")
                for err in errors[:25]:
                    st.write(err)
                if len(errors) > 25:
                    st.write(f"... {len(errors)-25} more")
                return
            
            st.success(f"✅ {len(validated)} rows validated!")
            
            with st.expander("📋 Preview Import", expanded=True):
                preview = [{
                    'Row': r['row_number'],
                    'Category': r['category_path'],
                    'Date': r['event_date'],
                    'Attrs': len(r['attributes'])
                } for r in validated[:15]]
                st.dataframe(pd.DataFrame(preview), use_container_width=True)
            
            # Step 4: Import
            st.markdown("### ✅ Step 4: Import")
            skip = st.checkbox("⚠️ Skip duplicates (same category + date)", value=False)
            st.warning(f"Will create up to {len(validated)} events")
            
            col1, col2, col3 = st.columns([1,1,1])
            with col2:
                if st.button("🚀 Import Events", type="primary", use_container_width=True):
                    success, fail, skipped, errs = import_events(client, user_id, validated, skip)
                    
                    st.markdown("---")
                    if fail == 0 and skipped == 0:
                        st.success(f"🎉 Imported {success} events!")
                        st.balloons()
                    else:
                        if success > 0:
                            st.success(f"✅ Imported: {success}")
                        if skipped > 0:
                            st.info(f"⏭️ Skipped: {skipped}")
                        if fail > 0:
                            st.error(f"❌ Failed: {fail}")
                    
                    if errs:
                        with st.expander("Errors"):
                            for e in errs:
                                st.write(e)
        
        except Exception as e:
            st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    st.write("Import by streamlit_app.py")
