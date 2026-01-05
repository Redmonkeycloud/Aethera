#!/usr/bin/env python3
"""Download OpenStreetMap data for Italy and Greece from Geofabrik."""

import sys
import argparse
from pathlib import Path
import requests
import zipfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DATA_DIR = project_root / "data2"

# Geofabrik download URLs
OSM_URLS = {
    "ITA": "https://download.geofabrik.de/europe/italy-latest-free.shp.zip",
    "GRC": "https://download.geofabrik.de/europe/greece-latest-free.shp.zip"
}


def download_osm_data(country_code: str):
    """Download OpenStreetMap shapefiles for a country."""
    country_code = country_code.upper()
    
    if country_code not in OSM_URLS:
        print(f"[ERROR] Country must be ITA or GRC")
        return False
    
    url = OSM_URLS[country_code]
    output_dir = DATA_DIR / "osm" / country_code
    zip_path = output_dir / f"{country_code}_latest-free.shp.zip"
    
    print(f"[INFO] Downloading OSM data for {country_code}...")
    print(f"[INFO] URL: {url}")
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Download
        print("[INFO] Downloading (this may take several minutes)...")
        response = requests.get(url, stream=True, timeout=600)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r[INFO] Progress: {percent:.1f}%", end='', flush=True)
        
        print(f"\n[OK] Downloaded {zip_path.name}")
        
        # Extract
        print("[INFO] Extracting archive...")
        extract_dir = output_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print(f"[OK] Extracted to {extract_dir}")
        print(f"[INFO] Look for cities in: {extract_dir}/gis_osm_places_*.shp")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download OpenStreetMap data")
    parser.add_argument("--country", required=True, choices=["ITA", "GRC"], help="Country code")
    args = parser.parse_args()
    
    success = download_osm_data(args.country)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

