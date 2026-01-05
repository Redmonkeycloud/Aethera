# Dataset Summary - Italy and Greece

## Status: In Progress

This document summarizes the current status of geospatial datasets for Italy (ITA) and Greece (GRC).

## ✅ Completed Datasets

### 1. CORINE Land Cover
- **Europe-wide**: ✅ `data2/corine/U2018_CLC2018_V2020_20u1.gpkg` (8.25 GB) - **NEWLY ADDED**
- **ITA**: ✅ `data2/corine/corine_ITA.shp` (237.7 MB) - Country-specific clip (faster)
- **GRC**: ✅ Available via Europe-wide dataset (backend clips dynamically)
- **Source**: Copernicus Land Monitoring Service
- **Note**: Europe-wide GPKG can be used for all countries. Backend handles dynamic clipping.

### 2. Natura 2000 Protected Areas
- **ITA**: ✅ `data2/protected_areas/natura2000/natura2000_ITA.shp` (49.6 MB) - **NEWLY CLIPPED**
- **GRC**: ✅ `data2/protected_areas/natura2000/natura2000_GRC.shp` - **NEWLY CLIPPED**
- **Full Dataset**: `data2/protected_areas/natura2000/Natura2000_end2021_rev1_epsg3035.shp` (988.6 MB)
- **Source**: EEA

### 3. Rivers
- **EUR**: ✅ `data2/rivers/HydroRIVERS_v10_eu_shp/HydroRIVERS_v10_eu.shp` (144.5 MB)
- **Source**: HydroRIVERS
- **Note**: Europe-wide, can be clipped to countries if needed

### 4. Administrative Boundaries
- **ITA**: ✅ `data2/gadm/gadm41_ITA_shp/gadm41_ITA_0.shp` (4.6 MB)
- **GRC**: ✅ `data2/gadm/gadm41_GRC_shp/gadm41_GRC_0.shp`
- **Source**: GADM

### 5. Agricultural Lands
- **ITA**: ✅ `data2/agricultural/agricultural_lands_ITA.shp` - **EXTRACTED**
- **GRC**: ⚠️ Need CORINE GRC first (can use Europe-wide dataset)
- **Source**: Extracted from CORINE (codes 2xx)

## ⚠️ Missing Datasets (Need Download)

### High Priority
1. ~~**CORINE Land Cover - Greece**~~ ✅ **COMPLETED**
   - Status: Europe-wide dataset available (8.25 GB GPKG)
   - Backend clips dynamically. Optional: Create country-specific clip for performance

2. **Agricultural Lands - Greece**
   - Action: Extract from CORINE GRC (once available)
   - Script: `scripts/extract_agricultural_lands.py --country GRC`

### Medium Priority
3. **Protected Areas (Beyond Natura 2000)**
   - Source: ProtectedPlanet (WDPA)
   - Action: Download from https://www.protectedplanet.net/
   - Save as: `data2/protected_areas/wdpa/wdpa_ITA.shp` and `wdpa_GRC.shp`

4. **Forests**
   - Source: Copernicus High Resolution Forest Layers
   - Action: Download Tree Cover Density and Forest Type
   - Requires: Registration on Copernicus portal

5. ~~**Cities and Urban Areas**~~ ✅ **COMPLETED**
   - Status: Urban Atlas merged for ITA and GRC
   - Alternative: OpenStreetMap data (optional)

### Low Priority
6. ~~**Biodiversity and Endangered Species - Italy**~~ ✅ **COMPLETED**
   - Status: Full GBIF dataset downloaded for Italy (7.34 GB)
   - Greece: Sample available, full dataset optional

## Implementation Status

### Backend
- ✅ DatasetCatalog updated to support country-specific Natura 2000
- ✅ Layer endpoints use country-specific files when available
- ✅ File size optimization (skips GADM for small files)
- ⚠️ Need to add endpoints for new datasets (rivers, forests, cities, etc.)

### Frontend
- ✅ Basic layer display (CORINE, Natura 2000)
- ⚠️ Need to add UI for new datasets

## Next Steps

1. ~~**Download CORINE GRC**~~ ✅ **COMPLETED** (Europe-wide dataset available)
2. **Extract agricultural lands GRC** - Run extraction script (can use Europe-wide GPKG)
3. ~~**Download protected areas (WDPA)**~~ ✅ **NOT NEEDED** (Using Natura 2000)
4. ~~**Download Urban Atlas**~~ ✅ **COMPLETED** (Merged for ITA and GRC)
5. ~~**Download GBIF full dataset**~~ ✅ **COMPLETED** (Italy full dataset)
6. **Update catalog** - Add methods for new datasets (Urban Atlas, GBIF full)
7. **Create API endpoints** - For rivers, forests, cities, etc.
8. **Update frontend** - Add layer toggles for new datasets

## Scripts Available

- `scripts/download_datasets.py` - Organize and tag datasets
- `scripts/clip_natura2000.py` - Clip Natura 2000 to countries ✅ USED
- `scripts/extract_agricultural_lands.py` - Extract agricultural lands from CORINE ✅ USED

## Documentation

- `DATA_SOURCES.md` - Authoritative data sources
- `DATA_DOWNLOAD_GUIDE.md` - Step-by-step download instructions
- `data2/README.md` - Data directory structure
- `data2/datasets_metadata.json` - Metadata for all datasets

