# WDPA Format Recommendation

## Recommended: **Shapefile (SHP)**

**Format**: Shapefile (SHP)

## Why Shapefile?

### ✅ Advantages:
1. **Vector Geospatial Format**: 
   - Preserves geometry (polygons for protected areas)
   - Essential for spatial operations (intersection, clipping, etc.)

2. **Well-Supported**:
   - GeoPandas reads Shapefiles natively
   - No additional dependencies needed
   - Standard format widely used in GIS

3. **Compatible with Our Codebase**:
   - We're already using Shapefiles for other datasets
   - Catalog already configured for Shapefiles
   - Backend code expects vector GeoDataFrames

4. **Simple Structure**:
   - Easy to work with
   - No special drivers needed
   - Direct compatibility with our tools

### Why NOT the Others?

- **CSV**: 
  - ❌ Loses geometry information
  - ❌ Not suitable for spatial data
  - ❌ Would need WKT columns, complex to work with
  - ❌ Can't perform spatial operations directly

- **PDF**: 
  - ❌ Not a geospatial data format
  - ❌ Just documentation/maps, not data
  - ❌ Can't be read by GeoPandas

- **File Geodatabase**: 
  - ⚠️ Works but more complex
  - ⚠️ Requires additional drivers (fiona with GDB support)
  - ⚠️ More complex folder structure
  - ✅ Shapefile is simpler and equally functional

## After Download

1. **Download Shapefile format** from ProtectedPlanet

2. **Extract the ZIP file** (WDPA downloads come as ZIP archives)

3. **Find the shapefile** (usually named something like `WDPA_*.shp`)

4. **Save to project**:
   - Italy: `data2/protected_areas/wdpa/wdpa_ITA.shp`
   - Greece: `data2/protected_areas/wdpa/wdpa_GRC.shp`

5. **Tag the dataset**:
   ```bash
   python scripts/download_datasets.py
   ```

6. **Note**: WDPA files include all protected areas (not just Natura 2000), so this complements the Natura 2000 data.

## Summary

**Download: Shapefile (SHP) format**

This is the standard format for vector geospatial data and the best choice for our use case!

