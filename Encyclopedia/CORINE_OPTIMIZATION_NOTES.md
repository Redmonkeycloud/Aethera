# CORINE Loading Optimization Notes

## Current Issue

The CORINE dataset is very large (237 MB shapefile → 591 MB GeoJSON), which causes timeout issues when trying to load it in the browser.

## Problem

Even with pre-converted GeoJSON:
- File size: 591.86 MB
- HTTP transfer time: Several minutes
- Browser loading time: Very slow
- Memory usage: High (both server and client)

## Solutions

### Option 1: Vector Tiles (Recommended)
Convert CORINE to vector tiles (MVT - Mapbox Vector Tiles) or use a tile server.
- Pros: Only loads visible tiles, fast, scalable
- Cons: Requires tile generation and tile server setup

### Option 2: Simplify Geometries More Aggressively
Reduce geometry complexity to significantly reduce file size.
- Pros: Simple, keeps GeoJSON format
- Cons: May lose detail

### Option 3: Use Map Services (WMS/WMTS)
Serve CORINE as a raster tile service using Geoserver or similar.
- Pros: Standard approach, handles large datasets well
- Cons: Requires additional infrastructure

### Option 4: Load on Demand (Zoom-based)
Only load CORINE when zoomed in to a certain level.
- Pros: Simple to implement
- Cons: User needs to zoom in first

### Option 5: Reduce Attribute Data
Keep only essential attributes, remove unnecessary fields.
- Pros: Reduces file size
- Cons: Less data available

## Immediate Workaround

For now, consider:
1. Loading CORINE only when user zooms to a specific level
2. Showing a message that CORINE is very large and may take time
3. Providing a "Load CORINE" button instead of auto-loading
4. Using a progress indicator for large dataset loading

## Long-term Solution

Implement vector tiles or use a proper tile server for large geospatial datasets.

