"""
Structure Viewer Module - FIXED VERSION
========================================
Displays hierarchical Area → Category → Attribute structure
WITHOUT nested expanders (which Streamlit doesn't allow)

FIX: Uses indentation and containers instead of nested expanders
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Area:
    """Represents an Area in the structure"""
    id: str
    name: str
    icon: Optional[str]
    color: Optional[str]
    description: Optional[str]
    sort_order: int


@dataclass
class Category:
    """Represents a Category in the structure"""
    id: str
    area_id: str
    parent_category_id: Optional[str]
    name: str
    description: Optional[str]
    level: int
    sort_order: int
    path: Optional[str] = None
    children: List['Category'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class Attribute:
    """Represents an Attribute definition"""
    id: str
    category_id: str
    name: str
    data_type: str
    unit: Optional[str]
    is_required: bool
    default_value: Optional[str]
    sort_order: int


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
    # Create Category objects
    categories = {cat['id']: Category(**cat) for cat in categories_data}
    
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
    
    if attr.data_type:
        parts.append(f"_{attr.data_type}_")
    
    if attr.unit:
        parts.append(f"[{attr.unit}]")
    
    if attr.is_required:
        parts.append("⚠️ Required")
    
    if attr.default_value:
        parts.append(f"(default: {attr.default_value})")
    
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
    level_emoji = "📁" if indent_level == 0 else ("📂" if indent_level == 1 else "📄")
    
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
    
    # Show metadata in a subtle way (not in expander to avoid nesting)
    if indent_level == 0:  # Only for root categories
        with st.expander(f"🔍 Details for '{category.name}'", expanded=False):
            st.text(f"Category ID: {category.id}")
            st.text(f"Sort Order: {category.sort_order}")
            if category.path:
                st.text(f"Path: {category.path}")
            
            # Show children count
            if category.children:
                st.info(f"Has {len(category.children)} subcategories")
    
    # Recursively render children with increased indentation
    if category.children:
        st.markdown(f"{indent}  **Subcategories ({len(category.children)}):**")
        for child in sorted(category.children, key=lambda x: x.sort_order):
            render_category_recursive(child, attributes_map, indent_level + 1)
        st.markdown("---")  # Separator after subcategories


def render_structure_viewer(client, user_id: str):
    """
    Main function to render the structure viewer
    FIXED: No nested expanders
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
    
    # Build structures
    areas = [Area(**area_data) for area_data in areas_data]
    roots_by_area = build_category_tree(categories_data)
    
    # Map attributes to categories
    attributes_map = {}
    for attr_data in attributes_data:
        attr = Attribute(**attr_data)
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
                # Check if this category or any of its descendants match
                # For simplicity, we'll show the whole tree if root matches
                if root_cat.level != level_num and not has_level_in_tree(root_cat, level_num):
                    continue
            
            # Apply search filter
            if search_term and not matches_search(root_cat, search_term, attributes_map):
                continue
            
            # Render the category tree starting from this root
            render_category_recursive(root_cat, attributes_map, indent_level=0)
            
            st.markdown("")  # Add spacing
    
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
        
        for level in sorted(level_counts.keys()):
            st.write(f"Level {level}: {level_counts[level]} categories")


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
