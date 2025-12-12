"""
Events Tracker - Structure Graph Viewer Module
===============================================
Created: 2025-12-03 13:30 UTC
Last Modified: 2025-12-12 11:00 UTC
Python: 3.11
Version: 1.4.0 - Enhanced hover tooltips with more entity details

CHANGELOG v1.4.0 (Enhanced Hover Tooltips):
- ✨ IMPROVED: Hover tooltips now show more details per entity type:
  - Area: Name, Description
  - Category: Name, Description
  - Attribute: Name, Data_Type, Unit, Description
  - Events: Count
- 🔧 Added 'unit' and 'description' fields to attribute nodes in load_graph_data()
- 🎨 Consistent tooltip format across all graph types (Treemap, Sunburst, Network)
- 📝 Bold labels for better readability in tooltips

CHANGELOG v1.3.1 (Critical Fix - All Areas Graph Display):
- 🐛 CRITICAL FIX: Sunburst/Treemap now display correctly with "All Areas"
  - ROOT CAUSE: Plotly used 'labels' as unique identifiers
  - If two categories had same name in different Areas, graph broke
  - SOLUTION: Added 'ids' parameter with unique node IDs
  - 'labels' now only for display, 'ids' for parent-child mapping
- 🔧 Updated build_plotly_tree() to use ids parameter
- 🔧 Updated build_plotly_sunburst() to use ids parameter
- ✅ Network Graph already used unique IDs (no change needed)

Description:
Interactive hierarchical graph visualization of Areas → Categories → Attributes → Events
Multiple visualization modes with drill-down capability for focused exploration.
**NEW: Integrated mode for seamless filter control from parent module.**

Features:
- THREE visualization modes:
  * Treemap: Rectangular hierarchical view with click-to-zoom
  * Sunburst: Circular hierarchical view with click-to-focus
  * Network Graph: Obsidian-style force-directed graph with drill-down
- **NEW: render_graph_viewer_integrated()** - accepts external filters (no internal UI)
- Category Drill-Down - Focus on specific category branch
- Proper Area filtering (works for all graph types)
- Drag nodes to rearrange (Network Graph)
- Zoom, pan, and hover tooltips
- Color-coded by entity type
- Shows relationships with connectors (lines)
- Filters: Area, Category (drill-down), show/hide Events
- Breadcrumb navigation when focused
- Statistics panel

Dependencies: plotly, streamlit, pandas, streamlit-agraph

Technical Implementation:
- Uses Plotly Graph Objects for Treemap/Sunburst
- Uses streamlit-agraph for Network Graph
- Force-directed layout with physics simulation
- Hierarchical filtering with BFS traversal
- Dynamic data loading from Supabase
- Dual-mode: Standalone (with UI) or Integrated (filter-less)

Version History:
- v1.3.0: Added render_graph_viewer_integrated() for parent module control
- v1.2.0: Added Category drill-down, fixed Area filtering for Network Graph
- v1.1.0: Added Network Graph with streamlit-agraph
- v1.0.3: Fixed parent-child hierarchy mapping
- v1.0.2: Fixed Supabase .order() method call
- v1.0.1: Syntax fix + plotly dependency
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Tuple, Optional
import json
from streamlit_agraph import agraph, Node, Edge, Config


# ============================================
# DATA LOADING & TRANSFORMATION
# ============================================

def load_graph_data(client, user_id: str, filter_area: Optional[str] = None, filter_category: Optional[str] = None) -> Dict:
    """
    Load hierarchical structure data for graph visualization.
    
    Args:
        client: Supabase client
        user_id: User UUID
        filter_area: Optional area filter
        
    Returns:
        Dictionary with nodes and edges for graph
    """
    # Load Areas
    areas_query = client.table('areas').select('*').eq('user_id', user_id)
    if filter_area:
        areas_query = areas_query.eq('name', filter_area)
    areas = areas_query.order('sort_order').execute().data
    
    # Get area IDs for filtering (if filter is applied)
    area_ids = [area['id'] for area in areas] if areas else []
    
    # Load Categories (filter by area if needed)
    categories_query = client.table('categories').select('*').eq('user_id', user_id)
    if filter_area and area_ids:
        # Filter categories that belong to selected areas
        categories_query = categories_query.in_('area_id', area_ids)
    categories = categories_query.order('sort_order').execute().data
    
    # Get category IDs for filtering attributes
    category_ids = [cat['id'] for cat in categories] if categories else []
    
    # Load Attributes (filter by category if needed)
    attributes_query = client.table('attribute_definitions').select('*').eq('user_id', user_id)
    if filter_area and category_ids:
        # Filter attributes that belong to selected categories
        attributes_query = attributes_query.in_('category_id', category_ids)
    attributes = attributes_query.order('sort_order').execute().data
    
    # Load Events (count per category, filter by categories if needed)
    events_query = client.table('events').select('id, category_id').eq('user_id', user_id)
    if filter_area and category_ids:
        events_query = events_query.in_('category_id', category_ids)
    events = events_query.execute().data
    
    # Build hierarchical structure
    nodes = []
    edges = []
    
    # Root node (invisible)
    nodes.append({
        'id': 'root',
        'label': 'Structure',
        'type': 'root',
        'parent': None,
        'color': '#FFFFFF',
        'size': 0
    })
    
    # Area nodes (top-level in hierarchy)
    for area in areas:
        nodes.append({
            'id': f"area_{area['id']}",
            'label': area['name'],
            'type': 'area',
            'parent': '',  # Empty string = top-level for Plotly
            'color': area.get('color', '#4472C4'),
            'icon': area.get('icon', '📁'),
            'description': area.get('description', ''),
            'size': 30
        })
        edges.append({'from': 'root', 'to': f"area_{area['id']}"})  # Keep for potential future use    
    # Category nodes
    for category in categories:
        parent_id = f"area_{category['area_id']}" if category.get('parent_category_id') is None else f"cat_{category['parent_category_id']}"
        
        nodes.append({
            'id': f"cat_{category['id']}",
            'label': category['name'],
            'type': 'category',
            'parent': parent_id,
            'level': category['level'],
            'color': '#70AD47',
            'icon': '📂',
            'description': category.get('description', ''),
            'size': 20
        })
        edges.append({'from': parent_id, 'to': f"cat_{category['id']}"})
    
    # Attribute nodes
    for attr in attributes:
        parent_id = f"cat_{attr['category_id']}"
        
        nodes.append({
            'id': f"attr_{attr['id']}",
            'label': attr['name'],
            'type': 'attribute',
            'parent': parent_id,
            'data_type': attr['data_type'],
            'unit': attr.get('unit', ''),
            'description': attr.get('description', ''),
            'color': '#FFC000',
            'icon': '🏷️',
            'size': 15
        })
        edges.append({'from': parent_id, 'to': f"attr_{attr['id']}"})
    
    # Event count nodes (aggregate)
    event_counts = {}
    for event in events:
        cat_id = event['category_id']
        event_counts[cat_id] = event_counts.get(cat_id, 0) + 1
    
    for cat_id, count in event_counts.items():
        parent_id = f"cat_{cat_id}"
        nodes.append({
            'id': f"events_{cat_id}",
            'label': f"{count} Events",
            'type': 'events',
            'parent': parent_id,
            'count': count,
            'color': '#ED7D31',
            'icon': '📅',
            'size': 10
        })
        edges.append({'from': parent_id, 'to': f"events_{cat_id}"})
    
    return {
        'nodes': nodes,
        'edges': edges
    }


def filter_graph_by_category(graph_data: Dict, category_name: str) -> Dict:
    """
    Filter graph data to show only a specific category and its descendants.
    
    Args:
        graph_data: Full graph data
        category_name: Name of category to focus on
        
    Returns:
        Filtered graph data with only the category branch
    """
    # Find the category node
    category_node = None
    for node in graph_data['nodes']:
        if node['type'] == 'category' and node['label'] == category_name:
            category_node = node
            break
    
    if not category_node:
        return graph_data  # Category not found, return full graph
    
    # Build set of descendant IDs (BFS traversal)
    descendants = {category_node['id']}
    to_process = [category_node['id']]
    
    while to_process:
        current_id = to_process.pop(0)
        # Find all children of current node
        for node in graph_data['nodes']:
            if node.get('parent') == current_id and node['id'] not in descendants:
                descendants.add(node['id'])
                to_process.append(node['id'])
    
    # Also include the parent area of the category
    parent_area_id = category_node.get('parent')
    if parent_area_id:
        descendants.add(parent_area_id)
    
    # Filter nodes and edges
    filtered_nodes = [n for n in graph_data['nodes'] if n['id'] in descendants]
    filtered_edges = [e for e in graph_data['edges'] if e['from'] in descendants and e['to'] in descendants]
    
    return {
        'nodes': filtered_nodes,
        'edges': filtered_edges
    }


def build_plotly_tree(graph_data: Dict) -> go.Figure:
    """
    Build Plotly tree diagram from graph data.
    
    v1.3.1 FIX: Use 'ids' parameter for unique identification.
    This fixes the bug where categories with same name in different Areas
    caused the graph to not render properly.
    
    Args:
        graph_data: Dictionary with nodes and edges
        
    Returns:
        Plotly Figure object
    """
    nodes = graph_data['nodes']
    edges = graph_data['edges']
    
    # Build hierarchy for treemap
    # v1.3.1: Use separate ids and labels to handle duplicate names
    ids = []
    labels = []
    parents = []
    values = []
    colors = []
    texts = []
    
    for node in nodes:
        if node['id'] == 'root':
            continue  # Skip root
        
        # v1.3.1: Use node ID as unique identifier
        ids.append(node['id'])
        labels.append(node['label'])
        
        # Parent ID directly (no label conversion needed with ids parameter)
        parent_id = node.get('parent', '')
        if parent_id and parent_id != 'root':
            parents.append(parent_id)
        else:
            parents.append('')  # Top-level node
        
        # Size based on type
        if node['type'] == 'area':
            values.append(100)
        elif node['type'] == 'category':
            values.append(50)
        elif node['type'] == 'attribute':
            values.append(20)
        elif node['type'] == 'events':
            values.append(node.get('count', 10))
        else:
            values.append(10)
        
        colors.append(node['color'])
        
        # Hover text - enhanced with more details per type
        icon = node.get('icon', '')
        if node['type'] == 'area':
            hover_text = f"<b>{icon} {node['label']}</b><br><b>Type:</b> Area"
            if node.get('description'):
                hover_text += f"<br><b>Description:</b> {node['description']}"
        elif node['type'] == 'category':
            hover_text = f"<b>{icon} {node['label']}</b><br><b>Type:</b> Category"
            if node.get('description'):
                hover_text += f"<br><b>Description:</b> {node['description']}"
        elif node['type'] == 'attribute':
            hover_text = f"<b>{icon} {node['label']}</b><br><b>Type:</b> Attribute"
            if node.get('data_type'):
                hover_text += f"<br><b>Data Type:</b> {node['data_type']}"
            if node.get('unit'):
                hover_text += f"<br><b>Unit:</b> {node['unit']}"
            if node.get('description'):
                hover_text += f"<br><b>Description:</b> {node['description']}"
        elif node['type'] == 'events':
            hover_text = f"<b>{icon} {node['label']}</b><br><b>Count:</b> {node.get('count', 0)}"
        else:
            hover_text = f"{icon} {node['label']}<br>Type: {node['type'].title()}"
        texts.append(hover_text)
    
    # Create treemap with ids parameter
    fig = go.Figure(go.Treemap(
        ids=ids,  # v1.3.1: Unique identifiers
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(width=2, color='white')
        ),
        text=texts,
        hovertemplate='%{text}<extra></extra>',
        textposition='middle center',
        textfont=dict(size=12, color='white'),
        pathbar=dict(
            visible=True,
            thickness=30,
            textfont=dict(size=14)
        )
    ))
    
    fig.update_layout(
        title={
            'text': 'Structure Hierarchy - Interactive View',
            'font': {'size': 20, 'color': '#1f77b4'}
        },
        height=800,
        margin=dict(t=50, l=0, r=0, b=0),
        paper_bgcolor='#f8f9fa'
    )
    
    return fig


def build_plotly_sunburst(graph_data: Dict) -> go.Figure:
    """
    Build Plotly sunburst diagram (circular hierarchy).
    
    v1.3.1 FIX: Use 'ids' parameter for unique identification.
    This fixes the bug where categories with same name in different Areas
    caused the graph to not render properly when "All Areas" is selected.
    
    Args:
        graph_data: Dictionary with nodes and edges
        
    Returns:
        Plotly Figure object
    """
    nodes = graph_data['nodes']
    
    # v1.3.1: Use separate ids and labels to handle duplicate names
    ids = []
    labels = []
    parents = []
    values = []
    colors = []
    texts = []
    
    for node in nodes:
        if node['id'] == 'root':
            continue
        
        # v1.3.1: Use node ID as unique identifier
        ids.append(node['id'])
        labels.append(node['label'])
        
        # Parent ID directly (no label conversion needed with ids parameter)
        parent_id = node.get('parent', '')
        if parent_id and parent_id != 'root':
            parents.append(parent_id)
        else:
            parents.append('')  # Top-level node
        
        if node['type'] == 'area':
            values.append(100)
        elif node['type'] == 'category':
            values.append(50)
        elif node['type'] == 'attribute':
            values.append(20)
        elif node['type'] == 'events':
            values.append(node.get('count', 10))
        else:
            values.append(10)
        
        colors.append(node['color'])
        
        # Hover text - enhanced with more details per type
        icon = node.get('icon', '')
        if node['type'] == 'area':
            hover_text = f"<b>{icon} {node['label']}</b><br><b>Type:</b> Area"
            if node.get('description'):
                hover_text += f"<br><b>Description:</b> {node['description']}"
        elif node['type'] == 'category':
            hover_text = f"<b>{icon} {node['label']}</b><br><b>Type:</b> Category"
            if node.get('description'):
                hover_text += f"<br><b>Description:</b> {node['description']}"
        elif node['type'] == 'attribute':
            hover_text = f"<b>{icon} {node['label']}</b><br><b>Type:</b> Attribute"
            if node.get('data_type'):
                hover_text += f"<br><b>Data Type:</b> {node['data_type']}"
            if node.get('unit'):
                hover_text += f"<br><b>Unit:</b> {node['unit']}"
            if node.get('description'):
                hover_text += f"<br><b>Description:</b> {node['description']}"
        elif node['type'] == 'events':
            hover_text = f"<b>{icon} {node['label']}</b><br><b>Count:</b> {node.get('count', 0)}"
        else:
            hover_text = f"{icon} {node['label']}"
        texts.append(hover_text)
    
    # v1.3.1: Create sunburst with ids parameter for unique identification
    fig = go.Figure(go.Sunburst(
        ids=ids,  # v1.3.1: Unique identifiers
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(width=2, color='white')
        ),
        text=texts,
        hovertemplate='%{text}<extra></extra>',
        branchvalues='remainder',
        textfont=dict(size=14, color='white')
    ))
    
    fig.update_layout(
        title={
            'text': 'Structure Hierarchy - Circular View',
            'font': {'size': 20, 'color': '#1f77b4'}
        },
        height=800,
        margin=dict(t=50, l=0, r=0, b=0),
        paper_bgcolor='#f8f9fa'
    )
    
    return fig


def build_network_graph(graph_data: Dict) -> Tuple[List, List, Dict]:
    """
    Build interactive network graph (Obsidian-style) using streamlit-agraph.
    
    Args:
        graph_data: Dictionary with nodes and edges
        
    Returns:
        Tuple of (nodes_list, edges_list, config)
    """
    nodes_list = []
    edges_list = []
    
    # Color mapping by type
    color_map = {
        'root': '#E0E0E0',
        'area': '#4472C4',      # Blue
        'category': '#70AD47',   # Green
        'attribute': '#FFC000',  # Yellow/Gold
        'events': '#ED7D31'      # Orange
    }
    
    # Size mapping by type
    size_map = {
        'root': 20,
        'area': 30,
        'category': 25,
        'attribute': 20,
        'events': 15
    }
    
    # Build nodes
    for node in graph_data['nodes']:
        if node['id'] == 'root':
            continue  # Skip root for cleaner visualization
        
        # Create node with proper formatting
        node_color = node.get('color', color_map.get(node['type'], '#999999'))
        node_size = size_map.get(node['type'], 20)
        
        # Build label with icon
        icon = node.get('icon', '')
        label = f"{icon} {node['label']}" if icon else node['label']
        
        # Build title (tooltip) - enhanced with more details per type
        if node['type'] == 'area':
            title = f"<b>{node['label']}</b><br><b>Type:</b> Area"
            if node.get('description'):
                title += f"<br><b>Description:</b> {node['description']}"
        elif node['type'] == 'category':
            title = f"<b>{node['label']}</b><br><b>Type:</b> Category"
            if node.get('description'):
                title += f"<br><b>Description:</b> {node['description']}"
        elif node['type'] == 'attribute':
            title = f"<b>{node['label']}</b><br><b>Type:</b> Attribute"
            if node.get('data_type'):
                title += f"<br><b>Data Type:</b> {node['data_type']}"
            if node.get('unit'):
                title += f"<br><b>Unit:</b> {node['unit']}"
            if node.get('description'):
                title += f"<br><b>Description:</b> {node['description']}"
        elif node['type'] == 'events':
            title = f"<b>{node['label']}</b><br><b>Count:</b> {node.get('count', 0)}"
        else:
            title = f"<b>{node['label']}</b><br>Type: {node['type'].title()}"
        
        nodes_list.append(Node(
            id=node['id'],
            label=label,
            size=node_size,
            color=node_color,
            title=title,
            shape='dot'
        ))
    
    # Build edges
    for edge in graph_data['edges']:
        # Skip edges from root
        if edge['from'] == 'root':
            edge_from = edge['to']
            # Find parent from nodes
            for node in graph_data['nodes']:
                if node['id'] == edge_from:
                    parent_id = node.get('parent', '')
                    if parent_id and parent_id != 'root':
                        edges_list.append(Edge(
                            source=parent_id,
                            target=edge_from,
                            color='#CCCCCC'
                        ))
        else:
            edges_list.append(Edge(
                source=edge['from'],
                target=edge['to'],
                color='#CCCCCC'
            ))
    
    # Configuration for interactive graph
    config = Config(
        width='100%',
        height=800,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        node={
            'labelProperty': 'label',
            'renderLabel': True
        },
        link={'renderLabel': False}
    )
    
    return nodes_list, edges_list, config


def render_statistics(graph_data: Dict):
    """
    Render statistics panel showing counts by entity type.
    
    Args:
        graph_data: Dictionary with nodes data
    """
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    areas_count = len([n for n in graph_data['nodes'] if n['type'] == 'area'])
    categories_count = len([n for n in graph_data['nodes'] if n['type'] == 'category'])
    attributes_count = len([n for n in graph_data['nodes'] if n['type'] == 'attribute'])
    events_count = sum(n.get('count', 0) for n in graph_data['nodes'] if n['type'] == 'events')
    
    with col1:
        st.metric("📁 Areas", areas_count)
    with col2:
        st.metric("📂 Categories", categories_count)
    with col3:
        st.metric("🏷️ Attributes", attributes_count)
    with col4:
        st.metric("📅 Events", events_count)


# ============================================
# STREAMLIT UI COMPONENTS
# ============================================

def render_graph_viewer_integrated(client, user_id: str, filters: Dict):
    """
    Render graph viewer with EXTERNAL filter control (no internal filter UI).
    Called from Interactive Structure Viewer with centralized filters.
    
    Args:
        client: Supabase client
        user_id: User UUID
        filters: Dictionary with filter settings:
            - view_type: 'Sunburst' | 'Treemap' | 'Network Graph'
            - area: 'All Areas' | area name
            - category: 'All Categories' | category name
            - show_events: True | False
    
    Usage:
        from structure_graph_viewer import render_graph_viewer_integrated
        
        filters = {
            'view_type': 'Sunburst',
            'area': 'Health',
            'category': 'All Categories',
            'show_events': True
        }
        render_graph_viewer_integrated(client, user_id, filters)
    """
    # Extract filters
    view_type = filters.get('view_type', 'Sunburst')
    selected_area = filters.get('area', 'All Areas')
    selected_category = filters.get('category', 'All Categories')
    show_events = filters.get('show_events', True)
    
    # Load data with area filter
    filter_area = None if selected_area == "All Areas" else selected_area
    
    with st.spinner("Loading graph data..."):
        graph_data = load_graph_data(client, user_id, filter_area)
        
        # Apply category drill-down filter
        if selected_category and selected_category != "All Categories":
            graph_data = filter_graph_by_category(graph_data, selected_category)
        
        # Filter events if needed
        if not show_events:
            graph_data['nodes'] = [n for n in graph_data['nodes'] if n['type'] != 'events']
            graph_data['edges'] = [e for e in graph_data['edges'] if not e['to'].startswith('events_')]
    
    # Show breadcrumb if filters are active
    if selected_area != "All Areas" or selected_category != "All Categories":
        breadcrumb_parts = []
        if selected_area != "All Areas":
            breadcrumb_parts.append(f"📁 {selected_area}")
        if selected_category != "All Categories":
            breadcrumb_parts.append(f"📂 {selected_category}")
        
        breadcrumb = " → ".join(breadcrumb_parts)
        st.info(f"🔍 **Focused View:** {breadcrumb}")
    
    # Render based on view type
    if view_type == "Treemap":
        fig = build_plotly_tree(graph_data)
        st.plotly_chart(fig, use_container_width=True)
    
    elif view_type == "Sunburst":
        fig = build_plotly_sunburst(graph_data)
        st.plotly_chart(fig, use_container_width=True)
    
    elif view_type == "Network Graph":
        # Build and render interactive network graph
        nodes_list, edges_list, config = build_network_graph(graph_data)
        st.markdown("**🕸️ Interactive Network Graph** - Drag nodes to rearrange, hover for details")
        agraph(nodes=nodes_list, edges=edges_list, config=config)
    
    # Statistics
    render_statistics(graph_data)


def render_graph_viewer(client, user_id: str):
    """
    Render interactive graph viewer in Streamlit.
    
    Args:
        client: Supabase client
        user_id: User UUID
    """
    st.header("📊 Structure Graph Viewer")
    
    st.markdown("""
    **Interactive hierarchical view** of your event structure.  
    Click on any section to drill down into details.
    """)
    
    # Filters and options
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        # Area filter
        areas_response = client.table('areas').select('name').eq('user_id', user_id).order('sort_order').execute()
        area_options = ["All Areas"] + [a['name'] for a in areas_response.data]
        selected_area = st.selectbox("Filter by Area", area_options, key="graph_area_filter")
    
    with col2:
        # Category drill-down (only if Area is selected)
        if selected_area != "All Areas":
            # Get categories for selected area
            area_id_query = client.table('areas').select('id').eq('user_id', user_id).eq('name', selected_area).execute()
            if area_id_query.data:
                area_id = area_id_query.data[0]['id']
                categories_response = client.table('categories').select('name').eq('user_id', user_id).eq('area_id', area_id).order('sort_order').execute()
                category_options = ["All Categories"] + [c['name'] for c in categories_response.data]
                selected_category = st.selectbox("Drill-down to Category", category_options, key="graph_category_filter")
            else:
                selected_category = "All Categories"
        else:
            selected_category = "All Categories"
            st.selectbox("Drill-down to Category", ["Select Area first"], key="graph_category_disabled", disabled=True)
    
    with col3:
        # View type
        view_type = st.selectbox(
            "View Type",
            ["Treemap", "Sunburst", "Network Graph"],
            key="graph_view_type"
        )
    
    with col4:
        # Show events toggle
        show_events = st.checkbox("Show Events", value=True, key="graph_show_events")
    
    # Load data
    filter_area = None if selected_area == "All Areas" else selected_area
    
    with st.spinner("Loading graph data..."):
        graph_data = load_graph_data(client, user_id, filter_area)
        
        # Apply category drill-down filter (for focused view)
        if selected_category and selected_category != "All Categories":
            graph_data = filter_graph_by_category(graph_data, selected_category)
        
        # Filter events if needed
        if not show_events:
            graph_data['nodes'] = [n for n in graph_data['nodes'] if n['type'] != 'events']
            graph_data['edges'] = [e for e in graph_data['edges'] if not e['to'].startswith('events_')]
    
    # Render based on view type
    if view_type == "Treemap":
        fig = build_plotly_tree(graph_data)
        st.plotly_chart(fig, use_container_width=True)
    
    elif view_type == "Sunburst":
        fig = build_plotly_sunburst(graph_data)
        st.plotly_chart(fig, use_container_width=True)
    
    elif view_type == "Network Graph":
        # Show breadcrumb if drill-down is active
        if selected_area != "All Areas" or (selected_category and selected_category != "All Categories"):
            breadcrumb_parts = []
            if selected_area != "All Areas":
                breadcrumb_parts.append(f"📁 {selected_area}")
            if selected_category and selected_category != "All Categories":
                breadcrumb_parts.append(f"📂 {selected_category}")
            
            breadcrumb = " → ".join(breadcrumb_parts)
            st.info(f"🔍 **Focused View:** {breadcrumb} | Select 'All Areas' / 'All Categories' to zoom out")
        
        # Build and render interactive network graph (Obsidian-style)
        nodes_list, edges_list, config = build_network_graph(graph_data)
        
        st.markdown("**🕸️ Interactive Network Graph** - Drag nodes to rearrange, hover for details")
        
        # Render the graph
        return_value = agraph(nodes=nodes_list, edges=edges_list, config=config)
    
    # Statistics
    render_statistics(graph_data)


# ============================================
# INTEGRATION HELPER
# ============================================

def add_graph_view_tab(client, user_id: str):
    """
    Helper function to add graph view as a tab in Interactive Structure Viewer.
    
    Usage in interactive_structure_viewer.py:
        tab1, tab2 = st.tabs(["Table View", "Graph View"])
        with tab1:
            # Existing table view
        with tab2:
            from structure_graph_viewer import render_graph_viewer
            render_graph_viewer(client, user_id)
    """
    render_graph_viewer(client, user_id)


if __name__ == "__main__":
    st.set_page_config(page_title="Structure Graph Viewer", layout="wide")
    st.title("Structure Graph Viewer - Demo")
    st.info("This is a demo module. Integrate into Interactive Structure Viewer for full functionality.")
