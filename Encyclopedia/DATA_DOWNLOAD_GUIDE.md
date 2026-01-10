# Data Download Guide for Italy and Greece

This guide provides step-by-step instructions for downloading geospatial datasets for Italy and Greece.

## Quick Start

Run the organization script first to tag existing datasets:
```bash
python scripts/download_datasets.py
```

## Datasets to Download

### 1. CORINE Land Cover

#### Greece (GRC) - MISSING
- **Source**: Copernicus Land Monitoring Service
- **Manual Download**: 
  1. Go to: https://land.copernicus.eu/pan-european/corine-land-cover
  2. Download CORINE Land Cover 2018 (Vector)
  3. Use QGIS or Python to clip to Greece boundary
  4. Save as: `data2/corine/corine_GRC.shp`

#### Italy (ITA) - ✅ EXISTS
- **Location**: `data2/corine/corine_ITA.shp`
- **Status**: Already available

### 2. Natura 2000 Protected Areas

#### Country-Specific Clips - RECOMMENDED
- **Full Dataset**: `data2/protected_areas/natura2000/Natura2000_end2021_rev1_epsg3035.shp` (EXISTS)
- **Action Needed**: Clip to Italy and Greece boundaries using GADM

**Using Python (GeoPandas):**
```python
import geopandas as gpd

# Load full Natura 2000
natura = gpd.read_file("data2/protected_areas/natura2000/Natura2000_end2021_rev1_epsg3035.shp")

# Load country boundaries
ita_boundary = gpd.read_file("data2/gadm/gadm41_ITA_shp/gadm41_ITA_0.shp")
grc_boundary = gpd.read_file("data2/gadm/gadm41_GRC_shp/gadm41_GRC_0.shp")

# Clip and save
natura_ita = gpd.clip(natura, ita_boundary)
natura_grc = gpd.clip(natura, grc_boundary)

natura_ita.to_file("data2/protected_areas/natura2000/natura2000_ITA.shp")
natura_grc.to_file("data2/protected_areas/natura2000/natura2000_GRC.shp")
```

### 3. Protected Areas (Beyond Natura 2000)

#### ProtectedPlanet (WDPA)
- **Source**: UNEP-WCMC ProtectedPlanet
- **Italy**: https://www.protectedplanet.net/country/ITA
- **Greece**: https://www.protectedplanet.net/country/GRC
- **Download**: Click "Download" → WDPA Shapefile
- **Save as**: `data2/protected_areas/wdpa/wdpa_ITA.shp` and `wdpa_GRC.shp`

### 4. Rivers

#### HydroRIVERS - ✅ EXISTS
- **Location**: `data2/rivers/HydroRIVERS_v10_eu_shp/HydroRIVERS_v10_eu.shp`
- **Status**: Already available (Europe-wide)
- **Action**: Can clip to countries if needed

### 5. Forests

#### Copernicus High Resolution Forest Layers
- **Source**: Copernicus Land Monitoring Service
- **URL**: https://land.copernicus.eu/pan-european/high-resolution-layers/forests
- **Download Options**:
  - Tree Cover Density (raster)
  - Forest Type (raster)
- **Note**: Requires registration (free)
- **Save as**: `data2/forests/tree_cover_density_ITA.tif` and `tree_cover_density_GRC.tif`

### 6. Agricultural Lands

#### Extract from CORINE
- **Method**: Filter CORINE data by agricultural codes (2xx)
- **CORINE Codes**: 
  - 211: Non-irrigated arable land
  - 212: Permanently irrigated land
  - 213: Rice fields
  - 221: Vineyards
  - 222: Fruit trees and berry plantations
  - 223: Olive groves
  - 231: Pastures
  - 241: Annual crops associated with permanent crops
  - 242: Complex cultivation patterns
  - 243: Land principally occupied by agriculture

**Python Script:**
```python
import geopandas as gpd

# Load CORINE
corine_ita = gpd.read_file("data2/corine/corine_ITA.shp")

# Filter agricultural classes (codes starting with 2)
agri_ita = corine_ita[corine_ita['CODE_18'].astype(str).str.startswith('2')]

# Save
agri_ita.to_file("data2/agricultural/agricultural_lands_ITA.shp")
```

### 7. Cities and Urban Areas

#### Urban Atlas (Copernicus)
- **Source**: Copernicus Land Monitoring Service
- **URL**: https://land.copernicus.eu/local/urban-atlas
- **Coverage**: Major cities only
- **Italy Cities**: Rome, Milan, Naples, Turin
- **Greece Cities**: Athens, Thessaloniki
- **Save as**: `data2/urban/urban_atlas_ITA.shp` and `urban_atlas_GRC.shp`

#### Alternative: OpenStreetMap (OSM)
- **Source**: Geofabrik
- **Italy**: https://download.geofabrik.de/europe/italy-latest-free.shp.zip
- **Greece**: https://download.geofabrik.de/europe/greece-latest-free.shp.zip
- **Extract**: `gis_osm_places_*.shp` for cities/towns
- **Save as**: `data2/urban/cities_ITA.shp` and `cities_GRC.shp`

### 8. Biodiversity and Endangered Species

#### GBIF (Global Biodiversity Information Facility)
- **Source**: GBIF API
- **API Docs**: https://www.gbif.org/developer/summary
- **Download Script**: Use `scripts/download_gbif_data.py` (see below)

**Example Download:**
- Italy: https://www.gbif.org/occurrence/search?country=IT
- Greece: https://www.gbif.org/occurrence/search?country=GR
- **Save as**: `data2/biodiversity/gbif_occurrences_ITA.csv` and `gbif_occurrences_GRC.csv`

#### IUCN Red List Species Ranges
- **Source**: IUCN Red List
- **URL**: https://www.iucnredlist.org/resources/spatial-data-download
- **Note**: Requires registration
- **Save as**: `data2/biodiversity/iucn_species_ranges_ITA.shp`

## Automated Download Scripts

### Download GBIF Data
```bash
python scripts/download_gbif_data.py --country ITA --output data2/biodiversity/gbif_ITA.csv
python scripts/download_gbif_data.py --country GRC --output data2/biodiversity/gbif_GRC.csv
```

### Clip Natura 2000 to Countries
```bash
python scripts/clip_natura2000.py --country ITA
python scripts/clip_natura2000.py --country GRC
```

### Extract Agricultural Lands from CORINE
```bash
python scripts/extract_agricultural_lands.py --country ITA
python scripts/extract_agricultural_lands.py --country GRC
```

## Recommended Priority Order

1. **High Priority** (Essential for basic functionality):
   - ✅ CORINE ITA (exists)
   - ⚠️ CORINE GRC (needs download/clip)
   - ⚠️ Natura 2000 country clips (can clip from existing)
   - ✅ Rivers (exists)

2. **Medium Priority** (Important for analysis):
   - Protected Areas (WDPA)
   - Forests
   - Agricultural Lands (can extract from CORINE)
   - Cities/Urban

3. **Low Priority** (Nice to have):
   - Biodiversity/GBIF
   - IUCN Species Ranges

## After Downloading

1. Run organization script: `python scripts/download_datasets.py`
2. Verify files are tagged correctly in `data2/datasets_metadata.json`
3. Test with backend: Check if datasets are found by catalog
4. Update frontend if new layer types are added

