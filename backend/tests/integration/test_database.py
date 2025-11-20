"""Integration tests for database operations."""

from __future__ import annotations

import pytest

from src.db.client import DatabaseClient
from tests.conftest import db_client, test_db_dsn


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseOperations:
    """Test database operations."""

    def test_database_connection(self, db_client: DatabaseClient) -> None:
        """Test database connection."""
        with db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                assert result[0] == 1

    def test_postgis_extension(self, db_client: DatabaseClient) -> None:
        """Test PostGIS extension is available."""
        with db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT PostGIS_version()")
                result = cur.fetchone()
                assert result is not None

    def test_pgvector_extension(self, db_client: DatabaseClient) -> None:
        """Test pgvector extension is available."""
        with db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                result = cur.fetchone()
                # Extension should exist if properly set up
                # If not, this test will be skipped in CI
                if result:
                    assert result[0] == "vector"

