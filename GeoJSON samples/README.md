# GeoJSON Samples

This folder contains sample GeoJSON files for testing the AOI (Area of Interest) upload functionality.

## Sample Files

### `sample_aoi.geojson`
- **Location**: Central Italy (around Rome area)
- **Type**: Simple rectangular polygon
- **Coordinates**: 12.0-13.0°E, 42.0-43.0°N
- **Use case**: Basic testing of AOI upload and display

### `sample_aoi_complex.geojson`
- **Location**: Northern Italy (around Milan area)
- **Type**: Complex polygon with multiple vertices
- **Coordinates**: 10.5-11.8°E, 45.3-45.9°N
- **Use case**: Testing with more complex geometries

## How to Use

1. Open a project in the AETHERA frontend
2. Navigate to the "Define Area of Interest (AOI)" section
3. Drag and drop one of these GeoJSON files onto the upload area
4. The AOI should appear on the map

## Note

This folder is excluded from Git (see `.gitignore`) to keep the repository clean. You can add your own test files here without worrying about committing them.

