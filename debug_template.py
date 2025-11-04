"""
DEBUG SCRIPT - Template & Parser Tester
Run this to see exactly what's in your template and why validation fails
"""
import pandas as pd
import sys
from pathlib import Path

# Add src to path (adjust if needed)
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 80)
print("TEMPLATE & PARSER DEBUG TOOL")
print("=" * 80)

# 1. Load template
template_path = input("\nEnter path to template (or drag & drop file): ").strip('"')

if not Path(template_path).exists():
    print(f"❌ File not found: {template_path}")
    sys.exit(1)

print(f"\n✅ Loading: {template_path}")

# 2. Read all sheets
try:
    areas_df = pd.read_excel(template_path, sheet_name='Areas')
    categories_df = pd.read_excel(template_path, sheet_name='Categories')
    attributes_df = pd.read_excel(template_path, sheet_name='Attributes')
    print("✅ All sheets loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Excel: {e}")
    sys.exit(1)

# 3. Inspect Attributes sheet in detail
print("\n" + "=" * 80)
print("ATTRIBUTES SHEET INSPECTION")
print("=" * 80)

print(f"\nTotal rows: {len(attributes_df)}")
print(f"Columns: {list(attributes_df.columns)}")

print("\n--- DEFAULT_VALUE COLUMN ANALYSIS ---")
if 'default_value' in attributes_df.columns:
    dv_col = attributes_df['default_value']
    
    print(f"Data type: {dv_col.dtype}")
    print(f"NaN count: {dv_col.isna().sum()} / {len(dv_col)}")
    print(f"Empty string count: {(dv_col == '').sum()}")
    
    print("\nFirst 5 values (with type):")
    for idx, val in enumerate(dv_col.head()):
        print(f"  Row {idx+2}: {repr(val)} (type: {type(val).__name__}, is NaN: {pd.isna(val)})")
    
    print("\nAll unique values:")
    for val in dv_col.unique():
        count = (dv_col == val).sum() if not pd.isna(val) else dv_col.isna().sum()
        print(f"  {repr(val)} → {count} times (type: {type(val).__name__})")
else:
    print("❌ default_value column NOT FOUND!")

print("\n--- UNIT COLUMN ANALYSIS ---")
if 'unit' in attributes_df.columns:
    unit_col = attributes_df['unit']
    
    print(f"Data type: {unit_col.dtype}")
    print(f"NaN count: {unit_col.isna().sum()} / {len(unit_col)}")
    print(f"Empty string count: {(unit_col == '').sum()}")
    
    print("\nFirst 5 values:")
    for idx, val in enumerate(unit_col.head()):
        print(f"  Row {idx+2}: {repr(val)} (is NaN: {pd.isna(val)})")
else:
    print("❌ unit column NOT FOUND!")

# 4. Test parser
print("\n" + "=" * 80)
print("TESTING PARSER")
print("=" * 80)

try:
    from excel_parser import ExcelParser
    print("✅ Parser imported successfully")
    
    # Check if parser has NaN handling
    import inspect
    parser_source = inspect.getsource(ExcelParser._validate_attributes)
    has_nan_handling = 'pd.isna' in parser_source and 'default_value' in parser_source
    
    print(f"\nParser has NaN handling for default_value: {'✅ YES' if has_nan_handling else '❌ NO'}")
    
    if not has_nan_handling:
        print("\n⚠️ WARNING: Parser does NOT have NaN handling!")
        print("The parser code needs to be updated.")
        print("\nExpected code snippet:")
        print("---")
        print("if pd.isna(row_dict.get('default_value')):")
        print("    row_dict['default_value'] = ''")
        print("---")
    
except ImportError as e:
    print(f"❌ Failed to import parser: {e}")
    print("\nMake sure you're running this script from the events-tracker directory!")
    sys.exit(1)

# 5. Try parsing
print("\n" + "=" * 80)
print("ATTEMPTING TO PARSE TEMPLATE")
print("=" * 80)

try:
    parser = ExcelParser(template_path)
    success, errors, warnings = parser.parse()
    
    if success:
        print("✅ VALIDATION PASSED!")
        print(f"  - Areas: {len(parser.areas)}")
        print(f"  - Categories: {len(parser.categories)}")
        print(f"  - Attributes: {len(parser.attributes)}")
    else:
        print("❌ VALIDATION FAILED!")
        print(f"\nErrors ({len(errors)}):")
        for err in errors:
            print(f"  • {err}")
        
        if warnings:
            print(f"\nWarnings ({len(warnings)}):")
            for warn in warnings:
                print(f"  • {warn}")
    
except Exception as e:
    print(f"❌ Parser crashed: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

# 6. Summary
print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

# Check for issues
issues = []

if 'default_value' in attributes_df.columns and attributes_df['default_value'].isna().any():
    issues.append("❌ Template has NaN values in default_value column")
    
if 'unit' in attributes_df.columns and attributes_df['unit'].isna().any():
    issues.append("❌ Template has NaN values in unit column")

try:
    from excel_parser import ExcelParser
    import inspect
    parser_source = inspect.getsource(ExcelParser._validate_attributes)
    if 'pd.isna' not in parser_source or 'default_value' not in parser_source:
        issues.append("❌ Parser does NOT handle NaN in default_value")
except:
    issues.append("❌ Cannot check parser code")

if not issues:
    print("✅ No issues detected - validation should work!")
else:
    print("Found issues:\n")
    for issue in issues:
        print(f"  {issue}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDED FIXES")
    print("=" * 80)
    
    if any('Template has NaN' in i for i in issues):
        print("\n1. FIX TEMPLATE:")
        print("   Open template in Excel/Python and replace NaN with empty strings")
        print("   OR use the garmin_fitness_template_WORKING.xlsx provided")
    
    if any('Parser does NOT handle' in i for i in issues):
        print("\n2. FIX PARSER:")
        print("   Make sure excel_parser.py has this code in _validate_attributes:")
        print("   ---")
        print("   row_dict = row.to_dict()")
        print("   if pd.isna(row_dict.get('default_value')):")
        print("       row_dict['default_value'] = ''")
        print("   if pd.isna(row_dict.get('unit')):")
        print("       row_dict['unit'] = ''")
        print("   ---")

print("\n" + "=" * 80)
print("Debug complete! Press Enter to exit...")
input()
