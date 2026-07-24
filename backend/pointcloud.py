"""
LAZ point cloud streaming from Lantmäteriet STAC API.
Parses ASPRS classifications (Ground=2, Water=9, Vegetation=4-5, etc.)
"""

import laspy
import numpy as np
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass


# ASPRS Classification codes
ASPRS_CODES = {
    0: "Never Classified",
    1: "Unclassified",
    2: "Ground",
    3: "Low Vegetation",
    4: "Medium Vegetation",
    5: "High Vegetation",
    6: "Building",
    7: "Low Point (noise)",
    8: "Reserved",
    9: "Water",
    10: "Rail",
    11: "Road Surface",
    12: "Reserved",
    13: "Wire - Guard (Shield)",
    14: "Wire - Conductor (Phase)",
    15: "Transmission Tower",
    16: "Wire - Structure Connector",
    17: "Bridge Deck",
    18: "High Noise",
    19: "Overhead Structure",
    20: "Ignored Ground",
    21: "Snow",
    22: "Temporal Exclusion",
}


@dataclass
class PointCloudTile:
    """Parsed LAZ point cloud tile with semantic classification."""

    id: str  # STAC item ID
    points: np.ndarray  # Nx3 array (x, y, z)
    classifications: np.ndarray  # Nx1 classification codes
    intensities: Optional[np.ndarray] = None
    returns: Optional[np.ndarray] = None

    @property
    def point_count(self) -> int:
        return len(self.points)

    def filter_by_class(self, class_code: int) -> "PointCloudTile":
        """Extract points of a specific ASPRS class."""
        mask = self.classifications == class_code
        return PointCloudTile(
            id=f"{self.id}_class_{class_code}",
            points=self.points[mask],
            classifications=self.classifications[mask],
            intensities=self.intensities[mask] if self.intensities is not None else None,
            returns=self.returns[mask] if self.returns is not None else None,
        )

    def downsample(self, target_points: int = 35000) -> "PointCloudTile":
        """Reduce points while preserving classification distribution."""
        if len(self.points) <= target_points:
            return self

        ratio = target_points / len(self.points)
        indices = np.random.choice(
            len(self.points),
            size=int(len(self.points) * ratio),
            replace=False
        )

        return PointCloudTile(
            id=f"{self.id}_downsampled_{target_points}",
            points=self.points[indices],
            classifications=self.classifications[indices],
            intensities=self.intensities[indices] if self.intensities is not None else None,
            returns=self.returns[indices] if self.returns is not None else None,
        )


def parse_laz_file(filepath: str) -> PointCloudTile:
    """Parse LAZ/COPC file and extract point cloud data."""
    las = laspy.read(filepath)

    # Extract XYZ coordinates
    points = np.vstack((las.x, las.y, las.z)).T

    # Extract classification
    classifications = las.classification

    # Extract optional fields
    intensities = getattr(las, 'intensity', None)
    return_num = getattr(las, 'return_num', None)

    return PointCloudTile(
        id=filepath,
        points=points,
        classifications=classifications,
        intensities=intensities,
        returns=return_num,
    )


def get_ground_points(tile: PointCloudTile) -> PointCloudTile:
    """Extract only ground points (ASPRS class 2) for terrain."""
    return tile.filter_by_class(2)


def get_semantic_colors(classifications: np.ndarray) -> np.ndarray:
    """
    Map ASPRS classifications to RGB colors for visualization.

    Returns Nx3 array with RGB values (0-255).
    """
    colors = np.zeros((len(classifications), 3), dtype=np.uint8)

    # Color mapping by class
    class_colors = {
        0: (200, 200, 200),    # Never Classified: gray
        1: (100, 100, 100),    # Unclassified: dark gray
        2: (139, 90, 43),      # Ground: brown
        3: (34, 139, 34),      # Low Veg: forest green
        4: (50, 205, 50),      # Medium Veg: lime green
        5: (0, 100, 0),        # High Veg: dark green
        6: (255, 0, 0),        # Building: red
        7: (255, 255, 0),      # Low Point: yellow (noise)
        9: (0, 0, 255),        # Water: blue
        11: (128, 128, 128),   # Road: gray
        17: (200, 100, 0),     # Bridge: orange-brown
    }

    for class_code, rgb in class_colors.items():
        mask = classifications == class_code
        colors[mask] = rgb

    # Default color for unmapped classes
    default_color = (200, 200, 200)  # light gray
    unset_mask = np.all(colors == 0, axis=1)
    colors[unset_mask] = default_color

    return colors


def compute_terrain_dem(ground_points: np.ndarray, grid_size: int = 256) -> np.ndarray:
    """
    Rasterize ground points to DEM grid.

    Args:
        ground_points: Nx3 array of (x, y, z) coordinates
        grid_size: Output grid dimensions (pixels per side)

    Returns:
        grid_size x grid_size elevation array
    """
    if len(ground_points) == 0:
        return np.zeros((grid_size, grid_size))

    # Create grid from point extent
    minx, miny = ground_points[:, :2].min(axis=0)
    maxx, maxy = ground_points[:, :2].max(axis=0)

    # Bin points to grid
    grid = np.zeros((grid_size, grid_size))
    grid_x = (grid_size - 1) * (ground_points[:, 0] - minx) / (maxx - minx + 0.001)
    grid_y = (grid_size - 1) * (ground_points[:, 1] - miny) / (maxy - miny + 0.001)

    grid_x = np.clip(grid_x, 0, grid_size - 1).astype(int)
    grid_y = np.clip(grid_y, 0, grid_size - 1).astype(int)

    # Assign max elevation (DSM/DTM effect)
    for i in range(len(ground_points)):
        grid[grid_y[i], grid_x[i]] = max(grid[grid_y[i], grid_x[i]], ground_points[i, 2])

    return grid
