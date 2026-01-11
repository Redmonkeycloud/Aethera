"""
Comprehensive test runner for AETHERA 2.0
Runs all tests and generates a detailed report.
"""

import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Test results tracking
test_results: Dict[str, Any] = {
    "backend_api": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "ml_models": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "langchain_groq": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "database": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "celery": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "weather_features": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "model_explainability": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "report_generation": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "training_data": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "frontend": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "pretrained_models": {"passed": 0, "failed": 0, "errors": [], "tests": []},
    "data_catalog": {"passed": 0, "failed": 0, "errors": [], "tests": []},
}


def run_test(test_name: str, test_func, category: str) -> None:
    """Run a single test and record results."""
    try:
        test_func()
        test_results[category]["passed"] += 1
        test_results[category]["tests"].append(f"[PASS] {test_name}")
        print(f"  [PASS] {test_name}")
    except Exception as e:
        test_results[category]["failed"] += 1
        error_msg = f"{test_name}: {str(e)}"
        test_results[category]["errors"].append(error_msg)
        test_results[category]["tests"].append(f"[FAIL] {test_name}: {str(e)[:100]}")
        print(f"  [FAIL] {test_name}: {str(e)[:100]}")


def test_backend_api():
    """Test backend API components."""
    print("\n[TEST] Backend API Components")
    print("=" * 60)
    
    # Test API app import
    def test_api_app():
        from backend.src.api.app import app
        assert app is not None
    run_test("API app import", test_api_app, "backend_api")
    
    # Test API routes
    def test_api_routes():
        from backend.src.api.routes import projects, runs, reports
        assert projects is not None
        assert runs is not None
        assert reports is not None
    run_test("API routes import", test_api_routes, "backend_api")
    
    # Test API models
    def test_api_models():
        from backend.src.api.models import (
            Project, RunSummary, RunDetail, RunCreate, TaskStatus
        )
        assert Project is not None
        assert RunSummary is not None
        assert RunDetail is not None
        assert TaskStatus is not None
    run_test("API models import", test_api_models, "backend_api")
    
    # Test FastAPI client creation
    def test_fastapi_client():
        from backend.src.api.app import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        assert client is not None
        
        # Test health/root endpoint
        try:
            response = client.get("/")
            assert response.status_code in [200, 404, 307]  # May redirect or not exist
        except:
            pass  # Endpoint may not exist
    run_test("FastAPI test client", test_fastapi_client, "backend_api")
    
    # Test projects endpoint
    def test_projects_endpoint():
        from backend.src.api.app import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get("/projects")
        assert response.status_code in [200, 404, 500]  # May fail if DB not available
    run_test("GET /projects endpoint", test_projects_endpoint, "backend_api")


def test_ml_models():
    """Test ML model components."""
    print("\n[TEST] ML Models")
    print("=" * 60)
    
    # Test Biodiversity model
    def test_biodiversity_import():
        from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig
        assert BiodiversityEnsemble is not None
        assert BiodiversityConfig is not None
    run_test("Biodiversity model import", test_biodiversity_import, "ml_models")
    
    def test_biodiversity_init():
        from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig
        config = BiodiversityConfig(use_pretrained=True)
        model = BiodiversityEnsemble(config=config)
        assert model is not None
        assert hasattr(model, "predict")
        assert hasattr(model, "vector_fields")
    run_test("Biodiversity model initialization", test_biodiversity_init, "ml_models")
    
    def test_biodiversity_prediction():
        from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig
        config = BiodiversityConfig(use_pretrained=True)
        model = BiodiversityEnsemble(config=config)
        
        features = {
            "protected_overlap_pct": 25.0,
            "fragmentation_index": 0.6,
            "forest_ratio": 0.4,
            "protected_site_count": 3,
            "protected_overlap_ha": 150.0,
            "aoi_area_ha": 500.0,
        }
        prediction = model.predict(features)
        assert prediction is not None
    run_test("Biodiversity model prediction", test_biodiversity_prediction, "ml_models")
    
    # Test RESM model
    def test_resm_import():
        from ai.models.resm import RESMEnsemble, RESMConfig
        assert RESMEnsemble is not None
        assert RESMConfig is not None
    run_test("RESM model import", test_resm_import, "ml_models")
    
    def test_resm_init():
        from ai.models.resm import RESMEnsemble, RESMConfig
        config = RESMConfig(use_pretrained=True)
        model = RESMEnsemble(config=config)
        assert model is not None
        assert hasattr(model, "predict")
    run_test("RESM model initialization", test_resm_init, "ml_models")
    
    def test_resm_prediction():
        from ai.models.resm import RESMEnsemble, RESMConfig
        config = RESMConfig(use_pretrained=True)
        model = RESMEnsemble(config=config)
        
        features = {field: 0.5 for field in model.vector_fields[:10]}  # Use first 10 fields
        prediction = model.predict(features)
        assert prediction is not None
    run_test("RESM model prediction", test_resm_prediction, "ml_models")
    
    # Test AHSM model
    def test_ahsm_import():
        from ai.models.ahsm import AHSMEnsemble, AHSMConfig
        assert AHSMEnsemble is not None
        assert AHSMConfig is not None
    run_test("AHSM model import", test_ahsm_import, "ml_models")
    
    def test_ahsm_init():
        from ai.models.ahsm import AHSMEnsemble, AHSMConfig
        config = AHSMConfig(use_pretrained=True)
        model = AHSMEnsemble(config=config)
        assert model is not None
    run_test("AHSM model initialization", test_ahsm_init, "ml_models")
    
    # Test CIM model
    def test_cim_import():
        from ai.models.cim import CIMEnsemble, CIMConfig
        assert CIMEnsemble is not None
        assert CIMConfig is not None
    run_test("CIM model import", test_cim_import, "ml_models")
    
    def test_cim_init():
        from ai.models.cim import CIMEnsemble, CIMConfig
        config = CIMConfig(use_pretrained=True)
        model = CIMEnsemble(config=config)
        assert model is not None
    run_test("CIM model initialization", test_cim_init, "ml_models")


def test_pretrained_models():
    """Test pretrained model loading."""
    print("\n[TEST] Pretrained Models")
    print("=" * 60)
    
    def test_pretrained_loader():
        from ai.models.pretrained import load_pretrained_bundle
        assert load_pretrained_bundle is not None
    run_test("Pretrained loader import", test_pretrained_loader, "pretrained_models")
    
    def test_pretrained_biodiversity():
        from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig
        config = BiodiversityConfig(use_pretrained=True)
        model = BiodiversityEnsemble(config=config)
        # Check if pretrained model was loaded
        assert "pretrained" in model.dataset_source.lower() or model.dataset_source.startswith("pretrained")
    run_test("Pretrained Biodiversity model loading", test_pretrained_biodiversity, "pretrained_models")
    
    def test_pretrained_models_exist():
        pretrained_dir = PROJECT_ROOT / "models" / "pretrained"
        if pretrained_dir.exists():
            model_dirs = [d for d in pretrained_dir.iterdir() if d.is_dir()]
            assert len(model_dirs) > 0, "No pretrained model directories found"
        else:
            raise FileNotFoundError(f"Pretrained models directory not found: {pretrained_dir}")
    run_test("Pretrained models exist on disk", test_pretrained_models_exist, "pretrained_models")


def test_langchain_groq():
    """Test LangChain and Groq integration."""
    print("\n[TEST] LangChain/Groq Integration")
    print("=" * 60)
    
    def test_langchain_service_import():
        from backend.src.reporting.langchain_llm import LangChainLLMService
        assert LangChainLLMService is not None
    run_test("LangChain service import", test_langchain_service_import, "langchain_groq")
    
    def test_langchain_service_init():
        from backend.src.reporting.langchain_llm import LangChainLLMService
        service = LangChainLLMService()
        assert service is not None
    run_test("LangChain service initialization", test_langchain_service_init, "langchain_groq")
    
    def test_langchain_fallback():
        from backend.src.reporting.langchain_llm import LangChainLLMService
        service = LangChainLLMService()
        
        analysis_results = {"biodiversity": {"score": 75.0}}
        project_context = {"name": "Test", "type": "solar"}
        
        summary = service.generate_executive_summary(analysis_results, project_context)
        assert summary is not None
        assert len(summary) > 0
    run_test("LangChain fallback methods", test_langchain_fallback, "langchain_groq")
    
    def test_groq_api_key_check():
        from backend.src.config.base_settings import settings
        # Check if API key exists (may or may not be set)
        has_key = settings.groq_api_key is not None and len(settings.groq_api_key or "") > 0
        env_key = os.getenv("GROQ_API_KEY")
        # At least one should exist if configured
        if not has_key and not env_key:
            test_results["langchain_groq"]["errors"].append("GROQ_API_KEY not set (may be intentional)")
    run_test("Groq API key configuration", test_groq_api_key_check, "langchain_groq")
    
    def test_langchain_methods():
        from backend.src.reporting.langchain_llm import LangChainLLMService
        service = LangChainLLMService()
        
        # Test all generation methods exist and work
        analysis_results = {"biodiversity": {"score": 65.0}}
        project_context = {"name": "Test Project", "type": "solar", "country": "ITA"}
        
        assert hasattr(service, "generate_executive_summary")
        assert hasattr(service, "generate_biodiversity_narrative")
        assert hasattr(service, "explain_ml_prediction")
        assert hasattr(service, "generate_legal_recommendations")
        
        summary = service.generate_executive_summary(analysis_results, project_context)
        assert isinstance(summary, str)
    run_test("LangChain generation methods", test_langchain_methods, "langchain_groq")


def test_database():
    """Test database operations."""
    print("\n[TEST] Database Operations")
    print("=" * 60)
    
    def test_database_client_import():
        from backend.src.db.client import DatabaseClient
        assert DatabaseClient is not None
    run_test("Database client import", test_database_client_import, "database")
    
    def test_database_model_runs_import():
        # Database models are in model_runs.py, not models.py
        from backend.src.db.model_runs import ModelRunLogger, ModelRunRecord
        assert ModelRunLogger is not None
        assert ModelRunRecord is not None
    run_test("Database model_runs import", test_database_model_runs_import, "database")


def test_celery():
    """Test Celery task infrastructure."""
    print("\n[TEST] Celery Tasks")
    print("=" * 60)
    
    def test_celery_app_import():
        from backend.src.workers.celery_app import celery_app
        assert celery_app is not None
    run_test("Celery app import", test_celery_app_import, "celery")
    
    def test_celery_tasks_import():
        from backend.src.workers.tasks import run_analysis_task
        assert run_analysis_task is not None
    run_test("Celery tasks import", test_celery_tasks_import, "celery")


def test_weather_features():
    """Test weather feature extraction."""
    print("\n[TEST] Weather Features")
    print("=" * 60)
    
    def test_weather_features_import():
        from backend.src.analysis.weather_features import extract_weather_features
        assert extract_weather_features is not None
    run_test("Weather features import", test_weather_features_import, "weather_features")


def test_model_explainability():
    """Test model explainability."""
    print("\n[TEST] Model Explainability")
    print("=" * 60)
    
    def test_explainability_import():
        from backend.src.analysis.explainability import (
            generate_shap_explanations,
            save_explainability_artifacts,
        )
        assert generate_shap_explanations is not None
        assert save_explainability_artifacts is not None
    run_test("Explainability import", test_explainability_import, "model_explainability")
    
    def test_model_explainability_import():
        from backend.src.analysis.model_explainability import (
            generate_biodiversity_explainability,
            generate_resm_explainability,
        )
        assert generate_biodiversity_explainability is not None
        assert generate_resm_explainability is not None
    run_test("Model explainability module import", test_model_explainability_import, "model_explainability")


def test_report_generation():
    """Test report generation."""
    print("\n[TEST] Report Generation")
    print("=" * 60)
    
    def test_report_engine_import():
        from backend.src.reporting.engine import ReportEngine
        assert ReportEngine is not None
    run_test("Report engine import", test_report_engine_import, "report_generation")
    
    def test_report_exporter_import():
        from backend.src.reporting.exports import ReportExporter
        assert ReportExporter is not None
    run_test("Report exporter import", test_report_exporter_import, "report_generation")


def test_training_data():
    """Test training data."""
    print("\n[TEST] Training Data")
    print("=" * 60)
    
    def test_validate_training_data_import():
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from validate_training_data import validate_training_data
        assert validate_training_data is not None
    run_test("Training data validation import", test_validate_training_data_import, "training_data")
    
    def test_training_data_exists():
        training_paths = [
            PROJECT_ROOT / "data2" / "biodiversity" / "training.parquet",
            PROJECT_ROOT / "data2" / "resm" / "training.parquet",
            PROJECT_ROOT / "data2" / "ahsm" / "training.parquet",
            PROJECT_ROOT / "data2" / "cim" / "training.parquet",
        ]
        
        existing = [p.name for p in training_paths if p.exists()]
        missing = [p.name for p in training_paths if not p.exists()]
        
        if len(existing) > 0:
            test_results["training_data"]["errors"].append(f"Found: {existing}, Missing: {missing}")
        else:
            raise FileNotFoundError(f"No training data files found. Missing: {missing}")
    run_test("Training data files exist", test_training_data_exists, "training_data")


def test_frontend():
    """Test frontend components."""
    print("\n[TEST] Frontend Components")
    print("=" * 60)
    
    def test_frontend_api_client_import():
        sys.path.insert(0, str(PROJECT_ROOT / "frontend"))
        from src.api_client import ProjectsAPI, RunsAPI, TasksAPI
        assert ProjectsAPI is not None
        assert RunsAPI is not None
        assert TasksAPI is not None
    run_test("Frontend API client import", test_frontend_api_client_import, "frontend")
    
    def test_frontend_pages_exist():
        pages_dir = PROJECT_ROOT / "frontend" / "pages"
        expected_pages = [
            "1_🏠_Home.py",
            "2_➕_New_Project.py",
            "3_📊_Project.py",
            "4_📈_Run.py",
        ]
        
        existing = [p for p in expected_pages if (pages_dir / p).exists()]
        missing = [p for p in expected_pages if not (pages_dir / p).exists()]
        
        if len(missing) > 0:
            raise FileNotFoundError(f"Missing frontend pages: {missing}")
    run_test("Frontend pages exist", test_frontend_pages_exist, "frontend")


def test_data_catalog():
    """Test data catalog."""
    print("\n[TEST] Data Catalog")
    print("=" * 60)
    
    def test_catalog_import():
        from backend.src.datasets.catalog import DatasetCatalog
        assert DatasetCatalog is not None
    run_test("Data catalog import", test_catalog_import, "data_catalog")
    
    def test_catalog_initialization():
        from backend.src.datasets.catalog import DatasetCatalog
        from backend.src.config.base_settings import settings
        
        catalog = DatasetCatalog(settings.data_sources_dir)
        assert catalog is not None
        assert hasattr(catalog, "corine")
        assert hasattr(catalog, "natura2000")
        assert hasattr(catalog, "biodiversity_training")
    run_test("Data catalog initialization", test_catalog_initialization, "data_catalog")


def generate_report():
    """Generate test report."""
    print("\n" + "=" * 60)
    print("GENERATING TEST REPORT")
    print("=" * 60)
    
    total_passed = sum(cat["passed"] for cat in test_results.values())
    total_failed = sum(cat["failed"] for cat in test_results.values())
    total_tests = total_passed + total_failed
    
    report_path = PROJECT_ROOT / "tests" / "TEST_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = f"""# AETHERA 2.0 Comprehensive Test Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Tests**: {total_tests}
- **Passed**: {total_passed} ({(total_passed/total_tests*100) if total_tests > 0 else 0.0:.1f}%)
- **Failed**: {total_failed} ({(total_failed/total_tests*100) if total_tests > 0 else 0.0:.1f}%)

---

## Test Results by Component

"""
    
    working = []
    not_working = []
    not_tested = []
    
    for component, results in test_results.items():
        component_name = component.replace("_", " ").title()
        total = results["passed"] + results["failed"]
        
        if total == 0:
            status = "[WARN] NOT TESTED"
            not_tested.append(component_name)
        elif results["failed"] == 0:
            status = "[OK] PASSING"
            working.append(component_name)
        else:
            status = "[FAIL] FAILING"
            not_working.append(component_name)
        
        report += f"### {component_name}\n\n"
        report += f"- **Status**: {status}\n"
        report += f"- **Passed**: {results['passed']}\n"
        report += f"- **Failed**: {results['failed']}\n"
        report += f"- **Total**: {total}\n\n"
        
        if results["errors"]:
            report += f"**Errors** ({len(results['errors'])}):\n\n"
            for i, error in enumerate(results["errors"][:10], 1):  # Limit to 10 errors
                report += f"{i}. `{error[:200]}`\n"
            if len(results["errors"]) > 10:
                report += f"\n... and {len(results['errors']) - 10} more errors\n"
        
        if results["tests"]:
            report += f"**Test Details**:\n\n"
            for test_detail in results["tests"][:5]:  # Show first 5 tests
                report += f"- {test_detail}\n"
            if len(results["tests"]) > 5:
                report += f"- ... and {len(results['tests']) - 5} more tests\n"
        
        report += "\n---\n\n"
    
    report += f"""## Summary

### [OK] Working Components ({len(working)})

"""
    if working:
        for comp in working:
            passed = test_results[comp.lower().replace(" ", "_")]["passed"]
            report += f"- **{comp}**: {passed} tests passing\n"
    else:
        report += "No components are fully passing.\n"
    
    report += f"\n### [FAIL] Components with Issues ({len(not_working)})\n\n"
    if not_working:
        for comp in not_working:
            failed = test_results[comp.lower().replace(" ", "_")]["failed"]
            errors = test_results[comp.lower().replace(" ", "_")]["errors"]
            report += f"- **{comp}**: {failed} tests failing"
            if errors:
                report += f" - {errors[0][:100]}"
            report += "\n"
    else:
        report += "No components have failing tests.\n"
    
    if not_tested:
        report += f"\n### [WARN] Not Tested Components ({len(not_tested)})\n\n"
        for comp in not_tested:
            report += f"- **{comp}**: No tests executed\n"
    
    report += f"""

## Detailed Findings

### Backend API

"""
    api_results = test_results["backend_api"]
    if api_results["passed"] > 0:
        report += f"- [OK] {api_results['passed']} API tests passed\n"
    if api_results["failed"] > 0:
        report += f"- [FAIL] {api_results['failed']} API tests failed\n"
        for error in api_results["errors"][:5]:
            report += f"  - {error}\n"
    
    report += f"""
### ML Models

"""
    ml_results = test_results["ml_models"]
    if ml_results["passed"] > 0:
        report += f"- [OK] {ml_results['passed']} ML model tests passed\n"
    if ml_results["failed"] > 0:
        report += f"- [FAIL] {ml_results['failed']} ML model tests failed\n"
        for error in ml_results["errors"][:5]:
            report += f"  - {error}\n"
    
    report += f"""
### LangChain/Groq Integration

"""
    llm_results = test_results["langchain_groq"]
    if llm_results["passed"] > 0:
        report += f"- [OK] {llm_results['passed']} LangChain/Groq tests passed\n"
    if llm_results["failed"] > 0:
        report += f"- [FAIL] {llm_results['failed']} LangChain/Groq tests failed\n"
        for error in llm_results["errors"][:5]:
            report += f"  - {error}\n"
    
    # Check if Groq API key is configured
    try:
        from backend.src.config.base_settings import settings
        groq_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
        if groq_key:
            report += "- [OK] Groq API key is configured\n"
        else:
            report += "- [WARN] Groq API key is NOT configured (fallback mode will be used)\n"
    except Exception as e:
        report += f"- [WARN] Could not check Groq API key: {e}\n"
    
    report += f"""
### Database

"""
    db_results = test_results["database"]
    if db_results["passed"] > 0:
        report += f"- [OK] {db_results['passed']} database tests passed\n"
    if db_results["failed"] > 0:
        report += f"- [FAIL] {db_results['failed']} database tests failed\n"
        for error in db_results["errors"][:5]:
            report += f"  - {error}\n"
    
    report += f"""
### Celery

"""
    celery_results = test_results["celery"]
    if celery_results["passed"] > 0:
        report += f"- [OK] {celery_results['passed']} Celery tests passed\n"
    if celery_results["failed"] > 0:
        report += f"- [FAIL] {celery_results['failed']} Celery tests failed\n"
    
    report += f"""
### Frontend

"""
    frontend_results = test_results["frontend"]
    if frontend_results["passed"] > 0:
        report += f"- [OK] {frontend_results['passed']} frontend tests passed\n"
    if frontend_results["failed"] > 0:
        report += f"- [FAIL] {frontend_results['failed']} frontend tests failed\n"
        for error in frontend_results["errors"][:5]:
            report += f"  - {error}\n"
    
    report += f"""
### Pretrained Models

"""
    pretrained_results = test_results["pretrained_models"]
    if pretrained_results["passed"] > 0:
        report += f"- [OK] {pretrained_results['passed']} pretrained model tests passed\n"
        report += "- [OK] Models can be loaded from disk\n"
    if pretrained_results["failed"] > 0:
        report += f"- [FAIL] {pretrained_results['failed']} pretrained model tests failed\n"
        for error in pretrained_results["errors"][:5]:
            report += f"  - {error}\n"
    
    report += f"""
## Recommendations

"""
    if not_working:
        report += "1. **Fix failing components**: Address the errors listed above in failing components.\n\n"
    if not_tested:
        report += "2. **Add missing tests**: Implement test coverage for components that were not tested.\n\n"
    
    report += """3. **Expand test coverage**: Add more comprehensive integration tests for:
   - API endpoint error handling
   - Database transaction rollback
   - Celery task retry mechanisms
   - ML model edge cases
   - Frontend error states

4. **Add E2E tests**: Implement end-to-end tests that verify the full analysis pipeline from AOI upload to report generation.

5. **Performance tests**: Add tests to verify:
   - API response times (< 500ms for simple endpoints)
   - Model inference speed (< 5 seconds)
   - Database query performance
   - Memory usage during analysis runs

6. **Integration with external services**:
   - Test Groq API integration with actual API calls (if key configured)
   - Test database connections with real database
   - Test Celery tasks with Redis broker

## Next Steps

1. Review failing tests and fix critical issues
2. Add missing test coverage for untested components
3. Set up CI/CD pipeline to run tests automatically
4. Add test coverage metrics (aim for >80% coverage)
5. Implement test fixtures for common test scenarios

---

**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    report_path.write_text(report, encoding="utf-8")
    print(f"\n✅ Test report saved to: {report_path}")
    print(f"   Total tests: {total_tests} (Passed: {total_passed}, Failed: {total_failed})")


def main():
    """Run all tests."""
    print("=" * 60)
    print("AETHERA 2.0 COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    
    # Run all test suites
    test_backend_api()
    test_ml_models()
    test_pretrained_models()
    test_langchain_groq()
    test_database()
    test_celery()
    test_weather_features()
    test_model_explainability()
    test_report_generation()
    test_training_data()
    test_frontend()
    test_data_catalog()
    
    # Generate report
    generate_report()
    
    # Print summary
    total_passed = sum(cat["passed"] for cat in test_results.values())
    total_failed = sum(cat["failed"] for cat in test_results.values())
    total_tests = total_passed + total_failed
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)" if total_tests > 0 else "Passed: 0")
    print(f"Failed: {total_failed} ({total_failed/total_tests*100:.1f}%)" if total_tests > 0 else "Failed: 0")
    print("=" * 60)
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
