"""
Structure Viewer Module
Displays hierarchical Area → Category → Attribute structure

VERSION: 3.0
LAST UPDATED: 2025-11-11 12:00 UTC
CHANGES: Ultra-defensive coding + error reporting + explicit list initialization
"""

import streamlit as st
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class AreaNode:
    """Area data structure"""
    id: str
    name: str
    icon: str
    color: str
    sort_order: int
    description: str
    category_count: int = 0


@dataclass 
class CategoryNode:
    """Category data structure"""
    id: str
    name: str
    area_id: str
    area_name: str
    parent_id: Optional[str]
    parent_name: Optional[str]
    level: int
    sort_order: int
    description: str
    path: str
    children: List['CategoryNode'] = field(default_factory=list)
    attributes: List['AttributeNode'] = field(default_factory=list)


@dataclass
class AttributeNode:
    """Attribute definition data structure"""
    id: str
    name: str
    category_id: str
    category_name: str
    data_type: str
    unit: Optional[str]
    is_required: bool
    default_value: Optional[str]
    sort_order: int


class StructureViewer:
    """Handles loading and displaying hierarchical structure"""
    
    def __init__(self, supabase_client, user_id: str):
        self.client = supabase_client
        self.user_id = user_id
        self.areas: Dict[str, AreaNode] = {}
        self.categories: Dict[str, CategoryNode] = {}
        self.attributes: List[AttributeNode] = []
        
    def load_structure(self) -> Tuple[bool, str]:
        """Load all structure from database"""
        try:
            # Load areas
            areas_response = self.client.table('areas') \
                .select('*') \
                .eq('user_id', self.user_id) \
                .order('sort_order') \
                .execute()
            
            if not areas_response.data:
                return False, "No areas found. Upload a template first!"
            
            for row in areas_response.data:
                area = AreaNode(
                    id=row['id'],
                    name=row['name'],
                    icon=row.get('icon', '📦'),
                    color=row.get('color', '#999999'),
                    sort_order=row['sort_order'],
                    description=row.get('description', '')
                )
                self.areas[area.id] = area
            
            # Load categories
            cats_response = self.client.table('categories') \
                .select('*') \
                .eq('user_id', self.user_id) \
                .order('area_id, level, sort_order') \
                .execute()
            
            for row in cats_response.data:
                # Find area name
                area = self.areas.get(row['area_id'])
                area_name = area.name if area else 'Unknown'
                
                # Count categories per area
                if area:
                    area.category_count += 1
                
                cat = CategoryNode(
                    id=row['id'],
                    name=row['name'],
                    area_id=row['area_id'],
                    area_name=area_name,
                    parent_id=row.get('parent_category_id'),
                    parent_name=None,  # Will be set later
                    level=row['level'],
                    sort_order=row['sort_order'],
                    description=row.get('description', ''),
                    path=str(row.get('path', '')) if row.get('path') else ''
                )
                
                # EXPLICIT initialization to ensure lists exist
                if not hasattr(cat, 'children') or cat.children is None:
                    cat.children = []
                if not hasattr(cat, 'attributes') or cat.attributes is None:
                    cat.attributes = []
                
                self.categories[cat.id] = cat
            
            # Build parent names and hierarchy
            for cat in self.categories.values():
                if cat.parent_id:
                    parent = self.categories.get(cat.parent_id)
                    if parent:
                        cat.parent_name = parent.name
                        parent.children.append(cat)
            
            # Load attributes
            attrs_response = self.client.table('attribute_definitions') \
                .select('*') \
                .eq('user_id', self.user_id) \
                .order('category_id, sort_order') \
                .execute()
            
            for row in attrs_response.data:
                # Find category name
                cat = self.categories.get(row['category_id'])
                cat_name = cat.name if cat else 'Unknown'
                
                attr = AttributeNode(
                    id=row['id'],
                    name=row['name'],
                    category_id=row['category_id'],
                    category_name=cat_name,
                    data_type=row['data_type'],
                    unit=row.get('unit'),
                    is_required=row.get('is_required', False),
                    default_value=row.get('default_value'),
                    sort_order=row['sort_order']
                )
                self.attributes.append(attr)
                
                # Add to category
                if cat:
                    cat.attributes.append(attr)
            
            return True, f"Loaded {len(self.areas)} areas, {len(self.categories)} categories, {len(self.attributes)} attributes"
            
        except Exception as e:
            return False, f"Error loading structure: {str(e)}"
    
    def get_root_categories(self, area_id: str) -> List[CategoryNode]:
        """Get root level categories for an area"""
        return [
            cat for cat in self.categories.values()
            if cat.area_id == area_id and cat.parent_id is None
        ]
    
    def filter_areas(self, search_term: str = "") -> List[AreaNode]:
        """Filter areas by search term"""
        if not search_term:
            return sorted(self.areas.values(), key=lambda x: x.sort_order)
        
        search_lower = search_term.lower()
        filtered = [
            area for area in self.areas.values()
            if search_lower in area.name.lower() or 
               search_lower in area.description.lower()
        ]
        return sorted(filtered, key=lambda x: x.sort_order)
    
    def filter_categories(self, area_id: Optional[str] = None, 
                         level: Optional[int] = None,
                         search_term: str = "") -> List[CategoryNode]:
        """Filter categories by area, level, and search"""
        filtered = list(self.categories.values())
        
        if area_id:
            filtered = [cat for cat in filtered if cat.area_id == area_id]
        
        if level:
            filtered = [cat for cat in filtered if cat.level == level]
        
        if search_term:
            search_lower = search_term.lower()
            filtered = [
                cat for cat in filtered
                if search_lower in cat.name.lower() or
                   search_lower in cat.description.lower()
            ]
        
        return sorted(filtered, key=lambda x: (x.level, x.sort_order))


def render_attribute_line(attr: AttributeNode):
    """Render single attribute line"""
    required_star = "⭐" if attr.is_required else ""
    unit_text = f" ({attr.unit})" if attr.unit else ""
    default_text = f" [default: {attr.default_value}]" if attr.default_value else ""
    
    # Color by data type
    type_colors = {
        'number': '🔢',
        'text': '📝',
        'datetime': '📅',
        'boolean': '✓',
        'link': '🔗',
        'image': '🖼️'
    }
    type_icon = type_colors.get(attr.data_type, '❓')
    
    return f"**{attr.name}**{required_star} {type_icon} `{attr.data_type}`{unit_text}{default_text}"


def render_category_tree(category: CategoryNode, depth: int = 0):
    """Recursively render category with children and attributes"""
    # Safety check
    if not category or not hasattr(category, 'name'):
        return
    
    indent = "    " * depth
    
    # Safe access to attributes with explicit checks
    attrs = []
    if hasattr(category, 'attributes') and category.attributes is not None:
        attrs = category.attributes
    attrs_count = len(attrs) if attrs else 0
    
    # Safe string conversion for all values
    try:
        cat_name = str(category.name) if category.name else "Unnamed"
        cat_level = int(category.level) if hasattr(category, 'level') else 0
        expander_title = f"{indent}📁 **{cat_name}** (Level {cat_level}) - {attrs_count} attributes"
    except Exception as e:
        # Ultimate fallback
        expander_title = f"{indent}📁 Category - {attrs_count} attributes"
    
    # Category header
    with st.expander(expander_title, expanded=(depth < 2)):
        # Description
        desc = getattr(category, 'description', '')
        if desc:
            st.caption(str(desc))
        
        # Attributes
        if attrs:
            st.markdown("**Attributes:**")
            try:
                sorted_attrs = sorted(attrs, key=lambda x: getattr(x, 'sort_order', 0))
            except (AttributeError, TypeError):
                sorted_attrs = attrs
            
            for attr in sorted_attrs:
                st.markdown(f"• {render_attribute_line(attr)}")
        else:
            st.info("No attributes defined")
        
        # Metadata
        with st.expander("🔍 Metadata", expanded=False):
            cat_id = getattr(category, 'id', 'N/A')
            cat_sort = getattr(category, 'sort_order', 'N/A')
            cat_path = getattr(category, 'path', '')
            
            st.text(f"Category ID: {cat_id}")
            st.text(f"Sort Order: {cat_sort}")
            if cat_path and str(cat_path).strip():
                st.text(f"Path: {cat_path}")
        
        # Children categories
        children = []
        if hasattr(category, 'children') and category.children is not None:
            children = category.children
        
        if children:
            st.markdown(f"**Subcategories ({len(children)}):**")
            # Safe sort with fallback
            try:
                sorted_children = sorted(children, key=lambda x: getattr(x, 'sort_order', 0))
            except (AttributeError, TypeError):
                sorted_children = children
            
            for child in sorted_children:
                render_category_tree(child, depth + 1)


def render_structure_viewer(supabase_client, user_id: str):
    """Main function to render structure viewer page"""
    
    st.header("📊 Structure Viewer")
    st.markdown("View your hierarchical data structure: Areas → Categories → Attributes")
    
    # Initialize viewer
    viewer = StructureViewer(supabase_client, user_id)
    
    # Load structure
    with st.spinner("Loading structure from database..."):
        success, message = viewer.load_structure()
    
    if not success:
        st.error(message)
        st.info("💡 Upload a template first to create your structure!")
        return
    
    st.success(message)
    
    # ============================================
    # FILTERS & SEARCH
    # ============================================
    st.subheader("🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Area filter
        area_options = {"All Areas": None}
        area_options.update({
            f"{area.icon} {area.name}": area.id 
            for area in sorted(viewer.areas.values(), key=lambda x: x.sort_order)
        })
        selected_area_name = st.selectbox("Filter by Area", list(area_options.keys()))
        selected_area_id = area_options[selected_area_name]
    
    with col2:
        # Level filter
        if viewer.categories:
            max_level = max(cat.level for cat in viewer.categories.values())
            level_options = ["All Levels"] + [f"Level {i}" for i in range(1, max_level + 1)]
            selected_level_name = st.selectbox("Filter by Level", level_options)
            selected_level = None if selected_level_name == "All Levels" else int(selected_level_name.split()[1])
        else:
            selected_level = None
    
    with col3:
        # Search
        search_term = st.text_input("🔎 Search", placeholder="Search by name...")
    
    st.divider()
    
    # ============================================
    # DISPLAY STRUCTURE
    # ============================================
    
    # Filter areas
    filtered_areas = viewer.filter_areas(search_term)
    if selected_area_id:
        filtered_areas = [area for area in filtered_areas if area.id == selected_area_id]
    
    if not filtered_areas:
        st.warning("No areas match your filters.")
        return
    
    # Display each area
    for area in filtered_areas:
        st.markdown("---")
        
        # Area header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"## {area.icon} {area.name}")
            if area.description:
                st.caption(area.description)
        with col2:
            st.metric("Categories", area.category_count)
        
        # Get root categories for this area
        root_categories = viewer.get_root_categories(area.id)
        
        # Apply level filter if set
        if selected_level:
            # Get all categories at this level for this area
            filtered_cats = [
                cat for cat in viewer.categories.values()
                if cat.area_id == area.id and cat.level == selected_level
            ]
            
            if not filtered_cats:
                st.info(f"No categories at Level {selected_level}")
                continue
            
            # Display flat list
            for cat in sorted(filtered_cats, key=lambda x: x.sort_order):
                attrs = getattr(cat, 'attributes', [])
                attrs_count = len(attrs) if attrs else 0
                parent_text = f" (parent: {cat.parent_name})" if cat.parent_name else ""
                
                with st.expander(f"📁 {cat.name}{parent_text} - {attrs_count} attributes"):
                    if cat.description:
                        st.caption(cat.description)
                    
                    if attrs:
                        st.markdown("**Attributes:**")
                        for attr in sorted(attrs, key=lambda x: x.sort_order):
                            st.markdown(f"• {render_attribute_line(attr)}")
        else:
            # Display hierarchical tree
            if not root_categories:
                st.info("No categories in this area")
                continue
            
            # Safe sort with try/except
            try:
                sorted_roots = sorted(root_categories, key=lambda x: getattr(x, 'sort_order', 0))
            except (AttributeError, TypeError):
                sorted_roots = root_categories
            
            for root_cat in sorted_roots:
                # Extra safety check
                if root_cat and hasattr(root_cat, 'name'):
                    try:
                        render_category_tree(root_cat)
                    except Exception as e:
                        st.error(f"Error rendering category: {str(e)}")
                        continue
    
    # ============================================
    # STATISTICS
    # ============================================
    st.divider()
    st.subheader("📈 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Areas", len(viewer.areas))
    
    with col2:
        st.metric("Total Categories", len(viewer.categories))
    
    with col3:
        st.metric("Total Attributes", len(viewer.attributes))
    
    with col4:
        if viewer.categories:
            avg_attrs = len(viewer.attributes) / len(viewer.categories)
            st.metric("Avg Attributes/Category", f"{avg_attrs:.1f}")
    
    # Breakdown by area
    with st.expander("📊 Breakdown by Area"):
        for area in sorted(viewer.areas.values(), key=lambda x: x.sort_order):
            area_cats = [cat for cat in viewer.categories.values() if cat.area_id == area.id]
            # Safe sum with fallback for categories without attributes list
            area_attrs = sum(len(getattr(cat, 'attributes', [])) for cat in area_cats)
            
            st.markdown(f"**{area.icon} {area.name}**")
            st.text(f"  Categories: {len(area_cats)} | Attributes: {area_attrs}")
