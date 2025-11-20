# Country-Wide Analyses

This document explains how to run analyses for entire countries using GADM administrative boundaries.

## Overview

AETHERA supports running analyses for entire countries using GADM (Global Administrative Areas) level 0 boundaries. This allows you to assess environmental impacts, suitability, and hazards across entire countries.

## Prerequisites

1. **GADM Data**: Download GADM data for your target country from [GADM Downloads](https://gadm.org/download_country.html)
   - Recommended format: GeoJSON (`.json`) for easier handling
   - Alternative: Shapefile (`.shp`) - will be converted automatically
   - Place in `data2/gadm/gadm41_{COUNTRY_CODE}_shp/` or `data2/gadm/gadm41_{COUNTRY_CODE}_0.json`

2. **Country Code**: Use ISO 3166-1 alpha-3 country codes (e.g., `ITA` for Italy, `GRC` for Greece)

## Running Country Analyses

### Using the Script

```bash
cd scripts
python run_country_analysis.py {COUNTRY_CODE} --project-type {PROJECT_TYPE}
```

**Examples:**

```bash
# Analyze Italy for solar farm suitability
python run_country_analysis.py ITA --project-type solar_farm

# Analyze Greece for wind farm suitability
python run_country_analysis.py GRC --project-type wind_farm
```

### What Gets Generated

Each country analysis run produces:

1. **Geospatial Layers**:
   - Land cover summary (CORINE clipped to country)
   - Biodiversity layers (Natura 2000 sites, sensitivity maps, overlap areas)
   - Receptor distances (protected areas, settlements, water bodies)

2. **Environmental Indicators**:
   - 20+ advanced environmental KPIs (emissions, biodiversity, ecosystem services, etc.)
   - Distance-to-receptor analysis
   - Land use efficiency metrics

3. **AI/ML Model Predictions**:
   - **RESM**: Renewable energy suitability score (0-100) with categorization
   - **AHSM**: Hazard susceptibility risk score (0-100) for multiple hazards
   - **CIM**: Cumulative impact score (0-100) integrating all models
   - **Biodiversity**: Sensitivity score and category

4. **Emissions Analysis**:
   - Baseline emissions
   - Project-induced emissions
   - Net carbon balance

5. **Output Files** (in `data/run_{timestamp}/processed/`):
   - `land_cover_summary.json`
   - `biodiversity/prediction.json`
   - `biodiversity/sensitivity.geojson`
   - `biodiversity/natura_clipped.geojson`
   - `biodiversity/overlap.geojson`
   - `emissions_summary.json`
   - `receptor_distances.json`
   - `environmental_kpis.json`
   - `resm_prediction.json`
   - `ahsm_prediction.json`
   - `cim_prediction.json`
   - `manifest.json`

## Available Countries

Currently configured countries (based on available GADM data):

- **Italy (ITA)**: Full country coverage
- **Greece (GRC)**: Full country coverage

To add more countries:
1. Download GADM level 0 data for the country
2. Place in `data2/gadm/gadm41_{COUNTRY_CODE}_shp/` or as `gadm41_{COUNTRY_CODE}_0.json`
3. The system will automatically detect it

## API Access

Once an analysis is complete, access results via the API:

```bash
# Get country bounds
GET /countries/{code}/bounds

# Get run details
GET /runs/{run_id}

# Get biodiversity layers
GET /runs/{run_id}/biodiversity/sensitivity
GET /runs/{run_id}/biodiversity/natura
GET /runs/{run_id}/biodiversity/overlap

# Get environmental indicators
GET /runs/{run_id}/indicators/receptor-distances
GET /runs/{run_id}/indicators/kpis
GET /runs/{run_id}/indicators/resm
GET /runs/{run_id}/indicators/ahsm
GET /runs/{run_id}/indicators/cim
```

## Frontend Visualization

The frontend (`frontend/index.html`) supports:
- Country selection dropdown (auto-populated from available GADM data)
- Run listing filtered by country
- Biodiversity layer visualization
- Map centering on country bounds

## Performance Considerations

- **Large Countries**: Country-wide analyses can take 10-30 minutes depending on:
  - Country size
  - Dataset complexity
  - Number of protected areas
  - Computational resources

- **Memory Usage**: Large countries may require significant RAM (4-8GB recommended)

- **Caching**: Dataset caching is enabled by default to speed up repeated analyses

## Troubleshooting

### "GADM data not found for country {CODE}"

1. Check that GADM data exists in `data2/gadm/`
2. Verify the directory name format: `gadm41_{CODE}_shp` or file `gadm41_{CODE}_0.json`
3. Ensure the level 0 file exists (country boundary)

### "No CORINE data found"

1. Download CORINE Land Cover data for the country
2. Place in `data2/corine/`
3. Ensure the file is named correctly (e.g., `corine_{CODE}.shp` or `corine_{CODE}.gpkg`)

### "Analysis taking too long"

1. Check dataset cache is enabled (reduces load time)
2. Consider analyzing smaller regions first
3. Verify system has sufficient RAM

## Next Steps

- Add more countries to the analysis
- Compare results across countries
- Generate country-specific reports
- Integrate with legal rules engine for compliance checking
