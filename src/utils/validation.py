"""
Validation Utility Module
==========================
Created: 2025-11-29 11:00 UTC
Last Modified: 2025-11-29 11:00 UTC
Python: 3.11

Description:
Data validation utilities for Events Tracker.
Pydantic models and custom validators for all entity types.

Features:
- Pydantic models for Areas, Categories, Attributes
- Custom validation rules
- Error message generation
- Data sanitization

Dependencies: pydantic, typing

Usage:
    from src.utils.validation import AreaValidator, validate_area_data
    
    errors = validate_area_data(area_dict)
    if errors:
        for error in errors:
            st.error(error)
"""

from pydantic import BaseModel, Field, validator, ValidationError
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class AreaModel(BaseModel):
    """Pydantic model for Area validation."""
    
    name: str = Field(..., min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=10)
    color: Optional[str] = Field(None, max_length=7)
    description: Optional[str] = Field(None, max_length=500)
    sort_order: int = Field(..., ge=0)
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('color')
    def valid_color(cls, v):
        if v and not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color must be in hex format (#RRGGBB)')
        return v
    
    class Config:
        extra = 'ignore'  # Ignore extra fields


class CategoryModel(BaseModel):
    """Pydantic model for Category validation."""
    
    name: str = Field(..., min_length=1, max_length=100)
    area_id: str = Field(..., min_length=36, max_length=36)  # UUID
    parent_category_id: Optional[str] = Field(None, min_length=36, max_length=36)
    description: Optional[str] = Field(None, max_length=500)
    level: int = Field(..., ge=1, le=10)
    sort_order: int = Field(..., ge=0)
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('area_id', 'parent_category_id')
    def valid_uuid(cls, v):
        if v and not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', v, re.I):
            raise ValueError('Invalid UUID format')
        return v
    
    class Config:
        extra = 'ignore'


class AttributeModel(BaseModel):
    """Pydantic model for Attribute Definition validation."""
    
    name: str = Field(..., min_length=1, max_length=100)
    category_id: str = Field(..., min_length=36, max_length=36)  # UUID
    data_type: str = Field(..., regex='^(number|text|datetime|boolean|link|image)$')
    unit: Optional[str] = Field(None, max_length=50)
    is_required: bool = Field(default=False)
    default_value: Optional[str] = Field(None, max_length=255)
    validation_rules: Optional[Dict] = Field(default_factory=dict)
    sort_order: int = Field(..., ge=0)
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('unit')
    def unit_only_for_number(cls, v, values):
        """Unit should only be set for number type."""
        if v and values.get('data_type') != 'number':
            raise ValueError('Unit is only applicable for number data type')
        return v
    
    @validator('default_value')
    def default_value_not_for_link_image(cls, v, values):
        """Default value not allowed for link and image types."""
        if v and values.get('data_type') in ['link', 'image']:
            raise ValueError('Default value not applicable for link/image types')
        return v
    
    class Config:
        extra = 'ignore'


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_area_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate area data dictionary.
    
    Args:
        data: Dictionary with area fields
        
    Returns:
        List of error messages (empty if valid)
        
    Example:
        errors = validate_area_data({'name': 'Training', 'sort_order': 1})
        if errors:
            for error in errors:
                st.error(error)
    """
    errors = []
    
    try:
        AreaModel(**data)
    except ValidationError as e:
        for error in e.errors():
            field = error['loc'][0]
            message = error['msg']
            errors.append(f"{field}: {message}")
    
    return errors


def validate_category_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate category data dictionary.
    
    Args:
        data: Dictionary with category fields
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    try:
        CategoryModel(**data)
    except ValidationError as e:
        for error in e.errors():
            field = error['loc'][0]
            message = error['msg']
            errors.append(f"{field}: {message}")
    
    return errors


def validate_attribute_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate attribute definition data dictionary.
    
    Args:
        data: Dictionary with attribute fields
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    try:
        AttributeModel(**data)
    except ValidationError as e:
        for error in e.errors():
            field = error['loc'][0]
            message = error['msg']
            errors.append(f"{field}: {message}")
    
    # Additional business logic validation
    if data.get('data_type') in ['link', 'image']:
        if data.get('unit'):
            errors.append("Unit field should be empty for link/image types")
        if data.get('default_value'):
            errors.append("Default value should be empty for link/image types")
        if data.get('validation_rules', {}).get('min') or data.get('validation_rules', {}).get('max'):
            errors.append("Validation min/max should be empty for link/image types")
    
    if data.get('data_type') in ['text', 'boolean']:
        if data.get('validation_rules', {}).get('min') or data.get('validation_rules', {}).get('max'):
            errors.append("Validation min/max should be empty for text/boolean types")
    
    return errors


# ============================================================================
# SANITIZATION FUNCTIONS
# ============================================================================

def sanitize_area_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize area data by removing None/empty values and trimming strings.
    
    Args:
        data: Raw area data
        
    Returns:
        Sanitized area data
        
    Example:
        clean_data = sanitize_area_data(form_data)
    """
    sanitized = {}
    
    for key, value in data.items():
        # Skip None values
        if value is None:
            continue
        
        # Trim strings
        if isinstance(value, str):
            value = value.strip()
            # Skip empty strings
            if value == '':
                continue
        
        sanitized[key] = value
    
    return sanitized


def sanitize_category_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize category data."""
    sanitized = {}
    
    for key, value in data.items():
        if value is None:
            continue
        
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                continue
        
        sanitized[key] = value
    
    return sanitized


def sanitize_attribute_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize attribute data based on data_type.
    
    Removes fields that shouldn't be set for certain data types.
    """
    sanitized = {}
    data_type = data.get('data_type')
    
    for key, value in data.items():
        # Skip None values
        if value is None:
            continue
        
        # Trim strings
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                continue
        
        # Smart field filtering based on data_type
        if data_type in ['link', 'image']:
            # Skip unit, default_value, validation for link/image
            if key in ['unit', 'default_value']:
                continue
            if key == 'validation_rules' and isinstance(value, dict):
                if 'min' in value or 'max' in value:
                    continue
        
        if data_type in ['text', 'boolean']:
            # Skip validation min/max for text/boolean
            if key == 'validation_rules' and isinstance(value, dict):
                value = {k: v for k, v in value.items() if k not in ['min', 'max']}
                if not value:  # Empty dict after filtering
                    continue
        
        sanitized[key] = value
    
    return sanitized


# ============================================================================
# VALIDATION RULE BUILDERS
# ============================================================================

def build_validation_rules(
    data_type: str,
    min_value: Optional[Any] = None,
    max_value: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Build validation_rules JSON based on data type and constraints.
    
    Args:
        data_type: Type of attribute (number, text, datetime, etc.)
        min_value: Minimum value/length
        max_value: Maximum value/length
        
    Returns:
        validation_rules dict for database storage
        
    Example:
        rules = build_validation_rules('number', min_value=0, max_value=100)
        # Returns: {'min': 0, 'max': 100}
    """
    rules = {}
    
    if data_type in ['number', 'datetime']:
        if min_value is not None:
            rules['min'] = min_value
        if max_value is not None:
            rules['max'] = max_value
    
    # For text, could add length constraints (future)
    # For boolean, link, image - no validation rules needed
    
    return rules


# ============================================================================
# BATCH VALIDATION
# ============================================================================

def validate_batch_areas(areas: List[Dict[str, Any]]) -> Dict[int, List[str]]:
    """
    Validate multiple areas at once.
    
    Args:
        areas: List of area data dictionaries
        
    Returns:
        Dict mapping index to list of errors
        
    Example:
        errors_by_index = validate_batch_areas(areas_list)
        for idx, errors in errors_by_index.items():
            st.error(f"Area {idx}: {errors}")
    """
    errors_by_index = {}
    
    for idx, area in enumerate(areas):
        errors = validate_area_data(area)
        if errors:
            errors_by_index[idx] = errors
    
    return errors_by_index


def validate_batch_categories(categories: List[Dict[str, Any]]) -> Dict[int, List[str]]:
    """Validate multiple categories at once."""
    errors_by_index = {}
    
    for idx, category in enumerate(categories):
        errors = validate_category_data(category)
        if errors:
            errors_by_index[idx] = errors
    
    return errors_by_index


def validate_batch_attributes(attributes: List[Dict[str, Any]]) -> Dict[int, List[str]]:
    """Validate multiple attributes at once."""
    errors_by_index = {}
    
    for idx, attribute in enumerate(attributes):
        errors = validate_attribute_data(attribute)
        if errors:
            errors_by_index[idx] = errors
    
    return errors_by_index


# ============================================================================
# EXCEL VALIDATION (for imports)
# ============================================================================

def validate_excel_row(
    row: Dict[str, Any],
    row_type: str
) -> List[str]:
    """
    Validate a single Excel row based on its type.
    
    Args:
        row: Dictionary representing one Excel row
        row_type: 'Area', 'Category', or 'Attribute'
        
    Returns:
        List of error messages
        
    Example:
        errors = validate_excel_row(excel_row, 'Area')
    """
    if row_type == 'Area':
        return validate_area_data(row)
    elif row_type == 'Category':
        return validate_category_data(row)
    elif row_type == 'Attribute':
        return validate_attribute_data(row)
    else:
        return [f"Unknown row type: {row_type}"]


# ============================================================================
# UTILITY VALIDATORS
# ============================================================================

def is_valid_uuid(uuid_string: str) -> bool:
    """
    Check if string is valid UUID format.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID, False otherwise
        
    Example:
        if is_valid_uuid(area_id):
            proceed()
    """
    if not uuid_string:
        return False
    
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, uuid_string, re.IGNORECASE))


def is_valid_hex_color(color: str) -> bool:
    """
    Check if string is valid hex color.
    
    Args:
        color: Color string to validate
        
    Returns:
        True if valid hex color (#RRGGBB), False otherwise
    """
    if not color:
        return False
    
    return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))


def is_valid_data_type(data_type: str) -> bool:
    """
    Check if data type is valid.
    
    Args:
        data_type: Data type string
        
    Returns:
        True if valid data type, False otherwise
    """
    valid_types = ['number', 'text', 'datetime', 'boolean', 'link', 'image']
    return data_type in valid_types


# ============================================================================
# ERROR MESSAGE FORMATTERS
# ============================================================================

def format_validation_errors(errors: List[str], prefix: str = "") -> str:
    """
    Format validation errors into readable string.
    
    Args:
        errors: List of error messages
        prefix: Optional prefix for each error
        
    Returns:
        Formatted error string
        
    Example:
        error_msg = format_validation_errors(errors, "Area validation")
        st.error(error_msg)
    """
    if not errors:
        return ""
    
    if prefix:
        header = f"{prefix}:\n"
    else:
        header = "Validation errors:\n"
    
    formatted = header + "\n".join(f"• {error}" for error in errors)
    
    return formatted


def get_friendly_error_message(field: str, error_type: str) -> str:
    """
    Get user-friendly error message for common validation errors.
    
    Args:
        field: Field name that failed validation
        error_type: Type of error (e.g., 'required', 'invalid')
        
    Returns:
        User-friendly error message
    """
    friendly_messages = {
        'name': {
            'required': 'Name is required',
            'empty': 'Name cannot be empty',
            'too_long': 'Name is too long (max 100 characters)'
        },
        'data_type': {
            'required': 'Data type is required',
            'invalid': 'Invalid data type. Must be: number, text, datetime, boolean, link, or image'
        },
        'color': {
            'invalid': 'Color must be in hex format (e.g., #FF5733)'
        },
        'sort_order': {
            'required': 'Sort order is required',
            'negative': 'Sort order must be 0 or greater'
        }
    }
    
    return friendly_messages.get(field, {}).get(error_type, f"{field}: {error_type}")
