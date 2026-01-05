#!/usr/bin/env python3
"""Download CORINE Land Cover data using the Copernicus Land Monitoring Service API.

Based on: https://eea.github.io/clms-api-docs/download.html
"""

import sys
import argparse
from pathlib import Path
import requests
import time
import json
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DATA_DIR = project_root / "data2"

# CLMS API endpoints
CLMS_SEARCH_URL = "https://land.copernicus.eu/api/@search"
CLMS_DOWNLOAD_REQUEST_URL = "https://land.copernicus.eu/api/@datarequest_post"
CLMS_DOWNLOAD_STATUS_URL = "https://land.copernicus.eu/api/@datarequest_get"


def search_corine_datasets(country_code: Optional[str] = None) -> list[Dict[str, Any]]:
    """Search for CORINE Land Cover datasets."""
    print(f"[INFO] Searching for CORINE Land Cover datasets...")
    
    params = {
        "portal_type": "DataSet",
        "SearchableText": "CORINE"
    }
    
    if country_code:
        params["SearchableText"] = f"CORINE {country_code}"
    
    all_items = []
    start = 0
    
    while True:
        current_params = params.copy()
        current_params["b_start"] = start
        # Add metadata_fields as query string (requests handles multiple values)
        response = requests.get(
            CLMS_SEARCH_URL, 
            params=current_params,
            headers={"Accept": "application/json"}
        )
        # Manually add metadata_fields to URL since requests doesn't handle duplicates well
        url = response.url
        if "metadata_fields" not in url:
            url += "&metadata_fields=UID&metadata_fields=dataset_full_format&metadata_fields=dataset_download_information"
            response = requests.get(url, headers={"Accept": "application/json"})
        
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        all_items.extend(items)
        
        batching = data.get("batching", {})
        if "next" not in batching:
            break
        
        start += len(items)
        if start >= 100:  # Limit search to first 100 results
            break
    
    corine_datasets = [item for item in all_items if "CORINE" in item.get("title", "").upper()]
    
    print(f"[INFO] Found {len(corine_datasets)} CORINE datasets")
    for i, dataset in enumerate(corine_datasets[:10], 1):  # Show first 10
        print(f"  {i}. {dataset.get('title', 'N/A')} (UID: {dataset.get('UID', 'N/A')})")
    
    return corine_datasets


def request_download(dataset_uid: str, auth_token: str, country_code: Optional[str] = None, 
                     output_format: str = "Shapefile") -> Optional[str]:
    """Request a download from CLMS API.
    
    Note: Requires authentication token. Get token from:
    https://land.copernicus.eu/registration/
    """
    print(f"[INFO] Requesting download for dataset {dataset_uid}...")
    
    # First, get download information for the dataset
    search_response = requests.get(
        CLMS_SEARCH_URL,
        params={
            "portal_type": "DataSet",
            "UID": dataset_uid,
            "metadata_fields": "dataset_download_information"
        },
        headers={"Accept": "application/json"}
    )
    search_response.raise_for_status()
    
    search_data = search_response.json()
    items = search_data.get("items", [])
    if not items:
        print(f"[ERROR] Dataset {dataset_uid} not found")
        return None
    
    dataset = items[0]
    download_info = dataset.get("dataset_download_information", {})
    download_items = download_info.get("items", [])
    
    if not download_items:
        print(f"[ERROR] No download information available for dataset {dataset_uid}")
        return None
    
    # Use first available download option
    download_item = download_items[0]
    download_info_id = download_item.get("@id", "").split("/")[-1]
    
    # Build download request
    download_request = {
        "Datasets": [{
            "DatasetID": dataset_uid,
            "DatasetDownloadInformationID": download_info_id,
            "OutputFormat": output_format,
        }]
    }
    
    # Add country restriction if specified
    if country_code:
        # Use NUTS code format (e.g., "GR" for Greece, "IT" for Italy)
        # Note: You may need to specify specific NUTS regions
        download_request["Datasets"][0]["Country"] = country_code
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    response = requests.post(CLMS_DOWNLOAD_REQUEST_URL, json=download_request, headers=headers)
    
    if response.status_code == 401:
        print(f"[ERROR] Authentication failed. Please check your token.")
        print(f"[INFO] Get a token from: https://land.copernicus.eu/registration/")
        return None
    
    response.raise_for_status()
    result = response.json()
    
    task_ids = result.get("TaskIds", [])
    if not task_ids:
        print(f"[ERROR] No task ID returned")
        return None
    
    task_id = task_ids[0].get("TaskID")
    print(f"[OK] Download requested. Task ID: {task_id}")
    print(f"[INFO] You will receive an email when the download is ready.")
    print(f"[INFO] You can also check status with: python {sys.argv[0]} --check-status {task_id} --token <YOUR_TOKEN>")
    
    return task_id


def check_download_status(task_id: str, auth_token: str) -> Optional[str]:
    """Check download status and get download URL if ready."""
    print(f"[INFO] Checking status for task {task_id}...")
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    response = requests.get(f"{CLMS_DOWNLOAD_STATUS_URL}/{task_id}", headers=headers)
    
    if response.status_code == 401:
        print(f"[ERROR] Authentication failed. Please check your token.")
        return None
    
    response.raise_for_status()
    result = response.json()
    
    status = result.get("status", "unknown")
    print(f"[INFO] Status: {status}")
    
    if status == "completed":
        download_url = result.get("download_url")
        if download_url:
            print(f"[OK] Download ready!")
            print(f"[INFO] Download URL: {download_url}")
            return download_url
        else:
            print(f"[WARNING] Status is completed but no download URL found")
    elif status == "failed":
        error = result.get("error", "Unknown error")
        print(f"[ERROR] Download failed: {error}")
    else:
        print(f"[INFO] Download still processing. Check again later.")
    
    return None


def download_file(url: str, output_path: Path):
    """Download a file from URL."""
    print(f"[INFO] Downloading file...")
    print(f"[INFO] URL: {url}")
    print(f"[INFO] Output: {output_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    response = requests.get(url, stream=True, timeout=600)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r[INFO] Progress: {percent:.1f}%", end='', flush=True)
    
    print(f"\n[OK] Downloaded successfully!")
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"[INFO] File size: {file_size_mb:.2f} MB")


def main():
    parser = argparse.ArgumentParser(description="Download CORINE data using CLMS API")
    parser.add_argument("--country", choices=["ITA", "GRC"], help="Country code")
    parser.add_argument("--token", help="CLMS API authentication token (Bearer token)")
    parser.add_argument("--dataset-uid", help="Dataset UID (from search)")
    parser.add_argument("--search", action="store_true", help="Search for CORINE datasets")
    parser.add_argument("--request", action="store_true", help="Request download")
    parser.add_argument("--check-status", help="Check status of download task ID")
    parser.add_argument("--download-url", help="Direct download URL (if already have it)")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()
    
    country_code = args.country
    if country_code == "GRC":
        country_code_api = "GR"  # API uses ISO 3166-1 alpha-2
    elif country_code == "ITA":
        country_code_api = "IT"
    else:
        country_code_api = None
    
    if args.search:
        search_corine_datasets(country_code_api)
        return
    
    if args.check_status:
        if not args.token:
            print("[ERROR] --token required for checking status")
            sys.exit(1)
        download_url = check_download_status(args.check_status, args.token)
        if download_url and args.output:
            download_file(download_url, Path(args.output))
        return
    
    if args.download_url:
        if not args.output:
            print("[ERROR] --output required when using --download-url")
            sys.exit(1)
        download_file(args.download_url, Path(args.output))
        return
    
    if args.request:
        if not args.token:
            print("[ERROR] --token required for requesting download")
            print("[INFO] Get a token from: https://land.copernicus.eu/registration/")
            sys.exit(1)
        if not args.dataset_uid:
            print("[ERROR] --dataset-uid required for requesting download")
            print("[INFO] Use --search to find dataset UIDs")
            sys.exit(1)
        request_download(args.dataset_uid, args.token, country_code_api)
        return
    
    # Default: show help
    parser.print_help()
    print("\n[INFO] Example usage:")
    print("  1. Search for datasets: python download_corine_clms_api.py --search --country GRC")
    print("  2. Request download: python download_corine_clms_api.py --request --dataset-uid <UID> --token <TOKEN> --country GRC")
    print("  3. Check status: python download_corine_clms_api.py --check-status <TASK_ID> --token <TOKEN> --output data2/corine/corine_GRC.zip")
    print("\n[INFO] Get authentication token from: https://land.copernicus.eu/registration/")


if __name__ == "__main__":
    main()

