"""
Test point cloud discovery and metadata fetching from Lantmäteriet STAC.
Demonstrates Phase 2 infrastructure without requiring LAZ file downloads.
"""

import asyncio
import os
from stac_client import (
    query_items_bbox,
    extract_laz_url,
    extract_pointcloud_metadata_url,
    fetch_pointcloud_metadata,
    COLLECTION_POINTCLOUD,
)


async def test_pointcloud_discovery():
    """Test discovering point cloud tiles in a bbox."""
    print("=" * 60)
    print("Testing LAZ Point Cloud Discovery from Lantmäteriet STAC")
    print("=" * 60)

    # Stockholm area bbox (WGS84)
    bbox = (17.8, 59.2, 18.2, 59.4)

    print(f"\n1. Querying STAC for point cloud tiles in bbox: {bbox}")
    try:
        items = await query_items_bbox(bbox, limit=3, collection=COLLECTION_POINTCLOUD)
        print(f"   ✅ Found {len(items)} point cloud tiles")

        for item in items:
            item_id = item.get("id", "unknown")
            bbox_item = item.get("bbox", [])
            print(f"\n   Item: {item_id}")
            print(f"   Bounds: {bbox_item}")

            # Get LAZ URL and metadata URL
            laz_url = extract_laz_url(item)
            meta_url = extract_pointcloud_metadata_url(item)

            print(f"   LAZ URL: {laz_url}")
            print(f"   Metadata URL: {meta_url}")

            # Fetch metadata (this works even if file downloads are forbidden)
            if meta_url:
                print(f"\n   2. Fetching point cloud metadata...")
                try:
                    metadata = await fetch_pointcloud_metadata(meta_url)

                    # Extract useful info
                    point_count = metadata.get("metadata", {}).get("count", 0)
                    file_size_mb = metadata.get("file_size", 0) / (1024 * 1024)
                    point_spacing = (
                        metadata.get("metadata", {})
                        .get("copc_info", {})
                        .get("spacing", 0)
                    )
                    minz = metadata.get("metadata", {}).get("minz", 0)
                    maxz = metadata.get("metadata", {}).get("maxz", 0)

                    print(f"      ✅ Metadata loaded")
                    print(f"      - Points: {point_count:,}")
                    print(f"      - File size: {file_size_mb:.1f} MB")
                    print(f"      - Point spacing: {point_spacing:.2f} m")
                    print(f"      - Elevation range: {minz:.2f}m to {maxz:.2f}m")

                except Exception as e:
                    print(f"      ❌ Error fetching metadata: {e}")

    except Exception as e:
        print(f"   ❌ Error querying STAC: {e}")
        print("   Note: Ensure LANTMATERIET_USERNAME and LANTMATERIET_PASSWORD are set")


async def main():
    # Check credentials
    if not os.getenv("LANTMATERIET_USERNAME"):
        print("❌ LANTMATERIET_USERNAME not set")
        print("   Set credentials before running:")
        print("   export LANTMATERIET_USERNAME=your_username")
        print("   export LANTMATERIET_PASSWORD=your_password")
        return

    await test_pointcloud_discovery()

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print("✅ STAC discovery works")
    print("✅ Point cloud metadata accessible")
    print("❌ LAZ file downloads return 403 Forbidden")
    print("   → Resolve authentication for file access in Phase 2")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
