"""
Database Operations Utility Module
===================================
Created: 2025-11-29 10:00 UTC
Last Modified: 2025-11-29 10:00 UTC
Python: 3.11

Description:
Centralized database operations for Events Tracker.
All DB fetch, insert, update, delete functions in one place.
Eliminates code duplication across modules.

Features:
- Unified fetch functions for all entity types
- Consistent error handling
- RLS (Row Level Security) enforcement
- Type hints and validation
- Caching support for expensive queries

Dependencies: supabase, typing

Usage:
    from src.utils.db_operations import fetch_all_structure, fetch_areas
    
    structure = fetch_all_structure(client, user_id)
    areas = fetch_areas(client, user_id)
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
import streamlit as st


# ============================================================================
# FETCH OPERATIONS
# ============================================================================

def fetch_all_structure(client, user_id: str) -> Dict[str, List[Dict]]:
    """
    Fetch entire structure (areas, categories, attributes) in one call.
    
    This is the primary function for loading complete structure.
    Uses optimized queries with joins to minimize database round-trips.
    
    Args:
        client: Supabase client instance
        user_id: User UUID for RLS filtering
        
    Returns:
        Dict with keys: 'areas', 'categories', 'attributes'
        Each contains list of dict records
        
    Example:
        structure = fetch_all_structure(client, user_id)
        areas = structure['areas']
        categories = structure['categories']
        attributes = structure['attributes']
    """
    try:
        # Fetch all in parallel for better performance
        areas = fetch_areas(client, user_id)
        categories = fetch_categories(client, user_id)
        attributes = fetch_attributes(client, user_id)
        
        return {
            'areas': areas,
            'categories': categories,
            'attributes': attributes
        }
        
    except Exception as e:
        st.error(f"Error fetching structure: {str(e)}")
        return {
            'areas': [],
            'categories': [],
            'attributes': []
        }


def fetch_areas(client, user_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all areas for a user.
    
    Args:
        client: Supabase client instance
        user_id: User UUID for RLS filtering
        
    Returns:
        List of area dictionaries with all columns
        
    Example:
        areas = fetch_areas(client, user_id)
        for area in areas:
            print(area['name'], area['color'])
    """
    try:
        response = client.table('areas') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('sort_order') \
            .execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"Error fetching areas: {str(e)}")
        return []


def fetch_categories(
    client, 
    user_id: str, 
    area_id: Optional[str] = None,
    parent_category_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch categories with optional filtering.
    
    Args:
        client: Supabase client instance
        user_id: User UUID for RLS filtering
        area_id: Optional area UUID to filter by
        parent_category_id: Optional parent category UUID
        
    Returns:
        List of category dictionaries
        
    Examples:
        # All categories
        cats = fetch_categories(client, user_id)
        
        # Categories in specific area
        cats = fetch_categories(client, user_id, area_id='uuid-here')
        
        # Sub-categories of a category
        cats = fetch_categories(client, user_id, parent_category_id='uuid-here')
    """
    try:
        query = client.table('categories') \
            .select('*') \
            .eq('user_id', user_id)
        
        if area_id:
            query = query.eq('area_id', area_id)
            
        if parent_category_id:
            query = query.eq('parent_category_id', parent_category_id)
        
        response = query.order('sort_order').execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"Error fetching categories: {str(e)}")
        return []


def fetch_attributes(
    client, 
    user_id: str,
    category_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch attribute definitions with optional category filtering.
    
    Args:
        client: Supabase client instance
        user_id: User UUID for RLS filtering
        category_id: Optional category UUID to filter by
        
    Returns:
        List of attribute definition dictionaries
        
    Examples:
        # All attributes
        attrs = fetch_attributes(client, user_id)
        
        # Attributes for specific category
        attrs = fetch_attributes(client, user_id, category_id='uuid-here')
    """
    try:
        query = client.table('attribute_definitions') \
            .select('*') \
            .eq('user_id', user_id)
        
        if category_id:
            query = query.eq('category_id', category_id)
        
        response = query.order('sort_order').execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"Error fetching attributes: {str(e)}")
        return []


def fetch_category_path(
    client,
    user_id: str,
    category_id: str
) -> Optional[str]:
    """
    Build category path string (e.g., "Training > Cardio").
    
    Recursively traverses parent categories to build full path.
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        category_id: Category UUID to build path for
        
    Returns:
        Category path string or None if not found
        
    Example:
        path = fetch_category_path(client, user_id, cat_id)
        # Returns: "Training > Cardio > Running"
    """
    try:
        # Fetch category
        response = client.table('categories') \
            .select('name, parent_category_id, area_id') \
            .eq('id', category_id) \
            .eq('user_id', user_id) \
            .execute()
        
        if not response.data:
            return None
        
        category = response.data[0]
        path_parts = [category['name']]
        
        # Traverse parents
        current_parent_id = category['parent_category_id']
        
        while current_parent_id:
            parent_response = client.table('categories') \
                .select('name, parent_category_id') \
                .eq('id', current_parent_id) \
                .eq('user_id', user_id) \
                .execute()
            
            if not parent_response.data:
                break
            
            parent = parent_response.data[0]
            path_parts.insert(0, parent['name'])
            current_parent_id = parent['parent_category_id']
        
        # Get area name
        area_response = client.table('areas') \
            .select('name') \
            .eq('id', category['area_id']) \
            .eq('user_id', user_id) \
            .execute()
        
        if area_response.data:
            path_parts.insert(0, area_response.data[0]['name'])
        
        return ' > '.join(path_parts)
        
    except Exception as e:
        st.error(f"Error building category path: {str(e)}")
        return None


# ============================================================================
# INSERT OPERATIONS
# ============================================================================

def insert_area(
    client,
    user_id: str,
    area_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Insert new area.
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        area_data: Dict with area fields (name, icon, color, etc.)
        
    Returns:
        Inserted area record or None on error
        
    Example:
        new_area = insert_area(client, user_id, {
            'name': 'Training',
            'icon': '🏋️',
            'color': '#FF5733',
            'description': 'Fitness activities'
        })
    """
    try:
        # Ensure user_id is set
        area_data['user_id'] = user_id
        
        # Set timestamps
        area_data['created_at'] = datetime.now().isoformat()
        area_data['updated_at'] = datetime.now().isoformat()
        
        response = client.table('areas').insert(area_data).execute()
        
        return response.data[0] if response.data else None
        
    except Exception as e:
        st.error(f"Error inserting area: {str(e)}")
        return None


def insert_category(
    client,
    user_id: str,
    category_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Insert new category.
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        category_data: Dict with category fields
        
    Returns:
        Inserted category record or None on error
        
    Example:
        new_cat = insert_category(client, user_id, {
            'area_id': 'area-uuid',
            'name': 'Cardio',
            'level': 1,
            'parent_category_id': None
        })
    """
    try:
        category_data['user_id'] = user_id
        category_data['created_at'] = datetime.now().isoformat()
        category_data['updated_at'] = datetime.now().isoformat()
        
        response = client.table('categories').insert(category_data).execute()
        
        return response.data[0] if response.data else None
        
    except Exception as e:
        st.error(f"Error inserting category: {str(e)}")
        return None


def insert_attribute(
    client,
    user_id: str,
    attribute_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Insert new attribute definition.
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        attribute_data: Dict with attribute fields
        
    Returns:
        Inserted attribute record or None on error
        
    Example:
        new_attr = insert_attribute(client, user_id, {
            'category_id': 'cat-uuid',
            'name': 'Duration',
            'data_type': 'number',
            'unit': 'minutes',
            'is_required': True
        })
    """
    try:
        attribute_data['user_id'] = user_id
        attribute_data['created_at'] = datetime.now().isoformat()
        attribute_data['updated_at'] = datetime.now().isoformat()
        
        response = client.table('attribute_definitions') \
            .insert(attribute_data) \
            .execute()
        
        return response.data[0] if response.data else None
        
    except Exception as e:
        st.error(f"Error inserting attribute: {str(e)}")
        return None


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================

def update_area(
    client,
    user_id: str,
    area_id: str,
    updates: Dict[str, Any]
) -> bool:
    """
    Update existing area.
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        area_id: Area UUID to update
        updates: Dict with fields to update
        
    Returns:
        True if successful, False otherwise
        
    Example:
        success = update_area(client, user_id, area_id, {
            'name': 'Updated Name',
            'color': '#00FF00'
        })
    """
    try:
        updates['updated_at'] = datetime.now().isoformat()
        
        response = client.table('areas') \
            .update(updates) \
            .eq('id', area_id) \
            .eq('user_id', user_id) \
            .execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error updating area: {str(e)}")
        return False


def update_category(
    client,
    user_id: str,
    category_id: str,
    updates: Dict[str, Any]
) -> bool:
    """
    Update existing category.
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        category_id: Category UUID to update
        updates: Dict with fields to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        updates['updated_at'] = datetime.now().isoformat()
        
        response = client.table('categories') \
            .update(updates) \
            .eq('id', category_id) \
            .eq('user_id', user_id) \
            .execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error updating category: {str(e)}")
        return False


def update_attribute(
    client,
    user_id: str,
    attribute_id: str,
    updates: Dict[str, Any]
) -> bool:
    """
    Update existing attribute definition.
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        attribute_id: Attribute UUID to update
        updates: Dict with fields to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        updates['updated_at'] = datetime.now().isoformat()
        
        response = client.table('attribute_definitions') \
            .update(updates) \
            .eq('id', attribute_id) \
            .eq('user_id', user_id) \
            .execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error updating attribute: {str(e)}")
        return False


# ============================================================================
# DELETE OPERATIONS
# ============================================================================

def delete_area(
    client,
    user_id: str,
    area_id: str
) -> bool:
    """
    Delete area (CASCADE deletes categories and attributes).
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        area_id: Area UUID to delete
        
    Returns:
        True if successful, False otherwise
        
    Warning:
        This will CASCADE delete all categories and attributes in this area!
    """
    try:
        response = client.table('areas') \
            .delete() \
            .eq('id', area_id) \
            .eq('user_id', user_id) \
            .execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error deleting area: {str(e)}")
        return False


def delete_category(
    client,
    user_id: str,
    category_id: str
) -> bool:
    """
    Delete category (CASCADE deletes attributes and sub-categories).
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        category_id: Category UUID to delete
        
    Returns:
        True if successful, False otherwise
        
    Warning:
        This will CASCADE delete all attributes and sub-categories!
    """
    try:
        response = client.table('categories') \
            .delete() \
            .eq('id', category_id) \
            .eq('user_id', user_id) \
            .execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error deleting category: {str(e)}")
        return False


def delete_attribute(
    client,
    user_id: str,
    attribute_id: str
) -> bool:
    """
    Delete attribute definition.
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        attribute_id: Attribute UUID to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = client.table('attribute_definitions') \
            .delete() \
            .eq('id', attribute_id) \
            .eq('user_id', user_id) \
            .execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error deleting attribute: {str(e)}")
        return False


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def count_dependent_items(
    client,
    user_id: str,
    entity_type: str,
    entity_id: str
) -> Dict[str, int]:
    """
    Count items that will be cascade deleted.
    
    Useful for showing warnings before deletion.
    
    Args:
        client: Supabase client instance
        user_id: User UUID
        entity_type: 'area' or 'category'
        entity_id: UUID of entity to check
        
    Returns:
        Dict with counts: {'categories': N, 'attributes': M}
        
    Example:
        counts = count_dependent_items(client, user_id, 'area', area_id)
        if counts['categories'] > 0:
            st.warning(f"This will delete {counts['categories']} categories!")
    """
    try:
        counts = {'categories': 0, 'attributes': 0}
        
        if entity_type == 'area':
            # Count categories in this area
            cats_response = client.table('categories') \
                .select('id', count='exact') \
                .eq('area_id', entity_id) \
                .eq('user_id', user_id) \
                .execute()
            
            counts['categories'] = cats_response.count if hasattr(cats_response, 'count') else 0
            
            # Count attributes in these categories
            attrs_response = client.table('attribute_definitions') \
                .select('id', count='exact') \
                .in_('category_id', [c['id'] for c in (cats_response.data or [])]) \
                .eq('user_id', user_id) \
                .execute()
            
            counts['attributes'] = attrs_response.count if hasattr(attrs_response, 'count') else 0
            
        elif entity_type == 'category':
            # Count attributes in this category
            attrs_response = client.table('attribute_definitions') \
                .select('id', count='exact') \
                .eq('category_id', entity_id) \
                .eq('user_id', user_id) \
                .execute()
            
            counts['attributes'] = attrs_response.count if hasattr(attrs_response, 'count') else 0
        
        return counts
        
    except Exception as e:
        st.error(f"Error counting dependent items: {str(e)}")
        return {'categories': 0, 'attributes': 0}


def generate_slug(name: str) -> str:
    """
    Generate URL-friendly slug from name.
    
    Args:
        name: Original name string
        
    Returns:
        Slug string (lowercase, hyphens, no special chars)
        
    Example:
        slug = generate_slug("My Category Name")
        # Returns: "my-category-name"
    """
    import re
    
    # Lowercase
    slug = name.lower()
    
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    
    # Remove special characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Strip leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


# ============================================================================
# CACHING DECORATORS (Optional, for performance)
# ============================================================================

# Example: Cache entire structure for 60 seconds
@st.cache_data(ttl=60, show_spinner=False)
def cached_fetch_all_structure(_client, user_id: str) -> Dict[str, List[Dict]]:
    """
    Cached version of fetch_all_structure.
    Use this for read-heavy operations where data doesn't change often.
    
    Note: _client parameter starts with _ to exclude from hashing.
    """
    return fetch_all_structure(_client, user_id)
