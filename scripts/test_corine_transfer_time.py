#!/usr/bin/env python3
"""Test how long it takes to transfer CORINE GeoJSON over HTTP."""

import sys
import time
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

API_BASE_URL = "http://localhost:8001"
TIMEOUT = 600  # 10 minutes timeout for the test


def test_corine_transfer(country: str = "ITA"):
    """Test CORINE layer transfer time."""
    print("=" * 60)
    print("CORINE HTTP Transfer Time Test")
    print("=" * 60)
    print(f"\nTesting CORINE transfer for country: {country}")
    print(f"Backend URL: {API_BASE_URL}")
    print(f"Timeout: {TIMEOUT} seconds\n")
    
    # Check file size first
    geojson_path = project_root / "data2" / "corine" / f"corine_{country}.geojson"
    if geojson_path.exists():
        file_size_mb = geojson_path.stat().st_size / (1024 * 1024)
        print(f"GeoJSON file size: {file_size_mb:.2f} MB")
    else:
        print(f"WARNING: GeoJSON file not found: {geojson_path}")
    
    url = f"{API_BASE_URL}/layers/corine"
    params = {"country": country}
    
    print(f"\nMaking request to: {url}")
    print(f"Parameters: {params}")
    print("\nStarting transfer...")
    print("(This may take several minutes...)\n")
    
    start_time = time.time()
    
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT, stream=False)
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            content_length = len(response.content)
            content_length_mb = content_length / (1024 * 1024)
            
            print("=" * 60)
            print("SUCCESS: Transfer Complete!")
            print("=" * 60)
            print(f"\nStatus Code: {response.status_code}")
            print(f"Content Length: {content_length_mb:.2f} MB")
            print(f"Transfer Time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
            
            if elapsed_time > 0:
                transfer_speed_mbps = (content_length_mb * 8) / elapsed_time  # Mbps
                transfer_speed_mb_per_sec = content_length_mb / elapsed_time  # MB/s
                print(f"Transfer Speed: {transfer_speed_mb_per_sec:.2f} MB/s ({transfer_speed_mbps:.2f} Mbps)")
            
            # Check if it's valid GeoJSON
            try:
                data = response.json()
                if "features" in data:
                    print(f"Features: {len(data['features'])}")
                print("Valid GeoJSON format")
            except Exception as e:
                print(f"WARNING: Response is not valid JSON: {e}")
            
            print("\n" + "=" * 60)
            print("RECOMMENDATION:")
            if elapsed_time < 60:
                print("OK: Transfer time is acceptable (< 1 minute)")
            elif elapsed_time < 180:
                print("SLOW: Transfer time is slow (1-3 minutes) - consider optimization")
            else:
                print("TOO LONG: Transfer time is too long (> 3 minutes) - optimization required")
            print("=" * 60)
            
        else:
            print(f"ERROR: Request failed with status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        print("=" * 60)
        print("ERROR: Request timed out!")
        print("=" * 60)
        print(f"Time before timeout: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        print(f"Timeout setting: {TIMEOUT} seconds")
        print("\nWARNING: The file is too large to transfer within the timeout period.")
        
    except requests.exceptions.ConnectionError:
        print("=" * 60)
        print("ERROR: Connection Error!")
        print("=" * 60)
        print("Could not connect to the backend API.")
        print(f"Make sure the backend is running on {API_BASE_URL}")
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print("=" * 60)
        print("ERROR: Error occurred!")
        print("=" * 60)
        print(f"Error: {e}")
        print(f"Time before error: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test CORINE HTTP transfer time")
    parser.add_argument("--country", default="ITA", help="Country code (default: ITA)")
    args = parser.parse_args()
    
    test_corine_transfer(country=args.country)

