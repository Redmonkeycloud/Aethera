# GADM Levels Explained

## What are GADM Levels?

GADM (Global Administrative Areas) provides administrative boundaries at different levels of detail:

### Level 0: Country
- **What it is**: The entire country boundary
- **Use case**: Full country-wide analysis (what we need!)
- **Example**: All of Italy, all of Greece
- **File**: `gadm41_ITA_0.shp` (country boundary)

### Level 1: States/Regions/Provinces
- **What it is**: First-level administrative divisions
- **Use case**: State/province-level analysis
- **Example**: 
  - Italy: Regions (Lombardy, Tuscany, Sicily, etc.)
  - Greece: Administrative regions (Attica, Central Macedonia, etc.)
- **File**: `gadm41_ITA_1.shp` (multiple regions)

### Level 2: Counties/Districts
- **What it is**: Second-level administrative divisions
- **Use case**: County/district-level analysis
- **Example**:
  - Italy: Provinces (Milan, Florence, Palermo, etc.)
  - Greece: Regional units
- **File**: `gadm41_ITA_2.shp` (many provinces)

### Level 3: Municipalities/Communes
- **What it is**: Third-level administrative divisions (most detailed)
- **Use case**: City/municipality-level analysis
- **Example**:
  - Italy: Comuni (municipalities)
  - Greece: Municipalities
- **File**: `gadm41_ITA_3.shp` (thousands of municipalities)

## For AETHERA Country Analysis

**You need Level 0** - the country boundary. This gives you the full country outline for:
- Full country biodiversity mapping
- Country-wide protected area analysis
- Complete land cover assessment

## Format: GeoJSON vs KMZ

### GeoJSON ✅ **RECOMMENDED**
- **Format**: `.geojson` or `.json`
- **Pros**:
  - Native format for web mapping (Leaflet, Mapbox, etc.)
  - Easy to work with in Python (GeoPandas)
  - Human-readable text format
  - No conversion needed
  - Smaller file size
- **Cons**: None for our use case
- **Download**: Select "GeoJSON" format on GADM website

### KMZ (Google Earth)
- **Format**: `.kmz` (compressed KML)
- **Pros**: 
  - Good for viewing in Google Earth
  - Can contain styling
- **Cons**:
  - Need to convert to GeoJSON/Shapefile for analysis
  - Not directly usable in our pipeline
  - Extra conversion step required
- **Download**: Only if you want to view in Google Earth first

### Shapefile (Alternative)
- **Format**: `.shp` + `.dbf` + `.shx` + `.prj` (multiple files)
- **Pros**:
  - Standard GIS format
  - Works directly with GeoPandas
  - What we're currently using
- **Cons**:
  - Multiple files (need to keep all together)
  - Slightly more complex than GeoJSON
- **Download**: Also works, but GeoJSON is simpler

## Recommendation

**Download GeoJSON format for Level 0** - it's the simplest and works directly with our system.

## Download Instructions for Greece

1. Go to: https://gadm.org/download_country.html
2. Select "Greece" from the country dropdown
3. Select format: **GeoJSON** (or Shapefile if GeoJSON not available)
4. Select level: **Level 0** (country boundary)
5. Click "Download"
6. Extract the file to: `D:\Aethera_original\data2\gadm\gadm41_GRC_shp\`
7. Rename if needed to match pattern: `gadm41_GRC_0.geojson` or `gadm41_GRC_0.shp`

## File Structure After Download

```
data2/gadm/
├── gadm41_ITA_shp/
│   ├── gadm41_ITA_0.shp  ✅ (country)
│   ├── gadm41_ITA_1.shp  (regions)
│   ├── gadm41_ITA_2.shp  (provinces)
│   └── gadm41_ITA_3.shp  (municipalities)
└── gadm41_GRC_shp/
    └── gadm41_GRC_0.geojson  ✅ (country - after download)
```

## Quick Reference

| Level | What It Is | File Count | Use Case |
|-------|------------|------------|----------|
| 0 | Country | 1 file | Full country analysis ✅ |
| 1 | States/Regions | ~10-20 files | Regional analysis |
| 2 | Counties/Provinces | ~100-200 files | County-level analysis |
| 3 | Municipalities | 1000+ files | City-level analysis |

For AETHERA, **Level 0 in GeoJSON format** is what you need!

