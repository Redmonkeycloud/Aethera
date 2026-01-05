#!/usr/bin/env python3
"""Extract forest areas from CORINE Land Cover dataset."""

import sys
from pathlib import Path
import geopandas as gpd
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DATA_DIR = project_root / "data2"

# CORINE forest class codes (3xx)
FOREST_CODES = [
    "311",  # Broad-leaved forest
    "312",  # Coniferous forest
    "313",  # Mixed forest
]


def extract_forests_from_corine(country_code: str):
    """Extract forest areas from CORINE dataset."""
    country_code = country_code.upper()
    
    # File paths
    corine_path = DATA_DIR / "corine" / f"corine_{country_code}.shp"
    output_dir = DATA_DIR / "forests"
    output_path = output_dir / f"forests_{country_code}.shp"
    
    if not corine_path.exists():
        print(f"[ERROR] CORINE file not found: {corine_path}")
        return False
    
    print(f"[INFO] Loading CORINE dataset...")
    corine = gpd.read_file(corine_path)
    print(f"[INFO] Loaded {len(corine)} features")
    
    # Find the code column (may vary: CODE_18, code_18, CLC_CODE, etc.)
    code_column = None
    for col in corine.columns:
        if 'code' in col.lower() or 'clc' in col.lower():
            code_column = col
            break
    
    if not code_column:
        print("[ERROR] Could not find CORINE code column")
        print(f"[INFO] Available columns: {list(corine.columns)}")
        return False
    
    print(f"[INFO] Using code column: {code_column}")
    
    # Convert codes to string and filter
    corine[code_column] = corine[code_column].astype(str)
    
    # Filter forest classes (codes starting with 3)
    forests = corine[corine[code_column].str.startswith('3')]
    
    print(f"[INFO] Found {len(forests)} forest features")
    
    if len(forests) == 0:
        print("[WARNING] No forest features found")
        return False
    
    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    forests.to_file(output_path)
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"[OK] Saved to {output_path}")
    print(f"[INFO] File size: {file_size_mb:.2f} MB")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Extract forests from CORINE")
    parser.add_argument("--country", required=True, help="Country code (ITA or GRC)")
    args = parser.parse_args()
    
    if args.country.upper() not in ["ITA", "GRC"]:
        print("[ERROR] Country must be ITA or GRC")
        sys.exit(1)
    
    success = extract_forests_from_corine(args.country)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

