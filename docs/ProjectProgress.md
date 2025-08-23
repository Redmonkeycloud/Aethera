# **AETHERA: Current Status and Roadmap (2025-08-05, updated)**

## I. What’s DONE (now)

### A. Data Ingestion & Spatial Core
- ✅ Automated download/validation:
  - Natural Earth country boundaries
  - GADM (per ISO3; zip + extract)
  - Eurostat NUTS shapefile
- ✅ Manual placement (with checks) for CORINE 2018 GPKG
- ✅ `core/gis_handler.py` modular with extraction/progress
- ✅ Centralized logging (`utils/logging_utils.py`) with file + console output, memory usage

### B. AOI Extraction & Land Cover
- ✅ AOI extraction from GADM by ISO3
- ✅ CORINE vector clip per country AOI (bbox read via pyogrio)
- ✅ Intersection with AOI; robust handling of `Code_18` field; land cover summary
- ✅ Export:
  - `outputs/clipped_landcover_<ISO3>.geojson`
  - `outputs/land_cover_map_<ISO3>.png` (if plotting enabled)

### C. Protected Areas (Natura/WDPA)
- ✅ `core/protected_area_analysis.py`:
  - Load Natura2000 shapefile (EPSG:3035 preferred), or WDPA fallback
  - AOI intersection, per-site overlap/area summary
  - Optional clipped GeoJSON
- ✅ Integrated into `main_controller.py`, Excel sheet `<Source>_Overlap`

### D. Proximity/Buffer Analysis (Roads + Rivers)
- ✅ `core/osm_utils.py`:
  - OSMnx roads by ISO (cached to GPKG)
  - Optional PBF route (pyrosm) with filter to drivable network
- ✅ `core/buffer_analysis.py`:
  - Fast nearest (STRtree.nearest), distance stats
  - Multi-buffer generation and AOI overlap summary
  - River loader with bbox clip (HydroRIVERS EU/global)
- ✅ Integrated into `main_controller.py`
  - Output GeoJSONs for nearest roads/rivers
  - Excel sheets: `Proximity_Roads_Summary`, `Proximity_Rivers_Summary`

### E. Emissions & Uncertainty
- ✅ Expanded `core/emissions_api.py`:
  - CORINE class → category mapping
  - IPCC Tier-1 defaults + placeholders for country-specific factors
  - Monte Carlo uncertainty (n_sim configurable), returns mean and quantiles
- ✅ Integrated into `main_controller.py`:
  - Excel sheet: `Emissions Uncertainty (MC)`

### F. AI/ML Scaffold
- ✅ Folder structure under `ai/` for models/training/config/evaluation
- ✅ Baseline RESM config + training skeleton (XGB/RF/GBM ready)
- ✅ Logging integration in training scripts

---

## II. IN PROGRESS / PARTIAL

### A. Advanced Analytics
- ⏳ Raster ingestion (NDVI, WorldCover) – **not yet**
- ⏳ Watershed/catchment – **not yet**
- ⏳ Maps/PNGs for proximity/buffers – **planned**

### B. ML/AI
- ⏳ RESM: training script works but **needs**:
  - richer feature engineering, multiple metrics (R², RMSE, MAE, MAPE)
  - model comparison + persisted leaderboard
- ⏳ Biodiversity model – **not started**
- ⏳ Legal compliance AI – **not started**

### C. Reports / Outputs
- ⏳ PDF EIA generator (maps, tables, text, compliance) – **not started**
- ⏳ Interactive dashboard – **not started**

### D. Deployment
- ⏳ FastAPI server / cloud pipeline – **not started**
- ⏳ Docker image – **not started**

---

## III. PRIORITIZED TODO LIST

### 1) Spatial & Emissions (short term)
- [ ] Add PNG map exports for buffers and nearest features
- [ ] Add **distance-to-grid** (requires grid layer under `data/grid/grid.gpkg`, layer="grid")
- [ ] Raster ingestion (NDVI/WorldCover), summary per AOI
- [ ] Country-specific emission factors (GR, IT, ES first)

### 2) ML/AI
- [ ] Finish **RESM** pipeline:
  - train/test split, multiple metrics (R², RMSE, MAE, MAPE)
  - SHAP feature importance
  - model registry with timestamped versions
- [ ] Biodiversity risk model:
  - use corine + protected area + optional species ranges
  - start with RF baseline, plan CNN/GeoNN later
- [ ] Legal compliance AI (config-driven rules per country)

### 3) Reporting
- [ ] PDF EIA builder:
  - maps (AOI, PA, buffers), tables (land cover, emissions, proximity), compliance sections
  - multi-language support (EN/EL/IT/ES)

### 4) Deployment
- [ ] FastAPI endpoints for jobs & results
- [ ] Docker image / compose for local + cloud

---

## IV. Run Outputs (Current)

- `outputs/analysis_summary_<ISO3>.xlsx` with sheets:
  - `Land Cover Summary`
  - `Emissions Summary`
  - `Emissions Uncertainty (MC)`
  - `<Natura or WDPA>_Overlap`
  - `Proximity_Roads_Summary` *(if roads present)*
  - `Proximity_Rivers_Summary` *(if rivers present)*
- Optional GeoJSONs:
  - `clipped_<PA source>_<ISO3>.geojson`
  - `aoi_nearest_roads_<ISO3>.geojson`
  - `aoi_nearest_rivers_<ISO3>.geojson`

---

## V. Notes on Data Locations

- Place CORINE GPKG under: `data/corine/U2018_CLC2018_V2020_20u1.gpkg`
- Natura2000 shapefile under: `data/protected_areas/natura2000/`
- WDPA shapefile (optional) under: `data/protected_areas/wdpa/`
- HydroRIVERS EU/global under: `data/rivers/HydroRIVERS_v10_eu_shp/` or `data/rivers/HydroRIVERS_v10_shp/`
- OSMnx roads cache will be created under: `data/roads/roads_<ISO3>.gpkg`
