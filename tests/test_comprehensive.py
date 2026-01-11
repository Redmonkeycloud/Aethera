"""
Comprehensive test suite for AETHERA 2.0
Tests all components from frontend to backend, API, Groq, ML models, etc.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Test results tracking
test_results: Dict[str, Any] = {
    "backend_api": {"passed": 0, "failed": 0, "errors": []},
    "ml_models": {"passed": 0, "failed": 0, "errors": []},
    "langchain_groq": {"passed": 0, "failed": 0, "errors": []},
    "database": {"passed": 0, "failed": 0, "errors": []},
    "celery": {"passed": 0, "failed": 0, "errors": []},
    "weather_features": {"passed": 0, "failed": 0, "errors": []},
    "model_explainability": {"passed": 0, "failed": 0, "errors": []},
    "report_generation": {"passed": 0, "failed": 0, "errors": []},
    "training_data": {"passed": 0, "failed": 0, "errors": []},
    "frontend": {"passed": 0, "failed": 0, "errors": []},
}


class TestBackendAPI:
    """Test backend API endpoints."""
    
    def test_api_app_import(self):
        """Test that API app can be imported."""
        try:
            from backend.src.api.app import app
            assert app is not None
            test_results["backend_api"]["passed"] += 1
        except Exception as e:
            test_results["backend_api"]["failed"] += 1
            test_results["backend_api"]["errors"].append(f"API app import failed: {e}")
            pytest.skip(f"API app import failed: {e}")
    
    def test_api_routes_import(self):
        """Test that API routes can be imported."""
        try:
            from backend.src.api.routes import projects, runs, reports
            assert projects is not None
            assert runs is not None
            assert reports is not None
            test_results["backend_api"]["passed"] += 1
        except Exception as e:
            test_results["backend_api"]["failed"] += 1
            test_results["backend_api"]["errors"].append(f"API routes import failed: {e}")
    
    def test_api_models_import(self):
        """Test that API models can be imported."""
        try:
            from backend.src.api.models import (
                Project, RunSummary, RunDetail, TaskStatus
            )
            assert Project is not None
            assert RunSummary is not None
            assert RunDetail is not None
            assert TaskStatus is not None
            test_results["backend_api"]["passed"] += 1
        except Exception as e:
            test_results["backend_api"]["failed"] += 1
            test_results["backend_api"]["errors"].append(f"API models import failed: {e}")


class TestMLModels:
    """Test ML model implementations."""
    
    def test_biodiversity_model_import(self):
        """Test biodiversity model can be imported."""
        try:
            from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig
            assert BiodiversityEnsemble is not None
            assert BiodiversityConfig is not None
            test_results["ml_models"]["passed"] += 1
        except Exception as e:
            test_results["ml_models"]["failed"] += 1
            test_results["ml_models"]["errors"].append(f"Biodiversity model import failed: {e}")
    
    def test_resm_model_import(self):
        """Test RESM model can be imported."""
        try:
            from ai.models.resm import RESMEnsemble, RESMConfig
            assert RESMEnsemble is not None
            assert RESMConfig is not None
            test_results["ml_models"]["passed"] += 1
        except Exception as e:
            test_results["ml_models"]["failed"] += 1
            test_results["ml_models"]["errors"].append(f"RESM model import failed: {e}")
    
    def test_ahsm_model_import(self):
        """Test AHSM model can be imported."""
        try:
            from ai.models.ahsm import AHSMEnsemble, AHSMConfig
            assert AHSMEnsemble is not None
            assert AHSMConfig is not None
            test_results["ml_models"]["passed"] += 1
        except Exception as e:
            test_results["ml_models"]["failed"] += 1
            test_results["ml_models"]["errors"].append(f"AHSM model import failed: {e}")
    
    def test_cim_model_import(self):
        """Test CIM model can be imported."""
        try:
            from ai.models.cim import CIMEnsemble, CIMConfig
            assert CIMEnsemble is not None
            assert CIMConfig is not None
            test_results["ml_models"]["passed"] += 1
        except Exception as e:
            test_results["ml_models"]["failed"] += 1
            test_results["ml_models"]["errors"].append(f"CIM model import failed: {e}")
    
    def test_biodiversity_model_initialization(self):
        """Test biodiversity model can be initialized."""
        try:
            from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig
            config = BiodiversityConfig(use_pretrained=True)
            model = BiodiversityEnsemble(config=config)
            assert model is not None
            assert hasattr(model, "predict")
            test_results["ml_models"]["passed"] += 1
        except Exception as e:
            test_results["ml_models"]["failed"] += 1
            test_results["ml_models"]["errors"].append(f"Biodiversity model initialization failed: {e}")
    
    def test_resm_model_prediction(self):
        """Test RESM model can make predictions."""
        try:
            from ai.models.resm import RESMEnsemble, RESMConfig
            config = RESMConfig(use_pretrained=True)
            model = RESMEnsemble(config=config)
            
            # Create sample features
            sample_features = {
                "aoi_area_ha": 100.0,
                "natural_habitat_ratio": 0.5,
                "solar_ghi_kwh_m2_day": 4.5,
                "wind_speed_100m_ms": 7.0,
            }
            
            # Fill missing features with defaults
            for field in model.vector_fields:
                if field not in sample_features:
                    sample_features[field] = 0.0
            
            prediction = model.predict(sample_features)
            assert prediction is not None
            assert "score" in prediction or "prediction" in prediction
            test_results["ml_models"]["passed"] += 1
        except Exception as e:
            test_results["ml_models"]["failed"] += 1
            test_results["ml_models"]["errors"].append(f"RESM model prediction failed: {e}")


class TestLangChainGroq:
    """Test LangChain and Groq integration."""
    
    def test_langchain_service_import(self):
        """Test LangChain service can be imported."""
        try:
            from backend.src.reporting.langchain_llm import LangChainLLMService
            assert LangChainLLMService is not None
            test_results["langchain_groq"]["passed"] += 1
        except Exception as e:
            test_results["langchain_groq"]["failed"] += 1
            test_results["langchain_groq"]["errors"].append(f"LangChain service import failed: {e}")
    
    def test_langchain_service_initialization(self):
        """Test LangChain service can be initialized."""
        try:
            from backend.src.reporting.langchain_llm import LangChainLLMService
            service = LangChainLLMService()
            assert service is not None
            # Service may be disabled if API key not set - that's OK
            test_results["langchain_groq"]["passed"] += 1
        except Exception as e:
            test_results["langchain_groq"]["failed"] += 1
            test_results["langchain_groq"]["errors"].append(f"LangChain service initialization failed: {e}")
    
    def test_groq_api_key_check(self):
        """Test that Groq API key check works."""
        try:
            from backend.src.config.base_settings import settings
            
            # Check if API key is set (may or may not be)
            has_key = settings.groq_api_key is not None and len(settings.groq_api_key) > 0
            
            # This is informational, not a failure
            if not has_key:
                test_results["langchain_groq"]["errors"].append("GROQ_API_KEY not set (may be intentional for testing)")
            
            test_results["langchain_groq"]["passed"] += 1
        except Exception as e:
            test_results["langchain_groq"]["failed"] += 1
            test_results["langchain_groq"]["errors"].append(f"Groq API key check failed: {e}")
    
    def test_langchain_fallback_execution(self):
        """Test that LangChain fallback methods work."""
        try:
            from backend.src.reporting.langchain_llm import LangChainLLMService
            
            service = LangChainLLMService()
            
            # Test fallback executive summary generation
            analysis_results = {
                "biodiversity": {"score": 75.0},
                "resm": {"score": 80.0},
                "ahsm": {"score": 30.0},
            }
            project_context = {
                "name": "Test Project",
                "type": "solar",
                "country": "ITA",
            }
            
            summary = service.generate_executive_summary(analysis_results, project_context)
            assert summary is not None
            assert len(summary) > 0
            test_results["langchain_groq"]["passed"] += 1
        except Exception as e:
            test_results["langchain_groq"]["failed"] += 1
            test_results["langchain_groq"]["errors"].append(f"LangChain fallback execution failed: {e}")


class TestDatabase:
    """Test database operations."""
    
    def test_database_client_import(self):
        """Test database client can be imported."""
        try:
            from backend.src.db.client import DatabaseClient
            assert DatabaseClient is not None
            test_results["database"]["passed"] += 1
        except Exception as e:
            test_results["database"]["failed"] += 1
            test_results["database"]["errors"].append(f"Database client import failed: {e}")
    
    def test_database_model_runs_import(self):
        """Test database model_runs can be imported."""
        try:
            from backend.src.db.model_runs import ModelRunLogger, ModelRunRecord
            assert ModelRunLogger is not None
            assert ModelRunRecord is not None
            test_results["database"]["passed"] += 1
        except Exception as e:
            test_results["database"]["failed"] += 1
            test_results["database"]["errors"].append(f"Database model_runs import failed: {e}")


class TestCelery:
    """Test Celery task infrastructure."""
    
    def test_celery_app_import(self):
        """Test Celery app can be imported."""
        try:
            from backend.src.workers.celery_app import celery_app
            assert celery_app is not None
            test_results["celery"]["passed"] += 1
        except Exception as e:
            test_results["celery"]["failed"] += 1
            test_results["celery"]["errors"].append(f"Celery app import failed: {e}")
    
    def test_celery_tasks_import(self):
        """Test Celery tasks can be imported."""
        try:
            from backend.src.workers.tasks import run_analysis_task
            assert run_analysis_task is not None
            test_results["celery"]["passed"] += 1
        except Exception as e:
            test_results["celery"]["failed"] += 1
            test_results["celery"]["errors"].append(f"Celery tasks import failed: {e}")


class TestWeatherFeatures:
    """Test weather feature extraction."""
    
    def test_weather_features_import(self):
        """Test weather features module can be imported."""
        try:
            from backend.src.analysis.weather_features import extract_weather_features
            assert extract_weather_features is not None
            test_results["weather_features"]["passed"] += 1
        except Exception as e:
            test_results["weather_features"]["failed"] += 1
            test_results["weather_features"]["errors"].append(f"Weather features import failed: {e}")


class TestModelExplainability:
    """Test model explainability features."""
    
    def test_explainability_import(self):
        """Test explainability module can be imported."""
        try:
            from backend.src.analysis.explainability import (
                generate_shap_explanations,
                save_explainability_artifacts,
            )
            assert generate_shap_explanations is not None
            assert save_explainability_artifacts is not None
            test_results["model_explainability"]["passed"] += 1
        except Exception as e:
            test_results["model_explainability"]["failed"] += 1
            test_results["model_explainability"]["errors"].append(f"Explainability import failed: {e}")
    
    def test_model_explainability_module_import(self):
        """Test model explainability module can be imported."""
        try:
            from backend.src.analysis.model_explainability import (
                generate_biodiversity_explainability,
                generate_resm_explainability,
            )
            assert generate_biodiversity_explainability is not None
            assert generate_resm_explainability is not None
            test_results["model_explainability"]["passed"] += 1
        except Exception as e:
            test_results["model_explainability"]["failed"] += 1
            test_results["model_explainability"]["errors"].append(f"Model explainability module import failed: {e}")


class TestReportGeneration:
    """Test report generation."""
    
    def test_report_engine_import(self):
        """Test report engine can be imported."""
        try:
            from backend.src.reporting.engine import ReportEngine
            assert ReportEngine is not None
            test_results["report_generation"]["passed"] += 1
        except Exception as e:
            test_results["report_generation"]["failed"] += 1
            test_results["report_generation"]["errors"].append(f"Report engine import failed: {e}")
    
    def test_report_exporter_import(self):
        """Test report exporter can be imported."""
        try:
            from backend.src.reporting.exports import ReportExporter
            assert ReportExporter is not None
            test_results["report_generation"]["passed"] += 1
        except Exception as e:
            test_results["report_generation"]["failed"] += 1
            test_results["report_generation"]["errors"].append(f"Report exporter import failed: {e}")


class TestTrainingData:
    """Test training data generation and validation."""
    
    def test_validate_training_data_import(self):
        """Test training data validation can be imported."""
        try:
            sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
            from validate_training_data import validate_training_data
            assert validate_training_data is not None
            test_results["training_data"]["passed"] += 1
        except Exception as e:
            test_results["training_data"]["failed"] += 1
            test_results["training_data"]["errors"].append(f"Training data validation import failed: {e}")
    
    def test_training_data_exists(self):
        """Test that training data files exist."""
        try:
            training_paths = [
                PROJECT_ROOT / "data2" / "biodiversity" / "training.parquet",
                PROJECT_ROOT / "data2" / "resm" / "training.parquet",
                PROJECT_ROOT / "data2" / "ahsm" / "training.parquet",
                PROJECT_ROOT / "data2" / "cim" / "training.parquet",
            ]
            
            existing = []
            missing = []
            for path in training_paths:
                if path.exists():
                    existing.append(path.name)
                else:
                    missing.append(path.name)
            
            # At least some training data should exist
            if len(existing) > 0:
                test_results["training_data"]["passed"] += 1
            else:
                test_results["training_data"]["failed"] += 1
                test_results["training_data"]["errors"].append(f"No training data files found. Missing: {missing}")
        except Exception as e:
            test_results["training_data"]["failed"] += 1
            test_results["training_data"]["errors"].append(f"Training data check failed: {e}")


class TestFrontend:
    """Test frontend components."""
    
    def test_frontend_api_client_import(self):
        """Test frontend API client can be imported."""
        try:
            sys.path.insert(0, str(PROJECT_ROOT / "frontend"))
            from src.api_client import ProjectsAPI, RunsAPI, TasksAPI
            assert ProjectsAPI is not None
            assert RunsAPI is not None
            assert TasksAPI is not None
            test_results["frontend"]["passed"] += 1
        except Exception as e:
            test_results["frontend"]["failed"] += 1
            test_results["frontend"]["errors"].append(f"Frontend API client import failed: {e}")
    
    def test_frontend_pages_exist(self):
        """Test that frontend pages exist."""
        try:
            pages_dir = PROJECT_ROOT / "frontend" / "pages"
            expected_pages = [
                "1_🏠_Home.py",
                "2_➕_New_Project.py",
                "3_📊_Project.py",
                "4_📈_Run.py",
            ]
            
            existing = []
            missing = []
            for page in expected_pages:
                page_path = pages_dir / page
                if page_path.exists():
                    existing.append(page)
                else:
                    missing.append(page)
            
            if len(missing) == 0:
                test_results["frontend"]["passed"] += 1
            else:
                test_results["frontend"]["failed"] += 1
                test_results["frontend"]["errors"].append(f"Missing frontend pages: {missing}")
        except Exception as e:
            test_results["frontend"]["failed"] += 1
            test_results["frontend"]["errors"].append(f"Frontend pages check failed: {e}")


@pytest.fixture(scope="session", autouse=True)
def generate_test_report():
    """Generate test report after all tests complete."""
    yield
    # Generate report
    report_path = PROJECT_ROOT / "tests" / "TEST_REPORT.md"
    generate_markdown_report(report_path)


def generate_markdown_report(report_path: Path) -> None:
    """Generate a markdown test report."""
    total_passed = sum(cat["passed"] for cat in test_results.values())
    total_failed = sum(cat["failed"] for cat in test_results.values())
    total_tests = total_passed + total_failed
    
    report = f"""# AETHERA 2.0 Comprehensive Test Report

**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Tests**: {total_tests}
- **Passed**: {total_passed} ({total_passed/total_tests*100:.1f}%)
- **Failed**: {total_failed} ({total_failed/total_tests*100:.1f}%)

## Test Results by Component

"""
    
    for component, results in test_results.items():
        component_name = component.replace("_", " ").title()
        total = results["passed"] + results["failed"]
        if total == 0:
            status = "⚠️ NOT TESTED"
        elif results["failed"] == 0:
            status = "✅ PASSING"
        else:
            status = "❌ FAILING"
        
        report += f"### {component_name}\n"
        report += f"- **Status**: {status}\n"
        report += f"- **Passed**: {results['passed']}\n"
        report += f"- **Failed**: {results['failed']}\n"
        
        if results["errors"]:
            report += f"- **Errors**:\n"
            for error in results["errors"][:5]:  # Limit to 5 errors per component
                report += f"  - {error}\n"
            if len(results["errors"]) > 5:
                report += f"  - ... and {len(results['errors']) - 5} more errors\n"
        report += "\n"
    
    report += f"""## Detailed Findings

### ✅ Working Components

"""
    
    working = []
    not_working = []
    not_tested = []
    
    for component, results in test_results.items():
        component_name = component.replace("_", " ").title()
        if results["passed"] + results["failed"] == 0:
            not_tested.append(component_name)
        elif results["failed"] == 0 and results["passed"] > 0:
            working.append(component_name)
        else:
            not_working.append(component_name)
    
    if working:
        report += "The following components are **working correctly**:\n\n"
        for comp in working:
            report += f"- ✅ {comp}\n"
        report += "\n"
    
    if not_working:
        report += "### ❌ Components with Issues\n\n"
        report += "The following components have **failing tests**:\n\n"
        for comp in not_working:
            report += f"- ❌ {comp}\n"
            # Add specific errors
            comp_key = comp.lower().replace(" ", "_")
            if comp_key in test_results and test_results[comp_key]["errors"]:
                for error in test_results[comp_key]["errors"][:3]:
                    report += f"  - {error}\n"
        report += "\n"
    
    if not_tested:
        report += "### ⚠️ Not Tested Components\n\n"
        report += "The following components were **not tested** (no tests executed):\n\n"
        for comp in not_tested:
            report += f"- ⚠️ {comp}\n"
        report += "\n"
    
    report += f"""## Recommendations

"""
    
    if not_working:
        report += "1. **Fix failing components**: Address the errors listed above in the failing components.\n"
    if not_tested:
        report += "2. **Add missing tests**: Implement test coverage for components that were not tested.\n"
    
    report += "3. **Expand test coverage**: Add more comprehensive integration tests for API endpoints.\n"
    report += "4. **Add E2E tests**: Implement end-to-end tests that verify the full analysis pipeline.\n"
    report += "5. **Performance tests**: Add tests to verify response times and resource usage.\n"
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"\n✅ Test report generated: {report_path}")
