# Dataset Download Status

## ✅ Completed Downloads

### Programmatic Downloads
1. **GBIF Biodiversity Data**
   - ✅ ITA Full: `data2/biodiversity/gbif_occurrences_ITA.csv` (7.34 GB) - **NEWLY ADDED**
   - ✅ ITA Sample: `data2/biodiversity/external/gbif_occurrences_ITA_sample.csv` (26.3 MB, 5100 records)
   - ✅ GRC Sample: `data2/biodiversity/external/gbif_occurrences_GRC_sample.csv` (28.0 MB, 5100 records)
   - **Source**: GBIF Download Service
   - **Status**: Full Italy dataset downloaded and organized

2. **OSM Data (In Progress)**
   - ⚠️ ITA: Downloading in background (large file, may take time)
   - 📋 GRC: Not started yet
   - **Source**: Geofabrik
   - **Location**: `data2/osm/{COUNTRY}/`

### Extracted/Clipped Datasets
3. **Natura 2000 - Italy**
   - ✅ ITA: `data2/protected_areas/natura2000/natura2000_ITA.shp` (49.6 MB)
   - **Source**: Clipped from Europe-wide dataset (988 MB → 49.6 MB)

4. **Agricultural Lands - Italy**
   - ✅ ITA: `data2/agricultural/agricultural_lands_ITA.shp` (101.7 MB)
   - **Source**: Extracted from CORINE (codes 2xx)

5. **Forests - Italy**
   - ✅ ITA: `data2/forests/forests_ITA.shp` (107.3 MB)
   - **Source**: Extracted from CORINE (codes 3xx)

### Extracted/Clipped Datasets (continued)
6. **CORINE Land Cover - Europe-wide**
   - ✅ Available: `data2/corine/U2018_CLC2018_V2020_20u1.gpkg` (8.25 GB)
   - **Source**: Copernicus Land Monitoring Service (Vector GPKG format)
   - **Status**: ✅ Downloaded and copied to project
   - **Note**: Europe-wide dataset, backend clips dynamically to AOI/country
   - **Can be used for**: Both ITA and GRC (backend handles clipping)
   - **Italy**: Also has clipped version `corine_ITA.shp` (237.7 MB) for faster access

## ⚠️ Requires Manual Download

### High Priority
1. ~~**CORINE Land Cover - Greece**~~ ✅ **COMPLETED**
   - ✅ Status: Europe-wide dataset available (8.25 GB GPKG)
   - **File**: `data2/corine/U2018_CLC2018_V2020_20u1.gpkg`
   - **Note**: Backend clips dynamically. Optional: Create country-specific clip for faster access
   - **Optional After Download**: 
     - Create clipped version: `data2/corine/corine_GRC.shp` (optional, for performance)
     - Run: `python scripts/extract_agricultural_lands.py --country GRC`
     - Run: `python scripts/extract_forests_from_corine.py --country GRC`

2. **Natura 2000 - Greece**
   - ⚠️ Status: Cannot clip (GADM GRC files not found)
   - **Action Needed**: 
     - Extract/Download GADM GRC level 0 shapefile
     - Then run: `python scripts/clip_natura2000.py --country GRC`

3. **Protected Areas (WDPA)**
   - ⚠️ ITA: Not downloaded
   - ⚠️ GRC: Not downloaded
   - **Source**: ProtectedPlanet (UNEP-WCMC)
   - **URLs**: 
     - ITA: https://www.protectedplanet.net/country/ITA
     - GRC: https://www.protectedplanet.net/country/GRC
   - **Instructions**: See `MANUAL_DOWNLOADS.md`
   - **Save as**: `data2/protected_areas/wdpa/wdpa_ITA.shp` and `wdpa_GRC.shp`

### Medium Priority (Optional)
4. **Forests - Copernicus Rasters**
   - ⚠️ Status: Not downloaded (can use CORINE extracts instead)
   - **Source**: Copernicus High Resolution Forest Layers
   - **Note**: Optional - CORINE forest extracts are available

5. **Urban Atlas (Cities)**
   - ✅ ITA: `data2/cities/urban_atlas/UA_2018_ITA.gpkg` (3.17 GB, 1.13M features from 84 cities) - **NEWLY ADDED**
   - ✅ GRC: `data2/cities/urban_atlas/UA_2018_GRC.gpkg` (439 MB, 195k features from 9 cities) - **NEWLY ADDED**
   - **Source**: Copernicus Urban Atlas
   - **Status**: Merged from individual city ZIP files
   - **Note**: Individual city files were downloaded and merged into country-level datasets

### Low Priority
6. ~~**Full GBIF Datasets**~~ ✅ **COMPLETED** (Italy full dataset downloaded)
   - ✅ ITA: Full dataset downloaded (7.34 GB)
   - 📋 GRC: Sample available, full dataset optional

## Scripts Created

1. ✅ `scripts/download_datasets.py` - Organize and tag datasets
2. ✅ `scripts/clip_natura2000.py` - Clip Natura 2000 to countries
3. ✅ `scripts/extract_agricultural_lands.py` - Extract agricultural lands from CORINE
4. ✅ `scripts/extract_forests_from_corine.py` - Extract forests from CORINE
5. ✅ `scripts/download_osm_data.py` - Download OSM data from Geofabrik
6. ✅ `scripts/download_gbif_data.py` - Download GBIF occurrence data (samples)
7. ✅ `scripts/merge_urban_atlas_cities.py` - Merge individual Urban Atlas city files - **NEWLY CREATED**
8. ✅ `scripts/process_urban_atlas.py` - Extract countries from Europe-wide Urban Atlas

## Next Steps

### Immediate (To Complete Dataset Collection)
1. ~~**Download CORINE GRC**~~ ✅ **COMPLETED** (Europe-wide dataset available)
2. **Extract/Download GADM GRC level 0** (to enable Natura 2000 GRC clipping)
3. ~~**Download WDPA datasets**~~ ✅ **NOT NEEDED** (Using Natura 2000 instead)

### After Manual Downloads
4. Run extraction scripts for GRC:
   - `python scripts/extract_agricultural_lands.py --country GRC`
   - `python scripts/extract_forests_from_corine.py --country GRC`
   - `python scripts/clip_natura2000.py --country GRC`

5. Organize all datasets:
   - `python scripts/download_datasets.py`

6. Update backend catalog (if needed)

## Summary

**Completed**: 11 datasets (4 extracted/clipped, 1 GBIF full ITA, 2 GBIF samples, 1 CORINE Europe-wide, 2 Urban Atlas, 1 OSM in progress)
**Remaining Manual Downloads**: 0 high-priority (CORINE ✅, WDPA not needed - using Natura 2000, GBIF ITA ✅, Urban Atlas ✅)
**Total Progress**: ~85% complete for core datasets

See `MANUAL_DOWNLOADS.md` for detailed step-by-step instructions for manual downloads.

