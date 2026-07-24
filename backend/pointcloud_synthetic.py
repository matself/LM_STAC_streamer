"""
Synthetic point cloud generation from point cloud metadata.

Since LAZ downloads are 403 Forbidden, we can:
1. Fetch real point cloud metadata (point counts, spacing, elevation ranges)
2. Generate synthetic point clouds that match the metadata
3. This lets us test the full pipeline without needing actual LAZ files

For production: Replace with real LAZ parsing once download access is enabled.
"""

import numpy as np
from typing import Tuple
from pointcloud import PointCloudTile, get_ground_points, compute_terrain_dem


def generate_synthetic_ground_points(
    point_count: int = 82000000,
    bbox: Tuple[float, float, float, float] = (570000, 6270000, 575000, 6275000),
    elevation_range: Tuple[float, float] = (-4, 150),
) -> np.ndarray:
    """
    Generate synthetic ground points (ASPRS class 2) matching real metadata.

    Args:
        point_count: Total points in the tile (from metadata)
        bbox: (minx, miny, maxx, maxy) spatial extent
        elevation_range: (min_z, max_z) elevation range from metadata

    Returns:
        Nx3 array of (x, y, z) coordinates
    """
    minx, miny, maxx, maxy = bbox
    min_z, max_z = elevation_range

    # Ground points: 70% of total (typical for Swedish terrain with forest)
    ground_count = int(point_count * 0.7)

    # Random XY distribution
    x = np.random.uniform(minx, maxx, ground_count)
    y = np.random.uniform(miny, maxy, ground_count)

    # Realistic elevation: more variation at higher elevations
    z = np.random.normal(
        loc=(min_z + max_z) / 2,
        scale=(max_z - min_z) / 4,
        size=ground_count
    )
    z = np.clip(z, min_z, max_z)

    return np.vstack((x, y, z)).T


def generate_synthetic_tile(
    tile_id: str,
    point_count: int = 82000000,
    bbox: Tuple[float, float, float, float] = (570000, 6270000, 575000, 6275000),
    elevation_range: Tuple[float, float] = (-4, 150),
) -> PointCloudTile:
    """
    Create a full synthetic point cloud tile with all ASPRS classes.

    Distribution (realistic for Swedish terrain):
    - Ground (2): 70%
    - Low veg (3): 5%
    - Medium veg (4): 8%
    - High veg (5): 10%
    - Water (9): 2%
    - Buildings (6): 3%
    - Other: <1%
    """
    minx, miny, maxx, maxy = bbox
    min_z, max_z = elevation_range

    # Classification distribution
    counts = {
        2: int(point_count * 0.70),  # Ground
        3: int(point_count * 0.05),  # Low veg
        4: int(point_count * 0.08),  # Medium veg
        5: int(point_count * 0.10),  # High veg
        9: int(point_count * 0.02),  # Water
        6: int(point_count * 0.03),  # Buildings
        1: int(point_count * 0.02),  # Unclassified
    }

    points_list = []
    classifications_list = []

    for class_code, count in counts.items():
        if count == 0:
            continue

        # XY distribution
        x = np.random.uniform(minx, maxx, count)
        y = np.random.uniform(miny, maxy, count)

        # Elevation varies by class
        if class_code == 2:  # Ground: varies across range
            z = np.random.uniform(min_z, max_z, count)
        elif class_code in [3, 4, 5]:  # Vegetation: above ground
            ground_z = np.random.uniform(min_z, max_z, count)
            height = np.random.exponential(scale=5, size=count)
            z = ground_z + height
        elif class_code == 6:  # Buildings: taller than vegetation
            ground_z = np.random.uniform(min_z, max_z, count)
            height = np.random.uniform(10, 50, count)
            z = ground_z + height
        elif class_code == 9:  # Water: at local minima
            z = np.ones(count) * (min_z + 2)
        else:  # Other
            z = np.random.uniform(min_z, max_z, count)

        z = np.clip(z, min_z, min_z + 1000)  # Realistic ceiling

        points_list.append(np.vstack((x, y, z)).T)
        classifications_list.append(np.full(count, class_code))

    # Combine all points
    points = np.vstack(points_list)
    classifications = np.concatenate(classifications_list)

    # Shuffle to randomize order
    indices = np.random.permutation(len(points))
    points = points[indices]
    classifications = classifications[indices]

    return PointCloudTile(
        id=f"{tile_id}_synthetic",
        points=points,
        classifications=classifications,
    )


def demo_synthetic_pipeline():
    """Test full point cloud pipeline with synthetic data."""
    print("=" * 60)
    print("Synthetic Point Cloud Pipeline Demo")
    print("=" * 60)

    # Create synthetic tile matching Stockholm data
    print("\n1. Generating synthetic point cloud tile...")
    tile = generate_synthetic_tile(
        tile_id="synthetic-test",
        point_count=82_000_000,
        bbox=(570000, 6270000, 575000, 6275000),
        elevation_range=(-4, 150),
    )
    print(f"   [OK] Created {tile.point_count:,} points")

    # Extract ground points
    print("\n2. Extracting ground points (ASPRS class 2)...")
    ground = get_ground_points(tile)
    print(f"   [OK] Ground points: {ground.point_count:,}")
    print(f"      Elevation: {ground.points[:, 2].min():.1f}m to {ground.points[:, 2].max():.1f}m")

    # Downsample for visualization
    print("\n3. Downsampling to 35K points...")
    downsampled = ground.downsample(35000)
    print(f"   [OK] Downsampled: {downsampled.point_count:,} points")

    # Compute DEM from ground points
    print("\n4. Rasterizing ground points to DEM...")
    dem = compute_terrain_dem(downsampled.points, grid_size=512)
    print(f"   [OK] DEM created: 512x512 grid")
    print(f"      Elevation range: {dem.min():.1f}m to {dem.max():.1f}m")
    print(f"      Mean elevation: {dem[dem > 0].mean():.1f}m")

    # Semantic statistics
    print("\n5. Classification statistics...")
    unique, counts = np.unique(tile.classifications, return_counts=True)
    for cls, count in zip(unique, counts):
        pct = 100 * count / tile.point_count
        print(f"   Class {cls}: {count:,} points ({pct:.1f}%)")

    print("\n" + "=" * 60)
    print("[OK] Full pipeline works with synthetic data!")
    print("   Once LAZ downloads are enabled:")
    print("   - Replace generate_synthetic_tile() with parse_laz_file()")
    print("   - All downstream processing stays the same")
    print("=" * 60)


if __name__ == "__main__":
    demo_synthetic_pipeline()
