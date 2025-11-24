"""
Enhanced Structure Exporter - Excel with validation, formulas, and grouping

Features:
- Color-coded columns (Pink=auto-calculated, Blue=user-editable)
- Drop-down validation for Type, Data_Type, Is_Required
- Auto-calculated formulas for Level, Area, Category_Path
- Row grouping (collapsible by Area/Category)
- Column grouping (hide attribute details)
- Description and Validation columns added
- Smart Category_Path handling

**UPDATED:** Headers in row 2, Sort_Order moved to column C, new grouping, auto filter

Dependencies: openpyxl, pandas, supabase
Last Modified: 2025-11-24 12:00 UTC
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime
from typing import Dict, List, Optional
import json


class EnhancedStructureExporter:
    """
    Enhanced Excel export with advanced features for structure editing.
    """
    
    def __init__(self, client, user_id: str):
        """
        Initialize exporter.
        
        Args:
            client: Supabase client instance
            user_id: Current user's UUID
        """
        self.client = client
        self.user_id = user_id
        
        # Define colors
        self.PINK_FILL = PatternFill(start_color="FFE6F0", end_color="FFE6F0", fill_type="solid")
        self.BLUE_FILL = PatternFill(start_color="E6F2FF", end_color="E6F2FF", fill_type="solid")
        self.HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        self.BOLD_FONT = Font(bold=True, color="FFFFFF")
        self.NORMAL_FONT = Font(name='Calibri', size=11)
        
        self.THIN_BORDER = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )
        
        self.CENTER_ALIGN = Alignment(horizontal='center', vertical='center')
        self.LEFT_ALIGN = Alignment(horizontal='left', vertical='center')
    
    
    def export_hierarchical_view(self, output_path: Optional[str] = None) -> str:
        """
        Export structure to enhanced Excel with all features.
        
        Args:
            output_path: Optional custom path. If None, auto-generates timestamped filename.
            
        Returns:
            Path to created Excel file
        """
        # Load structure from database
        df = self._load_hierarchical_data()
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Hierarchical_View"
        
        # Setup headers and styling (row 2)
        self._setup_headers(ws)
        
        # Populate data with formulas (starts row 3)
        self._populate_data(ws, df)
        
        # Add data validations
        self._add_data_validations(ws)
        
        # Add grouping
        self._add_row_grouping(ws, df)
        self._add_column_grouping(ws)
        
        # Auto-size columns
        self._auto_size_columns(ws)
        
        # Freeze panes (G3 - after Attribute_Name column, row 3)
        ws.freeze_panes = 'G3'
        
        # Add auto filter (A2:N...)
        ws.auto_filter.ref = f'A2:N{len(df) + 2}'  # +2 for header row
        
        # Add Help sheet
        self._add_help_sheet(wb)
        
        # Generate filename if not provided
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"structure_hierarchical_{timestamp}.xlsx"
        
        # Save
        wb.save(output_path)
        
        return output_path
    
    
    def _load_hierarchical_data(self) -> pd.DataFrame:
        """
        Load Areas, Categories, and Attributes from database in hierarchical format.
        
        Returns:
            DataFrame with columns: Type, Level, Sort_Order, Area, Category_Path, 
                                   Category, Attribute_Name, Data_Type, Unit, 
                                   Is_Required, Default_Value, Validation_Min,
                                   Validation_Max, Description
        """
        rows = []
        
        # Load Areas
        areas_response = self.client.table('areas') \
            .select('*') \
            .eq('user_id', self.user_id) \
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
                'Description': area.get('description', '')
            })
            
            # Load Categories for this Area
            self._load_categories_recursive(area['id'], area['name'], rows)
        
        return pd.DataFrame(rows)
    
    
    def _load_categories_recursive(self, area_id: str, area_name: str, 
                                   rows: List[Dict], parent_id: Optional[str] = None, 
                                   parent_path: str = '', level: int = 1):
        """
        Recursively load categories and their attributes.
        
        Args:
            area_id: Area UUID
            area_name: Area name for building paths
            rows: List to append rows to
            parent_id: Parent category UUID (None for top-level)
            parent_path: Parent's full path
            level: Current hierarchy level
        """
        # Query categories at this level
        query = self.client.table('categories') \
            .select('*') \
            .eq('user_id', self.user_id) \
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
                'Description': category.get('description', '')
            })
            
            # Load Attributes for this Category
            attributes_response = self.client.table('attribute_definitions') \
                .select('*') \
                .eq('user_id', self.user_id) \
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
                
                val_min = val_rules.get('min', '') if val_rules else ''
                val_max = val_rules.get('max', '') if val_rules else ''
                
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
                    'Is_Required': 'TRUE' if attr.get('is_required', False) else 'FALSE',
                    'Default_Value': attr.get('default_value', ''),
                    'Validation_Min': val_min,
                    'Validation_Max': val_max,
                    'Description': attr.get('description', '')
                })
            
            # Recursive call for subcategories
            if level < 10:  # Max depth
                self._load_categories_recursive(
                    area_id, area_name, rows, 
                    category['id'], cat_path, level + 1
                )
    
    
    def _setup_headers(self, ws):
        """
        Setup header row with styling.
        Headers start at row 2 (row 1 is blank).
        """
        # New column order: Sort_Order moved after Level
        headers = [
            ('Type', False),              # A - Auto (Pink)
            ('Level', False),             # B - Auto (Pink)
            ('Sort_Order', False),        # C - Auto (Pink) - MOVED HERE
            ('Area', False),              # D - Auto (Pink)
            ('Category_Path', False),     # E - Auto (Pink)
            ('Category', True),           # F - Editable (Blue)
            ('Attribute_Name', True),     # G - Editable (Blue)
            ('Data_Type', True),          # H - Editable (Blue)
            ('Unit', True),               # I - Editable (Blue)
            ('Is_Required', True),        # J - Editable (Blue)
            ('Default_Value', True),      # K - Editable (Blue)
            ('Validation_Min', True),     # L - Editable (Blue)
            ('Validation_Max', True),     # M - Editable (Blue)
            ('Description', True)         # N - Editable (Blue)
        ]
        
        # Headers in row 2 (row 1 is blank)
        for col_idx, (header, is_editable) in enumerate(headers, start=1):
            cell = ws.cell(2, col_idx, header)  # Row 2, not 1
            cell.font = self.BOLD_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = self.CENTER_ALIGN
            cell.border = self.THIN_BORDER
    
    
    def _populate_data(self, ws, df: pd.DataFrame):
        """
        Populate data rows with formulas for auto-calculated columns.
        Data starts at row 3 (row 1 blank, row 2 headers).
        
        Column mapping:
        A=Type, B=Level, C=Sort_Order, D=Area, E=Category_Path, F=Category,
        G=Attribute_Name, H=Data_Type, I=Unit, J=Is_Required, K=Default_Value,
        L=Validation_Min, M=Validation_Max, N=Description
        """
        for row_idx, row in enumerate(df.itertuples(index=False), start=3):  # Start at row 3
            # A: Type (from data)
            cell_a = ws.cell(row_idx, 1, row.Type)
            cell_a.fill = self.PINK_FILL
            cell_a.border = self.THIN_BORDER
            cell_a.alignment = self.CENTER_ALIGN
            
            # B: Level (FORMULA - calculated from Category_Path)
            if row.Type == 'Area':
                cell_b = ws.cell(row_idx, 2, 0)
            elif row.Type == 'Attribute':
                # Attribute level = parent category level + 1
                # Count ">" in Category_Path + 1
                level_formula = f'=LEN(E{row_idx})-LEN(SUBSTITUTE(E{row_idx},">",""))+1'
                cell_b = ws.cell(row_idx, 2)
                cell_b.value = level_formula
            else:  # Category
                level_formula = f'=LEN(E{row_idx})-LEN(SUBSTITUTE(E{row_idx},">",""))'
                cell_b = ws.cell(row_idx, 2)
                cell_b.value = level_formula
            
            cell_b.fill = self.PINK_FILL
            cell_b.border = self.THIN_BORDER
            cell_b.alignment = self.CENTER_ALIGN
            
            # C: Sort_Order (from data)
            cell_c = ws.cell(row_idx, 3, row.Sort_Order)
            cell_c.fill = self.PINK_FILL
            cell_c.border = self.THIN_BORDER
            cell_c.alignment = self.CENTER_ALIGN
            
            # D: Area (FORMULA - extract first part before ">")
            area_formula = f'=TRIM(LEFT(E{row_idx},IFERROR(FIND(">",E{row_idx})-1,LEN(E{row_idx}))))'
            cell_d = ws.cell(row_idx, 4)
            cell_d.value = area_formula
            cell_d.fill = self.PINK_FILL
            cell_d.border = self.THIN_BORDER
            cell_d.alignment = self.LEFT_ALIGN
            
            # E: Category_Path (from data)
            cell_e = ws.cell(row_idx, 5, row.Category_Path)
            cell_e.fill = self.PINK_FILL
            cell_e.border = self.THIN_BORDER
            cell_e.alignment = self.LEFT_ALIGN
            
            # F: Category (editable)
            cell_f = ws.cell(row_idx, 6, row.Category)
            cell_f.fill = self.BLUE_FILL
            cell_f.border = self.THIN_BORDER
            cell_f.alignment = self.LEFT_ALIGN
            
            # G: Attribute_Name (editable)
            cell_g = ws.cell(row_idx, 7, row.Attribute_Name)
            cell_g.fill = self.BLUE_FILL
            cell_g.border = self.THIN_BORDER
            cell_g.alignment = self.LEFT_ALIGN
            
            # H: Data_Type (editable, dropdown)
            cell_h = ws.cell(row_idx, 8, row.Data_Type)
            cell_h.fill = self.BLUE_FILL
            cell_h.border = self.THIN_BORDER
            cell_h.alignment = self.CENTER_ALIGN
            
            # I: Unit (editable)
            cell_i = ws.cell(row_idx, 9, row.Unit)
            cell_i.fill = self.BLUE_FILL
            cell_i.border = self.THIN_BORDER
            cell_i.alignment = self.CENTER_ALIGN
            
            # J: Is_Required (editable, dropdown)
            cell_j = ws.cell(row_idx, 10, row.Is_Required)
            cell_j.fill = self.BLUE_FILL
            cell_j.border = self.THIN_BORDER
            cell_j.alignment = self.CENTER_ALIGN
            
            # K: Default_Value (editable)
            cell_k = ws.cell(row_idx, 11, row.Default_Value)
            cell_k.fill = self.BLUE_FILL
            cell_k.border = self.THIN_BORDER
            cell_k.alignment = self.LEFT_ALIGN
            
            # L: Validation_Min (editable)
            cell_l = ws.cell(row_idx, 12, row.Validation_Min)
            cell_l.fill = self.BLUE_FILL
            cell_l.border = self.THIN_BORDER
            cell_l.alignment = self.CENTER_ALIGN
            
            # M: Validation_Max (editable)
            cell_m = ws.cell(row_idx, 13, row.Validation_Max)
            cell_m.fill = self.BLUE_FILL
            cell_m.border = self.THIN_BORDER
            cell_m.alignment = self.CENTER_ALIGN
            
            # N: Description (editable)
            cell_n = ws.cell(row_idx, 14, row.Description)
            cell_n.fill = self.BLUE_FILL
            cell_n.border = self.THIN_BORDER
            cell_n.alignment = self.LEFT_ALIGN
    
    
    def _add_data_validations(self, ws):
        """
        Add drop-down validations for specific columns.
        """
        max_row = ws.max_row
        
        # Type column (A) - Area, Category, Attribute
        type_dv = DataValidation(
            type="list",
            formula1='"Area,Category,Attribute"',
            allow_blank=False,
            showDropDown=True
        )
        ws.add_data_validation(type_dv)
        type_dv.add(f'A3:A{max_row + 100}')  # Start at row 3, extra rows for new entries
        
        # Data_Type column (H) - number, text, datetime, boolean, link
        datatype_dv = DataValidation(
            type="list",
            formula1='"number,text,datetime,boolean,link"',
            allow_blank=True,
            showDropDown=True
        )
        ws.add_data_validation(datatype_dv)
        datatype_dv.add(f'H3:H{max_row + 100}')  # Column H (was G)
        
        # Is_Required column (J) - TRUE, FALSE
        required_dv = DataValidation(
            type="list",
            formula1='"TRUE,FALSE"',
            allow_blank=True,
            showDropDown=True
        )
        ws.add_data_validation(required_dv)
        required_dv.add(f'J3:J{max_row + 100}')  # Column J (was I)
    
    
    def _add_row_grouping(self, ws, df: pd.DataFrame):
        """
        Add row grouping for collapsible Areas and Categories.
        All groups are collapsed by default.
        """
        current_area_start = None
        current_cat_starts = {}  # level -> start_row
        
        for idx, row in enumerate(df.itertuples(), start=3):  # Start at row 3
            if row.Type == "Area":
                # Close previous area group if exists
                if current_area_start and current_area_start < idx - 1:
                    ws.row_dimensions.group(current_area_start, idx - 1, outline_level=1, hidden=True)
                
                current_area_start = idx + 1  # Next row starts new group
                current_cat_starts = {}  # Reset category tracking
            
            elif row.Type == "Category":
                # Close previous category group at same or higher level
                level = row.Level
                for cat_level in list(current_cat_starts.keys()):
                    if cat_level >= level:
                        start = current_cat_starts[cat_level]
                        if start < idx:
                            ws.row_dimensions.group(start, idx - 1, outline_level=level + 1, hidden=True)
                        del current_cat_starts[cat_level]
                
                # Start new category group
                current_cat_starts[level] = idx + 1
        
        # Close remaining groups (collapsed)
        max_row = ws.max_row
        if current_area_start and current_area_start <= max_row:
            ws.row_dimensions.group(current_area_start, max_row, outline_level=1, hidden=True)
        
        for level, start in current_cat_starts.items():
            if start <= max_row:
                ws.row_dimensions.group(start, max_row, outline_level=level + 1, hidden=True)
    
    
    def _add_column_grouping(self, ws):
        """
        Add column grouping to hide/show column groups.
        
        New groups (all at outline_level=1):
        - B:C (Level, Sort_Order) = CLOSED (hidden=True)
        - F (Category) = CLOSED (hidden=True)
        - H:M (Data_Type through Validation_Max) = OPEN (hidden=False)
        """
        # Group 1: B-C (Level, Sort_Order) - CLOSED
        for col in ['B', 'C']:
            ws.column_dimensions[col].outline_level = 1
            ws.column_dimensions[col].hidden = True  # Closed/collapsed
        
        # Group 2: F (Category) - CLOSED
        ws.column_dimensions['F'].outline_level = 1
        ws.column_dimensions['F'].hidden = True  # Closed/collapsed
        
        # Group 3: H-M (Data_Type through Validation_Max) - OPEN
        for col in ['H', 'I', 'J', 'K', 'L', 'M']:
            ws.column_dimensions[col].outline_level = 1
            ws.column_dimensions[col].hidden = False  # Open/visible
    
    
    def _auto_size_columns(self, ws):
        """
        Auto-size columns based on content with max width limit.
        Columns A-D (Type, Level, Sort_Order, Area) use fixed width of 10.
        """
        for column_cells in ws.columns:
            length = 0
            column_letter = column_cells[0].column_letter
            
            for cell in column_cells:
                try:
                    if cell.value:
                        cell_length = len(str(cell.value))
                        if cell_length > length:
                            length = cell_length
                except:
                    pass
            
            # Columns A-D (Type, Level, Sort_Order, Area) - fixed width 10
            if column_letter in ['A', 'B', 'C', 'D']:
                adjusted_width = 10
            else:
                # Other columns - normal width with limits
                adjusted_width = min(length + 2, 50)  # Max 50 characters
                adjusted_width = max(adjusted_width, 10)  # Min 10 characters
            
            ws.column_dimensions[column_letter].width = adjusted_width



    def _add_help_sheet(self, wb):
        """
        Add Help sheet with instructions for editing.
        """
        ws = wb.create_sheet("Help")
        
        # Title
        ws.cell(1, 1, "EVENTS TRACKER - Enhanced Structure Export").font = Font(bold=True, size=14)
        ws.cell(1, 1).fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        ws.cell(1, 1).font = Font(bold=True, size=14, color="FFFFFF")
        
        # Content
        help_content = [
            ("", ""),
            ("WHAT IS THIS FILE?", ""),
            ("This Excel file contains your event tracking structure exported from the Events Tracker app.", ""),
            ("You can VIEW and EDIT this structure, then re-import it back into the app.", ""),
            ("", ""),
            ("COLOR CODING:", ""),
            ("PINK columns = AUTO-CALCULATED (Read-Only)", ""),
            ("  • Type: Area, Category, or Attribute", ""),
            ("  • Level: Calculated from Category_Path depth", ""),
            ("  • Sort_Order: Order within parent", ""),
            ("  • Area: Extracted from Category_Path", ""),
            ("  • Category_Path: Full hierarchical path", ""),
            ("", ""),
            ("BLUE columns = EDITABLE", ""),
            ("  • Category: Category name", ""),
            ("  • Attribute_Name: Attribute name", ""),
            ("  • Data_Type: number, text, datetime, boolean, link", ""),
            ("  • Unit: Unit of measurement (e.g., 'kg', 'hours')", ""),
            ("  • Is_Required: TRUE or FALSE", ""),
            ("  • Default_Value: Default value for new events", ""),
            ("  • Validation_Min: Minimum value (for number types)", ""),
            ("  • Validation_Max: Maximum value (for number types)", ""),
            ("  • Description: Documentation and notes", ""),
            ("", ""),
            ("WHAT CAN YOU EDIT?", ""),
            ("✅ YES - Edit these:", ""),
            ("  • Category names (column F)", ""),
            ("  • Attribute names (column G)", ""),
            ("  • Data types (column H) - use dropdown", ""),
            ("  • Units (column I)", ""),
            ("  • Required status (column J) - use dropdown", ""),
            ("  • Default values (column K)", ""),
            ("  • Validation Min/Max (columns L-M)", ""),
            ("  • Descriptions (column N)", ""),
            ("", ""),
            ("❌ NO - Do NOT edit:", ""),
            ("  • PINK columns (Type, Level, Sort_Order, Area, Category_Path)", ""),
            ("  • Row 1 (keep blank)", ""),
            ("  • Row 2 (headers)", ""),
            ("  • Delete rows (use app to delete instead)", ""),
            ("  • Add rows (use app to add instead)", ""),
            ("", ""),
            ("HOW TO USE GROUPS:", ""),
            ("Column Groups (buttons at top):", ""),
            ("  • Click [+] button to expand collapsed groups", ""),
            ("  • Click [-] button to collapse expanded groups", ""),
            ("  • Group 1 (B-C): Level, Sort_Order", ""),
            ("  • Group 2 (F): Category", ""),
            ("  • Group 3 (H-M): Attribute details", ""),
            ("", ""),
            ("Row Groups (buttons at left):", ""),
            ("  • Click [+] to expand Area or Category", ""),
            ("  • Click [-] to collapse Area or Category", ""),
            ("  • All groups start collapsed for cleaner view", ""),
            ("", ""),
            ("HOW TO FILTER:", ""),
            ("Auto Filter is enabled on all columns:", ""),
            ("  1. Click filter icon in header (row 2)", ""),
            ("  2. Select filter criteria", ""),
            ("  3. Click OK to apply", ""),
            ("  4. Click 'Clear Filter' to remove", ""),
            ("", ""),
            ("TIPS:", ""),
            ("  • Use Freeze Panes: Columns A-F and row 2 stay visible when scrolling", ""),
            ("  • Use Auto Filter: Quickly find specific Areas, Categories, or Attributes", ""),
            ("  • Use Groups: Hide unnecessary details for cleaner view", ""),
            ("  • Category_Path shows full hierarchy: 'Area > Category > Subcategory'", ""),
            ("  • Level 0 = Area, Level 1 = Top Category, Level 2+ = Subcategories", ""),
            ("", ""),
            ("VALIDATION RULES:", ""),
            ("Drop-down lists are provided for:", ""),
            ("  • Type (A): Area, Category, Attribute", ""),
            ("  • Data_Type (H): number, text, datetime, boolean, link", ""),
            ("  • Is_Required (J): TRUE, FALSE", ""),
            ("", ""),
            ("FORMULAS:", ""),
            ("These columns use formulas (don't edit):", ""),
            ("  • Level (B): =LEN(E3)-LEN(SUBSTITUTE(E3,">",""))", ""),
            ("  • Area (D): =TRIM(LEFT(E3,IFERROR(FIND(">",E3)-1,LEN(E3))))", ""),
            ("", ""),
            ("RE-IMPORTING:", ""),
            ("After editing, you can re-import this file:", ""),
            ("  1. Save your changes in Excel", ""),
            ("  2. Go to Events Tracker app", ""),
            ("  3. Navigate to 'Upload Template'", ""),
            ("  4. Upload this edited file", ""),
            ("  5. Review detected changes", ""),
            ("  6. Confirm to apply changes", ""),
            ("", ""),
            ("IMPORTANT NOTES:", ""),
            ("  • Always keep the structure intact (don't delete columns)", ""),
            ("  • Don't change PINK column values", ""),
            ("  • Use app features to add/delete Areas, Categories, Attributes", ""),
            ("  • This file is for viewing and light editing only", ""),
            ("  • For major changes, use the app interface", ""),
            ("", ""),
            ("SUPPORT:", ""),
            ("If you have questions or issues:", ""),
            ("  • Check the app Help section", ""),
            ("  • Review this Help sheet", ""),
            ("  • Contact support if needed", ""),
            ("", ""),
            ("VERSION:", ""),
            ("Enhanced Structure Export v2.1", ""),
            ("Generated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ""),
        ]
        
        # Write content
        for row_idx, (text, extra) in enumerate(help_content, start=2):
            cell = ws.cell(row_idx, 1, text)
            
            # Format sections - ensure text is a string before calling string methods
            if text and isinstance(text, str):
                if text.isupper() and text.endswith(':'): 
                    cell.font = Font(bold=True, size=12)
                    cell.fill = PatternFill(start_color="E6F2FF", end_color="E6F2FF", fill_type="solid")
                elif text.startswith('✅') or text.startswith('❌'):
                    cell.font = Font(bold=True)
                elif text.startswith('  •'):
                    cell.alignment = Alignment(indent=1)
        ws.column_dimensions['A'].width = 100
        
        # Freeze first row
        ws.freeze_panes = 'A2'

# Usage example 1
if __name__ == "__main__":
    # Example usage (in your Streamlit app):
    """
    from src.enhanced_structure_exporter import EnhancedStructureExporter
    
    # In your Streamlit UI:
    if st.button("📥 Download Enhanced Structure"):
        with st.spinner("Generating enhanced Excel..."):
            exporter = EnhancedStructureExporter(
                client=st.session_state.client,
                user_id=st.session_state.user_id
            )
            
            file_path = exporter.export_hierarchical_view()
            
            # Read file for download
            with open(file_path, 'rb') as f:
                excel_data = f.read()
            
            st.download_button(
                label="⬇️ Download Hierarchical View",
                data=excel_data,
                file_name=file_path,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    """
    pass
