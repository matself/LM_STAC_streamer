"""
LM STAC Streamer - 3D Point Cloud Viewer
Streamlit + PyDeck for interactive terrain and point cloud visualization
"""

import streamlit as st
import pydeck as pdk
import numpy as np
import asyncio
from typing import Tuple
import os

from backend.stac_client import query_items_bbox, fetch_pointcloud_metadata, extract_pointcloud_metadata_url
from backend.pointcloud import PointCloudTile, get_ground_points, get_semantic_colors
from backend.pointcloud_synthetic import generate_synthetic_tile


# Page config
st.set_page_config(
    page_title="LM STAC Streamer - 3D Point Cloud",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Lantmäteriet 3D Point Cloud Viewer")
st.markdown("**LAZ Point Cloud Streaming & Semantic Visualization**")

# Sidebar
st.sidebar.header("Configuration")
bbox_input = st.sidebar.text_input(
    "Bounding box (minx, miny, maxx, maxy)",
    value="17.8,59.2,18.2,59.4",
    help="WGS84 coordinates for Stockholm area"
)

use_synthetic = st.sidebar.checkbox("Use synthetic data (for testing)", value=True)
max_points = st.sidebar.slider("Max points to display", 1000, 100000, 35000, step=1000)
elevation_scale = st.sidebar.slider("Elevation scale factor", 0.5, 5.0, 1.0, step=0.1)

# Parse bbox
try:
    minx, miny, maxx, maxy = map(float, bbox_input.split(','))
    bbox = (minx, miny, maxx, maxy)
except:
    st.error("Invalid bbox format. Use: minx,miny,maxx,maxy")
    st.stop()


async def fetch_real_metadata(bbox: Tuple[float, float, float, float]):
    """Fetch real point cloud metadata from Lantmäteriet STAC."""
    items = await query_items_bbox(bbox, limit=1, collection="dsm-skoglig-copc")

    if not items:
        return None

    item = items[0]
    meta_url = extract_pointcloud_metadata_url(item)

    if not meta_url:
        return None

    metadata = await fetch_pointcloud_metadata(meta_url)
    return {
        "item_id": item.get("id"),
        "bbox": item.get("bbox"),
        "metadata": metadata
    }


def get_point_cloud(bbox: Tuple[float, float, float, float], use_synthetic: bool = True):
    """Load or generate point cloud."""

    if use_synthetic:
        # Generate synthetic matching real statistics
        tile = generate_synthetic_tile(
            tile_id="demo",
            point_count=82_000_000,
            bbox=(bbox[0]*1000, bbox[1]*1000, bbox[2]*1000, bbox[3]*1000),  # Approximate projection
            elevation_range=(-4, 150),
        )
    else:
        # TODO: Load real LAZ when decompression available
        tile = generate_synthetic_tile(
            tile_id="real",
            point_count=82_000_000,
            bbox=(bbox[0]*1000, bbox[1]*1000, bbox[2]*1000, bbox[3]*1000),
            elevation_range=(-4, 150),
        )

    return tile


def create_pydeck_visualization(tile: PointCloudTile, max_points: int = 35000, elevation_scale: float = 1.0):
    """Create PyDeck 3D point cloud visualization."""

    # Downsample
    downsampled = tile.downsample(max_points)

    # Get semantic colors
    colors = get_semantic_colors(downsampled.classifications)

    # Prepare data for PyDeck
    points = downsampled.points.copy()

    # Scale elevation for visualization
    points[:, 2] = points[:, 2] * elevation_scale

    # Create DataFrame-like structure
    data = {
        'position': [points[i, :] for i in range(len(points))],
        'color': [tuple(colors[i]) for i in range(len(colors))],
        'class': downsampled.classifications.tolist(),
    }

    # Create ScatterplotLayer
    scatter = pdk.Layer(
        'ScatterplotLayer',
        data=[{'position': pos, 'color': col, 'class': cls}
              for pos, col, cls in zip(data['position'], data['color'], data['class'])],
        get_position='position',
        get_fill_color='color',
        get_radius=10,
        pickable=True,
    )

    # Initial viewport
    view_state = pdk.ViewState(
        longitude=np.mean([p[0] for p in points]) if len(points) > 0 else bbox[0],
        latitude=np.mean([p[1] for p in points]) if len(points) > 0 else bbox[1],
        zoom=13,
        pitch=45,
        bearing=0,
    )

    # Create deck
    deck = pdk.Deck(
        layers=[scatter],
        initial_view_state=view_state,
        tooltip={"text": "Class: {class}"},
    )

    return deck, downsampled


# Main content
col1, col2 = st.columns([3, 1])

with col1:
    st.header("3D Point Cloud Visualization")

    # Load data
    with st.spinner("Loading point cloud..."):
        tile = get_point_cloud(bbox, use_synthetic=use_synthetic)
        deck, downsampled = create_pydeck_visualization(tile, max_points, elevation_scale)

    st.pydeck_chart(deck)

with col2:
    st.header("Statistics")

    # Classification breakdown
    st.subheader("Classification")
    unique_classes, counts = np.unique(tile.classifications, return_counts=True)

    class_names = {
        0: "Never Classified",
        1: "Unclassified",
        2: "Ground",
        3: "Low Veg",
        4: "Medium Veg",
        5: "High Veg",
        6: "Building",
        9: "Water",
    }

    for cls, count in zip(unique_classes, counts):
        name = class_names.get(cls, f"Class {cls}")
        pct = 100 * count / len(tile)
        st.metric(name, f"{count:,}", f"{pct:.1f}%")

    st.subheader("Elevation")
    st.metric("Min", f"{tile.points[:, 2].min():.1f}m")
    st.metric("Max", f"{tile.points[:, 2].max():.1f}m")
    st.metric("Mean", f"{tile.points[:, 2].mean():.1f}m")

    st.subheader("Points")
    st.metric("Total", f"{len(tile):,}")
    st.metric("Displayed", f"{len(downsampled):,}")


# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("📍 Data: Lantmäteriet STAC API (dsm-skoglig-copc)")
with col2:
    st.caption("🎨 Rendering: PyDeck 3D")
with col3:
    st.caption("🐍 Built with: Python + Streamlit")
