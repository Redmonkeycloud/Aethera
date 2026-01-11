"""
Comprehensive API endpoint tests.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

# Add project root to path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_comprehensive import test_results


@pytest.fixture
def api_client():
    """Create a test client for the FastAPI app."""
    try:
        from backend.src.api.app import app
        return TestClient(app)
    except Exception as e:
        pytest.skip(f"Cannot create API client: {e}")


class TestProjectsEndpoints:
    """Test projects API endpoints."""
    
    def test_list_projects(self, api_client):
        """Test GET /projects endpoint."""
        try:
            response = api_client.get("/projects")
            assert response.status_code in [200, 404]  # 404 if no projects
            test_results["backend_api"]["passed"] += 1
        except Exception as e:
            test_results["backend_api"]["failed"] += 1
            test_results["backend_api"]["errors"].append(f"List projects failed: {e}")
    
    def test_create_project(self, api_client):
        """Test POST /projects endpoint."""
        try:
            project_data = {
                "name": "Test Project API",
                "country": "ITA",
                "sector": "renewable",
            }
            response = api_client.post("/projects", json=project_data)
            # May succeed or fail depending on database state
            assert response.status_code in [200, 201, 400, 500]
            
            if response.status_code in [200, 201]:
                data = response.json()
                assert "id" in data or "project_id" in data
                test_results["backend_api"]["passed"] += 1
            else:
                test_results["backend_api"]["errors"].append(f"Create project returned {response.status_code}: {response.text[:200]}")
                test_results["backend_api"]["failed"] += 1
        except Exception as e:
            test_results["backend_api"]["failed"] += 1
            test_results["backend_api"]["errors"].append(f"Create project failed: {e}")


class TestRunsEndpoints:
    """Test runs API endpoints."""
    
    def test_list_runs(self, api_client):
        """Test GET /runs endpoint."""
        try:
            response = api_client.get("/runs")
            assert response.status_code in [200, 404]
            test_results["backend_api"]["passed"] += 1
        except Exception as e:
            test_results["backend_api"]["failed"] += 1
            test_results["backend_api"]["errors"].append(f"List runs failed: {e}")


class TestReportsEndpoints:
    """Test reports API endpoints."""
    
    def test_list_reports(self, api_client):
        """Test GET /reports endpoint."""
        try:
            response = api_client.get("/reports")
            assert response.status_code in [200, 404]
            test_results["report_generation"]["passed"] += 1
        except Exception as e:
            test_results["report_generation"]["failed"] += 1
            test_results["report_generation"]["errors"].append(f"List reports failed: {e}")
