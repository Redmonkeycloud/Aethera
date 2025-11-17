## Implementation Plan

### Phase 0 – Foundation (Now)
- [x] Create repository structure, high-level documentation, and configuration placeholders.
- [x] Establish shared development environment (Python 3.11, uv/pip, Node 20, pnpm).
- [x] Set up CI (GitHub Actions) to lint Python (ruff, mypy) and TypeScript (eslint).
- [x] Provision Postgres/PostGIS + pgvector extensions (via Docker compose) and create `reports_history`, `report_embeddings`, and `model_runs` tables.
- [x] Prepare data ingestion scripts: `scripts/fetch_external_biodiversity_sources.py` (OWID + GBIF) and `scripts/build_biodiversity_training.py` (Natura + CORINE derived training set).

### Phase 1 – Core Geospatial Pipeline ✅
**Goals**
- [x] Implement `main_controller` orchestration CLI.
- [x] Build AOI loader/validator supporting shapefile, GeoJSON, **WKT (strings and files)**, and CRS normalization.
- [x] Implement dataset connectors (CORINE, GADM, Natural Earth, Natura) with **comprehensive caching mechanism**.
- [x] Develop clipping, buffering, intersection, and zonal statistics utilities.
- [x] Persist processed layers under `/data/processed/<run_id>/`.

**Python Modules**
- `backend/src/datasets/corine.py`
- `backend/src/utils/geometry.py`
- `backend/src/pipeline/geospatial.py`

### Phase 2 – Emissions & Indicators ✅
**Goals**
- [x] Implement `emissions_api.py` with baseline vs project calculations.
- [x] Define emission factor catalog (YAML/JSON) and override mechanism.
- [x] Add fragmentation metrics, land cover summaries, and **distance-to-receptor calculations**.
- [x] Implement **advanced environmental KPIs** with scientific accuracy (20+ indicators).
- [x] Create comprehensive **bibliography document** cataloging all scientific sources.

### Phase 3 – AI/ML Models
**Goals**
- Finalize config schema for RESM/AHSM/CIM and mandatory Biodiversity AI, each supporting multiple candidate models per run.
- Build data preprocessing pipeline to convert geospatial outputs into training tensors; enable ingestion of real training datasets (e.g., `data2/biodiversity/*.parquet`) and fall back to synthetic samples only when needed.
- Train baseline models using historical/global datasets; log runs via MLflow/W&B and store metrics in `model_runs`.
- Implement inference services that execute all configured models, evaluate projections, and select/blend the best outputs (stacking/ensemble selection) before persisting to run results.

### Phase 4 – Biodiversity AI & Legal Rules Engine
**Goals**
- Deliver the biodiversity pipeline (rule-based overlays + ML predictors) and wire its outputs into CIM, indicators, and report templates.
- Draft DSL/YAML format for country-specific rules (start with one country).
- Build parser/evaluator that consumes project metrics and emits compliance statuses + text snippets.
- Integrate with backend orchestrator to append biodiversity findings and legal determinations to run outputs.

### Phase 5 – Backend API & Orchestration
**Goals**
- Create FastAPI service with endpoints:
  - `POST /projects`
  - `POST /projects/{id}/runs`
  - `GET /runs/{id}`
  - `GET /runs/{id}/results`
- Integrate Celery workers for heavy tasks; store metadata in Postgres/PostGIS.
- Implement storage abstraction for rasters/exports (local filesystem initially, S3-compatible later).

### Phase 6 – Frontend Application
**Goals**
- Bootstrap React + Vite + MapLibre app.
- Build AOI upload/draw tool, scenario form, layer controls, indicator panels, result download area.
- Connect to backend endpoints; manage run status polling and map layers.

### Phase 7 – Reporting, Learning Memory & Automation
**Goals**
- Template-driven draft EIA chapters (Markdown/Docx) using Jinja2 + python-docx; integrate retrieval-augmented generation that pulls similar past sections from `reports_history` and embeddings to reach ≥80% completeness.
- Export tables (CSV/Excel), shapefiles/GeoPackage, and PDF summaries (Playwright or WeasyPrint).
- Add scenario comparison dashboards and versioning.
- Build reviewer feedback ingestion flow so accepted edits automatically feed the memory store for future improvements.

### Cross-Cutting Concerns
- **Testing** – pytest + hypothesis for backend, playwright for frontend.
- **Observability** – structured logging, OpenTelemetry traces, Prometheus metrics.
- **Performance** – tiling/chunking for large AOIs, optional Dask-Geopandas, caching of geospatial joins.
- **Security** – RBAC, OAuth/OpenID Connect integration, audit logs.
- **Model Governance** – track ensemble members, validation metrics, drift detection, and reproducible model versions.

### Staffing & Skills
- Python geospatial engineer(s) for pipelines.
- ML engineer(s) for RESM/AHSM/CIM.
- Backend engineer(s) for API/orchestration.
- Frontend engineer(s) skilled in React + geospatial visualization.
- Domain experts for legal rules and EIA methodology.

### Milestones & Timeline (indicative)
1. **M1 (6 weeks)** – Geospatial pipeline + emissions MVP producing indicators for a single AOI.
2. **M2 (10 weeks)** – RESM/AHSM/CIM inference integrated; legal engine prototype for one jurisdiction.
3. **M3 (14 weeks)** – FastAPI backend + queue + storage + logging ready; CLI/REST trigger end-to-end run.
4. **M4 (20 weeks)** – Frontend MVP, reporting templates, scenario comparison, readiness for pilot users.

This plan balances Python as the dominant backend/analysis language with TypeScript and SQL where appropriate, enabling an incremental path toward the full AETHERA vision.

