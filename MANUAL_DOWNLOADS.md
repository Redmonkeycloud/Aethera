# Manual Download Instructions

Some datasets require manual download from portals that require registration or don't provide direct download links. This guide provides step-by-step instructions.

## 1. CORINE Land Cover

### ✅ COMPLETED: Europe-wide Dataset Available

**Status**: ✅ **Downloaded and available in project!**

- **File**: `data2/corine/U2018_CLC2018_V2020_20u1.gpkg` (8.25 GB)
- **Format**: Vector GPKG (GeoPackage)
- **Coverage**: Full Europe (includes Italy, Greece, and all EU countries)
- **Source**: Copernicus Land Monitoring Service
- **Download Date**: Completed

**How it works:**
- ✅ Backend clips dynamically to AOI/country boundaries
- ✅ Can be used for both Italy and Greece (no separate downloads needed)
- ✅ Italy also has a pre-clipped version: `corine_ITA.shp` (237.7 MB) for faster access
- ✅ Greece can use the Europe-wide dataset (backend handles clipping automatically)

**No additional downloads needed!** The Europe-wide dataset covers all requirements.

---

### Optional: Create Country-Specific Clips (For Performance)

If you want to create country-specific files for faster loading (optional):

**For Greece:**
```bash
# Clip Europe-wide GPKG to Greece (requires GADM boundary)
# Can be done with QGIS or Python script
# This is optional - backend already clips dynamically
```

**Extract derived datasets:**
```bash
# Extract agricultural lands from Europe-wide CORINE
python scripts/extract_agricultural_lands.py --country GRC

# Extract forests from Europe-wide CORINE
python scripts/extract_forests_from_corine.py --country GRC
```

**Note**: The extraction scripts can work with the Europe-wide GPKG file. They may need to be updated to handle the full dataset, or you can clip to country first if needed.

---

### Historical Reference (Download Methods - No Longer Needed)

~~**Option A: Using CLMS API (Programmatic)**~~ - Completed  
~~**Option B: Manual Download (Web Portal)**~~ - Completed

The dataset has been downloaded. See `CORINE_DOWNLOAD_INSTRUCTIONS.md` for reference on the download methods used.

## 2. Protected Areas

### ✅ RECOMMENDED: Use Natura 2000 (Already Available!)

**Status**: ✅ Already in dataset!

- **Location**: `data2/protected_areas/natura2000/`
- **Italy**: `natura2000_ITA.shp` (49.6 MB - already clipped!)
- **Full dataset**: `Natura2000_end2021_rev1_epsg3035.shp` (Europe-wide)

**Why Natura 2000?**
- ✅ **Commercial use allowed** (EEA license - no restrictions!)
- ✅ Covers most important protected areas in EU (SPAs, SACs)
- ✅ Already clipped to Italy
- ✅ Smaller file size (49.6 MB vs several GB for WDPA)
- ✅ Perfect for Italy and Greece (EU countries)

**Natura 2000 covers:**
- Special Protection Areas (SPAs) - Birds Directive
- Special Areas of Conservation (SACs) - Habitats Directive
- These are the most legally protected areas in EU countries

**Action**: ✅ **No download needed!** Already available in your dataset.

---

### ⚠️ Alternative: WDPA (NOT RECOMMENDED - Commercial Restrictions)

**⚠️ IMPORTANT**: WDPA has **commercial use restrictions**. For commercial use, you must obtain an IBAT license (paid service).

**Recommendation**: Skip WDPA - Natura 2000 is sufficient for Italy and Greece!

**If you still need WDPA (non-commercial use only):**

**Italy:**
1. Go to: https://www.protectedplanet.net/country/ITA
2. Click "Download" button
3. Select "Shapefile (SHP)" format
4. Accept non-commercial license terms
5. Download and extract
6. Save to: `data2/protected_areas/wdpa/wdpa_ITA.shp`

**Greece:**
1. Go to: https://www.protectedplanet.net/country/GRC
2. Click "Download" button
3. Select "Shapefile (SHP)" format
4. Accept non-commercial license terms
5. Download and extract
6. Save to: `data2/protected_areas/wdpa/wdpa_GRC.shp`

**See**: `PROTECTED_AREAS_ALTERNATIVES.md` for more alternatives and details.

## 3. Forests Data

### ✅ RECOMMENDED: Extract from CORINE (Already Available!)

**Status**: ✅ No download needed - extract from existing CORINE data!

**Why Extract from CORINE?**
- ✅ Already have CORINE dataset
- ✅ Free and open license (commercial use OK)
- ✅ Script ready: `scripts/extract_forests_from_corine.py`
- ✅ Vector format (Shapefile) - easy to work with
- ✅ Good quality for environmental impact assessment

**CORINE Forest Classes:**
- **311**: Broad-leaved forest
- **312**: Coniferous forest
- **313**: Mixed forest

**Extraction Steps:**
```bash
# Extract forests for Italy (CORINE ITA already available)
python scripts/extract_forests_from_corine.py --country ITA

# Extract forests for Greece (using Europe-wide CORINE dataset)
python scripts/extract_forests_from_corine.py --country GRC
```

**Output**: 
- `data2/forests/forests_ITA.shp`
- `data2/forests/forests_GRC.shp`

**Action**: ✅ **Use CORINE extraction - no download needed!**

---

### ⬇️ Alternative: Copernicus High Resolution Forest Layers

**When to use**: Only if you need quantitative tree cover density percentages or higher resolution.

**What to choose on CLMS Portfolio:**
1. Go to: https://land.copernicus.eu/en/products?tab=explore
2. Under **"Full-coverage Land Cover & Use"** section
3. Click **"Tree Cover and Forests"**
4. Select **"Tree Cover Density"** product
5. Download Europe-wide raster (GeoTIFF)
6. Clip to country boundaries if needed

**Product Details:**
- **Name**: Tree Cover Density (High Resolution Layers)
- **Resolution**: 100m (or 20m for newer versions)
- **Format**: Raster (GeoTIFF)
- **Coverage**: Europe
- **License**: Copernicus open data license (commercial use OK)

**Save as**: 
- `data2/forests/tree_cover_density_ITA.tif`
- `data2/forests/tree_cover_density_GRC.tif`

**Note**: This is only needed if you require quantitative density data. For most EIA purposes, CORINE extraction is sufficient.

**See**: `FORESTS_DATA_RECOMMENDATION.md` for detailed comparison.

**Alternative:** Use CORINE Land Cover classes 3xx (Forests) if raster data is not needed.

## 4. Urban Atlas (Cities) - Italy and Greece

### ✅ Decision: Download Full Europe Dataset (37 GB)

**File Information:**
- **File**: `UA_2018_3035_eu.zip`
- **Format**: Vector GPKG (GeoPackage)
- **Version**: v013/v012
- **Size**: 37 GB (compressed)
- **Coverage**: Full Europe
- **License**: Copernicus open data license (commercial use OK)

### Download Steps:

1. Go to: https://land.copernicus.eu/local/urban-atlas/urban-atlas-2018
2. Register/Login (free registration required)
3. Select: **"Europe"** → **"UA_2018_3035_eu.zip"** (37 GB)
4. Download the ZIP file (may take time due to size)
5. Extract the ZIP file
6. Save extracted GPKG to: `data2/cities/urban_atlas/UA_2018_3035_eu.gpkg`

### Processing (Extract Italy and Greece):

After downloading, extract country-specific datasets:

```bash
# Extract Italy from full Europe dataset
python scripts/process_urban_atlas.py --country ITA

# Extract Greece from full Europe dataset
python scripts/process_urban_atlas.py --country GRC
```

**Output files**:
- `data2/cities/urban_atlas/UA_2018_ITA.gpkg`
- `data2/cities/urban_atlas/UA_2018_GRC.gpkg`

**Note**: The 37 GB file may require significant RAM to process. If the script fails due to memory, use QGIS or GDAL/OGR command-line tools (see `URBAN_ATLAS_PROCESSING.md` for alternatives).

**See**: `URBAN_ATLAS_PROCESSING.md` for detailed processing guide and alternatives.

**Alternative:** Use OpenStreetMap data (downloaded via script) which covers all cities.

## 5. Full GBIF Dataset (Large Download)

### Source: GBIF Download Service

For full biodiversity datasets (not just samples):

1. Go to: https://www.gbif.org/occurrence/download
2. Set filters:
   - Country: Italy (IT) or Greece (GR)
   - Optional: Add filters for specific taxa, dates, etc.
3. Click "Request download"
4. Wait for email notification (can take hours for large datasets)
5. Download the ZIP file when ready
6. Extract and save to: `data2/biodiversity/gbif_occurrences_ITA.csv` or `gbif_occurrences_GRC.csv`

**Note:** Full downloads can be very large (several GB). The script `download_gbif_data.py` downloads a sample (10,000 records) for testing.

## Download Checklist

- [x] CORINE Europe-wide - ✅ COMPLETED (8.25 GB GPKG - covers all countries)
- [ ] ~~WDPA ITA~~ - ⚠️ NOT NEEDED (Using Natura 2000 instead)
- [ ] ~~WDPA GRC~~ - ⚠️ NOT NEEDED (Using Natura 2000 instead)
- [ ] Forests ITA - ✅ Using CORINE extraction (script ready)
- [ ] Forests GRC - ✅ Using CORINE extraction (can use Europe-wide dataset)
- [ ] Urban Atlas Europe - ⚠️ Pending (37 GB download planned)
- [ ] Full GBIF ITA - ⚠️ Optional (sample available)
- [ ] Full GBIF GRC - ⚠️ Optional (sample available)

## After Manual Downloads

1. Organize files according to directory structure in `data2/README.md`
2. Run organization script: `python scripts/download_datasets.py`
3. Verify datasets are tagged in `data2/datasets_metadata.json`
4. Test with backend catalog

