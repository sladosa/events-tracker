"""
Events Tracker - Interactive Network Graph Viewer (Obsidian-Style)
===================================================================
Created: 2025-12-03 13:40 UTC
Last Modified: 2025-12-03 13:40 UTC
Python: 3.11
Version: 1.0.0 - Network Graph Implementation

Description:
Obsidian-style interactive network graph for structure visualization.
Click nodes to expand/collapse, drag to rearrange, zoom/pan navigation.

Features:
- Force-directed network layout (like Obsidian)
- Click to expand/collapse branches
- Drag nodes to rearrange
- Zoom, pan, filter
- Color-coded by entity type
- Edge connectors with labels
- Dynamic loading of children

Dependencies: streamlit-agraph, streamlit, pandas

IMPORTANT: Requires adding to requirements.txt:
    streamlit-agraph==0.0.45

Installation:
    pip install streamlit-agraph --break-system-packages
"""

import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
from typing import Dict, List, Set, Optional
import json


# ============================================
# CONFIGURATION
# ============================================

# Node styling by type
NODE_STYLES = {
    'area': {
        'color': '#4472C4',
        'shape': 'box',
        'size': 30,
        'font': {'size': 16, 'color': 'white', 'bold': True}
    },
    'category': {
        'color': '#70AD47',
        'shape': 'box',
        'size': 25,
        'font': {'size': 14, 'color': 'white'}
    },
    'attribute': {
        'color': '#FFC000',
        'shape': 'ellipse',
        'size': 20,
        'font': {'size': 12, 'color': 'black'}
    },
    'events': {
        'color': '#ED7D31',
        'shape': 'diamond',
        'size': 20,
        'font': {'size': 12, 'color': 'white'}
    }
}


# ============================================
# DATA LOADING
# ============================================

def load_structure_for_network(client, user_id: str, filter_area: Optional[str] = None) -> Dict:
    """
    Load structure data organized for network graph.
    
    Returns:
        Dictionary with areas, categories, attributes, event_counts
    """
    # Load Areas
    areas_query = client.table('areas').select('*').eq('user_id', user_id)
    if filter_area:
        areas_query = areas_query.eq('name', filter_area)
    areas = areas_query.order('sort_order').execute().data
    
    # Load Categories
    categories = client.table('categories').select('*').eq('user_id', user_id).order('level', 'sort_order').execute().data
    
    # Load Attributes
    attributes = client.table('attribute_definitions').select('*').eq('user_id', user_id).order('sort_order').execute().data
    
    # Load Events count per category
    events = client.table('events').select('id, category_id').eq('user_id', user_id).execute().data
    event_counts = {}
    for event in events:
        cat_id = event['category_id']
        event_counts[cat_id] = event_counts.get(cat_id, 0) + 1
    
    return {
        'areas': areas,
        'categories': categories,
        'attributes': attributes,
        'event_counts': event_counts
    }


def build_network_graph(data: Dict, show_events: bool = True, expanded_nodes: Set[str] = None) -> tuple:
    """
    Build network graph nodes and edges.
    
    Args:
        data: Structure data dictionary
        show_events: Whether to show event count nodes
        expanded_nodes: Set of node IDs that are expanded (show children)
        
    Returns:
        Tuple of (nodes_list, edges_list)
    """
    if expanded_nodes is None:
        expanded_nodes = set()
        # By default, expand all Area nodes
        for area in data['areas']:
            expanded_nodes.add(f"area_{area['id']}")
    
    nodes = []
    edges = []
    
    # Area nodes (always visible)
    for area in data['areas']:
        area_id = f"area_{area['id']}"
        
        icon = area.get('icon', '📁')
        label = f"{icon} {area['name']}"
        
        node = Node(
            id=area_id,
            label=label,
            title=area.get('description', area['name']),
            **NODE_STYLES['area']
        )
        nodes.append(node)
    
    # Category nodes (visible if parent is expanded)
    for category in data['categories']:
        cat_id = f"cat_{category['id']}"
        parent_id = f"area_{category['area_id']}" if category.get('parent_category_id') is None else f"cat_{category['parent_category_id']}"
        
        # Only show if parent is expanded
        if parent_id in expanded_nodes:
            icon = '📂'
            label = f"{icon} {category['name']}"
            level_info = f"Level {category['level']}"
            
            node = Node(
                id=cat_id,
                label=label,
                title=f"{category['name']}\n{level_info}\n{category.get('description', '')}",
                **NODE_STYLES['category']
            )
            nodes.append(node)
            
            # Edge from parent
            edge = Edge(
                source=parent_id,
                target=cat_id,
                label='',
                color='#95a5a6',
                width=2
            )
            edges.append(edge)
    
    # Attribute nodes (visible if parent category is expanded)
    for attr in data['attributes']:
        attr_id = f"attr_{attr['id']}"
        parent_id = f"cat_{attr['category_id']}"
        
        # Only show if parent is expanded
        if parent_id in expanded_nodes:
            icon = '🏷️'
            label = f"{icon} {attr['name']}"
            data_type = attr['data_type']
            
            node = Node(
                id=attr_id,
                label=label,
                title=f"{attr['name']}\nType: {data_type}",
                **NODE_STYLES['attribute']
            )
            nodes.append(node)
            
            # Edge from parent
            edge = Edge(
                source=parent_id,
                target=attr_id,
                label=data_type,
                color='#95a5a6',
                width=1,
                dashes=True
            )
            edges.append(edge)
    
    # Event count nodes (visible if show_events and parent category is expanded)
    if show_events:
        for cat_id, count in data['event_counts'].items():
            parent_id = f"cat_{cat_id}"
            
            # Only show if parent is expanded
            if parent_id in expanded_nodes:
                events_id = f"events_{cat_id}"
                icon = '📅'
                label = f"{icon} {count} Events"
                
                node = Node(
                    id=events_id,
                    label=label,
                    title=f"{count} Events in this category",
                    **NODE_STYLES['events']
                )
                nodes.append(node)
                
                # Edge from parent
                edge = Edge(
                    source=parent_id,
                    target=events_id,
                    label=f"{count}",
                    color='#e74c3c',
                    width=2
                )
                edges.append(edge)
    
    return nodes, edges


# ============================================
# STREAMLIT UI
# ============================================

def render_network_graph_viewer(client, user_id: str):
    """
    Render Obsidian-style network graph viewer.
    
    Args:
        client: Supabase client
        user_id: User UUID
    """
    st.header("🕸️ Network Graph Viewer (Obsidian-Style)")
    
    st.markdown("""
    **Interactive network graph** with expandable nodes.  
    - **Click nodes** to see connections
    - **Drag nodes** to rearrange
    - **Zoom/Pan** with mouse
    - **Filter** by Area
    """)
    
    # Initialize session state for expanded nodes
    if 'expanded_nodes' not in st.session_state:
        st.session_state.expanded_nodes = set()
    
    # Controls
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        # Area filter
        areas_response = client.table('areas').select('name').eq('user_id', user_id).order('sort_order').execute()
        area_options = ["All Areas"] + [a['name'] for a in areas_response.data]
        selected_area = st.selectbox("Filter by Area", area_options, key="network_area_filter")
    
    with col2:
        # Show events toggle
        show_events = st.checkbox("Show Events", value=True, key="network_show_events")
    
    with col3:
        # Expand all / Collapse all
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Expand All", use_container_width=True):
                # Load all node IDs
                filter_area = None if selected_area == "All Areas" else selected_area
                data = load_structure_for_network(client, user_id, filter_area)
                
                # Add all areas and categories to expanded set
                for area in data['areas']:
                    st.session_state.expanded_nodes.add(f"area_{area['id']}")
                for cat in data['categories']:
                    st.session_state.expanded_nodes.add(f"cat_{cat['id']}")
        
        with col_b:
            if st.button("Collapse All", use_container_width=True):
                st.session_state.expanded_nodes = set()
    
    # Load data
    filter_area = None if selected_area == "All Areas" else selected_area
    
    with st.spinner("Building network graph..."):
        data = load_structure_for_network(client, user_id, filter_area)
        
        # Expand Area nodes by default
        for area in data['areas']:
            st.session_state.expanded_nodes.add(f"area_{area['id']}")
        
        # Build graph
        nodes, edges = build_network_graph(
            data, 
            show_events=show_events,
            expanded_nodes=st.session_state.expanded_nodes
        )
    
    # Graph configuration
    config = Config(
        width='100%',
        height=700,
        directed=True,
        physics={
            'enabled': True,
            'stabilization': {'iterations': 100},
            'barnesHut': {
                'gravitationalConstant': -8000,
                'centralGravity': 0.3,
                'springLength': 95,
                'springConstant': 0.04,
                'damping': 0.09
            }
        },
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor='#F7A7A6',
        collapsible=True,
        node={'labelProperty': 'label'},
        link={'labelProperty': 'label', 'renderLabel': True}
    )
    
    # Render graph
    st.markdown("### Graph")
    return_value = agraph(nodes=nodes, edges=edges, config=config)
    
    # Handle node clicks for expand/collapse
    if return_value:
        clicked_node = return_value
        if clicked_node in st.session_state.expanded_nodes:
            st.session_state.expanded_nodes.remove(clicked_node)
            st.info(f"Collapsed: {clicked_node}")
        else:
            st.session_state.expanded_nodes.add(clicked_node)
            st.info(f"Expanded: {clicked_node}")
        st.rerun()
    
    # Statistics
    st.markdown("---")
    st.markdown("### Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    areas_count = len(data['areas'])
    categories_count = len(data['categories'])
    attributes_count = len(data['attributes'])
    events_count = sum(data['event_counts'].values())
    
    with col1:
        st.metric("📁 Areas", areas_count)
    with col2:
        st.metric("📂 Categories", categories_count)
    with col3:
        st.metric("🏷️ Attributes", attributes_count)
    with col4:
        st.metric("📅 Events", events_count)
    
    # Legend
    with st.expander("📖 Legend"):
        st.markdown("""
        **Node Types:**
        - 🟦 **Blue Box** - Areas (top level)
        - 🟩 **Green Box** - Categories
        - 🟡 **Yellow Ellipse** - Attributes
        - 🟠 **Orange Diamond** - Event counts
        
        **Interactions:**
        - **Click** node to expand/collapse children
        - **Drag** nodes to rearrange layout
        - **Scroll** to zoom in/out
        - **Pan** by dragging canvas
        """)


# ============================================
# INTEGRATION HELPER
# ============================================

def integrate_into_structure_viewer():
    """
    Integration instructions for Interactive Structure Viewer.
    
    Add this to interactive_structure_viewer.py render function:
    
    ```python
    # In Read-Only mode, add Graph View option
    if st.session_state.viewer_mode == 'read_only':
        view_option = st.radio(
            "View Mode",
            ["Table View", "Graph View"],
            horizontal=True,
            key="view_mode"
        )
        
        if view_option == "Graph View":
            from structure_graph_viewer_agraph import render_network_graph_viewer
            render_network_graph_viewer(client, user_id)
            return  # Exit early, don't show table
    ```
    """
    pass


if __name__ == "__main__":
    st.set_page_config(page_title="Network Graph Viewer", layout="wide")
    st.title("Network Graph Viewer - Demo")
    st.warning("⚠️ This requires `streamlit-agraph` package. Install with: `pip install streamlit-agraph`")
    st.info("Integrate this into Interactive Structure Viewer for full functionality.")
