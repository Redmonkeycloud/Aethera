## AETHERA 2.0

AETHERA is an AI-assisted Environmental Impact Assessment (EIA) copilot. It ingests project geometries and metadata, automates geospatial screening, applies legal rules, quantifies emissions, and drafts report-ready outputs so consultants can focus on expert judgement instead of manual GIS work.

### Vision
- Automate the data–analysis–reporting chain for EIAs.
- Encode geospatial, AI/ML (including mandatory biodiversity intelligence), emissions, and legal logic in a reproducible pipeline.
- Deliver 60–80% of the technical content now—with infrastructure already in place to reach and exceed 80% report readiness as the system learns from past submissions.

### System Layers
1. **Data & Ingestion** – manages AOI input, datasets (CORINE, GADM, Natura, hazards, socio-economic), caching, and provenance.
2. **Geospatial Processing Engine** – validates AOIs, clips base layers, performs overlays, distance/buffer analysis, and zonal statistics.
3. **AI/ML Engine** – RESM (suitability), AHSM (hazard), CIM (cumulative/biodiversity) pipelines with configuration-driven training/inference.
4. **Legal Rules Engine** – applies country-specific YAML/JSON logic for thresholds, buffers, and compliance statements.
5. **Emissions & Indicators Engine** – computes baseline and project-induced emissions, fragmentation metrics, and environmental KPIs.
6. **Application Backend** – orchestrates project runs, exposes an API (FastAPI) for async jobs, stores outputs, and records logs/manifests.
7. **Web Frontend** – interactive map/UI (TypeScript + React + MapLibre) for scenario setup, results exploration, and downloads.
8. **Logging & Monitoring** – structured logs, run manifests, telemetry, and performance metrics for reproducibility.

### Proposed Tech Stack
| Layer | Primary Language | Supporting Tech |
| --- | --- | --- |
| Geospatial + Backend | **Python 3.11+** | FastAPI, Pydantic, GeoPandas, Rasterio, Shapely, Pyogrio, PostGIS (via SQLAlchemy), Celery/RQ, GDAL |
| AI/ML (Suitability/Hazard/CIM/Biodiversity) | **Python** | PyTorch/Lightning, XGBoost, LightGBM, scikit-learn, Dask/Modin (scalability), MLflow/Weights&Biases, ensemble orchestrators |
| Rules Engine | **Python** | JSON/YAML configs, jsonlogic or simple DSL parser |
| Frontend | **TypeScript** | React, Vite, MapLibre/Deck.GL, Tailwind, Zustand/Redux Toolkit |
| Data Services | SQL | PostgreSQL + PostGIS + pgvector, Redis (task queue/cache), MinIO/S3 for rasters & reports |
| Reporting & Memory | Python + Node | Jinja2 templates for Markdown/Docx, pgvector/FAISS for report retrieval, optional Node/Playwright for PDF |

Python remains the core backend language. TypeScript powers the web client, while SQL handles persistence. Optional Go or Rust microservices could appear later for heavy raster tiling, but are not required for the initial build.

### Repository Layout (initial scaffold)
```
AETHERA_2.0/
├── README.md
├── docs/
│   ├── system_overview.md
│   └── implementation_plan.md
├── backend/
│   ├── pyproject.toml
│   └── src/
│       ├── __init__.py
│       ├── main_controller.py
│       ├── logging_utils.py
│       ├── config/
│       │   ├── base_settings.py
│       │   └── emission_factors.yaml
│       ├── api/
│       │   ├── app.py
│       │   ├── models.py
│       │   ├── storage.py
│       │   └── routes/
│       │       ├── biodiversity.py
│       │       ├── projects.py
│       │       └── runs.py
│       ├── analysis/
│       ├── datasets/
│       │   ├── catalog.py
│       │   └── biodiversity_sources.py
│       ├── emissions/
│       ├── db/
│       │   ├── schema.sql
│       │   ├── init_db.py
│       │   └── model_runs.py
│       ├── reporting/   # report templates + learning memory
│       └── utils/
├── ai/
│   ├── __init__.py
│   ├── config/
│   │   ├── resm_config.yaml
│   │   ├── ahsm_config.yaml
│   │   ├── cim_config.yaml
│   │   └── biodiversity_config.yaml
│   ├── models/
│   │   ├── __init__.py
│   │   ├── resm.py
│   │   ├── ahsm.py
│   │   ├── cim.py
│   │   └── biodiversity.py
│   ├── training/
│   │   └── train_resm.py
│   └── utils/
│       └── logging_utils.py
├── data/
│   ├── raw/      # downloaded datasets
│   └── processed/
└── frontend/
    └── README.md
```

Only placeholder files are committed so far; each component will be expanded iteratively. The backend already anticipates report-learning storage (history tables + embeddings) even though no past reports exist yet.

### Getting Started
1. **Python environment**
   ```
   cd backend
   uv venv .venv && .venv/Scripts/activate
   uv pip install -e .
   ```
2. **Run CLI scaffold**
   ```
   python -m src.main_controller --help
   ```
3. **Database (Docker)**
   ```
   docker compose up -d db
   python -m backend.src.db.init_db --dsn postgresql://aethera:aethera@localhost:55432/aethera
   ```
   Requires Docker Desktop + image build from `docker/postgres/Dockerfile` (PostGIS + pgvector). Update `.env` or `env.example` as needed.
4. **Training data + external sources**
   ```
   python scripts/fetch_external_biodiversity_sources.py
   python scripts/build_biodiversity_training.py --samples 150
   ```
   The first command fetches OWID and GBIF datasets into `data2/biodiversity/external/`. The second command generates `data2/biodiversity/training.csv` derived from Natura 2000 + CORINE intersections.
5. **Start Services (API, Celery, Redis)**
   
   **Option 1: Using Make (recommended)**
   ```bash
   # Start all services
   make start
   
   # Or start in background
   make start-background
   
   # Check service status
   make check
   
   # Stop all services
   make stop
   ```
   
   **Option 2: Using scripts**
   ```bash
   # Windows (PowerShell)
   .\scripts\start_services.ps1
   
   # Linux/Mac
   bash scripts/start_services.sh
   ```
   
   **Option 3: Manual start**
   ```bash
   # Terminal 1: Start Redis
   redis-server
   
   # Terminal 2: Start Celery worker
   celery -A backend.src.workers.celery_app worker --loglevel=info
   
   # Terminal 3: Start FastAPI server
   uvicorn backend.src.api.app:app --reload
   ```
   
   Once services are running:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Redis: localhost:6379
   
   **API Endpoints:**
   - `POST /projects` – create a project record
   - `GET /projects` – list projects
   - `POST /projects/{id}/runs` – trigger async analysis run
   - `GET /runs` – list completed runs
   - `GET /runs/{run_id}` – get run details
   - `GET /runs/{run_id}/results` – comprehensive results
   - `GET /runs/{run_id}/legal` – legal compliance results
   - `GET /runs/{run_id}/export` – download run package (ZIP)
   - `GET /tasks/{task_id}` – task status polling
6. **Frontend (later)**
   ```
   cd frontend
   pnpm install
   pnpm dev
   ```

### Next Steps
- Flesh out `main_controller` orchestration (dataset download, AOI validation, CORINE clipping).
- Implement GIS utilities (tiling, buffering, zonal stats).
- Stand up FastAPI service with project/run endpoints and Celery workers.
- Build RESM/AHSM/CIM training + inference scripts using the YAML configs.
- ✅ Legal Rules Engine implemented with YAML/JSON format, parser/evaluator, and compliance status generation
- ✅ Legal rules implemented for 4 countries (DEU, FRA, ITA, GRC) with comprehensive source documentation
- ✅ Legal determinations integrated with backend orchestrator
- Create the frontend map UI and data panels once backend APIs stabilize.

### Biodiversity Training Data
Place any curated biodiversity training dataset (CSV/Parquet) under `data2/biodiversity/`. `scripts/build_biodiversity_training.py` already generates `training.csv` from Natura 2000 and CORINE overlays (official EU datasets). The controller automatically discovers files such as `training.csv` or `training.parquet`, uses them for model ensembles, and logs the dataset source in the `model_runs` table. If no dataset is found, it falls back to synthetic samples so the pipeline can still operate.

Additional vetted internet sources can be downloaded with `scripts/fetch_external_biodiversity_sources.py`, which currently pulls:
- Our World in Data – *Biodiversity habitat loss (Williams et al. 2021)* (`data2/biodiversity/external/owid_biodiversity_habitat_loss.csv`).
- GBIF occurrence samples for Italian raptors (`data2/biodiversity/external/gbif_occurrences_italy_raptors.csv`).

### Legal Rules Engine

The Legal Rules Engine evaluates project metrics against country-specific EIA regulations and compliance requirements. Rules are defined in YAML format and cover:

- **EIA Thresholds**: Mandatory EIA requirements based on project capacity, area, and type
- **Biodiversity & Protected Areas**: Natura 2000 site protection, buffer zones, forest protection
- **Water Protection**: Water body proximity, wetland protection
- **Emissions & Climate**: GHG emissions thresholds, climate impact assessment
- **Land Use**: Agricultural land conversion, natural habitat protection
- **Cumulative Impact**: Multi-factor impact assessment requirements

**Available Countries**: Germany (DEU), France (FRA), Italy (ITA), Greece (GRC)

**Usage**:
```bash
python -m backend.src.main_controller \
  --aoi test_aoi.geojson \
  --project-type solar \
  --country DEU
```

Legal evaluation results are saved to `legal_evaluation.json` and included in the run manifest. See `docs/LEGAL_RULES_ENGINE.md` for detailed documentation and `docs/LEGAL_RULES_SOURCES.md` for comprehensive source bibliography.

See `docs/` for detailed architecture and implementation plans.

