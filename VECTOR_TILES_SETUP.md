# Vector Tiles (MVT) Setup for CORINE

## Overview

Vector Tiles (Mapbox Vector Tiles format) is the recommended solution for serving large geospatial datasets like CORINE. Instead of loading the entire 591 MB file, only visible tiles are loaded as the user pans and zooms.

## Installation

### Option 1: Tippecanoe (Recommended)

Tippecanoe is the industry-standard tool for generating vector tiles from large datasets.

**Windows:**
1. Download from: https://github.com/felt/tippecanoe/releases
2. Extract and add to PATH
3. Or use: `pip install tippecanoe-tool` (if available)

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install tippecanoe

# Mac
brew install tippecanoe
```

### Option 2: Python Libraries

```bash
pip install mapbox-vector-tile geopandas shapely
```

Note: Python-based tile generation is much slower for large datasets. Tippecanoe is recommended.

## Generating Tiles

### Using Tippecanoe (Recommended)

```bash
cd D:\AETHERA_2.0
python scripts/generate_corine_tiles.py --country ITA --method tippecanoe
```

This will:
1. Read the CORINE GeoJSON/shapefile
2. Generate vector tiles (MBTiles format)
3. Save to `data2/corine/tiles/ITA/`

### Tile Generation Process

The script generates tiles at zoom levels 0-14:
- Zoom 0: Entire country visible
- Zoom 14: Maximum detail (building level)
- Features are automatically simplified based on zoom level

## Serving Tiles

We need to create a tile server endpoint in the backend:

```
GET /tiles/corine/{z}/{x}/{y}.mvt
```

Where:
- `z`: Zoom level (0-14)
- `x`: Tile X coordinate
- `y`: Tile Y coordinate

## Frontend Integration

Update the frontend to use vector tiles with Folium/Leaflet:

```python
# Using folium.plugins.VectorGridProtobuf or similar
vector_tile_layer = folium.plugins.VectorGridProtobuf(
    url_template="http://localhost:8001/tiles/corine/{z}/{x}/{y}.mvt",
    options={"vectorTileLayerStyles": {...}}
)
```

## Benefits

1. **Fast Loading**: Only visible tiles are loaded
2. **Scalable**: Works for datasets of any size
3. **Efficient**: Tiles are cached by browsers
4. **Progressive**: Lower zoom = fewer features
5. **Standard**: Compatible with all major mapping libraries

## File Structure

```
data2/
  corine/
    corine_ITA.shp          # Original shapefile
    corine_ITA.geojson      # Pre-converted GeoJSON
    tiles/
      ITA/
        corine_ITA.mbtiles  # Generated tiles (MBTiles format)
```

## Next Steps

1. ✅ Create tile generation script
2. ⏳ Install tippecanoe
3. ⏳ Generate tiles for ITA (and GRC if needed)
4. ⏳ Create tile server endpoint
5. ⏳ Update frontend to use vector tiles
6. ⏳ Test performance

## References

- Tippecanoe: https://github.com/felt/tippecanoe
- Mapbox Vector Tiles: https://github.com/mapbox/vector-tile-spec
- Folium Vector Tiles: https://python-visualization.github.io/folium/plugins.html

