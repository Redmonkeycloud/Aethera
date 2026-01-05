#!/usr/bin/env python3
"""Clip Natura 2000 dataset to country boundaries."""

import sys
from pathlib import Path
import geopandas as gpd
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DATA_DIR = project_root / "data2"


def clip_natura2000_to_country(country_code: str):
    """Clip Natura 2000 dataset to a specific country."""
    country_code = country_code.upper()
    
    # File paths
    natura_path = DATA_DIR / "protected_areas" / "natura2000" / "Natura2000_end2021_rev1_epsg3035.shp"
    gadm_path = DATA_DIR / "gadm" / f"gadm41_{country_code}_shp" / f"gadm41_{country_code}_0.shp"
    output_path = DATA_DIR / "protected_areas" / "natura2000" / f"natura2000_{country_code}.shp"
    
    # Check if files exist
    if not natura_path.exists():
        print(f"[ERROR] Natura 2000 file not found: {natura_path}")
        return False
    
    if not gadm_path.exists():
        print(f"[ERROR] GADM boundary not found: {gadm_path}")
        return False
    
    print(f"[INFO] Loading Natura 2000 dataset...")
    natura = gpd.read_file(natura_path)
    print(f"[INFO] Loaded {len(natura)} features")
    
    print(f"[INFO] Loading {country_code} boundary...")
    boundary = gpd.read_file(gadm_path)
    boundary = boundary.dissolve()  # Merge if multiple features
    
    # Ensure same CRS
    if natura.crs != boundary.crs:
        print(f"[INFO] Reprojecting boundary to match Natura 2000 CRS: {natura.crs}")
        boundary = boundary.to_crs(natura.crs)
    
    print(f"[INFO] Clipping to {country_code} boundary...")
    clipped = gpd.clip(natura, boundary)
    print(f"[INFO] Clipped to {len(clipped)} features")
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clipped.to_file(output_path)
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"[OK] Saved to {output_path}")
    print(f"[INFO] File size: {file_size_mb:.2f} MB")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Clip Natura 2000 to country boundaries")
    parser.add_argument("--country", required=True, help="Country code (ITA or GRC)")
    args = parser.parse_args()
    
    if args.country.upper() not in ["ITA", "GRC"]:
        print("[ERROR] Country must be ITA or GRC")
        sys.exit(1)
    
    success = clip_natura2000_to_country(args.country)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

