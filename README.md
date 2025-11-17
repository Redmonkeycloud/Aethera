## AETHERA 2.0

AETHERA is an AI-assisted Environmental Impact Assessment (EIA) copilot. It ingests project geometries and metadata, automates geospatial screening, applies legal rules, quantifies emissions, and drafts report-ready outputs so consultants can focus on expert judgement instead of manual GIS work.

### Vision
- Automate the data–analysis–reporting chain for EIAs.
- Encode geospatial, AI/ML (including mandatory biodiversity intelligence), emissions, and legal logic in a reproducible pipeline.
- Deliver 60–80% of the technical content now—with infrastructure already in place to reach and exceed 80% report readiness as the system learns from past submissions.

### System Layers
1. **Data & Ingestion** – manages AOI input, datasets (CORINE, GADM, Natura, hazards, socio-economic), caching, and provenance.
2. **Geospatial Processing Engine** – validates AOIs, clips base layers, performs overlays, distance/buffer analysis, and zonal statistics.
3. **AI/ML Engine** – ✅ **FULLY IMPLEMENTED**: RESM (renewable suitability), AHSM (hazard susceptibility), CIM (cumulative impact), and Biodiversity AI (mandatory) with ensemble ML models and configuration-driven training/inference.
4. **Legal Rules Engine** – applies country-specific YAML/JSON logic for thresholds, buffers, and compliance statements.
5. **Emissions & Indicators Engine** – ✅ **FULLY IMPLEMENTED**: computes baseline and project-induced emissions, distance-to-receptor calculations, fragmentation metrics, and 20+ scientifically-accurate environmental KPIs.
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

#### Quick Setup (Automated)

**Linux/macOS:**
```bash
chmod +x scripts/setup_dev_env.sh
./scripts/setup_dev_env.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup_dev_env.ps1
```

#### Manual Setup

1. **Python environment**
   ```bash
   # Using venv
   python3.11 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   
   # Or using uv (faster)
   cd backend
   uv venv .venv && source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

2. **Install pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **Database (Docker)**
   ```bash
   docker compose up -d
   cd backend
   python -m src.db.init_db
   ```
   Requires Docker Desktop + image build from `docker/postgres/Dockerfile` (PostGIS + pgvector). Update `.env` or `env.example` as needed.

4. **Training data + external sources**
   ```bash
   python scripts/fetch_external_biodiversity_sources.py
   python scripts/build_biodiversity_training.py --samples 150
   ```
   The first command fetches OWID and GBIF datasets into `data2/biodiversity/external/`. The second command generates `data2/biodiversity/training.csv` derived from Natura 2000 + CORINE intersections.

5. **API preview**
   ```bash
   cd backend
   uvicorn src.api.app:app --reload
   ```
   - `POST /projects` – create a project record (stored in `data/projects.json`).
   - `GET /projects` – list projects.
   - `GET /runs` – list completed runs via `manifest.json` files.
   - `GET /runs/{run_id}/biodiversity/{layer}` – download GeoJSON layers (`sensitivity`, `natura`, `overlap`) for map rendering.
   - `GET /runs/{run_id}/indicators/receptor-distances` – get distance-to-receptor analysis.
   - `GET /runs/{run_id}/indicators/kpis` – get comprehensive environmental KPIs.
   - `GET /runs/{run_id}/indicators/resm` – get RESM (renewable suitability) predictions.
   - `GET /runs/{run_id}/indicators/ahsm` – get AHSM (hazard susceptibility) predictions.
   - `GET /runs/{run_id}/indicators/cim` – get CIM (cumulative impact) predictions.
   - `GET /cache/stats` – get dataset cache statistics.
   - `POST /cache/clear` – clear the dataset cache.

6. **Frontend (later)**
   ```bash
   cd frontend
   pnpm install
   pnpm dev
   ```

#### Using Make (Linux/macOS)

For convenience, use the Makefile:

```bash
make install-dev    # Install development dependencies
make docker-up      # Start Docker services
make db-init        # Initialize database
make test           # Run tests
make lint           # Run linting
make format         # Format code
```

See `DEVELOPMENT.md` for detailed development guide.

### Current Status

**✅ Completed Phases:**
- **Phase 0 (Foundation & Infrastructure)**: CI/CD pipeline, development environment standardization
- **Phase 1 (Core Geospatial Pipeline)**: WKT support, comprehensive dataset caching mechanism
- **Phase 2 (Emissions & Indicators)**: Distance-to-receptor calculations, advanced environmental KPIs (20+ indicators)
- **Phase 3 (AI/ML Models)**: RESM, AHSM, CIM, and Biodiversity AI fully implemented with ensemble ML approaches, training pipelines, and MLflow/W&B integration

**🚧 In Progress:**
- Legal Rules Engine (Phase 4)
- Async processing with Celery (Phase 5)
- Report generation integration (Phase 7)

### Training Models

Train individual models or all models at once:

```bash
# Train individual model
python -m ai.training.train_biodiversity --training-data data2/biodiversity/training.csv

# Train all models
python -m ai.training.train_all --training-data-dir data2

# With MLflow tracking (default)
python -m ai.training.train_biodiversity --training-data data2/biodiversity/training.csv

# With Weights & Biases
python -m ai.training.train_biodiversity --wandb --training-data data2/biodiversity/training.csv
```

See `docs/MLFLOW_WANDB_SETUP.md` for detailed setup instructions.

### Next Steps
- Design and implement the legal rules DSL and prototype a single-country ruleset.
- Stand up Celery workers for async processing.
- Wire report generation into the main pipeline.
- Create the modern frontend map UI (React + MapLibre) with AOI upload/drawing.

### AI/ML Models

All models support external training data with synthetic fallback:

- **Biodiversity AI** (mandatory): Ensemble classification (Logistic Regression, Random Forest, Gradient Boosting)
- **RESM** (Renewable/Resilience Suitability): Ensemble regression (Ridge, Random Forest, Gradient Boosting) - scores 0-100
- **AHSM** (Asset Hazard Susceptibility): Ensemble classification for multi-hazard risk assessment (flood, wildfire, landslide)
- **CIM** (Cumulative Impact Model): Integrates all other models and environmental KPIs for comprehensive impact assessment

Place training datasets (CSV/Parquet) under `data2/biodiversity/`, `data2/resm/`, `data2/ahsm/`, or `data2/cim/`. The controller automatically discovers these files, uses them for model ensembles, and logs the dataset source in the `model_runs` table. If no dataset is found, models fall back to synthetic samples so the pipeline can still operate.

### Biodiversity Training Data
`scripts/build_biodiversity_training.py` generates `training.csv` from Natura 2000 and CORINE overlays (official EU datasets).

Additional vetted internet sources can be downloaded with `scripts/fetch_external_biodiversity_sources.py`, which currently pulls:
- Our World in Data – *Biodiversity habitat loss (Williams et al. 2021)* (`data2/biodiversity/external/owid_biodiversity_habitat_loss.csv`).
- GBIF occurrence samples for Italian raptors (`data2/biodiversity/external/gbif_occurrences_italy_raptors.csv`).

See `docs/` for detailed architecture and implementation plans.

