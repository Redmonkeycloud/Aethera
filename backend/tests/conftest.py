"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.config.base_settings import settings
from src.db.client import DatabaseClient


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp(prefix="aethera_test_")
    return Path(temp_dir)


@pytest.fixture(scope="session")
def test_db_dsn() -> str:
    """Get test database DSN from environment or use default."""
    return os.getenv("TEST_POSTGRES_DSN", "postgresql://aethera:aethera@localhost:55432/aethera_test")


@pytest.fixture(scope="function")
def db_client(test_db_dsn: str) -> Generator[DatabaseClient, None, None]:
    """Create a database client for testing."""
    client = DatabaseClient(test_db_dsn)
    yield client
    # Cleanup if needed


@pytest.fixture(scope="function")
def api_client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function", autouse=True)
def reset_settings() -> Generator[None, None, None]:
    """Reset settings to defaults before each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)

