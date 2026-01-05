# CORINE Land Cover Download Instructions - Using CLMS API

## Overview

The Copernicus Land Monitoring Service (CLMS) provides an API for programmatic downloads of CORINE data. This is more efficient than manual downloads.

**API Documentation**: https://eea.github.io/clms-api-docs/download.html

## Prerequisites

1. **Registration**: Register for free at https://land.copernicus.eu/registration/
2. **Authentication Token**: Get your Bearer token from the Copernicus portal
   - Log in to https://land.copernicus.eu/
   - Navigate to your profile/API settings
   - Generate or copy your Bearer token

## Step-by-Step Process

### Step 1: Search for CORINE Datasets

Find the dataset UID you want to download:

```bash
python scripts/download_corine_clms_api.py --search --country GRC
```

This will show available CORINE datasets with their UIDs. For CORINE 2018, the UID is: `0407d497d3c44bcd93ce8fd5bf78596a`

### Step 2: Request Download

Request a download using the dataset UID and your authentication token:

```bash
python scripts/download_corine_clms_api.py --request \
  --dataset-uid 0407d497d3c44bcd93ce8fd5bf78596a \
  --token YOUR_BEARER_TOKEN \
  --country GRC \
  --output-format Shapefile
```

**Note**: 
- Replace `YOUR_BEARER_TOKEN` with your actual token
- The API will process the request in the background
- You'll receive an email when the download is ready
- The script will return a Task ID

### Step 3: Check Download Status

Check if your download is ready:

```bash
python scripts/download_corine_clms_api.py --check-status TASK_ID \
  --token YOUR_BEARER_TOKEN \
  --output data2/corine/corine_GRC.zip
```

The script will:
- Check the download status
- If ready, automatically download the file
- Save it to the specified output path

### Step 4: Process Downloaded File

After downloading:

1. Extract the ZIP file
2. Find the shapefile (usually in a subdirectory)
3. Move/rename to: `data2/corine/corine_GRC.shp`
4. Tag the dataset:
   ```bash
   python scripts/download_datasets.py
   ```
5. Extract additional datasets:
   ```bash
   python scripts/extract_agricultural_lands.py --country GRC
   python scripts/extract_forests_from_corine.py --country GRC
   ```

## Alternative: Manual Download

If you prefer manual download or if the API doesn't work:

1. Go to: https://land.copernicus.eu/pan-european/corine-land-cover/clc2018
2. Click "Download" or "Access data"
3. Register/Login
4. Download "CORINE Land Cover 2018 (Vector)"
5. Extract and process as above

## Troubleshooting

### Authentication Errors
- Verify your token is correct
- Check token hasn't expired
- Re-generate token if needed

### Download Not Ready
- Downloads can take several minutes to hours depending on file size
- Check your email for notifications
- Try checking status again later

### Country-Specific Downloads
- The API may not support direct country filtering for CORINE
- You may need to download the full Europe dataset and clip it using:
  ```bash
  python scripts/clip_corine_to_country.py --country GRC --input corine_europe.shp --output corine_GRC.shp
  ```

## Script Usage

```bash
# Search for datasets
python scripts/download_corine_clms_api.py --search [--country GRC]

# Request download
python scripts/download_corine_clms_api.py --request --dataset-uid <UID> --token <TOKEN> [--country GRC] [--output-format Shapefile]

# Check status and download
python scripts/download_corine_clms_api.py --check-status <TASK_ID> --token <TOKEN> --output <OUTPUT_PATH>

# Direct download (if you already have the URL)
python scripts/download_corine_clms_api.py --download-url <URL> --output <OUTPUT_PATH>
```

## References

- CLMS API Documentation: https://eea.github.io/clms-api-docs/download.html
- Copernicus Registration: https://land.copernicus.eu/registration/
- CORINE 2018 Dataset: https://land.copernicus.eu/pan-european/corine-land-cover/clc2018

