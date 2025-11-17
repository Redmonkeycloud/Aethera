## Migration Notes (November 2025)

This repository was refreshed with the new `AETHERA_2.0` scaffold. The previous prototype (directories such as `core/`, `ai/`, `utils/`, legacy README, etc.) has been archived so that future contributors can still reference the original ideas.

### What Changed
- Replaced the codebase with the layered architecture under `backend/`, `ai/`, `frontend/`, `docs/`, and `scripts/`.
- Added Docker/PostGIS/pgvector infrastructure (`docker-compose.yml`, `docker/postgres/Dockerfile`) and updated configuration defaults (`env.example`, `backend/src/config/base_settings.py`).
- Introduced the new FastAPI surface (`backend/src/api/…`), run manifests, reporting scaffold, biodiversity ensemble logic, and curated data scripts.
- Archived key legacy documents under `docs/legacy/`:
  - `Backend_Architecture_Guide.md`
  - `README_original.md`
  - `requirements_original.txt`

### Bringing Legacy Context Forward
- If you need to reference the original backend vision or dependency lists, start with the files in `docs/legacy/`.
- Any unique snippets from the previous `core/` and `ai/` directories can be recovered from Git history (`git show <old-commit> -- core/...`).

### Contributions Going Forward
- Use the `backend/pyproject.toml` environment (`uv pip install -e .`) instead of the old `requirements.txt`.
- Run `docker compose up -d db` and `python -m backend.src.db.init_db` to initialize Postgres/PostGIS/pgvector before logging model runs.
- Biodiversity training data lives under `data2/biodiversity/`; regenerate with:
  ```
  python scripts/fetch_external_biodiversity_sources.py
  python scripts/build_biodiversity_training.py --samples 150
  ```

This file should be updated if we perform another major restructuring so contributors always know where to look for historical context.***

