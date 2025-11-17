"""Extract Greece boundary from Natural Earth data."""

import geopandas as gpd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NE_DIR = BASE_DIR / "data2" / "natural_earth" / "ne_10m_admin_0_countries"

# Find shapefile
shp_file = next(NE_DIR.glob("*.shp"), None)
if not shp_file:
    print("Natural Earth shapefile not found!")
    exit(1)

print(f"Loading {shp_file.name}...")
gdf = gpd.read_file(shp_file)

# Filter for Greece
grc = gdf[gdf['ISO_A3'] == 'GRC']
if len(grc) == 0:
    # Try alternative column names
    if 'ISO_A3_EH' in gdf.columns:
        grc = gdf[gdf['ISO_A3_EH'] == 'GRC']
    elif 'ADM0_A3' in gdf.columns:
        grc = gdf[gdf['ADM0_A3'] == 'GRC']
    elif 'NAME' in gdf.columns:
        grc = gdf[gdf['NAME'].str.contains('Greece', case=False, na=False)]

if len(grc) == 0:
    print("Greece not found! Available countries:")
    if 'ISO_A3' in gdf.columns:
        print(gdf['ISO_A3'].unique()[:20])
    exit(1)

# Convert to WGS84 and save
grc = grc.to_crs("EPSG:4326")
output = BASE_DIR / "temp_greece.geojson"
grc.to_file(output, driver="GeoJSON")
print(f"Saved Greece boundary to {output}")

