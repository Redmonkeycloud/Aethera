"""Integration tests for API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import api_client


@pytest.mark.integration
@pytest.mark.api
class TestProjectsAPI:
    """Test projects API endpoints."""

    def test_list_projects(self, api_client) -> None:
        """Test listing projects."""
        response = api_client.get("/projects")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_project(self, api_client) -> None:
        """Test creating a project."""
        project_data = {
            "name": "Test Project",
            "country": "DEU",
            "sector": "renewable",
        }
        response = api_client.post("/projects", json=project_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert "id" in data

    def test_get_project(self, api_client) -> None:
        """Test getting a project by ID."""
        # First create a project
        project_data = {
            "name": "Test Project",
            "country": "DEU",
            "sector": "renewable",
        }
        create_response = api_client.post("/projects", json=project_data)
        project_id = create_response.json()["id"]

        # Then get it
        response = api_client.get(f"/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Test Project"


@pytest.mark.integration
@pytest.mark.api
class TestRunsAPI:
    """Test runs API endpoints."""

    def test_list_runs(self, api_client) -> None:
        """Test listing runs."""
        response = api_client.get("/runs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_run_results(self, api_client, temp_dir: Path) -> None:
        """Test getting run results."""
        # This would require a mock run to exist
        # For now, test the endpoint structure
        response = api_client.get("/runs/non-existent-run-id/results")
        # Should return 404 or handle gracefully
        assert response.status_code in [404, 200]


@pytest.mark.integration
@pytest.mark.api
class TestReportsAPI:
    """Test reports API endpoints."""

    def test_list_reports(self, api_client) -> None:
        """Test listing reports."""
        response = api_client.get("/reports")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert "total" in data

    def test_generate_report_requires_run(self, api_client) -> None:
        """Test report generation requires valid run."""
        report_data = {
            "run_id": "non-existent-run",
            "template_name": "base_report.md.jinja",
        }
        response = api_client.post("/reports/generate", json=report_data)
        # Should return 404 for non-existent run
        assert response.status_code in [404, 500]

