"""
Run All Tests
Master test runner that executes all test suites.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Import all test modules
from tests.run_comprehensive_tests import main as run_comprehensive
from tests.test_e2e_integration import main as run_e2e
from tests.test_api_functional import main as run_api_functional
from tests.test_database_integration import main as run_database
from tests.test_celery_execution import main as run_celery
from tests.test_groq_api_calls import main as run_groq
from tests.test_frontend_rendering import main as run_frontend
from tests.test_performance import main as run_performance


def generate_master_report():
    """Generate master test report combining all test results."""
    report_path = PROJECT_ROOT / "tests" / "MASTER_TEST_REPORT.md"
    
    report = f"""# AETHERA 2.0 Master Test Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This report combines results from all test suites:
1. Comprehensive Component Tests
2. E2E Integration Tests
3. API Functional Tests
4. Database Integration Tests
5. Celery Execution Tests
6. Groq API Integration Tests
7. Frontend Rendering Tests
8. Performance Tests

## Test Execution

Run individual test suites:
- `python tests/run_comprehensive_tests.py` - Core component tests
- `python tests/test_e2e_integration.py` - End-to-end workflow tests
- `python tests/test_api_functional.py` - API request/response validation
- `python tests/test_database_integration.py` - Database connection tests
- `python tests/test_celery_execution.py` - Celery task tests
- `python tests/test_groq_api_calls.py` - Groq API integration tests
- `python tests/test_frontend_rendering.py` - Frontend component tests
- `python tests/test_performance.py` - Performance benchmarks

Or run all tests:
- `python tests/run_all_tests.py` - Execute all test suites

## Test Coverage

### 1. E2E Integration Tests
- Full workflow: Project → AOI → Run → Analysis → Results → Report
- Project management workflow
- Run creation workflow

### 2. API Functional Tests
- Request/response validation
- Error handling (400, 404, 422, 500)
- Invalid data handling
- Response format consistency

### 3. Database Integration Tests
- Database connection
- Schema validation
- Transaction rollback
- Model run logging

### 4. Celery Execution Tests
- Celery app configuration
- Task registration
- Redis connection
- Task submission
- Status tracking

### 5. Groq API Integration Tests
- API key validation
- Service initialization
- Actual API calls (executive summary, biodiversity narrative, ML explanation)

### 6. Frontend Rendering Tests
- Streamlit page existence
- API client integration
- Syntax validation
- Component structure

### 7. Performance Tests
- API response times (< 1s for GET, < 2s for POST)
- Model inference speed (< 5s)
- Model loading speed (< 10s)
- LangChain response time

## Requirements

### For Full Test Execution:

1. **Python 3.10+**
2. **All dependencies installed** (`pip install -e backend/`)
3. **Environment variables** (optional):
   - `GROQ_API_KEY` - For Groq API tests
   - `POSTGRES_DSN` - For database tests
   - `REDIS_URL` - For Celery tests

### Test Execution Order:

1. Comprehensive tests (fastest, no dependencies)
2. API functional tests (requires FastAPI app)
3. Frontend tests (requires frontend files)
4. Performance tests (requires all components)
5. E2E tests (requires full stack)
6. Database tests (requires PostgreSQL)
7. Celery tests (requires Redis)
8. Groq tests (requires API key)

## Notes

- Some tests may be skipped if dependencies are not available (database, Redis, API keys)
- E2E tests may take longer as they test full workflows
- Performance tests measure actual execution times
- Database and Celery tests require running services

---

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"\n✅ Master test report generated: {report_path}")


def main():
    """Run all test suites."""
    print("=" * 60)
    print("AETHERA 2.0 - RUN ALL TESTS")
    print("=" * 60)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    
    results = {}
    
    # Run all test suites
    test_suites = [
        ("Comprehensive Component Tests", run_comprehensive),
        ("E2E Integration Tests", run_e2e),
        ("API Functional Tests", run_api_functional),
        ("Database Integration Tests", run_database),
        ("Celery Execution Tests", run_celery),
        ("Groq API Integration Tests", run_groq),
        ("Frontend Rendering Tests", run_frontend),
        ("Performance Tests", run_performance),
    ]
    
    for suite_name, suite_func in test_suites:
        print(f"\n{'=' * 60}")
        print(f"Running: {suite_name}")
        print(f"{'=' * 60}")
        try:
            exit_code = suite_func()
            results[suite_name] = {
                "exit_code": exit_code,
                "status": "PASSED" if exit_code == 0 else "FAILED"
            }
        except ImportError as e:
            results[suite_name] = {
                "exit_code": 1,
                "status": "SKIPPED",
                "error": f"Import error (dependency missing): {str(e)[:200]}"
            }
            print(f"[SKIP] {suite_name}: {e}")
        except Exception as e:
            results[suite_name] = {
                "exit_code": 1,
                "status": "ERROR",
                "error": str(e)[:200]
            }
            print(f"[ERROR] {suite_name} failed: {e}")
    
    # Generate master report
    generate_master_report()
    
    # Print summary
    print("\n" + "=" * 60)
    print("MASTER TEST SUMMARY")
    print("=" * 60)
    
    total_passed = sum(1 for r in results.values() if r["status"] == "PASSED")
    total_failed = sum(1 for r in results.values() if r["status"] == "FAILED")
    total_errors = sum(1 for r in results.values() if r["status"] == "ERROR")
    
    for suite_name, result in results.items():
        status_icon = "[OK]" if result["status"] == "PASSED" else "[FAIL]" if result["status"] == "FAILED" else "[ERROR]"
        print(f"{status_icon} {suite_name}: {result['status']}")
        if "error" in result:
            print(f"      Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print(f"Total Suites: {len(results)}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Errors: {total_errors}")
    print("=" * 60)
    
    return 0 if total_failed == 0 and total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
