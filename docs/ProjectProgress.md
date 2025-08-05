# **AETHERA: Current Status and Roadmap (2025-08-05)**

## **I. What’s DONE (as of now)**

*(All implemented and validated modules, scripts, and system features)*

### **A. Data Ingestion & Spatial Core**

* Automated download/validation for:

  * Natural Earth country boundaries
  * GADM country boundaries (by ISO3 code, zip+extract)
  * Eurostat NUTS shapefile
* Manual placement (with path checks) for CORINE 2018 GPKG
* Modular `gis_handler.py` with error handling, extraction, and CRS checks
* Data validation utilities (empty-check, CRS-check, metadata summary)
* Configurable paths/URLs for all base datasets

### **B. AOI Extraction & Land Cover Analysis**

* Automated AOI extraction from GADM by user ISO3 code
* CORINE vector extraction/clipping per country AOI (pyogrio, efficient bbox read)
* Intersection logic between AOI and CORINE for land cover stats
* Land cover summary: area per code, with CORINE to label mapping
* Robust logging (all steps, errors, memory), centralized in `utils/logging_utils.py`

### **C. Emissions Calculation**

* Tiered emission factors: IPCC Tier 1 defaults
* Area-based emission calculation for AOI (land cover → emissions)
* Modular, extensible `emissions_api.py` with summary outputs
* Output results: Excel file (multi-sheet: land cover, emissions), GeoJSON map

### **D. Automation & Logging**

* Step-wise progress logging (both file and console)
* Error, warning, and memory status logging
* .log file management (auto-naming per run/country)
* Logging abstraction in `logging_utils.py` (easy reuse)

### **E. ML/AI Infrastructure (Scaffold)**

* Modular AI pipeline folders: `ai/models`, `ai/training`, `ai/config`, etc.
* Baseline config files for RESM (features, model params, output path)
* Skeleton model: RandomForest/GBM/XGBoost, joblib save/load, basic logging

---

## **II. What is IN PROGRESS / PARTIALLY COMPLETE**

### **A. Advanced Spatial Analytics**

* Partial: Only basic AOI/land cover overlay implemented
* Not yet:

  * Buffering (e.g., distance to roads, infrastructure)
  * Protected area exclusion/intersection (Natura2000, WDPA)
  * Watershed/hydrological tools
  * Raster data ingestion (remote sensing)

### **B. ML/AI Modeling**

* RESM pipeline partially coded; not yet full data→train→multi-metric validation→save
* No deep learning/geospatial direct input yet (CNN/GeoNN not implemented)
* No AI modules for:

  * Biodiversity/sensitive habitat prediction
  * Legal compliance automation (country rules)
  * Impact scenario analysis (Monte Carlo/uncertainty quantification)
* No AI interpretability (SHAP, feature importance) or automated reporting

### **C. Emissions/Impact Expansion**

* Only static (single-year, Tier 1) emissions factors in use
* No country/sector/construction/transport/land use change (time-series) integration yet
* No uncertainty/Monte Carlo support
* No scenario analysis

### **D. EIA Output Generation**

* Only Excel/GeoJSON export available
* No PDF report builder (with maps, tables, text, compliance sections)
* No interactive/graphical result dashboards

### **E. Deployment/Workflow**

* CLI-based only
* No web API/server or cloud-native pipeline
* No plugin/extension interface yet
* No official Docker container or cloud deployment script

---

## **III. PRIORITIZED TODO LIST**

*(from highest to lowest priority; everything listed explicitly)*

---

### **1. ML/AI Module Expansion & Pipelines**

**a. Complete RESM (Renewable Energy Suitability Model) pipeline:**

* Data loading with full feature engineering
* Train/test split
* Model training (RandomForest/XGBoost/GBM—all three, compare)
* Multi-metric validation: R², RMSE, MAE, MAPE (minimum 4 metrics)
* Model saving/loading, version control
* Logging at each step

**b. Add biodiversity impact AI module**

* Data ingestion: land cover, protected areas, species range data (e.g., GBIF, WDPA, Natura2000)
* Predictive model: presence/absence or risk scoring (baseline: RF, future: CNN/GeoNN)
* Metrics: AUC, F1, recall, precision

**c. Add legal compliance AI module**

* Config-driven rules (buffer distances, protected exclusions) per country
* Automated checklist and summary scoring

**d. Add scenario analysis/Monte Carlo module**

* Uncertainty quantification for land cover change and emissions
* Batch runs with varying input data, summarize spread/confidence intervals

---

### **2. Emissions & Impact Module**

* Expand emissions database:

  * Construction materials (concrete, steel, asphalt, aggregates)
  * Transportation (by mode, fuel)
  * Country/region-specific factors (Greece, Italy, Spain, etc.)
* Add land use *change* emissions (time series, scenario)
* Integrate with project phases (construction, operation, decommissioning)
* Add uncertainty/Monte Carlo for all emission calculations

---

### **3. Advanced GIS & Spatial Analytics**

* Add buffer/proximity analysis (distance to infrastructure, settlements, protected areas)
* Overlay AOI/project with:

  * Natura2000, WDPA, IBAs, Ramsar wetlands (biodiversity overlays)
  * Custom layers (user upload)
* Watershed delineation (if hydrology relevant)
* Raster ingestion (e.g., WorldCover, Sentinel-2 NDVI for environmental baseline)
* Use dask-geopandas or modin for parallelization/large file support

---

### **4. EIA Report & Visualization**

* Automated PDF EIA report generator:

  * Maps, tables, summary text, legal compliance checklist
  * Country-language support (EN, EL, IT, ES at minimum)
* Interactive dashboard (optional for cloud/web phase)
* Excel report with detailed sheets for each module (land cover, emissions, biodiversity, legal, scenario results)

---

### **5. Deployment, API & Integration**

* Web API (RESTful or FastAPI) for job submission and result download
* Cloud-native deployment (Docker, container orchestration scripts)
* Retain CLI/desktop run capability for advanced/power users
* Plugin system for:

  * Custom data sources
  * Custom emissions/impact calculations
  * User-uploaded ML models or scenarios

---

### **6. Documentation & Quality Assurance**

* Full code documentation, docstrings, and usage examples
* Automated tests (unit, integration) for critical modules
* End-to-end sample project (input data to final PDF/Excel report)

---