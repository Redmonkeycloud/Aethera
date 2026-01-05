# CORINE Format Recommendation

## Recommended: **Vector GPKG** (GeoPackage)

**File**: `u2018_clc2018_v2020_20u1_geoPackage`  
**Size**: 4 GB  
**Format**: Vector GeoPackage

## Why GPKG?

### ✅ Advantages:
1. **Vector Data Required**: We need vector polygons for:
   - Land cover classification analysis
   - Extracting agricultural lands (codes 2xx)
   - Extracting forests (codes 3xx)
   - Spatial operations (clipping, intersection, etc.)

2. **Smaller File Size**: 4 GB vs 5 GB (GDB format)

3. **Modern Standard**: GeoPackage is an open standard (OGC standard)

4. **Good Support**: 
   - GeoPandas reads GPKG natively
   - Well-supported format
   - Single file (easier to manage than GDB folder structure)

5. **Compatible**: Works with our existing codebase that uses GeoPandas

### Why NOT Raster?
- **Raster Geotiff (125 MB)** is NOT suitable because:
  - We need vector polygons for land use classes
  - Can't easily extract specific land cover categories (agricultural, forests)
  - Backend analysis expects vector GeoDataFrames
  - Our extraction scripts (`extract_agricultural_lands.py`, `extract_forests_from_corine.py`) work with vector data

### Why NOT GDB?
- **File Geodatabase (5 GB)** is larger
- GPKG is more portable (single file)
- GPKG is equally well-supported

## After Download

1. **Download the GPKG file** (4 GB)

2. **If you prefer Shapefile format** (more reliable based on our earlier experience):
   - Can convert GPKG to Shapefile using QGIS or Python:
   ```python
   import geopandas as gpd
   gdf = gpd.read_file("u2018_clc2018_v2020_20u1_geoPackage.gpkg")
   gdf.to_file("corine_GRC.shp", driver="ESRI Shapefile")
   ```
   - Or keep as GPKG - both work with GeoPandas

3. **Clip to Greece** (if needed):
   - If the download is Europe-wide, clip to Greece boundary
   - Use GADM boundary: `data2/gadm/gadm41_GRC_shp/gadm41_GRC_0.shp`

4. **Save as**: `data2/corine/corine_GRC.gpkg` or `corine_GRC.shp`

5. **Process**:
   ```bash
   # Tag the dataset
   python scripts/download_datasets.py
   
   # Extract agricultural lands
   python scripts/extract_agricultural_lands.py --country GRC
   
   # Extract forests
   python scripts/extract_forests_from_corine.py --country GRC
   ```

## Summary

**Download: Vector GPKG format**  
**File**: `u2018_clc2018_v2020_20u1_geoPackage`  
**Size**: 4 GB

This is the best choice for our use case!

