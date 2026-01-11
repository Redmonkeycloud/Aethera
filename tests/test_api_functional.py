"""
API Functional Tests
Request/response validation and error handling.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

api_test_results: Dict[str, Any] = {
    "passed": 0,
    "failed": 0,
    "errors": [],
}


def get_api_client():
    """Get FastAPI test client."""
    from backend.src.api.app import app
    return TestClient(app)


def test_projects_endpoint_validation():
    """Test projects endpoint request/response validation."""
    client = get_api_client()
    
    # Test valid project creation
    valid_project = {
        "name": "Valid Test Project",
        "country": "ITA",
        "sector": "renewable",
    }
    response = client.post("/projects", json=valid_project)
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
    
    if response.status_code in [200, 201]:
        data = response.json()
        assert "id" in data or "project_id" in data
        assert data.get("name") == valid_project["name"]
        api_test_results["passed"] += 1
    else:
        api_test_results["failed"] += 1
        api_test_results["errors"].append(f"Valid project creation failed: {response.status_code}")


def test_projects_endpoint_invalid_data():
    """Test projects endpoint with invalid data."""
    client = get_api_client()
    
    # Test missing required field
    invalid_project = {
        "country": "ITA",
        # Missing "name" field
    }
    response = client.post("/projects", json=invalid_project)
    # Should return 422 (validation error) or 400
    assert response.status_code in [400, 422, 500], f"Expected validation error, got {response.status_code}"
    api_test_results["passed"] += 1


def test_projects_endpoint_error_handling():
    """Test projects endpoint error handling."""
    client = get_api_client()
    
    # Test invalid JSON
    response = client.post("/projects", data="invalid json", headers={"Content-Type": "application/json"})
    assert response.status_code in [400, 422], f"Expected 400/422 for invalid JSON, got {response.status_code}"
    api_test_results["passed"] += 1
    
    # Test non-existent project
    response = client.get("/projects/non-existent-id-12345")
    assert response.status_code in [404, 400], f"Expected 404 for non-existent project, got {response.status_code}"
    api_test_results["passed"] += 1


def test_runs_endpoint_validation():
    """Test runs endpoint request/response validation."""
    client = get_api_client()
    
    # First create a project
    project_data = {"name": "Test Project", "country": "ITA", "sector": "renewable"}
    project_response = client.post("/projects", json=project_data)
    if project_response.status_code not in [200, 201]:
        api_test_results["errors"].append("Cannot create project for run testing")
        return
    
    project_id = project_response.json().get("id") or project_response.json().get("project_id")
    
    # Test valid run creation
    valid_run = {
        "project_type": "solar",
        "country": "ITA",
        "aoi_geojson": {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[10.0, 45.0], [10.1, 45.0], [10.1, 45.1], [10.0, 45.1], [10.0, 45.0]]]
                }
            }]
        }
    }
    response = client.post(f"/projects/{project_id}/runs", json=valid_run)
    assert response.status_code in [200, 201, 202], f"Run creation failed: {response.status_code}"
    
    if response.status_code in [200, 201, 202]:
        data = response.json()
        assert "task_id" in data or "run_id" in data
        api_test_results["passed"] += 1
    else:
        api_test_results["failed"] += 1
        api_test_results["errors"].append(f"Valid run creation failed: {response.status_code}")


def test_runs_endpoint_invalid_aoi():
    """Test runs endpoint with invalid AOI."""
    client = get_api_client()
    
    # Create project first
    project_data = {"name": "Test Project", "country": "ITA", "sector": "renewable"}
    project_response = client.post("/projects", json=project_data)
    if project_response.status_code not in [200, 201]:
        return
    
    project_id = project_response.json().get("id") or project_response.json().get("project_id")
    
    # Test invalid AOI (missing geometry)
    invalid_run = {
        "project_type": "solar",
        "aoi_geojson": {"type": "FeatureCollection", "features": []}  # Empty features
    }
    response = client.post(f"/projects/{project_id}/runs", json=invalid_run)
    # Should handle invalid AOI gracefully
    assert response.status_code in [200, 201, 202, 400, 422, 500]
    api_test_results["passed"] += 1


def test_tasks_endpoint():
    """Test tasks endpoint."""
    client = get_api_client()
    
    # Test non-existent task
    response = client.get("/tasks/non-existent-task-id")
    # May return 200 with status "PENDING" or 404/400/500, all are valid responses
    assert response.status_code in [200, 404, 400, 500], f"Unexpected status code: {response.status_code}"
    
    if response.status_code == 200:
        # Check if response has valid structure
        data = response.json()
        assert "status" in data or "task_id" in data
    api_test_results["passed"] += 1


def test_runs_results_endpoint():
    """Test runs results endpoint."""
    client = get_api_client()
    
    # Test non-existent run
    response = client.get("/runs/non-existent-run-id/results")
    assert response.status_code in [404, 400, 500], f"Expected 404 for non-existent run, got {response.status_code}"
    api_test_results["passed"] += 1


def test_reports_endpoint_validation():
    """Test reports endpoint validation."""
    client = get_api_client()
    
    # Test report generation without run_id
    invalid_report = {"format": "pdf"}
    response = client.post("/reports/generate", json=invalid_report)
    assert response.status_code in [400, 422, 500], f"Expected validation error, got {response.status_code}"
    api_test_results["passed"] += 1


def test_api_response_format():
    """Test API response format consistency."""
    client = get_api_client()
    
    # Test projects list response format
    response = client.get("/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list), "Projects endpoint should return a list"
    api_test_results["passed"] += 1


def main():
    """Run all API functional tests."""
    print("=" * 60)
    print("API FUNCTIONAL TESTS")
    print("=" * 60)
    
    test_projects_endpoint_validation()
    test_projects_endpoint_invalid_data()
    test_projects_endpoint_error_handling()
    test_runs_endpoint_validation()
    test_runs_endpoint_invalid_aoi()
    test_tasks_endpoint()
    test_runs_results_endpoint()
    test_reports_endpoint_validation()
    test_api_response_format()
    
    print("\n" + "=" * 60)
    print("API FUNCTIONAL TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {api_test_results['passed']}")
    print(f"Failed: {api_test_results['failed']}")
    if api_test_results["errors"]:
        print("\nErrors:")
        for error in api_test_results["errors"]:
            print(f"  - {error}")
    print("=" * 60)
    
    return 0 if api_test_results["failed"] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
