#!/usr/bin/env python3
"""Merge individual Urban Atlas city ZIP files into country-level datasets."""

import sys
from pathlib import Path
import geopandas as gpd
import zipfile
import argparse
import tempfile
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DATA_DIR = project_root / "data2"
URBAN_ATLAS_DIR = DATA_DIR / "cities" / "urban_atlas"
INPUT_DIR = Path("D:/Users/User/Downloads/43411/Results/UA_2018_3035_eu")
OUTPUT_DIR = URBAN_ATLAS_DIR

# Country code mapping for Urban Atlas files
COUNTRY_PREFIXES = {
    'ITA': 'IT',  # Italy files start with IT
    'GRC': 'EL',  # Greece files start with EL
}


def merge_cities_for_country(country_code: str):
    """Merge all city ZIP files for a country into a single GPKG."""
    country_code = country_code.upper()
    
    if country_code not in COUNTRY_PREFIXES:
        print(f"[ERROR] Country must be ITA or GRC")
        return False
    
    prefix = COUNTRY_PREFIXES[country_code]
    
    # Find all ZIP files for this country
    zip_files = sorted(INPUT_DIR.glob(f"{prefix}*.zip"))
    
    if not zip_files:
        print(f"[ERROR] No Urban Atlas files found for {country_code} (prefix: {prefix})")
        print(f"[INFO] Searched in: {INPUT_DIR}")
        return False
    
    print(f"[INFO] Found {len(zip_files)} city files for {country_code}")
    
    # Output file
    output_file = OUTPUT_DIR / f"UA_2018_{country_code}.gpkg"
    
    # Temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        all_features = []
        
        for zip_file in zip_files:
            city_name = zip_file.stem
            print(f"[INFO] Processing {city_name}...")
            
            try:
                # Extract ZIP
                extract_dir = temp_path / city_name
                extract_dir.mkdir(exist_ok=True)
                
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # Find GPKG file in extracted contents
                gpkg_files = list(extract_dir.rglob("*.gpkg"))
                
                if not gpkg_files:
                    print(f"[WARNING] No GPKG file found in {city_name}")
                    continue
                
                gpkg_file = gpkg_files[0]
                
                # Read GPKG
                gdf = gpd.read_file(gpkg_file)
                
                if len(gdf) > 0:
                    all_features.append(gdf)
                    print(f"[INFO] Loaded {len(gdf)} features from {city_name}")
                else:
                    print(f"[WARNING] Empty dataset in {city_name}")
                
            except Exception as e:
                print(f"[WARNING] Error processing {city_name}: {e}")
                continue
        
        if not all_features:
            print(f"[ERROR] No features loaded for {country_code}")
            return False
        
        # Merge all GeoDataFrames
        print(f"[INFO] Merging {len(all_features)} city datasets...")
        merged = gpd.GeoDataFrame(pd.concat(all_features, ignore_index=True))
        
        # Ensure consistent CRS
        if merged.crs is None:
            # Urban Atlas typically uses EPSG:3035
            merged.set_crs("EPSG:3035", inplace=True)
        
        # Remove duplicates if any
        merged = merged.drop_duplicates(subset=merged.geometry.name, keep='first')
        
        # Save
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Saving merged dataset to {output_file}...")
        merged.to_file(output_file, driver='GPKG')
        
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"[OK] Saved to {output_file}")
        print(f"[INFO] Total features: {len(merged)}")
        print(f"[INFO] File size: {file_size_mb:.2f} MB")
        
        return True


def main():
    import pandas as pd  # Import here to avoid issues if not needed
    
    parser = argparse.ArgumentParser(description="Merge Urban Atlas city files for a country")
    parser.add_argument("--country", required=True, choices=["ITA", "GRC"], help="Country code")
    parser.add_argument("--input-dir", type=str, help="Input directory with ZIP files (default: Downloads)")
    args = parser.parse_args()
    
    global INPUT_DIR
    if args.input_dir:
        INPUT_DIR = Path(args.input_dir)
    
    success = merge_cities_for_country(args.country)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

