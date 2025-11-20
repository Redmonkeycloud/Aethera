# AETHERA Backend Tests

This directory contains the comprehensive test suite for the AETHERA backend.

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/                # Unit tests (fast, isolated)
│   ├── test_geometry.py
│   ├── test_emissions.py
│   ├── test_reporting.py
│   ├── test_legal_rules.py
│   ├── test_storage.py
│   ├── test_reporting_memory.py
│   └── test_api_models.py
└── integration/         # Integration tests (slower, require services)
    ├── test_api.py
    ├── test_pipeline.py
    ├── test_database.py
    └── test_celery.py
```

## Running Tests

### All Tests
```bash
pytest
```

### Unit Tests Only
```bash
pytest tests/unit -v
```

### Integration Tests Only
```bash
pytest tests/integration -v
```

### With Coverage
```bash
pytest --cov=src --cov-report=html
```

### Specific Test Categories
```bash
# API tests
pytest -m api

# Database tests
pytest -m database

# Geospatial tests
pytest -m geospatial

# Hypothesis property-based tests
pytest -m hypothesis
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (require services)
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.geospatial` - Tests requiring geospatial libraries
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.database` - Tests requiring database
- `@pytest.mark.celery` - Tests requiring Celery/Redis
- `@pytest.mark.hypothesis` - Property-based tests

## Property-Based Testing

We use Hypothesis for property-based testing. These tests generate random inputs and verify properties hold:

```python
@given(
    lon=st.floats(min_value=-180, max_value=180),
    lat=st.floats(min_value=-90, max_value=90),
)
def test_load_aoi_point_property_based(lon: float, lat: float) -> None:
    """Property-based test for point loading."""
    wkt = f"POINT({lon} {lat})"
    gdf = load_aoi(wkt, "EPSG:4326")
    # Verify properties...
```

## Test Fixtures

Common fixtures available in `conftest.py`:

- `test_data_dir` - Temporary directory for test data
- `test_db_dsn` - Test database connection string
- `db_client` - Database client instance
- `api_client` - FastAPI test client
- `temp_dir` - Temporary directory for test files
- `reset_settings` - Reset settings between tests

## Coverage Goals

- Target: 70%+ overall coverage
- Critical paths: 90%+ coverage
- New code: 80%+ coverage required

## CI/CD

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Coverage reports uploaded to Codecov

