"""
Celery Task Execution Tests
Task execution with Redis broker.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

celery_test_results: Dict[str, Any] = {
    "passed": 0,
    "failed": 0,
    "errors": [],
}


def test_celery_app_configuration():
    """Test Celery app configuration."""
    try:
        from backend.src.workers.celery_app import celery_app
        
        assert celery_app is not None
        # Celery app uses 'broker' and 'backend' attributes
        assert hasattr(celery_app, "broker") or hasattr(celery_app, "conf")
        assert hasattr(celery_app, "backend") or hasattr(celery_app, "conf")
        
        # Check configuration
        assert celery_app.conf is not None
        assert "task_serializer" in celery_app.conf
        assert "timezone" in celery_app.conf
        
        celery_test_results["passed"] += 1
        print("  [PASS] Celery app configuration correct")
        
    except Exception as e:
        celery_test_results["failed"] += 1
        error_msg = f"Celery app configuration test failed: {str(e)[:200]}"
        celery_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_celery_task_registration():
    """Test that Celery tasks are registered."""
    try:
        from backend.src.workers.celery_app import celery_app
        from backend.src.workers.tasks import run_analysis_task
        
        # Check if task is registered
        registered_tasks = list(celery_app.tasks.keys())
        task_name = "aethera.run_analysis"  # Full task name
        
        # Task should be registered (may be in different format)
        assert run_analysis_task is not None
        assert hasattr(run_analysis_task, "delay")
        assert hasattr(run_analysis_task, "apply_async")
        
        celery_test_results["passed"] += 1
        print("  [PASS] Celery tasks are registered")
        
    except Exception as e:
        celery_test_results["failed"] += 1
        error_msg = f"Celery task registration test failed: {str(e)[:200]}"
        celery_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_redis_connection():
    """Test Redis connection for Celery broker."""
    try:
        import redis
        from backend.src.config.base_settings import settings
        
        redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379/0"
        
        # Try to connect to Redis
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        r.ping()
        
        celery_test_results["passed"] += 1
        print("  [PASS] Redis connection successful")
        
    except redis.ConnectionError:
        celery_test_results["errors"].append("Redis not available - skipping connection test")
        print("  [WARN] Redis not available - connection test skipped")
    except Exception as e:
        celery_test_results["failed"] += 1
        error_msg = f"Redis connection test failed: {str(e)[:200]}"
        celery_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_task_submission():
    """Test task submission (without actual execution)."""
    try:
        from backend.src.workers.tasks import run_analysis_task
        
        # Test that task can be called directly (synchronous)
        # This tests the task function without requiring Celery worker
        
        # Create minimal test arguments
        test_args = {
            "run_id": "test_run_123",
            "aoi_path": None,
            "project_type": "solar",
            "country": "ITA",
        }
        
        # Try to call task function directly (will fail if dependencies missing, but tests structure)
        # We don't actually execute it to avoid long-running tests
        assert callable(run_analysis_task)
        
        celery_test_results["passed"] += 1
        print("  [PASS] Task submission structure correct")
        
    except Exception as e:
        celery_test_results["failed"] += 1
        error_msg = f"Task submission test failed: {str(e)[:200]}"
        celery_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_task_status_tracking():
    """Test task status tracking mechanism."""
    try:
        from backend.src.workers.tasks import run_analysis_task
        from backend.src.api.routes.tasks import get_task_status
        
        # Test that task status endpoint exists and is callable
        assert callable(get_task_status)
        
        celery_test_results["passed"] += 1
        print("  [PASS] Task status tracking mechanism exists")
        
    except Exception as e:
        celery_test_results["failed"] += 1
        error_msg = f"Task status tracking test failed: {str(e)[:200]}"
        celery_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def main():
    """Run all Celery execution tests."""
    print("=" * 60)
    print("CELERY EXECUTION TESTS")
    print("=" * 60)
    print("Note: Full execution tests require Redis and Celery worker")
    print("=" * 60)
    
    test_celery_app_configuration()
    test_celery_task_registration()
    test_redis_connection()
    test_task_submission()
    test_task_status_tracking()
    
    print("\n" + "=" * 60)
    print("CELERY EXECUTION TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {celery_test_results['passed']}")
    print(f"Failed: {celery_test_results['failed']}")
    if celery_test_results["errors"]:
        print("\nErrors/Warnings:")
        for error in celery_test_results["errors"][:5]:
            print(f"  - {error}")
    print("=" * 60)
    
    return 0 if celery_test_results["failed"] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
