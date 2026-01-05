# Vector Tiles Frontend Implementation Notes

## Current Status

✅ **Backend**: Vector tile server is implemented and working
- Endpoint: `GET /tiles/corine/{z}/{x}/{y}.mvt?country=ITA`
- Metadata endpoint: `GET /tiles/corine/metadata?country=ITA`
- MBTiles files are generated and served correctly

✅ **Frontend (Streamlit + Folium)**: 
- **Limitation**: Folium does not natively support vector tiles (MVT)
- **Current solution**: Falls back to GeoJSON (slower, but works)
- Vector tile URLs are available via `LayersAPI.get_corine_tile_url()`

## Options for Full Vector Tile Support

### Option 1: Use JavaScript-based Map Component (Recommended)

For full vector tile support in Streamlit, use `st.components.v1.html()` to embed a JavaScript map:

**Libraries to use:**
- **MapLibre GL JS** (recommended) - Open-source fork of Mapbox GL JS
- **Leaflet** + `leaflet.vectorgrid` plugin
- **OpenLayers**

**Example implementation:**
```python
import streamlit.components.v1 as components

# Generate HTML with MapLibre
html = f"""
<!DOCTYPE html>
<html>
<head>
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ width: 100%; height: 600px; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        const map = new maplibregl.Map({{
            container: 'map',
            style: {{
                version: 8,
                sources: {{
                    'openstreetmap': {{
                        type: 'raster',
                        tiles: ['https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png'],
                        tileSize: 256
                    }},
                    'corine': {{
                        type: 'vector',
                        tiles: ['{API_BASE_URL}/tiles/corine/{{z}}/{{x}}/{{y}}.mvt?country={country_code}'],
                        minzoom: 0,
                        maxzoom: 14
                    }}
                }},
                layers: [
                    {{
                        id: 'osm',
                        type: 'raster',
                        source: 'openstreetmap'
                    }},
                    {{
                        id: 'corine',
                        type: 'fill',
                        source: 'corine',
                        'source-layer': 'corine',
                        paint: {{
                            'fill-color': '#00ff00',
                            'fill-opacity': 0.2
                        }}
                    }}
                ]
            }},
            center: [{center_lon}, {center_lat}],
            zoom: {zoom}
        }});
    </script>
</body>
</html>
"""

components.html(html, height=600)
```

### Option 2: Keep GeoJSON with Optimization

- Continue using GeoJSON with Folium
- Add client-side simplification/thinning for large datasets
- Use country-specific clipping (already implemented)

### Option 3: Hybrid Approach

- Use GeoJSON for initial load (folium compatibility)
- Provide vector tile URLs for advanced users
- Add toggle to switch between modes

## Implementation Priority

1. ✅ Backend vector tile server - **DONE**
2. ✅ MBTiles generation - **DONE**
3. ✅ API client methods for vector tiles - **DONE**
4. ⏳ JavaScript map component (Option 1) - **TODO**
5. ⏳ Fallback handling - **Partially done**

## Testing Vector Tiles

Test the vector tile endpoint:
```python
from frontend.src.api_client import LayersAPI

# Get tile URL
tile_url = LayersAPI.get_corine_tile_url(z=2, x=2, y=1, country="ITA")
print(f"Tile URL: {tile_url}")

# Get metadata
metadata = LayersAPI.get_corine_tiles_metadata(country="ITA")
print(f"Bounds: {metadata['bounds']}")
```

## Performance Comparison

- **Vector Tiles**: Fast, efficient, loads only visible tiles
- **GeoJSON**: Slower, loads entire dataset, can timeout on large files

For CORINE Italy (~600 MB GeoJSON), vector tiles are **strongly recommended**.

