**“Advanced Spatial Analytics”** 
---

# **1. Buffering (Distance Analysis)**

**a. Typical use cases:**

* Minimum distance from roads, settlements, rivers, protected areas
* Legal compliance (e.g., 500m from Natura2000, 100m from streams)

**b. Direct Actions:**

* Add a `buffer_analysis.py` in `core/` (or as a utility module)
* For each relevant layer (roads, rivers, settlements, protected areas), compute a buffer (GeoPandas: `gdf.buffer(distance_meters)`)
* Use `gpd.overlay()` to check project AOI intersection or proximity with each buffer
* Output for reporting:

  * “Project AOI is within 180m of nearest river (legal minimum: 100m)”
  * Maps showing buffers and intersections

**c. Data:**

* Download OSM roads/rivers (e.g., via OSMnx or pre-prepared layers)
* Use Natural Earth for basic data, upgrade to Eurostat/OSM for detail

---

# **2. Protected Area Intersection (Natura2000, WDPA, etc.)**

**a. Use cases:**

* Regulatory exclusion or assessment triggers
* Species/habitat overlays

**b. Direct Actions:**

* Add a `protected_area_analysis.py` in `core/`
* Download/load protected areas:

  * **Natura2000**: [Download shapefile here](https://www.eea.europa.eu/data-and-maps/data/natura-11)
  * **WDPA**: [Download here](https://www.protectedplanet.net/en/thematic-areas/wdpa?tab=WDPA)
* Reproject if needed, use `gpd.overlay(aoi_gdf, protected_areas_gdf, how="intersection")`
* Output:

  * List all protected area types that overlap/intersect AOI
  * Area statistics, summary for reporting

---

# **3. Watershed/Hydrological Tools (optional, if relevant)**

**a. Use cases:**

* Impacts on catchments, runoff, flood risk, water quality

**b. Direct Actions:**

* Add a `hydro_analysis.py` (or expand `gis_handler.py`)
* Download catchment/watershed data (e.g., [HydroSHEDS](https://www.hydrosheds.org/), [EU CCM2](https://data.jrc.ec.europa.eu/collection/id-0053))
* Use raster/vector intersection to map project to catchment or drainage area
* Optional: Use raster DEM to delineate local watershed (with raster tools, e.g., richdem or whitebox)

---

# **4. Raster Data Ingestion (Remote Sensing Layers)**

**a. Use cases:**

* NDVI/vegetation, bare soil, burnt area, imperviousness
* Surface temperature, soil moisture

**b. Direct Actions:**

* Add `raster_ingestion.py` or expand `gis_handler.py`
* Use `rasterio` for GeoTIFF reading
* Clip/crop raster to AOI polygon (use `rasterio.mask`)
* Summarize stats per AOI: mean/median, histograms (e.g., average NDVI for project area)
* Example sources:

  * ESA WorldCover ([download](https://esa-worldcover.org/en))
  * Sentinel-2 NDVI (can use Google Earth Engine for batch export if needed)
  * Copernicus Imperviousness

---

## **Python Integration Plan**

* Each of the above modules gets its own script/class in `core/` (buffer\_analysis.py, protected\_area\_analysis.py, hydro\_analysis.py, raster\_ingestion.py)
* All steps logged using your `logging_utils`
* Results saved both as data (tables, CSV) and visualizations (PNG map overlays, possibly GeoJSON for web)
* Integrate step-by-step into `main_controller.py` pipeline, **but keep the system modular** (user can run each as needed)

---