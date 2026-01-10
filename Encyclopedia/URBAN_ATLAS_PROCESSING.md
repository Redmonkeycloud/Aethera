# Urban Atlas Processing Guide

## Dataset Information

**File**: `UA_2018_3035_eu.zip` (37 GB)  
**Format**: Vector GPKG (GeoPackage)  
**Version**: v013/v012  
**Coverage**: Full Europe  
**Source**: Copernicus Urban Atlas  
**License**: Copernicus open data license (commercial use OK)

## Download

**URL**: https://land.copernicus.eu/local/urban-atlas/urban-atlas-2018  
**File**: `UA_2018_3035_eu.zip` (37 GB)

**After Download**:
1. Extract the ZIP file (may take time due to size)
2. Save extracted GPKG to: `data2/cities/urban_atlas/UA_2018_3035_eu.gpkg`

## Processing Strategy

Since the full Europe dataset is 37 GB, we need to extract only Italy and Greece data for efficient use.

### Option 1: Clip by Country Boundary (Recommended)

Extract Italy and Greece using GADM country boundaries.

**Steps**:
1. Load full Urban Atlas GPKG
2. Load GADM country boundaries (Italy and Greece)
3. Clip Urban Atlas to each country boundary
4. Save as separate files: `UA_2018_ITA.gpkg` and `UA_2018_GRC.gpkg`

**Advantages**:
- Smaller file sizes (faster loading)
- Country-specific datasets
- Easier to manage

### Option 2: Filter by Country Code Column

If Urban Atlas has a country code column, filter directly.

**Steps**:
1. Load full Urban Atlas GPKG
2. Check available columns
3. Filter by country code (e.g., `CNTR_MN_NM = 'IT'` or `'GR'`)
4. Save filtered datasets

## Processing Script

Create a script: `scripts/process_urban_atlas.py`

```python
#!/usr/bin/env python3
"""Extract Italy and Greece from full Europe Urban Atlas dataset."""

import sys
from pathlib import Path
import geopandas as gpd
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DATA_DIR = project_root / "data2"
URBAN_ATLAS_DIR = DATA_DIR / "cities" / "urban_atlas"
OUTPUT_DIR = URBAN_ATLAS_DIR

def load_gadm_country(country_code: str):
    """Load GADM country boundary."""
    gadm_path = DATA_DIR / "boundaries" / "gadm" / "gadm_0.gpkg"
    if not gadm_path.exists():
        print(f"[ERROR] GADM file not found: {gadm_path}")
        return None
    
    gadm = gpd.read_file(gadm_path, layer="gadm_0")
    
    # Try different ISO code columns
    country_code_upper = country_code.upper()
    for col in ['ISO', 'ISO3', 'GID_0', 'NAME_0']:
        if col in gadm.columns:
            if country_code_upper in gadm[col].values:
                country = gadm[gadm[col] == country_code_upper]
                if len(country) > 0:
                    return country.unary_union
    
    print(f"[ERROR] Country {country_code} not found in GADM")
    return None

def process_urban_atlas(country_code: str):
    """Extract country data from full Europe Urban Atlas."""
    country_code = country_code.upper()
    
    # Input file
    input_file = URBAN_ATLAS_DIR / "UA_2018_3035_eu.gpkg"
    if not input_file.exists():
        print(f"[ERROR] Urban Atlas file not found: {input_file}")
        return False
    
    # Output file
    output_file = OUTPUT_DIR / f"UA_2018_{country_code}.gpkg"
    
    print(f"[INFO] Loading Urban Atlas dataset...")
    print(f"[INFO] This may take a while (37 GB file)...")
    
    try:
        # Read Urban Atlas
        urban_atlas = gpd.read_file(input_file)
        print(f"[INFO] Loaded {len(urban_atlas)} features")
        print(f"[INFO] Columns: {list(urban_atlas.columns)}")
        
        # Try filtering by country code column first (faster)
        country_filtered = None
        country_code_variants = {
            'ITA': ['IT', 'ITA', 'Italy', 'ITALY'],
            'GRC': ['GR', 'GRC', 'Greece', 'GREECE', 'EL']
        }
        
        variants = country_code_variants.get(country_code, [country_code])
        
        # Check for country code columns
        for col in urban_atlas.columns:
            if any(variant in ['code', 'cntr', 'country', 'iso'] for variant in col.lower().split('_')):
                print(f"[INFO] Trying to filter by column: {col}")
                for variant in variants:
                    if variant in urban_atlas[col].values:
                        country_filtered = urban_atlas[urban_atlas[col] == variant]
                        print(f"[INFO] Found {len(country_filtered)} features for {country_code} using column {col}")
                        break
                if country_filtered is not None:
                    break
        
        # If no country column, use spatial clipping
        if country_filtered is None:
            print(f"[INFO] No country code column found, using spatial clipping...")
            
            # Load country boundary
            country_boundary = load_gadm_country(country_code)
            if country_boundary is None:
                return False
            
            # Ensure same CRS
            if urban_atlas.crs != country_boundary.crs:
                urban_atlas = urban_atlas.to_crs(country_boundary.crs)
            
            # Clip
            print(f"[INFO] Clipping to country boundary...")
            country_filtered = urban_atlas.clip(country_boundary)
            print(f"[INFO] Found {len(country_filtered)} features after clipping")
        
        if len(country_filtered) == 0:
            print(f"[WARNING] No features found for {country_code}")
            return False
        
        # Save
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        country_filtered.to_file(output_file, driver='GPKG')
        
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"[OK] Saved to {output_file}")
        print(f"[INFO] File size: {file_size_mb:.2f} MB")
        print(f"[INFO] Features: {len(country_filtered)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Extract country data from Urban Atlas")
    parser.add_argument("--country", required=True, help="Country code (ITA or GRC)")
    args = parser.parse_args()
    
    if args.country.upper() not in ["ITA", "GRC"]:
        print("[ERROR] Country must be ITA or GRC")
        sys.exit(1)
    
    success = process_urban_atlas(args.country)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
```

## Usage

After downloading and extracting the full Urban Atlas:

```bash
# Extract Italy
python scripts/process_urban_atlas.py --country ITA

# Extract Greece
python scripts/process_urban_atlas.py --country GRC
```

**Output files**:
- `data2/cities/urban_atlas/UA_2018_ITA.gpkg`
- `data2/cities/urban_atlas/UA_2018_GRC.gpkg`

## Performance Considerations

**Large File Handling**:
- The 37 GB file may take significant time to load
- Consider using spatial indexing if available
- May need to process in chunks if memory is limited
- Alternative: Use QGIS to extract subsets if script fails

**Memory Requirements**:
- Loading 37 GB GPKG may require 50-100+ GB RAM
- If insufficient memory:
  1. Use QGIS to extract countries manually
  2. Or process using a system with more RAM
  3. Or use GDAL/OGR command-line tools for streaming processing

## Alternative: GDAL/OGR Command Line

If Python script has memory issues, use GDAL/OGR:

```bash
# Extract Italy (if country code column exists)
ogr2ogr -where "CNTR_MN_NM='IT'" UA_2018_ITA.gpkg UA_2018_3035_eu.gpkg

# Or clip using GADM boundary
ogr2ogr -clipsrc gadm_ITA.gpkg UA_2018_ITA.gpkg UA_2018_3035_eu.gpkg
```

## File Structure

```
data2/
  cities/
    urban_atlas/
      UA_2018_3035_eu.gpkg      # Full Europe (37 GB)
      UA_2018_ITA.gpkg          # Italy only (extracted)
      UA_2018_GRC.gpkg          # Greece only (extracted)
```

## Next Steps

1. ✅ Download `UA_2018_3035_eu.zip` (37 GB)
2. ✅ Extract ZIP file
3. ⬇️ Run processing script to extract ITA and GRC
4. ✅ Tag datasets using `scripts/download_datasets.py`

## Notes

- Urban Atlas provides detailed urban land use classification
- Includes classes like: residential, commercial, industrial, green urban areas, etc.
- Useful for city-level environmental impact assessment
- Compatible with CORINE (same coordinate system: EPSG:3035)

