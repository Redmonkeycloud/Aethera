# 📘 AETHERA Backend Architecture Guide

This document outlines the backend structure of **AETHERA**, the AI-powered Environmental Impact Assessment (EIA) automation tool. Each script is modular and serves a specific purpose in the workflow, from data ingestion to emissions calculation and results packaging.

---

## 🔧 Core Backend Scripts

### 1. `gis_handler.py`
- **Purpose**: Fetches, processes, and manages geospatial data.
- **Key Tools**: `geopandas`, `rasterio`, `fiona`
- **Functions**:
  - Load shapefiles, GeoJSON, raster data.
  - Apply coordinate transformation.
  - Clip/mask layers based on region of interest.

### 2. `emissions_api.py`
- **Purpose**: Calculates emissions baselines automatically using pre-defined emission factors and activity data.
- **Key Tools**: `pandas`, optional API connectors.
- **Functions**:
  - Integrate IPCC emission factors.
  - Calculate CO₂eq emissions from land use, transport, energy.

### 3. `land_filter.py`
- **Purpose**: Applies spatial filters to exclude or highlight specific land types or protection zones.
- **Key Tools**: `geopandas`, `shapely`
- **Functions**:
  - Remove restricted areas (Natura2000, protected zones).
  - Select lands based on distance to roads, slope, urban proximity.

### 4. `land_suitability_engine.py`
- **Purpose**: Core engine that scores land parcels for suitability.
- **Key Tools**: `geopandas`, `numpy`
- **Functions**:
  - Combine layers (slope, elevation, proximity).
  - Weight and score parcels.
  - Output suitability maps.

### 5. `api_connector.py`
- **Purpose**: Connects to remote GIS services, national data portals, and environmental databases.
- **Key Tools**: `requests`, `geopandas.read_file(<WFS_url>)`
- **Functions**:
  - Fetch land use, biodiversity, and soil datasets via API.

### 6. `data_ingestion.py`
- **Purpose**: Loads structured and semi-structured datasets into the platform.
- **Key Tools**: `pandas`, `geopandas`
- **Functions**:
  - Format conversion (CSV to GeoDataFrame, Shapefile to GeoJSON).
  - Metadata extraction.

### 7. `validator.py`
- **Purpose**: Validates integrity and quality of spatial and numeric datasets.
- **Key Tools**: `geopandas`, `pandas`
- **Functions**:
  - Detect overlaps, gaps, invalid polygons.
  - Flag inconsistent units, projections.

### 8. `project_initializer.py`
- **Purpose**: Bootstraps a new EIA project directory structure and config file.
- **Key Tools**: `os`, `yaml`
- **Functions**:
  - Create folders for each module.
  - Generate template config files.

### 9. `report_generator.py`
- **Purpose**: Assembles final outputs (maps, emissions, analysis) into a printable or web-readable report.
- **Key Tools**: `jinja2`, `pdfkit`, `matplotlib`
- **Functions**:
  - Injects maps and statistics into a styled HTML/PDF report.

### 10. `ui_handler.py`
- **Purpose**: Manages backend API calls from the front-end tool or web interface.
- **Key Tools**: `FastAPI` or `Flask`
- **Functions**:
  - Expose RESTful endpoints for map interaction, report download, emissions queries.

---

## 🧠 Optional AI Modules (Planned for Expansion)

### `nlp_preprocessor.py`
- Parses EIA regulations or documents to auto-tag requirements using NLP.

### `ml_predictor.py`
- Predicts environmental outcomes or suitability scores using ML algorithms.

---

## 📁 Suggested Folder Structure

```
aethera/
├── core/
│   ├── gis_handler.py
│   ├── emissions_api.py
│   ├── land_filter.py
│   ├── land_suitability_engine.py
│   ├── api_connector.py
│   ├── data_ingestion.py
│   ├── validator.py
├── utils/
│   ├── project_initializer.py
│   ├── report_generator.py
│   ├── ui_handler.py
├── ai/
│   ├── nlp_preprocessor.py
│   └── ml_predictor.py
├── assets/
├── data/
├── outputs/
└── README.md
```