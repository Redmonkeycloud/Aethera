# Vector Tiles Implementation for CORINE

## Status: ✅ Infrastructure Created

Vector tiles infrastructure has been set up. Now you need to:

1. Install tippecanoe
2. Generate tiles
3. Update frontend

## What's Been Created

✅ **Backend Tile Server** (`backend/src/api/routes/tiles.py`)
   - Endpoint: `GET /tiles/corine/{z}/{x}/{y}.mvt`
   - Serves tiles from MBTiles database
   - Supports country-specific tiles

✅ **Tile Generation Script** (`scripts/generate_corine_tiles.py`)
   - Uses tippecanoe to generate tiles
   - Creates MBTiles format (.mbtiles file)

✅ **Documentation** (`VECTOR_TILES_SETUP.md`)
   - Installation instructions
   - Usage examples

## Quick Start

### Step 1: Install Tippecanoe

**Windows:**
- Download from: https://github.com/felt/tippecanoe/releases
- Extract and add to PATH
- Or try: `pip install tippecanoe-tool` (if available)

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install tippecanoe

# Mac
brew install tippecanoe
```

### Step 2: Generate Tiles

```bash
cd D:\AETHERA_2.0
python scripts/generate_corine_tiles.py --country ITA --method tippecanoe
```

This will create: `data2/corine/tiles/ITA/corine_ITA.mbtiles`

**Note:** Tile generation can take 10-30 minutes for large datasets.

### Step 3: Verify Tiles

Check that the MBTiles file was created:
```bash
# Should exist after generation
data2/corine/tiles/ITA/corine_ITA.mbtiles
```

### Step 4: Test Tile Server

Once backend is running, test the endpoint:
```
http://localhost:8001/tiles/corine/10/500/400.mvt?country=ITA
```

### Step 5: Update Frontend

Update the frontend to use vector tiles instead of GeoJSON (see next section).

## Frontend Integration

To use vector tiles in the frontend, you'll need to use a library that supports MVT.

### Option 1: Folium with VectorGridProtobuf

```python
import folium
from folium.plugins import VectorGridProtobuf

# Add vector tile layer
vector_layer = VectorGridProtobuf(
    url_template="http://localhost:8001/tiles/corine/{z}/{x}/{y}.mvt?country=ITA",
    options={
        "vectorTileLayerStyles": {
            "corine": {
                "fill": True,
                "fillColor": "#00ff00",
                "fillOpacity": 0.3,
                "color": "#006400",
                "weight": 1
            }
        }
    }
)
vector_layer.add_to(map)
```

### Option 2: Leaflet with Leaflet.VectorGrid

If using Leaflet directly, you'll need the Leaflet.VectorGrid plugin.

## How It Works

1. **Tile Generation**: Tippecanoe converts the 591 MB GeoJSON into many small tile files stored in an MBTiles database
2. **Tile Serving**: Backend extracts individual tiles from MBTiles based on zoom/x/y coordinates
3. **Tile Loading**: Frontend only loads tiles for the visible map area
4. **Performance**: Only visible tiles are transferred (typically 50-200 KB per tile vs 591 MB for full dataset)

## Expected Performance

- **Tile Generation**: 10-30 minutes (one-time)
- **Tile Size**: ~50-200 KB per tile (depends on zoom level)
- **Load Time**: < 1 second per tile
- **Total Load**: Only loads ~10-50 tiles for visible area (5-10 MB total)

## Benefits

✅ Fast loading (only visible tiles)
✅ Scalable (works for any dataset size)
✅ Efficient (tiles are cached)
✅ Progressive (lower zoom = less detail)
✅ Standard format (compatible with all mapping libraries)

## Troubleshooting

**Tippecanoe not found:**
- Make sure it's installed and in PATH
- Try: `tippecanoe --version` to verify

**Tiles not generating:**
- Check file path is correct
- Ensure GeoJSON file exists
- Check disk space (tiles can be large)

**Tiles not serving:**
- Check MBTiles file exists
- Verify backend is running
- Check backend logs for errors

## Next Steps After Tiles Are Generated

1. Test tile endpoint works
2. Update frontend code to use vector tiles
3. Test performance
4. Consider generating tiles for GRC as well

