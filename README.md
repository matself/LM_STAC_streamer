# LM STAC Streamer – Terrain Hillshade Service

Web-based terrain visualization using Lantmäteriet's elevation data STAC API to compute and display hillshade maps.

## Phase 1: Interactive Hillshade Viewer ✅

**Current Status**: Working with synthetic demo data

- Interactive Leaflet map centered on Stockholm
- Draw rectangles to fetch and compute hillshade
- Real-time hillshade computation with PIL
- Image overlay display on map
- Responsive pan/zoom interaction

### Features
- **Draw tool**: Select regions of interest with rectangles
- **Auto-fetch**: Hillshade computes automatically on draw
- **Synthetic demo**: Built-in demo mode for testing (no auth needed)
- **Real data support**: Ready to connect to Lantmäteriet STAC API (requires auth)

## Data Source
- **STAC API**: https://api.lantmateriet.se/stac-hojd/v1/
- **Collection**: `dtm-cog` (Digital Terrain Model, 1m resolution, CC-BY-4.0)
- **Format**: Cloud-Optimized GeoTIFF (512×512 tiles, ~8.9 MB each)
- **Coverage**: All of Sweden (EPSG:5845 Swedish grid)
- **Note**: Download URLs require Lantmäteriet authentication

## Tech Stack
- **Backend**: Python 3.14 + FastAPI + Uvicorn
- **Frontend**: Leaflet.js + Leaflet.Draw + OpenStreetMap
- **Image Processing**: PIL (Pillow) + manual gradient computation
- **HTTP Client**: httpx (async)

## Quick Start

### Install
```bash
pip install -r requirements.txt
```

### Run
```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
# Open http://localhost:8000
```

### Use
1. Click "Draw a rectangle" tool (top-left)
2. Draw a box on the map
3. Hillshade computes automatically
4. Watch the elevation pattern render as a grayscale overlay

## Architecture

### Backend (`backend/`)
- **app.py**: FastAPI server, static file serving, `/api/hillshade` endpoint
- **stac_client.py**: STAC catalog queries, tile fetching
- **hillshade.py**: Elevation → hillshade computation, PIL image handling

### Frontend (`frontend/`)
- **index.html**: Single-page app with Leaflet map, draw tool, image overlay

### API

#### GET `/api/hillshade`
Compute hillshade for a bounding box.

**Query Parameters**:
- `minx, miny, maxx, maxy` (float): WGS84 bounding box
- `demo` (bool): Use synthetic data (default false; set true to avoid auth)

**Response**: PNG image (grayscale hillshade)

**Example**:
```
GET http://localhost:8000/api/hillshade?minx=17.5&miny=58.5&maxx=19.5&maxy=60.5&demo=true
```

## Hillshade Algorithm

Currently using a simple PIL-based approach:
1. Load elevation grid (DEM)
2. Enhance contrast for visibility
3. Compute local slope/aspect (simplified)
4. Apply simulated lighting (northwest azimuth, 45° altitude)
5. Render as 8-bit grayscale PNG

## Next Steps

### Phase 2: Real Lantmäteriet Data + Tiling
- [ ] Register for Lantmäteriet API access (free, CC-BY-4.0)
- [ ] Implement tile caching (Redis or local)
- [ ] Support WMTS output (pre-tiled Z/X/Y)
- [ ] Optimize for larger regions (multi-tile stitching)

### Phase 3: WMS Service
- [ ] Wrap in OGC WMS/WMTS standard (GeoServer or custom)
- [ ] GetCapabilities document
- [ ] Style/rendering options (azimuth, altitude, contrast)
- [ ] Publish as standard map service

### Future Enhancements
- Combine with vector layers (roads, buildings from stac-vektor)
- 3D visualization (Deck.gl, Cesium)
- Satellite/aerial imagery overlay
- Export to GeoTIFF, COG
- Streaming tiles for performance

## Notes on Authentication

Lantmäteriet's STAC collection is **free and open** (CC-BY-4.0), but the tile download URLs require registration:
- Register at https://www.lantmateriet.se/
- Request API access (free tier available)
- URLs are per-user authenticated

For production, consider:
- Tile mirroring/caching to avoid auth throttling
- CloudFront or similar CDN for public tiles
- Server-side credential storage (API key per request)

## File Structure
```
C:\GITHUB\LM_STAC_streamer\
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── backend/
│   ├── app.py            # FastAPI server
│   ├── stac_client.py    # STAC queries
│   └── hillshade.py      # Image processing
├── frontend/
│   └── index.html        # Web UI
└── .gitignore
```
