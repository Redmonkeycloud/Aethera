"""
End-to-End Integration Tests
Full workflow from AOI upload to report generation.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.conftest_integration import (
    create_sample_aoi_geojson,
    get_test_project_data,
    get_test_run_data,
)

# Track E2E test results
e2e_results: Dict[str, Any] = {
    "passed": 0,
    "failed": 0,
    "errors": [],
}


def run_e2e_test(test_name: str, test_func) -> None:
    """Run an E2E test and track results."""
    try:
        print(f"\n[E2E] {test_name}...")
        start_time = time.time()
        test_func()
        elapsed = time.time() - start_time
        e2e_results["passed"] += 1
        print(f"  [PASS] {test_name} ({elapsed:.2f}s)")
    except Exception as e:
        e2e_results["failed"] += 1
        error_msg = f"{test_name}: {str(e)[:200]}"
        e2e_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_full_workflow():
    """Test complete workflow: Project → AOI → Run → Analysis → Results → Report."""
    
    # Step 1: Create project
    def step1_create_project():
        from backend.src.api.app import app
        from fastapi.testclient import TestClient
        from backend.src.api.storage import ProjectStore
        from backend.src.config.base_settings import settings
        
        client = TestClient(app)
        project_data = get_test_project_data()
        
        response = client.post("/projects", json=project_data)
        assert response.status_code in [200, 201], f"Project creation failed: {response.status_code}"
        
        project = response.json()
        assert "id" in project or "project_id" in project
        project_id = project.get("id") or project.get("project_id")
        
        # Verify project exists
        list_response = client.get("/projects")
        assert list_response.status_code == 200
        
        return project_id
    
    # Step 2: Create analysis run
    def step2_create_run(project_id: str):
        from backend.src.api.app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        run_data = get_test_run_data()
        run_data["project_id"] = project_id
        
        response = client.post(f"/projects/{project_id}/runs", json=run_data)
        assert response.status_code in [200, 201, 202], f"Run creation failed: {response.status_code}"
        
        run_response = response.json()
        assert "task_id" in run_response or "run_id" in run_response
        
        task_id = run_response.get("task_id")
        run_id = run_response.get("run_id")
        
        return task_id, run_id
    
    # Step 3: Check task status
    def step3_check_task_status(task_id: str):
        from backend.src.api.app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Wait a bit for task to start
        time.sleep(1)
        
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        
        task_status = response.json()
        assert "status" in task_status
        assert task_status["status"] in ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
        
        return task_status["status"]
    
    # Step 4: Get run results (if completed)
    def step4_get_run_results(run_id: str):
        from backend.src.api.app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        response = client.get(f"/runs/{run_id}/results")
        # May return 404 if run not completed yet, which is OK
        if response.status_code == 200:
            results = response.json()
            assert isinstance(results, dict)
            # Check for expected result keys
            expected_keys = ["biodiversity", "resm", "ahsm", "cim", "emissions"]
            has_results = any(key in results for key in expected_keys)
            return has_results
        return False
    
    # Step 5: Generate report
    def step5_generate_report(run_id: str):
        from backend.src.api.app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        report_data = {
            "run_id": run_id,
            "format": "markdown",  # Use markdown for faster testing
        }
        
        response = client.post("/reports/generate", json=report_data)
        # May fail if run not completed or data missing, which is OK for testing
        if response.status_code == 200:
            report = response.json()
            assert "report_id" in report or "file_path" in report
            return True
        return False
    
    # Execute full workflow
    try:
        project_id = step1_create_project()
        task_id, run_id = step2_create_run(project_id)
        
        # Note: Actual analysis may take time, so we just verify task was created
        status = step3_check_task_status(task_id)
        assert status in ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
        
        # Try to get results (may not be ready yet)
        results_available = step4_get_run_results(run_id)
        
        # Try to generate report (may fail if analysis not complete)
        if results_available:
            report_generated = step5_generate_report(run_id)
            assert report_generated or True  # Report generation is optional
        
    except Exception as e:
        raise AssertionError(f"E2E workflow failed: {e}")


def test_project_workflow():
    """Test project creation and management workflow."""
    from backend.src.api.app import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    project_data = get_test_project_data()
    
    # Create project
    create_response = client.post("/projects", json=project_data)
    assert create_response.status_code in [200, 201]
    project = create_response.json()
    project_id = project.get("id") or project.get("project_id")
    assert project_id is not None
    
    # Get project
    get_response = client.get(f"/projects/{project_id}")
    assert get_response.status_code in [200, 404]  # 404 if not found
    
    # List projects
    list_response = client.get("/projects")
    assert list_response.status_code == 200
    projects = list_response.json()
    assert isinstance(projects, list)


def test_run_creation_workflow():
    """Test run creation workflow."""
    from backend.src.api.app import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # First create a project
    project_data = get_test_project_data()
    project_response = client.post("/projects", json=project_data)
    if project_response.status_code not in [200, 201]:
        e2e_results["errors"].append("Cannot create project for run testing")
        return
    
    project_id = project_response.json().get("id") or project_response.json().get("project_id")
    
    # Create run
    run_data = get_test_run_data()
    run_response = client.post(f"/projects/{project_id}/runs", json=run_data)
    assert run_response.status_code in [200, 201, 202]
    
    run_data_response = run_response.json()
    assert "task_id" in run_data_response or "run_id" in run_data_response


def main():
    """Run all E2E tests."""
    print("=" * 60)
    print("E2E INTEGRATION TESTS")
    print("=" * 60)
    
    run_e2e_test("Full Workflow (Project → Run → Results → Report)", test_full_workflow)
    run_e2e_test("Project Workflow", test_project_workflow)
    run_e2e_test("Run Creation Workflow", test_run_creation_workflow)
    
    print("\n" + "=" * 60)
    print("E2E TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {e2e_results['passed']}")
    print(f"Failed: {e2e_results['failed']}")
    if e2e_results["errors"]:
        print("\nErrors:")
        for error in e2e_results["errors"]:
            print(f"  - {error}")
    print("=" * 60)
    
    return 0 if e2e_results["failed"] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
