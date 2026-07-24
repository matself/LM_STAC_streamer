# LM STAC Streamer – Project Context

## Overview
Web-based terrain hillshade service streaming elevation data from Lantmäteriet's STAC API. Started July 24, 2026.

## Current State (Phase 1)
**Working MVP**: Interactive Leaflet map with draw-to-fetch hillshade computation.

### What's Done
- ✅ FastAPI backend with `/api/hillshade` endpoint
- ✅ Leaflet.Draw UI for rectangular selections
- ✅ PIL-based hillshade algorithm (gradient → lighting model)
- ✅ Demo mode with synthetic elevation (no auth needed)
- ✅ Image overlay on map
- ✅ Responsive design (pan/zoom)

### Tech Decisions
- **PIL only**: Avoided rasterio/numpy due to Python 3.14 compatibility issues (libraries not built for 3.14 yet)
- **Async httpx**: For non-blocking STAC queries and tile downloads
- **Synthetic demo**: Real Lantmäteriet URLs require auth; demo mode proves the pipeline works
- **No tiles yet**: Phase 1 is single-tile proof-of-concept; tiling comes in Phase 2

## Known Issues & Workarounds
1. **Lantmäteriet authentication**: Download URLs return 401 without valid credentials
   - Workaround: Demo mode uses synthetic DEM
   - Real data: Need to register at lantmateriet.se and store API keys

2. **Hillshade quality**: Current algorithm is simplified (not true differential-based hillshade)
   - Good enough for demo
   - Replace with proper scipy.ndimage gradients when Python 3.14 wheels ship

3. **SSL verification**: STAC API required `verify=False` for httpx (cert chain issue)
   - Note: Should investigate proper cert for production

## Architecture Notes
- **Separation**: Backend (Python/FastAPI) ↔ Frontend (vanilla JS/Leaflet)
- **Stateless**: No persistent state; each request is independent
- **Async-ready**: Backend uses async httpx for scaling
- **Browser-friendly**: Single HTML file, no build step

## Testing
Manual browser testing works:
1. Draw rectangle on map → hillshade computes
2. See image overlay update in real-time
3. Pan/zoom works normally

No automated tests yet; Phase 2 should add pytest suite.

## For Next Developer
### To resume work:
1. `python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000`
2. Navigate to http://localhost:8000
3. Try drawing a rectangle

### To add real data:
1. Register at https://www.lantmateriet.se/
2. Get API access to STAC and tile URLs
3. Store credentials (env vars or .env)
4. Remove `verify=False` from httpx, add auth header
5. Test with a real tile (may take 5-10s first time due to download)

### To improve hillshade:
- Import scipy.ndimage gradients (will need to wait for Python 3.14 wheels)
- Implement proper Zevenbergen-Thorne slope/aspect algorithm
- Add user-controllable azimuth/altitude sliders in UI

### To tile output:
- Slice large DEMs into z/x/y tiles
- Cache computed tiles locally
- Serve via WMTS endpoint

## Dependencies
- Python 3.14.6 (Windows, current stable)
- FastAPI 0.104.1
- Uvicorn 0.24.0
- Pillow 10.1.0 (pre-built wheels; source build fails on 3.14)
- httpx 0.25.1

## Resources
- Lantmäteriet STAC: https://api.lantmateriet.se/stac-hojd/v1/
- Leaflet docs: https://leafletjs.com
- FastAPI docs: https://fastapi.tiangolo.com
