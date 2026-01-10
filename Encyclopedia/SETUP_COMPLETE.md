# AETHERA Setup Complete ✅

## What is `run_20251117_132207`?

**`run_20251117_132207`** is a **Run ID** - a unique identifier for an analysis run. The format is:
- `run_` prefix
- `20251117` = Date (2025-11-17)
- `132207` = Time (13:22:07 UTC)

This was automatically generated when we ran the test analysis. Each time you run an analysis, a new run ID is created with the current timestamp.

## Recent Updates

### 1. **Country Selection Added** 🌍
- The frontend now asks you to select a country first
- Available countries are detected from your GADM data (currently: Italy, Greece)
- The map automatically centers on the selected country

### 2. **Improved Layer Loading** 🗺️
- Layers now load based on country selection
- Better error handling and status messages
- Visual feedback when layers are loading

### 3. **CORS Enabled** 🔓
- Added CORS middleware to the API so the frontend can access it
- No more cross-origin errors

## How to Use

1. **Start the API Server** (if not running):
   ```bash
   cd backend
   python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open the Frontend**:
   - Open `frontend/index.html` in your browser
   - OR visit `http://localhost:8080/frontend/index.html` if the HTTP server is running

3. **Select a Country**:
   - Choose a country from the dropdown (e.g., "Italy (ITA)")
   - The map will center on that country

4. **Select a Run**:
   - Available runs will appear in the list
   - Click on a run to select it
   - Click "Load Biodiversity Layers" to visualize

5. **Toggle Layers**:
   - Use checkboxes to show/hide:
     - Biodiversity Sensitivity (color-coded by risk level)
     - Natura 2000 Sites (protected areas)
     - Overlap Areas (where AOI intersects protected sites)

## API Endpoints

### Core Endpoints
- `GET /countries` - List available countries
- `GET /countries/{code}/bounds` - Get country bounding box
- `GET /runs` - List all analysis runs
- `GET /runs/{run_id}` - Get run details

### Biodiversity Layers
- `GET /runs/{run_id}/biodiversity/sensitivity` - Biodiversity sensitivity map
- `GET /runs/{run_id}/biodiversity/natura` - Natura 2000 protected areas
- `GET /runs/{run_id}/biodiversity/overlap` - Overlap between AOI and protected areas

### Environmental Indicators
- `GET /runs/{run_id}/indicators/receptor-distances` - Distance to sensitive receptors
- `GET /runs/{run_id}/indicators/kpis` - Comprehensive environmental KPIs (20+ indicators)

### AI/ML Model Predictions
- `GET /runs/{run_id}/indicators/resm` - RESM (Renewable Suitability) predictions
- `GET /runs/{run_id}/indicators/ahsm` - AHSM (Hazard Susceptibility) predictions
- `GET /runs/{run_id}/indicators/cim` - CIM (Cumulative Impact) predictions

### Cache Management
- `GET /cache/stats` - Dataset cache statistics
- `POST /cache/clear` - Clear the dataset cache

## Troubleshooting

### Layers Not Showing?
1. Make sure the API server is running on port 8000
2. Check browser console for errors (F12)
3. Verify the run ID exists and has biodiversity data
4. Make sure CORS is enabled (it should be now)

### No Countries Showing?
- Check that GADM data exists in `data2/gadm/`
- Look for directories like `gadm41_ITA_shp`, `gadm41_GRC_shp`

### No Runs Available?
- Run an analysis first:
  ```bash
  cd backend
  python -m src.main_controller --aoi ../test_aoi.geojson --project-type solar_farm
  ```

## What's New

### Phase 1 Complete ✅
- **WKT Support**: Full support for Well-Known Text strings and files
- **Dataset Caching**: In-memory and disk-based caching for faster repeated analyses

### Phase 2 Complete ✅
- **Distance-to-Receptor**: Calculates distances to protected areas, settlements, and water bodies
- **Advanced Environmental KPIs**: 20+ scientifically-accurate indicators with bibliography

### Phase 3 Complete ✅
- **RESM Model**: Renewable energy suitability assessment (0-100 score)
- **AHSM Model**: Multi-hazard susceptibility assessment (flood, wildfire, landslide)
- **CIM Model**: Cumulative impact model integrating all other models
- **All models**: Support external training data with synthetic fallback

## Next Steps

- Create new analyses for different countries
- Upload custom AOI files (GeoJSON, Shapefile, or WKT)
- Generate reports from analysis results
- Add more countries to the GADM dataset
- Explore model predictions via API endpoints
- Use cache management for performance optimization

