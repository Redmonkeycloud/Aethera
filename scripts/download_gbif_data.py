#!/usr/bin/env python3
"""Download biodiversity occurrence data from GBIF for Italy and Greece."""

import sys
import argparse
from pathlib import Path
import requests
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DATA_DIR = project_root / "data2" / "biodiversity"

# GBIF API endpoint
GBIF_API = "https://api.gbif.org/v1"

# Country codes
COUNTRY_CODES = {
    "ITA": "IT",
    "GRC": "GR"
}


def download_gbif_occurrences(country_code: str, limit: int = 10000):
    """Download GBIF occurrence data for a country.
    
    Note: GBIF API has rate limits. For large downloads, use their download service.
    This script downloads a sample for testing.
    """
    country_code = country_code.upper()
    
    if country_code not in COUNTRY_CODES:
        print(f"[ERROR] Country must be ITA or GRC")
        return False
    
    gbif_country_code = COUNTRY_CODES[country_code]
    output_dir = DATA_DIR / "external"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"gbif_occurrences_{country_code}_sample.csv"
    
    print(f"[INFO] Downloading GBIF occurrence data for {country_code}...")
    print(f"[INFO] Limit: {limit} records (sample)")
    
    try:
        # Search for occurrences
        search_url = f"{GBIF_API}/occurrence/search"
        params = {
            "country": gbif_country_code,
            "limit": min(limit, 300),  # API limit per request
            "offset": 0
        }
        
        all_records = []
        
        while len(all_records) < limit:
            print(f"[INFO] Fetching records {len(all_records)}-{len(all_records) + params['limit']}...")
            
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            records = data.get("results", [])
            
            if not records:
                break
            
            all_records.extend(records)
            params["offset"] += params["limit"]
            
            # Rate limiting
            time.sleep(1)
            
            if len(records) < params["limit"]:
                break
        
        if not all_records:
            print("[WARNING] No records found")
            return False
        
        # Convert to CSV
        print(f"[INFO] Converting {len(all_records)} records to CSV...")
        
        # Get all unique keys
        all_keys = set()
        for record in all_records:
            all_keys.update(record.keys())
        
        # Write CSV
        import csv
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(all_records)
        
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"[OK] Saved {len(all_records)} records to {output_file}")
        print(f"[INFO] File size: {file_size_mb:.2f} MB")
        print(f"[NOTE] This is a sample. For full download, use GBIF download service:")
        print(f"      https://www.gbif.org/occurrence/download?country={gbif_country_code}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download GBIF biodiversity data")
    parser.add_argument("--country", required=True, choices=["ITA", "GRC"], help="Country code")
    parser.add_argument("--limit", type=int, default=10000, help="Maximum records to download (default: 10000)")
    args = parser.parse_args()
    
    success = download_gbif_occurrences(args.country, args.limit)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

