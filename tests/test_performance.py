"""
Performance Tests
Benchmarks for API response times and model inference speed.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

perf_test_results: Dict[str, Any] = {
    "passed": 0,
    "failed": 0,
    "benchmarks": {},
    "errors": [],
}


def benchmark_api_endpoint(endpoint: str, method: str = "GET", json_data: dict = None) -> float:
    """Benchmark an API endpoint response time."""
    try:
        from backend.src.api.app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        start_time = time.time()
        
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        elapsed = time.time() - start_time
        
        return elapsed
        
    except Exception as e:
        raise Exception(f"API benchmark failed: {e}")


def test_api_response_time():
    """Test API response time for GET /projects."""
    try:
        elapsed = benchmark_api_endpoint("/projects")
        
        # API should respond in < 1 second (local test)
        assert elapsed < 1.0, f"API response too slow: {elapsed:.3f}s"
        
        perf_test_results["benchmarks"]["api_get_projects"] = elapsed
        perf_test_results["passed"] += 1
        print(f"  [PASS] GET /projects response time: {elapsed:.3f}s")
        
    except Exception as e:
        perf_test_results["failed"] += 1
        error_msg = f"API response time test failed: {str(e)[:200]}"
        perf_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_api_project_creation_time():
    """Test API response time for POST /projects."""
    try:
        project_data = {
            "name": "Perf Test Project",
            "country": "ITA",
            "sector": "renewable",
        }
        
        elapsed = benchmark_api_endpoint("/projects", method="POST", json_data=project_data)
        
        # Project creation should be < 2 seconds (local test)
        assert elapsed < 2.0, f"Project creation too slow: {elapsed:.3f}s"
        
        perf_test_results["benchmarks"]["api_post_projects"] = elapsed
        perf_test_results["passed"] += 1
        print(f"  [PASS] POST /projects response time: {elapsed:.3f}s")
        
    except Exception as e:
        perf_test_results["failed"] += 1
        error_msg = f"API project creation time test failed: {str(e)[:200]}"
        perf_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_model_inference_speed():
    """Test model inference speed."""
    try:
        from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig
        
        config = BiodiversityConfig(use_pretrained=True)
        model = BiodiversityEnsemble(config=config)
        
        # Sample features
        features = {
            "protected_overlap_pct": 25.0,
            "fragmentation_index": 0.6,
            "forest_ratio": 0.4,
            "protected_site_count": 3,
            "protected_overlap_ha": 150.0,
            "aoi_area_ha": 500.0,
        }
        
        # Warm-up prediction
        _ = model.predict(features)
        
        # Benchmark prediction
        start_time = time.time()
        prediction = model.predict(features)
        elapsed = time.time() - start_time
        
        assert prediction is not None
        # Model inference should be < 5 seconds (pretrained)
        assert elapsed < 5.0, f"Model inference too slow: {elapsed:.3f}s"
        
        perf_test_results["benchmarks"]["biodiversity_inference"] = elapsed
        perf_test_results["passed"] += 1
        print(f"  [PASS] Biodiversity model inference time: {elapsed:.3f}s")
        
    except Exception as e:
        perf_test_results["failed"] += 1
        error_msg = f"Model inference speed test failed: {str(e)[:200]}"
        perf_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_resm_inference_speed():
    """Test RESM model inference speed."""
    try:
        from ai.models.resm import RESMEnsemble, RESMConfig
        
        config = RESMConfig(use_pretrained=True)
        model = RESMEnsemble(config=config)
        
        # Sample features
        features = {field: 0.5 for field in model.vector_fields[:10]}
        
        # Warm-up
        _ = model.predict(features)
        
        # Benchmark
        start_time = time.time()
        prediction = model.predict(features)
        elapsed = time.time() - start_time
        
        assert prediction is not None
        assert elapsed < 5.0, f"RESM inference too slow: {elapsed:.3f}s"
        
        perf_test_results["benchmarks"]["resm_inference"] = elapsed
        perf_test_results["passed"] += 1
        print(f"  [PASS] RESM model inference time: {elapsed:.3f}s")
        
    except Exception as e:
        perf_test_results["failed"] += 1
        error_msg = f"RESM inference speed test failed: {str(e)[:200]}"
        perf_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_model_loading_speed():
    """Test pretrained model loading speed."""
    try:
        from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig
        
        start_time = time.time()
        config = BiodiversityConfig(use_pretrained=True)
        model = BiodiversityEnsemble(config=config)
        elapsed = time.time() - start_time
        
        assert model is not None
        # Model loading should be < 10 seconds (pretrained models)
        assert elapsed < 10.0, f"Model loading too slow: {elapsed:.3f}s"
        
        perf_test_results["benchmarks"]["model_loading"] = elapsed
        perf_test_results["passed"] += 1
        print(f"  [PASS] Model loading time: {elapsed:.3f}s")
        
    except Exception as e:
        perf_test_results["failed"] += 1
        error_msg = f"Model loading speed test failed: {str(e)[:200]}"
        perf_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def test_langchain_response_time():
    """Test LangChain fallback response time."""
    try:
        from backend.src.reporting.langchain_llm import LangChainLLMService
        
        service = LangChainLLMService()
        
        analysis_results = {"biodiversity": {"score": 75.0}}
        project_context = {"name": "Test", "type": "solar"}
        
        start_time = time.time()
        summary = service.generate_executive_summary(analysis_results, project_context)
        elapsed = time.time() - start_time
        
        assert summary is not None
        # Fallback generation should be < 2 seconds (text generation takes time)
        assert elapsed < 2.0, f"LangChain fallback too slow: {elapsed:.3f}s"
        
        perf_test_results["benchmarks"]["langchain_fallback"] = elapsed
        perf_test_results["passed"] += 1
        print(f"  [PASS] LangChain fallback response time: {elapsed:.3f}s")
        
    except Exception as e:
        perf_test_results["failed"] += 1
        error_msg = f"LangChain response time test failed: {str(e)[:200]}"
        perf_test_results["errors"].append(error_msg)
        print(f"  [FAIL] {error_msg}")


def main():
    """Run all performance tests."""
    print("=" * 60)
    print("PERFORMANCE TESTS")
    print("=" * 60)
    print("Benchmarking API and model performance...")
    print("=" * 60)
    
    test_api_response_time()
    test_api_project_creation_time()
    test_model_loading_speed()
    test_model_inference_speed()
    test_resm_inference_speed()
    test_langchain_response_time()
    
    print("\n" + "=" * 60)
    print("PERFORMANCE TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {perf_test_results['passed']}")
    print(f"Failed: {perf_test_results['failed']}")
    
    if perf_test_results["benchmarks"]:
        print("\nBenchmarks:")
        for name, value in perf_test_results["benchmarks"].items():
            print(f"  - {name}: {value:.3f}s")
    
    if perf_test_results["errors"]:
        print("\nErrors:")
        for error in perf_test_results["errors"][:5]:
            print(f"  - {error}")
    print("=" * 60)
    
    return 0 if perf_test_results["failed"] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
