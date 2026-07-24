import httpx
import json
import os
from typing import List, Dict, Any, Tuple, Optional


STAC_BASE = "https://api.lantmateriet.se/stac-hojd/v1"
COLLECTION = "dtm-cog"

# Get credentials from environment variables
STAC_USERNAME = os.getenv("LANTMATERIET_USERNAME")
STAC_PASSWORD = os.getenv("LANTMATERIET_PASSWORD")


async def query_items_bbox(bbox: Tuple[float, float, float, float], limit: int = 100) -> List[Dict[str, Any]]:
    """
    Query STAC collection for items intersecting a bounding box.

    Args:
        bbox: (minx, miny, maxx, maxy) in WGS84
        limit: Max items to return

    Returns:
        List of item dictionaries
    """
    auth = None
    if STAC_USERNAME and STAC_PASSWORD:
        auth = (STAC_USERNAME, STAC_PASSWORD)

    async with httpx.AsyncClient(verify=False, auth=auth) as client:
        url = f"{STAC_BASE}/collections/{COLLECTION}/items"
        params = {
            "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            "limit": limit
        }
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("features", [])


async def fetch_dem_tile(asset_url: str) -> bytes:
    """Download a GeoTIFF tile with Basic Auth if configured."""
    auth = None
    if STAC_USERNAME and STAC_PASSWORD:
        auth = (STAC_USERNAME, STAC_PASSWORD)

    async with httpx.AsyncClient(verify=False, auth=auth) as client:
        resp = await client.get(asset_url)
        resp.raise_for_status()
        return resp.content


def extract_geotiff_url(item: Dict[str, Any]) -> str:
    """Extract the GeoTIFF asset URL from a STAC item."""
    if "assets" in item and "data" in item["assets"]:
        return item["assets"]["data"]["href"]
    return None
