"""
Bulk Import Module - COMPREHENSIVE VERSION
===========================================
Created: 2025-11-13 11:00 UTC
Last Modified: 2025-11-13 11:00 UTC
Python: 3.11

FEATURES:
1. Uses ONLY ">" separator (matches Hierarchical_View template)
2. Supports Excel AND CSV direct input
3. Duplicate detection and handling options
4. Mixed categories with different attributes in same file
5. Empty cells for non-applicable attributes are OK
6. Detailed validation with clear error messages

USAGE:
- Download template (uses ">" separator)
- Fill in Excel directly (no need for CSV)
- Mix different categories in same file
- Leave non-applicable attribute cells empty
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any, Set
import json
from io import BytesIO


def get_structure_for_import(client, user_id: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Fetch complete structure needed for import"""
    try:
        areas_response = client.table('areas').select('*').eq('user_id', user_id).execute()
        categories_response = client.table('categories').select('*').eq('user_id', user_id).execute()
        attributes_response = client.table('attribute_definitions').select('*').eq('user_id', user_id).execute()
        
        return areas_response.data, categories_response.data, attributes_response.data
    except Exception as e:
        st.error(f"Error fetching structure: {str(e)}")
        return [], [], []


def build_category_lookup(categories: List[Dict]) -> Dict[str, str]:
    """
    Build lookup from category path to category ID
    Uses ONLY ">" as separator (matches Hierarchical_View)
    """
    cat_map = {cat['id']: cat for cat in categories}
    lookup = {}
    
    def get_full_path(cat_id: str) -> str:
        """Build hierarchical path with > separator"""
        cat = cat_map.get(cat_id)
        if not cat:
            return ""
        
        if cat['parent_category_id'] and cat['parent_category_id'] in cat_map:
            parent_path = get_full_path(cat['parent_category_id'])
            return f"{parent_path} > {cat['name']}"
        else:
            return cat['name']
    
    # Create lookups with > separator ONLY
    for cat_id, cat in cat_map.items():
        path = get_full_path(cat_id)
        lookup[path] = cat_id
        
        # Also store just the name for simple categories
        if ' > ' not in path:
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


def check_for_duplicates(client, user_id: str, validated_rows: List[Dict]) -> Dict[str, List[int]]:
    """
    Check if events with same category and date already exist
    
    Returns:
        Dict mapping "category_id|date" to list of existing event IDs
    """
    duplicates = {}
    
    try:
        # Get unique category-date combinations from import
        checks = set()
        for row in validated_rows:
            key = f"{row['category_id']}|{row['event_date'].isoformat()}"
            checks.add((row['category_id'], row['event_date'].isoformat()))
        
        # Check each combination
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
        st.warning(f"Could not check for duplicates: {str(e)}")
    
    return duplicates


def validate_import_file(df: pd.DataFrame, category_lookup: Dict, 
                        attribute_map: Dict) -> Tuple[bool, List[str], List[Dict]]:
    """
    Validate import file
    
    KEY FEATURES:
    - Supports mixed categories in same file
    - Empty cells for non-applicable attributes are OK
    - Clear error messages for each row
    """
    errors = []
    validated_rows = []
    
    # Check required columns
    if 'Category' not in df.columns or 'Date' not in df.columns:
        errors.append("❌ Missing required columns: Category and/or Date")
        return False, errors, []
    
    # Show available categories
    st.info(f"🔍 Found {len(category_lookup)} category paths in database")
    with st.expander("📋 Available Category Paths (click to expand)"):
        for path in sorted(category_lookup.keys()):
            st.text(f"  {path}")
        st.caption("💡 Copy exact path from above to use in your file")
    
    # Collect all unique categories used in file
    categories_in_file = set()
    for idx, row in df.iterrows():
        if not pd.isna(row.get('Category')):
            categories_in_file.add(str(row['Category']).strip())
    
    st.info(f"📊 Your file uses {len(categories_in_file)} different categories")
    
    # Validate each row
    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel row number
        row_errors = []
        
        # 1. VALIDATE CATEGORY
        category_str = str(row['Category']).strip()
        if pd.isna(row['Category']) or not category_str:
            row_errors.append(f"Row {row_num}: ❌ Missing category")
            errors.extend(row_errors)
            continue
        
        # Try to find exact match
        if category_str not in category_lookup:
            row_errors.append(f"Row {row_num}: ❌ Unknown category '{category_str}'")
            
            # Find similar matches
            from difflib import get_close_matches
            matches = get_close_matches(category_str, category_lookup.keys(), n=3, cutoff=0.5)
            if matches:
                row_errors.append(f"           💡 Did you mean: '{matches[0]}'?")
            else:
                row_errors.append(f"           💡 Check 'Available Category Paths' above")
            
            errors.extend(row_errors)
            continue
        
        category_id = category_lookup[category_str]
        
        # 2. VALIDATE DATE
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
            row_errors.append(f"           💡 Use: YYYY-MM-DD or DD.MM.YYYY")
            errors.extend(row_errors)
            continue
        
        # 3. VALIDATE ATTRIBUTES
        # Get expected attributes for THIS category
        expected_attrs = attribute_map.get(category_id, [])
        attr_values = {}
        
        # Get all column names (excluding Category, Date, Comment)
        data_columns = [col for col in df.columns if col not in ['Category', 'Date', 'Comment']]
        
        # Process each expected attribute
        for attr in expected_attrs:
            attr_name = attr['name']
            
            # Check if this attribute column exists in file
            if attr_name not in df.columns:
                # Missing column - only error if REQUIRED
                if attr.get('is_required', False):
                    row_errors.append(f"Row {row_num}: ❌ Required attribute '{attr_name}' missing")
                continue
            
            # Get value from cell
            value = row[attr_name]
            
            # Empty cell - only error if REQUIRED
            if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                if attr.get('is_required', False):
                    row_errors.append(f"Row {row_num}: ❌ Required '{attr_name}' is empty")
                continue  # Empty but optional - skip
            
            # Type conversion and validation
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
        
        # 4. GET COMMENT (optional)
        comment = ""
        if 'Comment' in df.columns and not pd.isna(row['Comment']):
            comment = str(row['Comment'])
        
        # Add to validated rows if no errors
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
    
    # Show summary of mixed categories
    if is_valid and len(categories_in_file) > 1:
        st.success(f"✅ Mixed categories validated successfully! ({len(categories_in_file)} different types)")
    
    return is_valid, errors, validated_rows


def import_events(client, user_id: str, validated_rows: List[Dict], 
                 skip_duplicates: bool = False) -> Tuple[int, int, int, List[str]]:
    """
    Import validated events to database
    
    Returns:
        Tuple of (success_count, fail_count, skipped_count, errors)
    """
    success_count = 0
    fail_count = 0
    skipped_count = 0
    errors = []
    
    # Check for duplicates if requested
    duplicates = {}
    if skip_duplicates:
        duplicates = check_for_duplicates(client, user_id, validated_rows)
    
    for row in validated_rows:
        try:
            # Check if duplicate
            dup_key = f"{row['category_id']}|{row['event_date'].isoformat()}"
            if skip_duplicates and dup_key in duplicates:
                skipped_count += 1
                continue
            
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
                     attributes: List[Dict]) -> BytesIO:
    """Generate Excel template with ">" separator"""
    
    cat_map = {cat['id']: cat for cat in categories}
    
    def get_full_path(cat_id: str) -> str:
        cat = cat_map.get(cat_id)
        if not cat:
            return ""
        if cat['parent_category_id'] and cat['parent_category_id'] in cat_map:
            parent_path = get_full_path(cat['parent_category_id'])
            return f"{parent_path} > {cat['name']}"
        return cat['name']
    
    # Collect ALL unique attribute names
    all_attr_names = set()
    for attr in attributes:
        all_attr_names.add(attr['name'])
    
    # Create example rows for first few categories
    example_rows = []
    for cat in categories[:5]:  # First 5 as examples
        cat_path = get_full_path(cat['id'])
        cat_attrs = [a for a in attributes if a['category_id'] == cat['id']]
        
        row = {
            'Category': cat_path,
            'Date': datetime.now().date().isoformat()
        }
        
        # Add columns for THIS category's attributes
        for attr in cat_attrs:
            if attr['data_type'] == 'number':
                row[attr['name']] = 0
            elif attr['data_type'] == 'boolean':
                row[attr['name']] = 'FALSE'
            else:
                row[attr['name']] = ''
        
        # Add empty columns for OTHER attributes (will be ignored)
        for attr_name in all_attr_names:
            if attr_name not in row:
                row[attr_name] = ''  # Empty for non-applicable
        
        row['Comment'] = ''
        example_rows.append(row)
    
    df = pd.DataFrame(example_rows)
    
    # Create Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Events', index=False)
        
        # Instructions
        instructions = pd.DataFrame({
            'BULK IMPORT INSTRUCTIONS': [
                '',
                '═══════════════════════════════════════',
                '1. CATEGORY FORMAT',
                '═══════════════════════════════════════',
                '',
                '✓ Use ">" as separator (NOT arrow →)',
                '✓ Example: Health > Sleep',
                '✓ Example: Training > Cardio > Running',
                '✓ Copy exact paths from Structure Viewer',
                '',
                '═══════════════════════════════════════',
                '2. DATE FORMAT',
                '═══════════════════════════════════════',
                '',
                '✓ YYYY-MM-DD (recommended)',
                '✓ DD.MM.YYYY (also works)',
                '✓ DD/MM/YYYY (also works)',
                '',
                '═══════════════════════════════════════',
                '3. MIXED CATEGORIES - YES!',
                '═══════════════════════════════════════',
                '',
                '✓ You CAN mix different categories in same file',
                '✓ Each row can be different category',
                '✓ Leave non-applicable attribute cells EMPTY',
                '',
                'Example:',
                'Row 1: Health > Sleep (uses Sleep attrs)',
                'Row 2: Training > Cardio (uses Cardio attrs)',
                'Row 3: Health > Sleep (uses Sleep attrs again)',
                '',
                '═══════════════════════════════════════',
                '4. ATTRIBUTES',
                '═══════════════════════════════════════',
                '',
                '✓ Only fill attributes for that category',
                '✓ Leave other columns EMPTY',
                '✓ Empty = OK (unless marked Required)',
                '',
                '═══════════════════════════════════════',
                '5. DUPLICATES',
                '═══════════════════════════════════════',
                '',
                '✓ Same category + same date = duplicate',
                '✓ You can choose to skip or import anyway',
                '✓ Useful for: updating data, avoiding mistakes',
                '',
                '═══════════════════════════════════════',
                'TIPS:',
                '',
                '• Work directly in Excel (no CSV needed)',
                '• Download template first',
                '• Copy category paths from Structure Viewer',
                '• Test with 1-2 rows first',
                '• Check validation before importing',
                ''
            ]
        })
        instructions.to_excel(writer, sheet_name='README', index=False)
    
    output.seek(0)
    return output


def render_bulk_import(client, user_id: str):
    """Main render function for bulk import page"""
    
    st.title("📤 Bulk Import Events")
    st.markdown("""
    Import multiple events from **Excel** (recommended) or CSV file.
    
    ✅ Mix different categories in same file  
    ✅ Leave non-applicable attribute cells empty  
    ✅ Duplicate detection  
    """)
    
    with st.spinner("Loading structure..."):
        areas, categories, attributes = get_structure_for_import(client, user_id)
    
    if not categories:
        st.warning("No structure defined. Upload a template first.")
        return
    
    category_lookup = build_category_lookup(categories)
    attribute_map = build_attribute_map(attributes)
    
    # Step 1: Download template
    st.markdown("### 📥 Step 1: Download Template")
    st.info("💡 Work directly in Excel - no need to convert to CSV!")
    
    template_file = generate_template(areas, categories, attributes)
    st.download_button(
        label="⬇️ Download Excel Template",
        data=template_file,
        file_name=f"bulk_import_template_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # Step 2: Upload
    st.markdown("### 📤 Step 2: Upload Your File")
    uploaded_file = st.file_uploader(
        "Choose Excel (.xlsx) or CSV (.csv) file",
        type=['xlsx', 'xls', 'csv'],
        help="Excel format recommended for mixed categories"
    )
    
    if uploaded_file:
        try:
            # Read file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
                st.info("📄 CSV file detected")
            else:
                df = pd.read_excel(uploaded_file)
                st.success("📊 Excel file detected (recommended)")
            
            st.success(f"✅ Loaded {len(df)} rows")
            
            with st.expander("📊 Preview Data", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)
            
            # Step 3: Validation
            st.markdown("### 🔍 Step 3: Validation")
            is_valid, errors, validated_rows = validate_import_file(
                df, category_lookup, attribute_map
            )
            
            if errors:
                st.error(f"❌ Found {len(errors)} validation errors:")
                for error in errors[:25]:
                    st.write(error)
                if len(errors) > 25:
                    st.write(f"... and {len(errors) - 25} more errors")
                
                st.warning("Please fix errors and re-upload")
                return
            
            st.success(f"✅ All {len(validated_rows)} rows validated!")
            
            # Preview
            with st.expander("📋 Preview Import", expanded=True):
                if validated_rows:
                    preview = []
                    for r in validated_rows[:15]:
                        preview.append({
                            'Row': r['row_number'],
                            'Category': r['category_path'],
                            'Date': r['event_date'],
                            'Attrs': len(r['attributes']),
                            'Comment': '✓' if r['comment'] else ''
                        })
                    st.dataframe(pd.DataFrame(preview), use_container_width=True)
                    if len(validated_rows) > 15:
                        st.caption(f"... and {len(validated_rows) - 15} more rows")
            
            # Step 4: Import options
            st.markdown("### ✅ Step 4: Import")
            
            # Duplicate handling
            skip_dupes = st.checkbox(
                "⚠️ Skip duplicates (same category + date)",
                value=False,
                help="Check this to avoid importing events that already exist"
            )
            
            st.warning(f"This will create up to {len(validated_rows)} new events")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🚀 Import Events", type="primary", use_container_width=True):
                    with st.spinner("Importing..."):
                        success, fail, skipped, errs = import_events(
                            client, user_id, validated_rows, skip_dupes
                        )
                    
                    st.markdown("---")
                    if fail == 0 and skipped == 0:
                        st.success(f"🎉 Successfully imported {success} events!")
                        st.balloons()
                    elif skipped > 0:
                        st.success(f"✅ Imported {success} events")
                        st.info(f"⏭️ Skipped {skipped} duplicates")
                        if fail > 0:
                            st.warning(f"❌ Failed: {fail}")
                    else:
                        st.warning(f"⚠️ Success: {success}, Failed: {fail}")
                    
                    if errs:
                        with st.expander("Error Details"):
                            for e in errs:
                                st.write(e)
        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    st.write("Import by streamlit_app.py")
