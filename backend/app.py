import asyncio
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import os

from stac_client import query_items_bbox, fetch_dem_tile, extract_geotiff_url
from hillshade import compute_hillshade, normalize_dem_simple

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


def create_synthetic_dem(width: int = 256, height: int = 256) -> Image.Image:
    """Create synthetic elevation data for demo purposes."""
    import random
    pixels = []
    for y in range(height):
        for x in range(width):
            # Create rolling hills pattern
            val = int(128 + 60 * (0.5 * (x / width) + 0.3 * (y / height)))
            val = max(0, min(255, val + random.randint(-5, 5)))
            pixels.append(val)
    img = Image.new('L', (width, height))
    img.putdata(pixels)
    return img


@app.get("/api/hillshade")
async def get_hillshade(
    minx: float, miny: float, maxx: float, maxy: float, demo: bool = False
):
    """
    Fetch DEM tiles and compute hillshade, return as PNG.

    Args:
        minx, miny, maxx, maxy: Bounding box in WGS84
        demo: Use synthetic data (default: False, requires auth)
    """
    try:
        if demo:
            # Use synthetic elevation data for testing
            dem_img = create_synthetic_dem(512, 512)
        else:
            bbox = (minx, miny, maxx, maxy)
            items = await query_items_bbox(bbox, limit=20)

            if not items:
                raise HTTPException(status_code=404, detail="No DEM tiles found for bbox")

            # Fetch first tile
            item = items[0]
            url = extract_geotiff_url(item)
            if not url:
                raise HTTPException(status_code=400, detail="No GeoTIFF asset in item")

            tile_data = await fetch_dem_tile(url)
            dem_img = Image.open(io.BytesIO(tile_data))

        # Normalize to 0-255 range
        dem_norm = normalize_dem_simple(dem_img)

        # Compute hillshade
        hillshade_img = compute_hillshade(dem_norm)

        # Convert to PNG bytes
        png_bytes = io.BytesIO()
        hillshade_img.save(png_bytes, format='PNG')
        png_bytes.seek(0)

        return StreamingResponse(
            png_bytes,
            media_type="image/png",
            headers={"Content-Disposition": "inline"}
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
