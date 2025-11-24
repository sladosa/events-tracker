"""
Events Tracker - Excel Parser Module - ssl
=====================================
Created: 2025-11-07 13:11 UTC
Last Modified: 2025-11-15 18:30 UTC
Python: 3.11

Description:
Reads and validates Excel templates for the EAV metadata system.
Handles template parsing with Pydantic models and UUID validation.
"""
import pandas as pd
import json
from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel, Field, validator
import uuid


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class Area(BaseModel):
    """Area data model with validation."""
    uuid: str
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: int
    description: Optional[str] = None
    
    @validator('uuid')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid UUID: {v}")


class Category(BaseModel):
    """Category data model with validation."""
    uuid: str
    area_uuid: str
    parent_uuid: Optional[str] = None
    name: str
    description: Optional[str] = None
    level: int = Field(ge=1, le=10)
    sort_order: int
    
    @validator('uuid', 'area_uuid')
    def validate_uuid(cls, v):
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError(f"Invalid UUID: {v}")
        return v
    
    @validator('parent_uuid')
    def validate_parent_uuid(cls, v):
        if v is not None and pd.notna(v):
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError(f"Invalid parent UUID: {v}")
        return None


class Attribute(BaseModel):
    """Attribute data model with validation."""
    uuid: str
    category_uuid: str
    name: str
    data_type: str
    unit: Optional[str] = None
    is_required: bool = False
    default_value: Optional[str] = None
    validation_rules: str = "{}"
    sort_order: int
    
    @validator('uuid', 'category_uuid')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid UUID: {v}")
    
    @validator('data_type')
    def validate_data_type(cls, v):
        valid_types = ['number', 'text', 'datetime', 'boolean', 'link', 'image']
        if v not in valid_types:
            raise ValueError(f"Invalid data_type: {v}. Must be one of {valid_types}")
        return v
    
    @validator('validation_rules')
    def validate_json(cls, v):
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in validation_rules: {v}")


class ExcelParser:
    """Parser for Excel template files with comprehensive validation."""
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.areas: List[Area] = []
        self.categories: List[Category] = []
        self.attributes: List[Attribute] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def parse(self) -> Tuple[bool, List[str], List[str]]:
        """
        Parse Excel file and validate structure.
        
        Returns:
            Tuple of (success: bool, errors: List[str], warnings: List[str])
        """
        try:
            # Read all sheets
            xl_file = pd.ExcelFile(self.excel_path)
            
            # Check required sheets
            required_sheets = ['Areas', 'Categories', 'Attributes']
            missing_sheets = [s for s in required_sheets if s not in xl_file.sheet_names]
            if missing_sheets:
                self.errors.append(f"Missing required sheets: {', '.join(missing_sheets)}")
                return False, self.errors, self.warnings
            
            # Parse each sheet
            df_areas = pd.read_excel(self.excel_path, sheet_name='Areas')
            df_categories = pd.read_excel(self.excel_path, sheet_name='Categories')
            df_attributes = pd.read_excel(self.excel_path, sheet_name='Attributes')
            
            # Validate Areas
            self._validate_areas(df_areas)
            
            # Validate Categories
            self._validate_categories(df_categories)
            
            # Validate Attributes
            self._validate_attributes(df_attributes)
            
            # Cross-reference validation
            self._validate_references()
            
            # Check for orphaned records
            self._check_orphans()
            
            if self.errors:
                return False, self.errors, self.warnings
            
            return True, [], self.warnings
            
        except Exception as e:
            self.errors.append(f"Failed to parse Excel file: {str(e)}")
            return False, self.errors, self.warnings
    
    def _validate_areas(self, df: pd.DataFrame):
        """Validate Areas sheet."""
        required_cols = ['uuid', 'name', 'sort_order']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            self.errors.append(f"Areas sheet missing columns: {', '.join(missing_cols)}")
            return
        
        for idx, row in df.iterrows():
            try:
                area = Area(**row.to_dict())
                self.areas.append(area)
            except Exception as e:
                self.errors.append(f"Areas row {idx + 2}: {str(e)}")
        
        # Check for duplicate names
        names = [a.name for a in self.areas]
        duplicates = [n for n in names if names.count(n) > 1]
        if duplicates:
            self.warnings.append(f"Duplicate area names: {', '.join(set(duplicates))}")
        
        # Check for duplicate UUIDs
        uuids = [a.uuid for a in self.areas]
        dup_uuids = [u for u in uuids if uuids.count(u) > 1]
        if dup_uuids:
            self.errors.append(f"Duplicate area UUIDs: {', '.join(set(dup_uuids))}")
    
    def _validate_categories(self, df: pd.DataFrame):
        """Validate Categories sheet."""
        required_cols = ['uuid', 'area_uuid', 'name', 'level', 'sort_order']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            self.errors.append(f"Categories sheet missing columns: {', '.join(missing_cols)}")
            return
        
        for idx, row in df.iterrows():
            try:
                # Handle NaN in parent_uuid
                row_dict = row.to_dict()
                if pd.isna(row_dict.get('parent_uuid')):
                    row_dict['parent_uuid'] = None
                
                category = Category(**row_dict)
                self.categories.append(category)
            except Exception as e:
                self.errors.append(f"Categories row {idx + 2}: {str(e)}")
        
        # Check for duplicate UUIDs
        uuids = [c.uuid for c in self.categories]
        dup_uuids = [u for u in uuids if uuids.count(u) > 1]
        if dup_uuids:
            self.errors.append(f"Duplicate category UUIDs: {', '.join(set(dup_uuids))}")
        
        # Check parent-child relationships
        category_uuids = set(c.uuid for c in self.categories)
        for cat in self.categories:
            if cat.parent_uuid and cat.parent_uuid not in category_uuids:
                self.errors.append(
                    f"Category '{cat.name}' references non-existent parent: {cat.parent_uuid}"
                )
    
    def _validate_attributes(self, df: pd.DataFrame):
        """Validate Attributes sheet."""
        required_cols = ['uuid', 'category_uuid', 'name', 'data_type', 'sort_order']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            self.errors.append(f"Attributes sheet missing columns: {', '.join(missing_cols)}")
            return
        
        for idx, row in df.iterrows():
            try:
                # Handle NaN values in optional fields
                row_dict = row.to_dict()
                
                # Convert NaN to empty string for default_value
                if pd.isna(row_dict.get('default_value')):
                    row_dict['default_value'] = ''
                
                # Convert NaN to empty string for unit
                if pd.isna(row_dict.get('unit')):
                    row_dict['unit'] = ''
                
                attribute = Attribute(**row_dict)
                self.attributes.append(attribute)
            except Exception as e:
                self.errors.append(f"Attributes row {idx + 2}: {str(e)}")
        
        # Check for duplicate UUIDs
        uuids = [a.uuid for a in self.attributes]
        dup_uuids = [u for u in uuids if uuids.count(u) > 1]
        if dup_uuids:
            self.errors.append(f"Duplicate attribute UUIDs: {', '.join(set(dup_uuids))}")
    
    def _validate_references(self):
        """Validate foreign key references between entities."""
        area_uuids = set(a.uuid for a in self.areas)
        category_uuids = set(c.uuid for c in self.categories)
        
        # Check category -> area references
        for cat in self.categories:
            if cat.area_uuid not in area_uuids:
                self.errors.append(
                    f"Category '{cat.name}' references non-existent area: {cat.area_uuid}"
                )
        
        # Check attribute -> category references
        for attr in self.attributes:
            if attr.category_uuid not in category_uuids:
                self.errors.append(
                    f"Attribute '{attr.name}' references non-existent category: {attr.category_uuid}"
                )
    
    def _check_orphans(self):
        """Check for potentially orphaned records."""
        # Check for categories without attributes
        category_uuids_with_attrs = set(a.category_uuid for a in self.attributes)
        categories_without_attrs = [
            c.name for c in self.categories 
            if c.uuid not in category_uuids_with_attrs
        ]
        if categories_without_attrs:
            self.warnings.append(
                f"Categories without attributes: {', '.join(categories_without_attrs)}"
            )
    
    def get_summary(self) -> Dict:
        """Get summary of parsed data."""
        return {
            'areas_count': len(self.areas),
            'categories_count': len(self.categories),
            'attributes_count': len(self.attributes),
            'errors_count': len(self.errors),
            'warnings_count': len(self.warnings)
        }
