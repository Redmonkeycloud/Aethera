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
    # Try different GADM locations
    gadm_paths = [
        DATA_DIR / "boundaries" / "gadm" / "gadm_0.gpkg",
        DATA_DIR / "gadm" / "gadm_0.gpkg",
    ]
    
    gadm_path = None
    for path in gadm_paths:
        if path.exists():
            gadm_path = path
            break
    
    if not gadm_path:
        print(f"[ERROR] GADM file not found. Tried: {gadm_paths}")
        return None
    
    print(f"[INFO] Loading GADM from: {gadm_path}")
    try:
        gadm = gpd.read_file(gadm_path, layer="gadm_0")
    except:
        # Try without layer specification
        gadm = gpd.read_file(gadm_path)
    
    # Try different ISO code columns
    country_code_upper = country_code.upper()
    country_mapping = {
        'ITA': ['IT', 'ITA', 'Italy', 'ITALY'],
        'GRC': ['GR', 'GRC', 'Greece', 'GREECE', 'EL', 'GRC']
    }
    
    variants = country_mapping.get(country_code_upper, [country_code_upper])
    
    for col in ['ISO', 'ISO3', 'GID_0', 'NAME_0', 'ISO_3', 'NAME_ENGLI']:
        if col in gadm.columns:
            for variant in variants:
                matching = gadm[gadm[col].astype(str).str.upper() == variant.upper()]
                if len(matching) > 0:
                    country_geom = matching.iloc[0].geometry
                    print(f"[INFO] Found country boundary using column {col} = {variant}")
                    return country_geom
    
    print(f"[ERROR] Country {country_code} not found in GADM")
    print(f"[INFO] Available columns: {list(gadm.columns)}")
    return None

def process_urban_atlas(country_code: str):
    """Extract country data from full Europe Urban Atlas."""
    country_code = country_code.upper()
    
    # Input file
    input_file = URBAN_ATLAS_DIR / "UA_2018_3035_eu.gpkg"
    if not input_file.exists():
        print(f"[ERROR] Urban Atlas file not found: {input_file}")
        print(f"[INFO] Please download and extract UA_2018_3035_eu.zip first")
        return False
    
    # Output file
    output_file = OUTPUT_DIR / f"UA_2018_{country_code}.gpkg"
    
    print(f"[INFO] Loading Urban Atlas dataset...")
    print(f"[INFO] File: {input_file}")
    file_size_gb = input_file.stat().st_size / (1024 * 1024 * 1024)
    print(f"[INFO] File size: {file_size_gb:.2f} GB")
    print(f"[INFO] This may take a while...")
    
    try:
        # Read Urban Atlas
        urban_atlas = gpd.read_file(input_file)
        print(f"[INFO] Loaded {len(urban_atlas)} features")
        print(f"[INFO] CRS: {urban_atlas.crs}")
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
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['code', 'cntr', 'country', 'iso', 'nation']):
                print(f"[INFO] Trying to filter by column: {col}")
                for variant in variants:
                    matching = urban_atlas[urban_atlas[col].astype(str).str.upper() == variant.upper()]
                    if len(matching) > 0:
                        country_filtered = matching
                        print(f"[INFO] Found {len(country_filtered)} features for {country_code} using column {col} = {variant}")
                        break
                if country_filtered is not None:
                    break
        
        # If no country column, use spatial clipping
        if country_filtered is None or len(country_filtered) == 0:
            print(f"[INFO] No country code column found or empty result, using spatial clipping...")
            
            # Load country boundary
            country_boundary = load_gadm_country(country_code)
            if country_boundary is None:
                print(f"[WARNING] Could not load country boundary, trying to use full dataset bounds...")
                return False
            
            # Convert boundary to GeoDataFrame with same CRS
            from shapely.geometry import box
            boundary_gdf = gpd.GeoDataFrame([1], geometry=[country_boundary], crs=urban_atlas.crs)
            
            # Ensure same CRS
            if urban_atlas.crs != boundary_gdf.crs:
                urban_atlas = urban_atlas.to_crs(boundary_gdf.crs)
            
            # Clip
            print(f"[INFO] Clipping to country boundary...")
            country_filtered = gpd.clip(urban_atlas, boundary_gdf)
            print(f"[INFO] Found {len(country_filtered)} features after clipping")
        
        if len(country_filtered) == 0:
            print(f"[WARNING] No features found for {country_code}")
            return False
        
        # Save
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Saving to {output_file}...")
        country_filtered.to_file(output_file, driver='GPKG')
        
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"[OK] Saved to {output_file}")
        print(f"[INFO] File size: {file_size_mb:.2f} MB")
        print(f"[INFO] Features: {len(country_filtered)}")
        
        return True
        
    except MemoryError:
        print(f"[ERROR] Out of memory. File is too large ({file_size_gb:.2f} GB)")
        print(f"[INFO] Consider using QGIS or GDAL/OGR command-line tools instead")
        print(f"[INFO] Example GDAL command:")
        print(f"  ogr2ogr -clipsrc <gadm_boundary.gpkg> {output_file} {input_file}")
        return False
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

