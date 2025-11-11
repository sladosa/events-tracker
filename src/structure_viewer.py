"""
Structure Viewer Module
========================
FIXED VERSION
Created: 2025-11-11 11:20 UTC
Last Modified: 2025-11-11 11:20 UTC

FIXES APPLIED:
1. ✅ All database fields added to dataclasses (user_id, template_id, slug, created_at, updated_at)
2. ✅ Field filtering before dataclass initialization
3. ✅ NO nested expanders - uses indentation for hierarchy
4. ✅ Complete error handling

This file displays hierarchical Area → Category → Attribute structure.
Replace your current src/structure_viewer.py with this file.
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Area:
    """Represents an Area in the structure - ALL database fields included"""
    id: str
    name: str
    sort_order: int
    user_id: Optional[str] = None
    template_id: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Category:
    """Represents a Category in the structure - ALL database fields included"""
    id: str
    name: str
    level: int
    sort_order: int
    area_id: Optional[str] = None
    parent_category_id: Optional[str] = None
    user_id: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    children: List['Category'] = field(default_factory=list)


@dataclass
class Attribute:
    """Represents an Attribute definition - ALL database fields included"""
    id: str
    name: str
    data_type: str
    sort_order: int
    category_id: Optional[str] = None
    user_id: Optional[str] = None
    unit: Optional[str] = None
    is_required: bool = False
    default_value: Optional[str] = None
    slug: Optional[str] = None
    validation_rules: Optional[Dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


def fetch_structure_data(client, user_id: str) -> tuple:
    """
    Fetches all structure data from Supabase
    
    Returns:
        tuple: (areas, categories, attributes)
    """
    try:
        # Fetch areas
        areas_response = client.table('areas')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('sort_order')\
            .execute()
        
        # Fetch categories with path
        categories_response = client.table('categories')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('level, sort_order')\
            .execute()
        
        # Fetch attributes
        attributes_response = client.table('attribute_definitions')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('sort_order')\
            .execute()
        
        return (
            areas_response.data,
            categories_response.data,
            attributes_response.data
        )
    except Exception as e:
        st.error(f"Error fetching structure: {str(e)}")
        return [], [], []


def build_category_tree(categories_data: List[Dict]) -> Dict[str, List[Category]]:
    """
    Builds a hierarchical tree of categories organized by area
    
    Returns:
        Dict[area_id, List[Category]]: Root categories for each area
    """
    # Create Category objects - IMPORTANT: Filter fields to match dataclass
    categories = {}
    for cat_data in categories_data:
        # Only pass fields that Category dataclass expects
        filtered_data = {
            'id': cat_data['id'],
            'name': cat_data['name'],
            'level': cat_data['level'],
            'sort_order': cat_data['sort_order'],
            'area_id': cat_data.get('area_id'),
            'parent_category_id': cat_data.get('parent_category_id'),
            'user_id': cat_data.get('user_id'),
            'description': cat_data.get('description'),
            'slug': cat_data.get('slug'),
            'path': cat_data.get('path'),
            'created_at': cat_data.get('created_at'),
            'updated_at': cat_data.get('updated_at'),
        }
        categories[cat_data['id']] = Category(**filtered_data)
    
    # Build parent-child relationships
    for cat in categories.values():
        if cat.parent_category_id and cat.parent_category_id in categories:
            parent = categories[cat.parent_category_id]
            parent.children.append(cat)
    
    # Group root categories by area
    roots_by_area = {}
    for cat in categories.values():
        if not cat.parent_category_id:  # Root category
            if cat.area_id not in roots_by_area:
                roots_by_area[cat.area_id] = []
            roots_by_area[cat.area_id].append(cat)
    
    return roots_by_area


def render_attribute_line(attr: Attribute) -> str:
    """Formats a single attribute for display"""
    parts = [f"**{attr.name}**"]
    
    # Data type with emoji
    type_emoji = {
        'number': '🔢',
        'text': '📝',
        'datetime': '📅',
        'boolean': '✓',
        'link': '🔗',
        'image': '🖼️'
    }
    emoji = type_emoji.get(attr.data_type, '📋')
    parts.append(f"{emoji} _{attr.data_type}_")
    
    if attr.unit:
        parts.append(f"[{attr.unit}]")
    
    if attr.is_required:
        parts.append("⚠️ _Required_")
    
    if attr.default_value:
        parts.append(f"(default: _{attr.default_value}_)")
    
    return " ".join(parts)


def render_category_recursive(
    category: Category, 
    attributes_map: Dict[str, List[Attribute]],
    indent_level: int = 0
):
    """
    Renders a category and its children using indentation
    NO nested expanders - uses containers and markdown instead
    
    Args:
        category: Category to render
        attributes_map: Map of category_id -> list of attributes
        indent_level: Current indentation level (0 = root)
    """
    indent = "  " * indent_level  # 2 spaces per level
    
    # Category header with level indicator
    if indent_level == 0:
        level_emoji = "📁"
    elif indent_level == 1:
        level_emoji = "📂"
    else:
        level_emoji = "📄"
    
    # Build category title
    title = f"{indent}{level_emoji} **{category.name}**"
    if category.level:
        title += f" _(Level {category.level})_"
    
    st.markdown(title)
    
    # Description
    if category.description:
        st.markdown(f"{indent}  💬 _{category.description}_")
    
    # Attributes for this category
    attrs = attributes_map.get(category.id, [])
    if attrs:
        st.markdown(f"{indent}  **Attributes ({len(attrs)}):**")
        for attr in sorted(attrs, key=lambda x: x.sort_order):
            st.markdown(f"{indent}    • {render_attribute_line(attr)}")
    else:
        st.markdown(f"{indent}  _No attributes defined_")
    
    # Show metadata ONLY for root categories (to avoid nested expanders)
    if indent_level == 0:
        with st.expander(f"🔍 Details for '{category.name}'", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.text(f"Category ID: {category.id}")
                st.text(f"Sort Order: {category.sort_order}")
            with col2:
                if category.path:
                    st.text(f"Path: {category.path}")
                if category.slug:
                    st.text(f"Slug: {category.slug}")
            
            # Show children count
            if category.children:
                st.info(f"Has {len(category.children)} direct subcategories")
    
    # Recursively render children with increased indentation
    if category.children:
        st.markdown(f"{indent}  **Subcategories ({len(category.children)}):**")
        for child in sorted(category.children, key=lambda x: x.sort_order):
            render_category_recursive(child, attributes_map, indent_level + 1)
        
        # Separator only after top-level categories
        if indent_level == 0:
            st.markdown("---")


def render_structure_viewer(client, user_id: str):
    """
    Main function to render the structure viewer
    FIXED: No nested expanders + all DB fields handled correctly
    """
    st.title("📊 Structure Viewer")
    st.markdown("""
    Browse your hierarchical structure:
    - **Areas** - Top-level organization
    - **Categories** - Hierarchical event types
    - **Attributes** - Data fields for each category
    """)
    
    # Fetch data
    with st.spinner("Loading structure..."):
        areas_data, categories_data, attributes_data = fetch_structure_data(client, user_id)
    
    if not areas_data:
        st.warning("No structure defined yet. Please upload a template first.")
        return
    
    # Build structures - IMPORTANT: Filter fields to match dataclass
    areas = []
    for area_data in areas_data:
        filtered_area = {
            'id': area_data['id'],
            'name': area_data['name'],
            'sort_order': area_data['sort_order'],
            'user_id': area_data.get('user_id'),
            'template_id': area_data.get('template_id'),
            'icon': area_data.get('icon'),
            'color': area_data.get('color'),
            'description': area_data.get('description'),
            'slug': area_data.get('slug'),
            'created_at': area_data.get('created_at'),
            'updated_at': area_data.get('updated_at'),
        }
        areas.append(Area(**filtered_area))
    
    roots_by_area = build_category_tree(categories_data)
    
    # Map attributes to categories - IMPORTANT: Filter fields to match dataclass
    attributes_map = {}
    for attr_data in attributes_data:
        filtered_attr = {
            'id': attr_data['id'],
            'name': attr_data['name'],
            'data_type': attr_data['data_type'],
            'sort_order': attr_data['sort_order'],
            'category_id': attr_data.get('category_id'),
            'user_id': attr_data.get('user_id'),
            'unit': attr_data.get('unit'),
            'is_required': attr_data.get('is_required', False),
            'default_value': attr_data.get('default_value'),
            'slug': attr_data.get('slug'),
            'validation_rules': attr_data.get('validation_rules'),
            'created_at': attr_data.get('created_at'),
            'updated_at': attr_data.get('updated_at'),
        }
        attr = Attribute(**filtered_attr)
        
        if attr.category_id not in attributes_map:
            attributes_map[attr.category_id] = []
        attributes_map[attr.category_id].append(attr)
    
    # ============================================
    # FILTERS
    # ============================================
    st.markdown("### 🔍 Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        area_options = ["All Areas"] + [area.name for area in areas]
        selected_area_name = st.selectbox("Filter by Area", area_options)
    
    with col2:
        level_options = ["All Levels"] + [f"Level {i}" for i in range(1, 11)]
        selected_level = st.selectbox("Filter by Level", level_options)
    
    # Search box
    search_term = st.text_input("🔎 Search categories/attributes", "")
    
    # ============================================
    # HIERARCHICAL VIEW
    # ============================================
    st.markdown("### 🌳 Hierarchical Structure")
    
    for area in sorted(areas, key=lambda x: x.sort_order):
        # Apply area filter
        if selected_area_name != "All Areas" and area.name != selected_area_name:
            continue
        
        # Area header
        icon = area.icon or "📦"
        color = area.color or "#3498db"
        
        st.markdown(f"## {icon} {area.name}")
        if area.description:
            st.caption(area.description)
        
        # Get root categories for this area
        root_categories = roots_by_area.get(area.id, [])
        
        if not root_categories:
            st.info(f"No categories defined for {area.name}")
            continue
        
        # Render each root category and its tree
        for root_cat in sorted(root_categories, key=lambda x: x.sort_order):
            # Apply level filter
            if selected_level != "All Levels":
                level_num = int(selected_level.split()[-1])
                if root_cat.level != level_num and not has_level_in_tree(root_cat, level_num):
                    continue
            
            # Apply search filter
            if search_term and not matches_search(root_cat, search_term, attributes_map):
                continue
            
            # Render the category tree starting from this root
            render_category_recursive(root_cat, attributes_map, indent_level=0)
            
            st.markdown("")  # Add spacing between root categories
    
    # ============================================
    # STATISTICS
    # ============================================
    st.markdown("### 📊 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Areas", len(areas))
    
    with col2:
        st.metric("Categories", len(categories_data))
    
    with col3:
        st.metric("Attributes", len(attributes_data))
    
    with col4:
        max_level = max([cat['level'] for cat in categories_data]) if categories_data else 0
        st.metric("Max Depth", max_level)
    
    # Level distribution
    if categories_data:
        st.markdown("#### Categories by Level")
        level_counts = {}
        for cat in categories_data:
            level = cat['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        level_dist_cols = st.columns(min(len(level_counts), 5))
        for idx, (level, count) in enumerate(sorted(level_counts.items())):
            with level_dist_cols[idx % 5]:
                st.metric(f"Level {level}", count)


def has_level_in_tree(category: Category, target_level: int) -> bool:
    """Check if category or any descendant has the target level"""
    if category.level == target_level:
        return True
    
    for child in category.children:
        if has_level_in_tree(child, target_level):
            return True
    
    return False


def matches_search(
    category: Category, 
    search_term: str,
    attributes_map: Dict[str, List[Attribute]]
) -> bool:
    """Check if category or its attributes match search term"""
    search_lower = search_term.lower()
    
    # Check category name and description
    if search_lower in category.name.lower():
        return True
    
    if category.description and search_lower in category.description.lower():
        return True
    
    # Check attributes
    attrs = attributes_map.get(category.id, [])
    for attr in attrs:
        if search_lower in attr.name.lower():
            return True
    
    # Check children
    for child in category.children:
        if matches_search(child, search_term, attributes_map):
            return True
    
    return False


if __name__ == "__main__":
    st.write("This module should be imported, not run directly.")
