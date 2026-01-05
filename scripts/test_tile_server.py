#!/usr/bin/env python3
"""Test script for the tile server endpoint."""

import requests
import sys

API_BASE_URL = "http://localhost:8001"

def test_tile_metadata(country="ITA"):
    """Test the metadata endpoint."""
    url = f"{API_BASE_URL}/tiles/corine/metadata"
    params = {"country": country}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("OK Metadata endpoint OK")
        print(f"   Country: {data.get('country')}")
        print(f"   Bounds: {data.get('bounds')}")
        print(f"   Metadata: {data.get('metadata', {}).get('name', 'N/A')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR Metadata endpoint failed: {e}")
        return False

def test_tile_request(z, x, y, country="ITA"):
    """Test a tile request."""
    url = f"{API_BASE_URL}/tiles/corine/{z}/{x}/{y}.mvt"
    params = {"country": country}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 204:
            print(f"   Zoom {z}, Tile {x}/{y}: No content (tile not found, this is OK)")
            return True
        elif response.status_code == 200:
            tile_size = len(response.content)
            print(f"OK Zoom {z}, Tile {x}/{y}: {tile_size} bytes")
            return True
        else:
            print(f"ERROR Zoom {z}, Tile {x}/{y}: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR Zoom {z}, Tile {x}/{y}: {e}")
        return False

def main():
    print("Testing tile server...")
    print(f"API Base URL: {API_BASE_URL}\n")
    
    # Test metadata
    if not test_tile_metadata("ITA"):
        print("\nWARNING Backend may not be running. Start it with:")
        print("   python -m uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8001 --reload")
        return 1
    
    print("\nTesting tile requests (zoom levels 0-2):")
    
    # Test tiles for zoom levels 0-2 (the ones we generated)
    test_cases = [
        (0, 0, 0),  # Zoom 0, tile 0/0
        (1, 0, 0),  # Zoom 1, tile 0/0
        (2, 2, 1),  # Zoom 2, tile 2/1 (Italy is around here)
    ]
    
    success_count = 0
    for z, x, y in test_cases:
        if test_tile_request(z, x, y, "ITA"):
            success_count += 1
    
    print(f"\nOK {success_count}/{len(test_cases)} tile requests succeeded")
    
    if success_count == len(test_cases):
        print("\nSUCCESS Tile server is working correctly!")
        return 0
    else:
        print("\nWARNING Some tile requests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

