"""
Frontend Rendering Tests
Streamlit component tests and UI verification.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

frontend_test_results: Dict[str, Any] = {
    "passed": 0,
    "failed": 0,
    "errors": [],
}


def test_frontend_pages_exist():
    """Test that all Streamlit pages exist."""
    try:
        pages_dir = PROJECT_ROOT / "frontend" / "pages"
        expected_pages = [
            "1_🏠_Home.py",
            "2_➕_New_Project.py",
            "3_📊_Project.py",
            "4_📈_Run.py",
        ]
        
        missing = []
        for page in expected_pages:
            if not (pages_dir / page).exists():
                missing.append(page)
        
        assert len(missing) == 0, f"Missing frontend pages: {missing}"
        frontend_test_results["passed"] += 1
        print("  [PASS] All Streamlit pages exist")
        
    except Exception as e:
        frontend_test_results["failed"] += 1
        error_msg = f"Frontend pages check failed: {str(e)[:200]}"
        frontend_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_frontend_api_client_import():
    """Test that frontend API client can be imported."""
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "frontend"))
        from src.api_client import ProjectsAPI, RunsAPI, TasksAPI
        
        assert ProjectsAPI is not None
        assert RunsAPI is not None
        assert TasksAPI is not None
        
        frontend_test_results["passed"] += 1
        print("  [PASS] Frontend API client imports successfully")
        
    except Exception as e:
        frontend_test_results["failed"] += 1
        error_msg = f"Frontend API client import failed: {str(e)[:200]}"
        frontend_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_frontend_api_client_initialization():
    """Test that frontend API client can be initialized."""
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "frontend"))
        from src.api_client import ProjectsAPI, RunsAPI, TasksAPI
        
        # Test initialization
        projects_api = ProjectsAPI()
        runs_api = RunsAPI()
        tasks_api = TasksAPI()
        
        assert projects_api is not None
        assert runs_api is not None
        assert tasks_api is not None
        
        frontend_test_results["passed"] += 1
        print("  [PASS] Frontend API clients initialize successfully")
        
    except Exception as e:
        frontend_test_results["failed"] += 1
        error_msg = f"Frontend API client initialization failed: {str(e)[:200]}"
        frontend_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_streamlit_app_file():
    """Test that Streamlit app.py exists and is valid."""
    try:
        app_file = PROJECT_ROOT / "frontend" / "app.py"
        assert app_file.exists(), "app.py not found"
        
        # Check if file can be parsed
        with open(app_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "streamlit" in content.lower(), "app.py should import streamlit"
            assert "st." in content or "streamlit" in content, "app.py should use streamlit"
        
        frontend_test_results["passed"] += 1
        print("  [PASS] Streamlit app.py exists and is valid")
        
    except Exception as e:
        frontend_test_results["failed"] += 1
        error_msg = f"Streamlit app.py check failed: {str(e)[:200]}"
        frontend_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_streamlit_page_imports():
    """Test that Streamlit pages can be imported (syntax check)."""
    try:
        pages_dir = PROJECT_ROOT / "frontend" / "pages"
        pages = [
            "1_🏠_Home.py",
            "2_➕_New_Project.py",
            "3_📊_Project.py",
            "4_📈_Run.py",
        ]
        
        for page in pages:
            page_path = pages_dir / page
            if not page_path.exists():
                continue
            
            # Try to compile the file to check syntax
            with open(page_path, "r", encoding="utf-8") as f:
                code = f.read()
                compile(code, str(page_path), "exec")
        
        frontend_test_results["passed"] += 1
        print("  [PASS] All Streamlit pages have valid syntax")
        
    except SyntaxError as e:
        frontend_test_results["failed"] += 1
        error_msg = f"Streamlit page syntax error: {str(e)[:200]}"
        frontend_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")
    except Exception as e:
        frontend_test_results["failed"] += 1
        error_msg = f"Streamlit page import check failed: {str(e)[:200]}"
        frontend_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_frontend_components_exist():
    """Test that frontend components exist."""
    try:
        components_file = PROJECT_ROOT / "frontend" / "src" / "components.py"
        
        # Components file may or may not exist
        if components_file.exists():
            with open(components_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert len(content) > 0, "components.py should not be empty"
        
        frontend_test_results["passed"] += 1
        print("  [PASS] Frontend components check passed")
        
    except Exception as e:
        frontend_test_results["failed"] += 1
        error_msg = f"Frontend components check failed: {str(e)[:200]}"
        frontend_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def main():
    """Run all frontend rendering tests."""
    print("=" * 60)
    print("FRONTEND RENDERING TESTS")
    print("=" * 60)
    print("Note: Full rendering tests require Streamlit server")
    print("=" * 60)
    
    test_frontend_pages_exist()
    test_frontend_api_client_import()
    test_frontend_api_client_initialization()
    test_streamlit_app_file()
    test_streamlit_page_imports()
    test_frontend_components_exist()
    
    print("\n" + "=" * 60)
    print("FRONTEND RENDERING TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {frontend_test_results['passed']}")
    print(f"Failed: {frontend_test_results['failed']}")
    if frontend_test_results["errors"]:
        print("\nErrors:")
        for error in frontend_test_results["errors"][:5]:
            print(f"  - {error}")
    print("=" * 60)
    
    return 0 if frontend_test_results["failed"] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
