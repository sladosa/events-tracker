"""
Events Tracker - Excel Parser Module
=====================================
Created: 2025-11-07 13:11 UTC
Last Modified: 2025-11-15 18:30 UTC
Python: 3.11

Description:
Parses Excel templates that use names as identifiers.
Creates TemplateObject structures for rename detection.
Handles hierarchical structure import and validation.
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple
from rename_detector import TemplateObject


class ExcelTemplateParser:
    """
    Parses Excel templates with name-based references.
    Converts to TemplateObject structures for processing.
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.areas: List[TemplateObject] = []
        self.categories: List[TemplateObject] = []
        self.attributes: List[TemplateObject] = []
    
    def parse(self) -> Tuple[List[TemplateObject], List[TemplateObject], List[TemplateObject]]:
        """
        Parse Excel file and extract objects.
        
        Returns:
            (areas, categories, attributes) as TemplateObject lists
        """
        # Read sheets
        df_areas = pd.read_excel(self.filepath, sheet_name='Areas')
        df_categories = pd.read_excel(self.filepath, sheet_name='Categories')
        df_attributes = pd.read_excel(self.filepath, sheet_name='Attributes')
        
        # Parse Areas
        self.areas = self._parse_areas(df_areas)
        
        # Parse Categories
        self.categories = self._parse_categories(df_categories)
        
        # Parse Attributes
        self.attributes = self._parse_attributes(df_attributes)
        
        return self.areas, self.categories, self.attributes
    
    def _parse_areas(self, df: pd.DataFrame) -> List[TemplateObject]:
        """Parse Areas sheet"""
        areas = []
        
        for idx, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.get('area_name')):
                continue
            
            # Get UUID if present (from previous upload)
            uuid_val = row.get('area_id')
            uuid_str = str(uuid_val) if pd.notna(uuid_val) and uuid_val else None
            
            obj = TemplateObject(
                row_number=idx + 2,  # Excel row (1-indexed + header)
                name=str(row['area_name']),
                object_type='area',
                uuid=uuid_str,
                attributes={
                    'icon': str(row.get('icon', '')),
                    'color': str(row.get('color', '')),
                    'sort_order': int(row.get('sort_order', 0)),
                    'description': str(row.get('description', ''))
                }
            )
            areas.append(obj)
        
        return areas
    
    def _parse_categories(self, df: pd.DataFrame) -> List[TemplateObject]:
        """Parse Categories sheet"""
        categories = []
        
        for idx, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.get('category_name')) or pd.isna(row.get('area_name')):
                continue
            
            # Get UUID if present
            uuid_val = row.get('category_id')
            uuid_str = str(uuid_val) if pd.notna(uuid_val) and uuid_val else None
            
            # Get parent name (may be None for root categories)
            parent_val = row.get('parent_category')
            parent_name = str(parent_val) if pd.notna(parent_val) and parent_val else None
            
            # Get level
            level = int(row.get('level', 1))
            
            # Build hierarchical path
            area_name = str(row['area_name'])
            cat_name = str(row['category_name'])
            path_parts = [area_name]
            if parent_name:
                path_parts.append(parent_name)
            path_parts.append(cat_name)
            
            obj = TemplateObject(
                row_number=idx + 2,
                name=cat_name,
                object_type='category',
                parent_name=parent_name,
                level=level,
                uuid=uuid_str,
                area_name=area_name,
                attributes={
                    'sort_order': int(row.get('sort_order', 0)),
                    'description': str(row.get('description', ''))
                },
                hierarchical_path=" > ".join(path_parts)
            )
            categories.append(obj)
        
        return categories
    
    def _parse_attributes(self, df: pd.DataFrame) -> List[TemplateObject]:
        """Parse Attributes sheet"""
        attributes = []
        
        for idx, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.get('attribute_name')) or pd.isna(row.get('category_name')):
                continue
            
            # Get UUID if present
            uuid_val = row.get('attribute_id')
            uuid_str = str(uuid_val) if pd.notna(uuid_val) and uuid_val else None
            
            category_name = str(row['category_name'])
            attr_name = str(row['attribute_name'])
            
            # Parse validation_rules if present
            validation_rules = row.get('validation_rules', '{}')
            if pd.isna(validation_rules) or not validation_rules:
                validation_rules = '{}'
            
            obj = TemplateObject(
                row_number=idx + 2,
                name=attr_name,
                object_type='attribute',
                uuid=uuid_str,
                category_name=category_name,
                attributes={
                    'data_type': str(row.get('data_type', 'text')),
                    'unit': str(row.get('unit', '')),
                    'is_required': bool(row.get('is_required', False)),
                    'default_value': str(row.get('default_value', '')),
                    'validation_rules': str(validation_rules),
                    'sort_order': int(row.get('sort_order', 0))
                },
                hierarchical_path=f"{category_name} > {attr_name}"
            )
            attributes.append(obj)
        
        return attributes
    
    def get_summary(self) -> Dict:
        """Get summary of parsed data"""
        return {
            'areas_count': len(self.areas),
            'categories_count': len(self.categories),
            'attributes_count': len(self.attributes)
        }


def load_from_database(supabase_client, user_id: str) -> Tuple[
    List[TemplateObject], 
    List[TemplateObject], 
    List[TemplateObject]
]:
    """
    Load existing template structure from Supabase.
    Converts database records to TemplateObject format.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User UUID
    
    Returns:
        (areas, categories, attributes) as TemplateObject lists
    """
    areas = []
    categories = []
    attributes = []
    
    # Load Areas
    areas_data = supabase_client.table('areas')\
        .select('*')\
        .eq('user_id', user_id)\
        .order('sort_order')\
        .execute()
    
    for record in areas_data.data:
        obj = TemplateObject(
            row_number=0,  # Not from Excel
            name=record['name'],
            object_type='area',
            uuid=record['id'],
            attributes={
                'icon': record.get('icon', ''),
                'color': record.get('color', ''),
                'sort_order': record.get('sort_order', 0),
                'description': record.get('description', '')
            }
        )
        areas.append(obj)
    
    # Build area name lookup
    area_names = {record['id']: record['name'] for record in areas_data.data}
    
    # Load Categories
    categories_data = supabase_client.table('categories')\
        .select('*')\
        .eq('user_id', user_id)\
        .order('level, sort_order')\
        .execute()
    
    # Build category lookup for parent resolution
    category_map = {record['id']: record for record in categories_data.data}
    
    for record in categories_data.data:
        area_name = area_names.get(record['area_id'], 'Unknown')
        
        # Resolve parent name
        parent_name = None
        if record.get('parent_category_id'):
            parent_record = category_map.get(record['parent_category_id'])
            if parent_record:
                parent_name = parent_record['name']
        
        # Build path
        path_parts = [area_name]
        if parent_name:
            path_parts.append(parent_name)
        path_parts.append(record['name'])
        
        obj = TemplateObject(
            row_number=0,
            name=record['name'],
            object_type='category',
            parent_name=parent_name,
            level=record['level'],
            uuid=record['id'],
            area_name=area_name,
            attributes={
                'sort_order': record.get('sort_order', 0),
                'description': record.get('description', '')
            },
            hierarchical_path=" > ".join(path_parts)
        )
        categories.append(obj)
    
    # Build category name lookup
    category_names = {record['id']: record['name'] for record in categories_data.data}
    
    # Load Attributes
    attributes_data = supabase_client.table('attribute_definitions')\
        .select('*')\
        .eq('user_id', user_id)\
        .order('sort_order')\
        .execute()
    
    for record in attributes_data.data:
        category_name = category_names.get(record['category_id'], 'Unknown')
        
        obj = TemplateObject(
            row_number=0,
            name=record['name'],
            object_type='attribute',
            uuid=record['id'],
            category_name=category_name,
            attributes={
                'data_type': record.get('data_type', 'text'),
                'unit': record.get('unit', ''),
                'is_required': record.get('is_required', False),
                'default_value': record.get('default_value', ''),
                'validation_rules': str(record.get('validation_rules', '{}')),
                'sort_order': record.get('sort_order', 0)
            },
            hierarchical_path=f"{category_name} > {record['name']}"
        )
        attributes.append(obj)
    
    return areas, categories, attributes
