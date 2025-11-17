# Country-Wide Analyses

## ✅ Completed Analyses

### Italy (ITA) - Full Country Coverage
- **Run ID**: `run_20251117_134815`
- **Coverage**: Full country (entire Italy)
- **Data Processed**:
  - 115,599 CORINE land cover records
  - 2,641 Natura 2000 protected sites
  - Full biodiversity sensitivity mapping
- **Status**: ✅ Complete and ready to view

### Greece (GRC) - Status
- **Issue**: GADM data for Greece appears to be missing or incomplete
- **Solution Options**:
  1. Download GADM data for Greece from https://gadm.org/download_country.html
  2. Use Natural Earth country boundaries (if available)
  3. Create a bounding box approximation

## How to View Full Country Coverage

1. **Open the frontend**: http://localhost:8080/frontend/index.html
2. **Select "Italy (ITA)"** from the country dropdown
3. **Select the run**: `run_20251117_134815` (the full country analysis)
4. **Click "Load Biodiversity Layers"**
5. The map will show **entire Italy** with:
   - Biodiversity sensitivity across the whole country
   - All Natura 2000 sites
   - Overlap areas

## Creating More Country Analyses

To create a full country analysis for any country with GADM data:

```bash
cd D:\Aethera_original
python scripts/run_country_analysis.py <COUNTRY_CODE> --project-type solar_farm
```

Example:
```bash
python scripts/run_country_analysis.py ITA --project-type solar_farm
```

## Data Requirements

For full country analysis, you need:
- ✅ CORINE land cover data (covers EU countries)
- ✅ Natura 2000 protected areas (covers EU countries)
- ✅ GADM country boundaries (download from https://gadm.org)

## Current Data Status

- ✅ **CORINE**: Available (covers EU)
- ✅ **Natura 2000**: Available (covers EU)
- ✅ **GADM Italy**: Available
- ❌ **GADM Greece**: Missing (directory exists but empty)

## Next Steps

1. **For Greece**: Download GADM data from https://gadm.org/download_country.html
   - Select "Greece" and download level 0 (country boundary)
   - Extract to `data2/gadm/gadm41_GRC_shp/`
   - Then run: `python scripts/run_country_analysis.py GRC`

2. **For other countries**: Follow the same process - download GADM data and run the analysis script

