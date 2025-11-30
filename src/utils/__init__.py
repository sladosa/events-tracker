"""
Utils Package - Events Tracker
===============================
Created: 2025-11-29 10:00 UTC

Centralized utility modules for Events Tracker.

Modules:
- db_operations: Database CRUD operations
- excel_operations: Excel export/import
- ui_components: Reusable Streamlit components
"""

from .db_operations import (
    fetch_all_structure,
    fetch_areas,
    fetch_categories,
    fetch_attributes,
    insert_area,
    insert_category,
    insert_attribute,
    update_area,
    update_category,
    update_attribute,
    delete_area,
    delete_category,
    delete_attribute
)

from .excel_operations import (
    export_structure_to_excel,
    import_structure_from_excel,
    generate_filename
)

from .ui_components import (
    show_contextual_help,
    show_success,
    show_error,
    show_warning,
    show_info
)

from .validation import (
    validate_area_data,
    validate_category_data,
    validate_attribute_data,
    sanitize_area_data,
    sanitize_category_data,
    sanitize_attribute_data
)

__all__ = [
    'fetch_all_structure',
    'fetch_areas',
    'fetch_categories',
    'fetch_attributes',
    'insert_area',
    'insert_category',
    'insert_attribute',
    'update_area',
    'update_category',
    'update_attribute',
    'delete_area',
    'delete_category',
    'delete_attribute',
    'export_structure_to_excel',
    'import_structure_from_excel',
    'generate_filename',
    'show_contextual_help',
    'show_success',
    'show_error',
    'show_warning',
    'show_info',
    'validate_area_data',
    'validate_category_data',
    'validate_attribute_data',
    'sanitize_area_data',
    'sanitize_category_data',
    'sanitize_attribute_data'
]
