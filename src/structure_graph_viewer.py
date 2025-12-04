"""
Events Tracker - Structure Graph Viewer Module
===============================================
Created: 2025-12-03 13:30 UTC
Last Modified: 2025-12-04 10:10 UTC
Python: 3.11
Version: 1.0.3 - Fixed parent-child hierarchy mapping

Description:
Interactive hierarchical graph visualization of Areas → Categories → Attributes → Events
Similar to Obsidian graph view with expandable/collapsible nodes.

Features:
- Interactive tree/network diagram
- Click to expand/collapse branches
- Zoom, pan, and hover tooltips
- Color-coded by entity type
- Shows relationships with connectors (lines)
- Filters: Area, Category, show/hide Events

Dependencies: plotly, streamlit, pandas

Technical Implementation:
- Uses Plotly Graph Objects for rendering
- Treemap or Network Graph layout options
- Dynamic data loading from Supabase
- Session state for expand/collapse tracking

Fix Log:
- v1.0.3: Fixed parent-child mapping (ID → label conversion for Plotly)
- v1.0.2: Fixed Supabase .order() method call
- v1.0.1: Syntax fix + plotly dependency
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Tuple, Optional
import json


# ============================================
# DATA LOADING & TRANSFORMATION
# ============================================

def load_graph_data(client, user_id: str, filter_area: Optional[str] = None) -> Dict:
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
    
    # Load Categories
    categories = client.table('categories').select('*').eq('user_id', user_id).order('sort_order').execute().data
    
    # Load Attributes
    attributes = client.table('attribute_definitions').select('*').eq('user_id', user_id).order('sort_order').execute().data
    
    # Load Events (count per category)
    events = client.table('events').select('id, category_id').eq('user_id', user_id).execute().data
    
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


def build_plotly_tree(graph_data: Dict) -> go.Figure:
    """
    Build Plotly tree diagram from graph data.
    
    Args:
        graph_data: Dictionary with nodes and edges
        
    Returns:
        Plotly Figure object
    """
    nodes = graph_data['nodes']
    edges = graph_data['edges']
    
    # Build ID to label mapping
    id_to_label = {node['id']: node['label'] for node in nodes}
    
    # Build hierarchy for treemap
    labels = []
    parents = []
    values = []
    colors = []
    texts = []
    
    for node in nodes:
        if node['id'] == 'root':
            continue  # Skip root
            
        labels.append(node['label'])
        
        # Convert parent ID to parent label (Plotly expects labels, not IDs)
        parent_id = node.get('parent', '')
        if parent_id and parent_id in id_to_label:
            parents.append(id_to_label[parent_id])
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
        
        # Hover text
        icon = node.get('icon', '')
        hover_text = f"{icon} {node['label']}<br>Type: {node['type'].title()}"
        if node['type'] == 'events':
            hover_text += f"<br>Count: {node.get('count', 0)}"
        if node.get('description'):
            hover_text += f"<br>{node['description']}"
        texts.append(hover_text)
    
    # Create treemap
    fig = go.Figure(go.Treemap(
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
    
    Args:
        graph_data: Dictionary with nodes and edges
        
    Returns:
        Plotly Figure object
    """
    nodes = graph_data['nodes']
    
    # Build ID to label mapping
    id_to_label = {node['id']: node['label'] for node in nodes}
    
    labels = []
    parents = []
    values = []
    colors = []
    texts = []
    
    for node in nodes:
        if node['id'] == 'root':
            continue
            
        labels.append(node['label'])
        
        # Convert parent ID to parent label (Plotly expects labels, not IDs)
        parent_id = node.get('parent', '')
        if parent_id and parent_id in id_to_label:
            parents.append(id_to_label[parent_id])
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
        
        icon = node.get('icon', '')
        hover_text = f"{icon} {node['label']}"
        texts.append(hover_text)
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(width=2, color='white')
        ),
        text=texts,
        hovertemplate='%{text}<br>%{label}<extra></extra>',
        branchvalues='total',
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


# ============================================
# STREAMLIT UI COMPONENTS
# ============================================

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
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Area filter
        areas_response = client.table('areas').select('name').eq('user_id', user_id).order('sort_order').execute()
        area_options = ["All Areas"] + [a['name'] for a in areas_response.data]
        selected_area = st.selectbox("Filter by Area", area_options, key="graph_area_filter")
    
    with col2:
        # View type
        view_type = st.selectbox(
            "View Type",
            ["Treemap", "Sunburst", "Network Graph (Coming Soon)"],
            key="graph_view_type"
        )
    
    with col3:
        # Show events toggle
        show_events = st.checkbox("Show Events", value=True, key="graph_show_events")
    
    # Load data
    filter_area = None if selected_area == "All Areas" else selected_area
    
    with st.spinner("Loading graph data..."):
        graph_data = load_graph_data(client, user_id, filter_area)
        
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
    
    else:
        st.info("🚧 Network Graph view coming soon! This will show an Obsidian-style force-directed graph.")
    
    # Statistics
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
