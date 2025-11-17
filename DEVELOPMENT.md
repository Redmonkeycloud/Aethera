# Development Guide

This guide covers setting up and working with the AETHERA development environment.

## Prerequisites

- **Python 3.11+** (use `pyenv` or similar to manage versions)
- **Docker Desktop** (for PostgreSQL/PostGIS database)
- **Git** (for version control)
- **Make** (optional, for convenience commands)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Redmonkeycloud/Aethera.git
cd Aethera
```

### 2. Set Up Python Environment

We recommend using a virtual environment:

**Using `venv` (built-in):**
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Using `pyenv` (recommended for version management):**
```bash
pyenv install 3.11.0
pyenv local 3.11.0
python -m venv .venv
source .venv/bin/activate
```

**Using `uv` (fast Python package installer):**
```bash
cd backend
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

**Production dependencies:**
```bash
cd backend
pip install -e .
```

**Development dependencies (includes testing, linting tools):**
```bash
cd backend
pip install -e ".[dev]"
```

**Or use Make:**
```bash
make install-dev
```

### 4. Set Up Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before commits:

```bash
pip install pre-commit
pre-commit install
```

This will run `ruff`, `mypy`, and other checks automatically on `git commit`.

### 5. Start Docker Services

```bash
docker compose up -d
```

**Or using Make:**
```bash
make docker-up
```

### 6. Initialize Database

```bash
cd backend
python -m src.db.init_db
```

**Or using Make:**
```bash
make db-init
```

### 7. Verify Setup

Run the tests to verify everything is working:

```bash
cd backend
pytest tests/ -v
```

**Or using Make:**
```bash
make test
```

## Development Workflow

### Code Quality Checks

**Linting (ruff):**
```bash
make lint
# Or manually:
cd backend && ruff check src/ ai/ scripts/
```

**Formatting (ruff):**
```bash
make format
# Or manually:
cd backend && ruff format src/ ai/ scripts/
```

**Type Checking (mypy):**
```bash
make type-check
# Or manually:
cd backend && mypy src/ ai/
```

**Run all checks:**
```bash
make check
```

### Running Tests

**Run all tests:**
```bash
make test
# Or manually:
cd backend && pytest tests/ -v
```

**Run tests with coverage:**
```bash
make test-cov
# Or manually:
cd backend && pytest tests/ -v --cov=src --cov-report=html
```

Coverage report will be generated in `backend/htmlcov/index.html`.

### Database Management

**Start database:**
```bash
make docker-up
```

**Stop database:**
```bash
make docker-down
```

**Reset database (stop, start, initialize):**
```bash
make db-reset
```

**Initialize schema only:**
```bash
make db-init
```

### Running the Application

**Start the API server:**
```bash
cd backend
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

**Run the main controller:**
```bash
cd backend
python -m src.main_controller --aoi path/to/aoi.geojson --project-type solar_farm
```

## Project Structure

```
Aethera/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD
├── backend/
│   ├── src/                # Main source code
│   │   ├── api/           # FastAPI routes
│   │   ├── db/            # Database client and schema
│   │   ├── datasets/      # Dataset connectors
│   │   ├── emissions/      # Emissions calculations
│   │   ├── reporting/     # Report generation
│   │   └── utils/         # Utility functions
│   ├── tests/             # Test suite
│   └── pyproject.toml     # Python project config
├── ai/
│   ├── models/            # ML models (RESM, AHSM, CIM, Biodiversity)
│   ├── config/            # Model configurations
│   └── training/          # Training scripts
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── docker/                # Docker configurations
├── .pre-commit-config.yaml # Pre-commit hooks
├── Makefile               # Convenience commands
└── .python-version        # Python version specification
```

## Code Style

### Python

- **Line length:** 100 characters
- **Formatter:** `ruff format`
- **Linter:** `ruff check`
- **Type checker:** `mypy` (non-strict mode)

### Import Organization

Imports should be organized as:
1. Standard library
2. Third-party packages
3. Local application imports

Example:
```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import geopandas as gpd
import pandas as pd

from ..config.base_settings import settings
from ..logging_utils import get_logger
```

### Type Hints

Use type hints for all function signatures and class attributes:

```python
def process_aoi(aoi_path: Path, output_dir: Path) -> gpd.GeoDataFrame:
    """Process an AOI and return clipped data."""
    ...
```

## Git Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```
   
   Pre-commit hooks will run automatically.

3. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **CI will run automatically** on push/PR to `main` or `develop`.

## CI/CD Pipeline

GitHub Actions automatically runs on every push and pull request:

1. **Lint Job:** Runs `ruff` and `mypy`
2. **Test Job:** Runs `pytest` with PostgreSQL service
3. **Docker Build Job:** Builds and tests Docker images

View CI status at: https://github.com/Redmonkeycloud/Aethera/actions

## Environment Variables

Create a `.env` file in the project root (see `env.example`):

```bash
# Database
POSTGRES_DSN=postgresql://aethera:aethera@localhost:55432/aethera

# API
API_HOST=0.0.0.0
API_PORT=8000

# Data paths
DATA_DIR=./data
DATA_SOURCES_DIR=./data2
```

## Troubleshooting

### Python Version Issues

If you see version errors, ensure you're using Python 3.11+:

```bash
python --version  # Should show 3.11.x
```

Use `pyenv` to manage versions:
```bash
pyenv install 3.11.0
pyenv local 3.11.0
```

### GDAL Installation Issues

On Linux/macOS, you may need system GDAL libraries:

**Ubuntu/Debian:**
```bash
sudo apt-get install gdal-bin libgdal-dev python3-gdal
```

**macOS (Homebrew):**
```bash
brew install gdal
```

**Windows:**
GDAL wheels should install automatically via pip.

### Database Connection Issues

Ensure Docker is running:
```bash
docker ps  # Should show postgres container
```

Check database logs:
```bash
docker compose logs db
```

### Pre-commit Hooks Not Running

Reinstall hooks:
```bash
pre-commit uninstall
pre-commit install
```

## Getting Help

- Check existing issues: https://github.com/Redmonkeycloud/Aethera/issues
- Review documentation in `docs/`
- Ask questions in discussions or create an issue

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

Make sure all CI checks pass before requesting review!

