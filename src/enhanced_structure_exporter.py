"""
Enhanced Structure Exporter - Excel with validation, formulas, and grouping

Features:
- 3-color system: Pink (read-only), Yellow (key identifiers), Blue (editable)
- Drop-down validation for Type, Data_Type, Is_Required
- Auto-calculated formulas for Level, Area
- Row grouping (collapsible by Area/Category) - EXPANDED by default
- Column grouping (B-C collapsed, others expanded)
- Header comments explaining each column's purpose
- Practical Help sheet with common scenarios and mistake avoidance
- Incremental upload support

**v3.0:** 3-color system, header comments, practical Help sheet

Dependencies: openpyxl, pandas, supabase
Last Modified: 2025-12-12 12:30 UTC
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime
from typing import Dict, List, Optional
import json


class EnhancedStructureExporter:
    """
    Enhanced Excel export with advanced features for structure editing.
    """
    
    def __init__(self, client, user_id: str, filter_area: Optional[str] = None, 
                 filter_category: Optional[str] = None):
        """
        Initialize exporter.
        
        Args:
            client: Supabase client instance
            user_id: Current user's UUID
            filter_area: Optional area filter (e.g., "Health" or "All Areas")
            filter_category: Optional category filter for drill-down (e.g., "Sleep" or "All Categories")
        """
        self.client = client
        self.user_id = user_id
        self.filter_area = filter_area if filter_area != "All Areas" else None
        self.filter_category = filter_category if filter_category != "All Categories" else None
        
        # Define colors (3-color system)
        # PINK = Auto-calculated, read-only (Type, Level, Area)
        self.PINK_FILL = PatternFill(start_color="FFE6F0", end_color="FFE6F0", fill_type="solid")
        # BLUE = Editable fields (Category, Attribute_Name, Data_Type, etc.)
        self.BLUE_FILL = PatternFill(start_color="E6F2FF", end_color="E6F2FF", fill_type="solid")
        # YELLOW/GOLD = Key identifier fields - edit only for NEW rows (Sort_Order, Category_Path)
        self.YELLOW_FILL = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        self.HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        self.BOLD_FONT = Font(bold=True, color="FFFFFF")
        self.NORMAL_FONT = Font(name='Calibri', size=11)
        
        # Header comments for each column
        self.HEADER_COMMENTS = {
            'A': "Type: Area, Category, or Attribute.\nDo NOT change for existing rows.",
            'B': "Level: Auto-calculated from Category_Path depth.\nRead-only.",
            'C': "Sort_Order: Position within parent element.\nCan edit to change display sequence.\nFor NEW rows: set desired position.",
            'D': "Area: Auto-calculated from Category_Path.\nRead-only.",
            'E': "⚠️ KEY FIELD - Category_Path\n\nUsed to IDENTIFY existing items in database.\n\n• For NEW rows: Set the full path (e.g., 'Area > Category > SubCat')\n• For EXISTING rows: DO NOT CHANGE!\n  Changing path creates a DUPLICATE instead of update.\n\n• Category (col F) must match the LAST part of this path.",
            'F': "Category: The category name.\n\n• Must match the LAST part of Category_Path\n• Example: If path is 'Finance > Auto > Gorivo'\n  then Category must be 'Gorivo'",
            'G': "Attribute_Name: Name of the attribute.\nRequired for Attribute type rows.",
            'H': "Data_Type: Type of data.\nValues: number, text, datetime, boolean, link, image",
            'I': "Unit: Unit of measurement.\nExample: kg, hours, EUR, km",
            'J': "Is_Required: Is this attribute mandatory?\nValues: TRUE or FALSE",
            'K': "Default_Value: Default value for new events.\nOptional.",
            'L': "Validation_Min: Minimum allowed value.\nFor number types only.",
            'M': "Validation_Max: Maximum allowed value.\nFor number types only.",
            'N': "Description: Documentation and notes.\nOptional but recommended."
        }
        
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
        Applies filters if specified.
        
        Returns:
            DataFrame with columns: Type, Level, Sort_Order, Area, Category_Path, 
                                   Category, Attribute_Name, Data_Type, Unit, 
                                   Is_Required, Default_Value, Validation_Min,
                                   Validation_Max, Description
        """
        rows = []
        
        # Load Areas (with optional filter)
        areas_query = self.client.table('areas') \
            .select('*') \
            .eq('user_id', self.user_id)
        
        # Apply Area filter if specified
        if self.filter_area:
            areas_query = areas_query.eq('name', self.filter_area)
        
        areas_response = areas_query.order('sort_order').execute()
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
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Apply category filter if specified (drill-down)
        if self.filter_category and not df.empty:
            # Filter to show:
            # 1. The selected category itself
            # 2. All its child categories (any level deep)
            # 3. All attributes belonging to selected category and its children
            mask = df['Category_Path'].str.contains(f"> {self.filter_category}", case=False, na=False, regex=False) | \
                   df['Category_Path'].str.endswith(self.filter_category, na=False)
            
            # Also include the Area row if it's shown (Type == 'Area')
            area_mask = df['Type'] == 'Area'
            
            df = df[mask | area_mask]
        
        return df
    
    
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
        Setup header row with styling and comments.
        Headers start at row 2 (row 1 is blank).
        Comments explain each column's purpose.
        """
        # Column definitions with color type:
        # 'pink' = auto-calculated read-only
        # 'yellow' = key identifier (edit only for new rows)
        # 'blue' = freely editable
        headers = [
            ('Type', 'pink'),              # A - Auto (Pink)
            ('Level', 'pink'),             # B - Auto (Pink)
            ('Sort_Order', 'yellow'),      # C - Key (Yellow) - position identifier
            ('Area', 'pink'),              # D - Auto (Pink)
            ('Category_Path', 'yellow'),   # E - Key (Yellow) - main identifier
            ('Category', 'blue'),          # F - Editable (Blue)
            ('Attribute_Name', 'blue'),    # G - Editable (Blue)
            ('Data_Type', 'blue'),         # H - Editable (Blue)
            ('Unit', 'blue'),              # I - Editable (Blue)
            ('Is_Required', 'blue'),       # J - Editable (Blue)
            ('Default_Value', 'blue'),     # K - Editable (Blue)
            ('Validation_Min', 'blue'),    # L - Editable (Blue)
            ('Validation_Max', 'blue'),    # M - Editable (Blue)
            ('Description', 'blue')        # N - Editable (Blue)
        ]
        
        # Column letters for comments
        col_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']
        
        # Headers in row 2 (row 1 is blank)
        for col_idx, (header, color_type) in enumerate(headers, start=1):
            cell = ws.cell(2, col_idx, header)  # Row 2, not 1
            cell.font = self.BOLD_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = self.CENTER_ALIGN
            cell.border = self.THIN_BORDER
            
            # Add comment to header cell
            col_letter = col_letters[col_idx - 1]
            if col_letter in self.HEADER_COMMENTS:
                comment = Comment(self.HEADER_COMMENTS[col_letter], "Events Tracker")
                comment.width = 300
                comment.height = 150
                cell.comment = comment
    
    
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
            
            # C: Sort_Order (from data) - YELLOW: key identifier, editable for new rows
            cell_c = ws.cell(row_idx, 3, row.Sort_Order)
            cell_c.fill = self.YELLOW_FILL
            cell_c.border = self.THIN_BORDER
            cell_c.alignment = self.CENTER_ALIGN
            
            # D: Area (FORMULA - extract first part before ">")
            area_formula = f'=TRIM(LEFT(E{row_idx},IFERROR(FIND(">",E{row_idx})-1,LEN(E{row_idx}))))'
            cell_d = ws.cell(row_idx, 4)
            cell_d.value = area_formula
            cell_d.fill = self.PINK_FILL
            cell_d.border = self.THIN_BORDER
            cell_d.alignment = self.LEFT_ALIGN
            
            # E: Category_Path (from data) - YELLOW: KEY identifier, DO NOT change for existing rows!
            cell_e = ws.cell(row_idx, 5, row.Category_Path)
            cell_e.fill = self.YELLOW_FILL
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
        All groups are EXPANDED by default (hidden=False).
        
        v2.2: Changed to expanded by default per user request.
        """
        current_area_start = None
        current_cat_starts = {}  # level -> start_row
        
        for idx, row in enumerate(df.itertuples(), start=3):  # Start at row 3
            if row.Type == "Area":
                # Close previous area group if exists
                if current_area_start and current_area_start < idx - 1:
                    ws.row_dimensions.group(current_area_start, idx - 1, outline_level=1, hidden=False)
                
                current_area_start = idx + 1  # Next row starts new group
                current_cat_starts = {}  # Reset category tracking
            
            elif row.Type == "Category":
                # Close previous category group at same or higher level
                level = row.Level
                for cat_level in list(current_cat_starts.keys()):
                    if cat_level >= level:
                        start = current_cat_starts[cat_level]
                        if start < idx:
                            ws.row_dimensions.group(start, idx - 1, outline_level=level + 1, hidden=False)
                        del current_cat_starts[cat_level]
                
                # Start new category group
                current_cat_starts[level] = idx + 1
        
        # Close remaining groups (expanded)
        max_row = ws.max_row
        if current_area_start and current_area_start <= max_row:
            ws.row_dimensions.group(current_area_start, max_row, outline_level=1, hidden=False)
        
        for level, start in current_cat_starts.items():
            if start <= max_row:
                ws.row_dimensions.group(start, max_row, outline_level=level + 1, hidden=False)
    
    
    def _add_column_grouping(self, ws):
        """
        Add column grouping to hide/show column groups.
        
        v2.2: Updated group visibility per user request:
        - B:C (Level, Sort_Order) = CLOSED (hidden=True)
        - F (Category) = OPEN (hidden=False)
        - H:M (Data_Type through Validation_Max) = OPEN (hidden=False)
        """
        # Group 1: B-C (Level, Sort_Order) - CLOSED
        for col in ['B', 'C']:
            ws.column_dimensions[col].outline_level = 1
            ws.column_dimensions[col].hidden = True  # Closed/collapsed
        
        # Group 2: F (Category) - OPEN
        ws.column_dimensions['F'].outline_level = 1
        ws.column_dimensions['F'].hidden = False  # Open/visible
        
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
        Add Help sheet with practical instructions for editing.
        Focused on common scenarios and avoiding mistakes.
        """
        ws = wb.create_sheet("Help")
        
        # Title
        ws.cell(1, 1, "EVENTS TRACKER - Structure Import/Export Guide").font = Font(bold=True, size=14)
        ws.cell(1, 1).fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        ws.cell(1, 1).font = Font(bold=True, size=14, color="FFFFFF")
        
        # Content - practical and focused
        help_content = [
            ("", ""),
            ("🎨 COLOR CODING (3 Colors):", ""),
            ("", ""),
            ("🟪 PINK = Auto-calculated, READ-ONLY", ""),
            ("   Columns: Type (A), Level (B), Area (D)", ""),
            ("   → Do NOT edit these columns", ""),
            ("", ""),
            ("🟨 YELLOW = KEY IDENTIFIER - Edit ONLY for NEW rows", ""),
            ("   Columns: Sort_Order (C), Category_Path (E)", ""),
            ("   → For EXISTING rows: DO NOT CHANGE!", ""),
            ("   → For NEW rows: Set the values correctly", ""),
            ("   ⚠️ Changing Category_Path for existing items creates DUPLICATES!", ""),
            ("", ""),
            ("🟦 BLUE = Freely EDITABLE", ""),
            ("   Columns: Category (F), Attribute_Name (G), Data_Type (H),", ""),
            ("            Unit (I), Is_Required (J), Default_Value (K),", ""),
            ("            Validation_Min (L), Validation_Max (M), Description (N)", ""),
            ("   → Edit these freely for existing or new rows", ""),
            ("", ""),
            ("═══════════════════════════════════════════════════════════════════", ""),
            ("", ""),
            ("📌 SCENARIO 1: Add New Category with Attributes", ""),
            ("─────────────────────────────────────────────────────", ""),
            ("You only need to add NEW rows - not the entire structure!", ""),
            ("", ""),
            ("Example - Add 'Novi auto' category under 'Finance > Domacinstvo > Automobili':", ""),
            ("", ""),
            ("Row 1: Type=Category, Category_Path='Finance > Domacinstvo > Automobili > Novi auto',", ""),
            ("       Category='Novi auto', Sort_Order=3", ""),
            ("", ""),
            ("Row 2: Type=Attribute, Category_Path='Finance > Domacinstvo > Automobili > Novi auto',", ""),
            ("       Category='Novi auto', Attribute_Name='Registracija', Data_Type='number'", ""),
            ("", ""),
            ("Row 3: Type=Attribute, Category_Path='Finance > Domacinstvo > Automobili > Novi auto',", ""),
            ("       Category='Novi auto', Attribute_Name='Gorivo', Data_Type='number'", ""),
            ("", ""),
            ("⚠️ IMPORTANT: Category column (F) MUST match the LAST part of Category_Path!", ""),
            ("", ""),
            ("═══════════════════════════════════════════════════════════════════", ""),
            ("", ""),
            ("📌 SCENARIO 2: Edit Existing Item Properties", ""),
            ("─────────────────────────────────────────────────────", ""),
            ("1. Find the row by Category_Path", ""),
            ("2. Edit ONLY the BLUE columns (Description, Unit, Data_Type, etc.)", ""),
            ("3. DO NOT change Category_Path or Sort_Order!", ""),
            ("4. Upload the file", ""),
            ("", ""),
            ("═══════════════════════════════════════════════════════════════════", ""),
            ("", ""),
            ("📌 SCENARIO 3: Change Display Order", ""),
            ("─────────────────────────────────────────────────────", ""),
            ("To reorder items within the same parent:", ""),
            ("1. Edit the Sort_Order values (column C)", ""),
            ("2. Use consecutive numbers (1, 2, 3...)", ""),
            ("3. Items with lower Sort_Order appear first", ""),
            ("", ""),
            ("═══════════════════════════════════════════════════════════════════", ""),
            ("", ""),
            ("⚠️ COMMON MISTAKES TO AVOID:", ""),
            ("─────────────────────────────────────────────────────", ""),
            ("", ""),
            ("❌ MISTAKE 1: Category doesn't match Category_Path", ""),
            ("   Wrong: Path='Area > Cat > SubCat', Category='DifferentName'", ""),
            ("   Right: Path='Area > Cat > SubCat', Category='SubCat'", ""),
            ("   → Category MUST be the LAST part of the path!", ""),
            ("", ""),
            ("❌ MISTAKE 2: Changing Category_Path for existing item", ""),
            ("   This creates a NEW item instead of updating the existing one!", ""),
            ("   → To rename: Edit Category column (F), keep path unchanged", ""),
            ("   → To move: Use app UI instead (safer)", ""),
            ("", ""),
            ("❌ MISTAKE 3: Missing parent in hierarchy", ""),
            ("   Can't add 'Area > Cat > SubCat' if 'Area > Cat' doesn't exist!", ""),
            ("   → Add parent categories first, or use existing parents", ""),
            ("", ""),
            ("❌ MISTAKE 4: Duplicate Category_Path in upload", ""),
            ("   Each path must be unique in the file!", ""),
            ("", ""),
            ("❌ MISTAKE 5: Wrong Attribute parent reference", ""),
            ("   Attribute's Category_Path and Category must match its parent Category", ""),
            ("", ""),
            ("═══════════════════════════════════════════════════════════════════", ""),
            ("", ""),
            ("💡 TIPS:", ""),
            ("─────────────────────────────────────────────────────", ""),
            ("• Hover over column headers to see detailed explanations", ""),
            ("• You can upload ONLY new/changed rows - incremental upload works!", ""),
            ("• Parent elements must exist in database before adding children", ""),
            ("• Use Copy-Paste to duplicate rows, then modify the paths", ""),
            ("• For renaming categories, use the app UI - it's safer", ""),
            ("• For deleting items, use the app UI - Excel upload can't delete", ""),
            ("", ""),
            ("═══════════════════════════════════════════════════════════════════", ""),
            ("", ""),
            ("📋 COLUMN REFERENCE:", ""),
            ("─────────────────────────────────────────────────────", ""),
            ("A - Type: Area, Category, or Attribute", ""),
            ("B - Level: Hierarchy depth (0=Area, 1+=Categories)", ""),
            ("C - Sort_Order: Display position within parent", ""),
            ("D - Area: Auto-extracted from path", ""),
            ("E - Category_Path: Full hierarchy path (KEY IDENTIFIER)", ""),
            ("F - Category: Category name (must match end of path)", ""),
            ("G - Attribute_Name: Name for Attribute rows", ""),
            ("H - Data_Type: number, text, datetime, boolean, link, image", ""),
            ("I - Unit: Measurement unit (kg, EUR, hours, etc.)", ""),
            ("J - Is_Required: TRUE or FALSE", ""),
            ("K - Default_Value: Default for new events", ""),
            ("L - Validation_Min: Minimum value (numbers only)", ""),
            ("M - Validation_Max: Maximum value (numbers only)", ""),
            ("N - Description: Notes and documentation", ""),
            ("", ""),
            ("VERSION:", ""),
            ("Enhanced Structure Export v3.0 (3-color system)", ""),
            ("Generated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ""),
        ]
        
        # Write content
        for row_idx, (text, extra) in enumerate(help_content, start=2):
            cell = ws.cell(row_idx, 1, text)
            
            # Format sections based on content type
            if text and isinstance(text, str):
                # Section headers with emoji
                if text.startswith('🎨') or text.startswith('📌') or text.startswith('⚠️') or text.startswith('💡') or text.startswith('📋'):
                    cell.font = Font(bold=True, size=12)
                    cell.fill = PatternFill(start_color="E6F2FF", end_color="E6F2FF", fill_type="solid")
                # Color coding headers
                elif text.startswith('🟪') or text.startswith('🟨') or text.startswith('🟦'):
                    cell.font = Font(bold=True, size=11)
                # Divider lines
                elif text.startswith('═') or text.startswith('─'):
                    cell.font = Font(color="888888")
                # Mistake items
                elif text.startswith('❌'):
                    cell.font = Font(bold=True, color="CC0000")
                # Version info
                elif text.startswith('VERSION:'):
                    cell.font = Font(bold=True, size=10)
                    cell.fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
        
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
