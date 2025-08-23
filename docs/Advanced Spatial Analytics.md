**“Advanced Spatial Analytics”**
---

# ✅ 1. Buffering (Distance / Proximity Analysis)

**Status:** Implemented (roads + rivers)

**What’s implemented:**
- `core/buffer_analysis.py`:
  - Fast minimum distance per AOI polygon using Shapely 2.0 `STRtree.nearest`
  - Multi-distance buffers (100/250/500/1000m), optional dissolve, and AOI buffer overlap (% of AOI)
  - Summary statistics (mean/min/max, p50, p95) for distances
  - Rivers loader with bbox clip and metric CRS checks
- Roads ingestion and caching via `core/osm_utils.py`:
  - OSMnx download (per ISO country) with *local caching* to GPKG
  - Optional PBF→roads using pyrosm (if pyrosm installed)
  - Automatic reuse of cached GPKG on subsequent runs
- Integrated in `core/main_controller.py`:
  - Computes nearest distance from AOI to **roads** and **rivers (HydroRIVERS)**
  - Saves per-AOI nearest tables as GeoJSON and summary sheets in Excel

**Data sources:**
- **Roads**: OSM via OSMnx (Overpass) or local `.pbf` (pyrosm)  
- **Rivers**: HydroRIVERS (EU or global) — local shapefile

**Outputs:**
- `outputs/aoi_nearest_roads_<ISO3>.geojson`
- `outputs/aoi_nearest_rivers_<ISO3>.geojson`
- Excel sheets: `Proximity_Roads_Summary`, `Proximity_Rivers_Summary`

**Next enhancements:**
- Add PNG maps: AOI + buffers + nearest feature lines
- Add distance-to-grid (if energy grid layers provided)
- Add settlements/ports/airports proximity (optional OSMnx queries)

---

# ✅ 2. Protected Area Intersection (Natura2000, WDPA)

**Status:** Implemented (with Natura2000 shapefile preferred; WDPA fallback)

**What’s implemented:**
- `core/protected_area_analysis.py`:
  - Loads **Natura2000** shapefile (EPSG:3035 recommended) OR **WDPA** polygons if Natura is missing
  - CRS normalization and area calculation in metric CRS
  - AOI intersection and per-site overlap summary (site_code, site_name, overlap_ha)
  - Optional GeoJSON export of clipped protected areas
- Integrated in `core/main_controller.py`:
  - Summaries saved in Excel as `<Source>_Overlap` sheet
  - Fallback logic: attempts Natura first → WDPA if not present

**Data sources:**
- **Natura2000** shapefile (EEA):  
  https://www.eea.europa.eu/data-and-maps/data/natura-11
- **WDPA** polygons:  
  https://www.protectedplanet.net/en/thematic-areas/wdpa?tab=WDPA

**Next enhancements:**
- Add Ramsar, IBAs, Emerald (if needed)
- Flag legal thresholds (e.g., AOI must avoid specific designations)

---

# ⏳ 3. Watershed/Hydrological Tools (optional)

**Status:** Not implemented yet

**Potential actions:**
- Add `core/hydro_analysis.py`:
  - Catchment/WBD junction using HydroBASINS/CCM2
  - If DEM available, basic watershed delineation
- Data sources:
  - HydroSHEDS HydroBASINS: https://www.hydrosheds.org/
  - EU CCM2 (JRC): https://data.jrc.ec.europa.eu/collection/id-0053

---

# ⏳ 4. Raster Data Ingestion (Remote Sensing)

**Status:** Not implemented yet

**Planned actions:**
- Add `core/raster_ingestion.py`:
  - `rasterio` read; `rasterio.mask` crop by AOI
  - Stats per AOI (mean/median/p95), histograms
- Example layers:
  - ESA WorldCover
  - Sentinel-2 NDVI (locally or via GEE batch)

---

## Python Integration & Logging

- All modules log to the centralized `utils/logging_utils.py` with per-run log files.
- `main_controller.py` orchestrates:
  1) AOI (GADM)  
  2) CORINE clip  
  3) Protected areas (Natura→WDPA)  
  4) Land cover + emissions + Monte Carlo  
  5) Proximity (roads, rivers)  
  6) Excel export (+ optional GeoJSON maps)

---

## Immediate TODOs (Spatial)

- [ ] Add PNG map exports for buffers and nearest features  
- [ ] Add distance-to-grid support (if grid GPKG provided under `data/grid/`)  
- [ ] Add settlements/ports/airports proximity (OSMnx)  
- [ ] Optional: dask-geopandas for parallelization on big countries
