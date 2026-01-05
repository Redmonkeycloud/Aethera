# Coordinate Input & Analysis Guide

## Overview

The AETHERA application allows you to input coordinates for your Area of Interest (AOI) and start environmental impact analysis.

## How to Input Coordinates

### Method 1: Bounding Box (Easiest)

1. Go to the **Project** page
2. In the sidebar, under "Or Enter Coordinates"
3. Select **"Bounding Box"** option
4. Click **"📍 Use Italy Example"** for a quick 10-hectare field, OR enter coordinates manually:
   - **Min Longitude**: Western boundary (Italy: 6.6° to 18.5°)
   - **Min Latitude**: Southern boundary (Italy: 35.5° to 47.1°)
   - **Max Longitude**: Eastern boundary
   - **Max Latitude**: Northern boundary
5. The area estimate is shown automatically
6. Click **"Create Bounding Box"**

**Quick Start Example (10 hectares in Central Italy):**
- Click **"📍 Use Italy Example"** button - this loads:
  - Min Longitude: `11.2585` (near Florence, Tuscany)
  - Min Latitude: `43.7685`
  - Max Longitude: `11.2615`
  - Max Latitude: `43.7715`
  - Area: ~10 hectares (~316m x 316m)

**Manual Entry Examples:**

*Small field (10 hectares):*
- Min Longitude: `11.2585`
- Min Latitude: `43.7685`
- Max Longitude: `11.2615`
- Max Latitude: `43.7715`

*Medium area (100 hectares):*
- Min Longitude: `11.25`
- Min Latitude: `43.76`
- Max Longitude: `11.27`
- Max Latitude: `43.78`

**Italy Bounds (for reference):**
- Min Longitude: `6.6` (Western border)
- Min Latitude: `35.5` (Southern border)
- Max Longitude: `18.5` (Eastern border)
- Max Latitude: `47.1` (Northern border)

### Method 2: GeoJSON (Advanced)

1. Select **"GeoJSON"** option
2. Paste a GeoJSON Feature or FeatureCollection
3. Click **"Load GeoJSON"**

**Example GeoJSON Feature:**
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [10.0, 35.0],
      [19.0, 35.0],
      [19.0, 47.0],
      [10.0, 47.0],
      [10.0, 35.0]
    ]]
  },
  "properties": {}
}
```

### Method 3: Upload File

1. In the sidebar, under "Area of Interest (AOI)"
2. Click **"Upload GeoJSON"**
3. Select a `.geojson` or `.json` file
4. The AOI will be loaded automatically

## Starting Analysis

Once you have an AOI defined:

1. In the sidebar, scroll to **"Create Analysis Run"**
2. Select:
   - **Project Type**: Solar, Wind, Hydro, or Other
   - **Country** (Optional): Select country for country-specific analysis
3. Click **"🚀 Start Analysis"**

The analysis will:
- Queue an async task
- Process the AOI with environmental datasets
- Generate biodiversity, emissions, and KPI results
- Create analysis outputs

## Monitoring Analysis

After starting analysis:

1. Go to the **"Runs"** tab
2. You'll see the analysis status:
   - ⏳ **Pending**: Task queued
   - 🔄 **Processing**: Analysis in progress
   - ✅ **Completed**: Results ready
   - ❌ **Failed**: Check error details

3. Click **"View Details"** on a completed run to see results

## Coordinate Formats

### Supported Formats:
- ✅ **GeoJSON Feature**: Single polygon/point/line
- ✅ **GeoJSON FeatureCollection**: Multiple features (first feature used)
- ✅ **Bounding Box**: Min/Max lat/lon values

### Coordinate System:
- **WGS84 (EPSG:4326)**: Longitude/Latitude in decimal degrees
- Longitude: -180 to 180 (negative = West, positive = East)
- Latitude: -90 to 90 (negative = South, positive = North)

## Tips

1. **Use Bounding Box** for rectangular areas (easiest)
2. **Use GeoJSON** for complex polygons
3. **Select Country** to enable country-specific datasets (faster loading)
4. **Check Map View** to visualize your AOI before starting analysis

## Troubleshooting

- **"Please define an AOI first"**: Upload a file or enter coordinates
- **Invalid bounding box**: Ensure min < max for both lon and lat
- **Invalid GeoJSON**: Check JSON syntax and geometry type
- **Analysis timeout**: Backend may be processing large datasets, wait and retry

