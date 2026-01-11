"""
Detailed ML model tests with actual predictions.
"""

import sys
from pathlib import Path

import pytest
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_comprehensive import test_results


class TestBiodiversityModelDetailed:
    """Detailed tests for Biodiversity model."""
    
    def test_biodiversity_prediction_with_sample_data(self):
        """Test biodiversity model prediction with sample features."""
        try:
            from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig
            
            config = BiodiversityConfig(use_pretrained=True)
            model = BiodiversityEnsemble(config=config)
            
            # Sample features matching vector_fields
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
            
            # Check prediction structure
            if isinstance(prediction, dict):
                assert "label" in prediction or "prediction" in prediction or "class" in prediction
            elif isinstance(prediction, (list, tuple)):
                assert len(prediction) > 0
            
            test_results["ml_models"]["passed"] += 1
        except Exception as e:
            test_results["ml_models"]["failed"] += 1
            test_results["ml_models"]["errors"].append(f"Biodiversity prediction failed: {e}")
    
    def test_biodiversity_model_vector_fields(self):
        """Test that biodiversity model has correct vector fields."""
        try:
            from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig
            
            config = BiodiversityConfig(use_pretrained=True)
            model = BiodiversityEnsemble(config=config)
            
            assert hasattr(model, "vector_fields")
            assert isinstance(model.vector_fields, list)
            assert len(model.vector_fields) > 0
            
            # Check expected fields
            expected_fields = ["protected_overlap_pct", "fragmentation_index", "forest_ratio"]
            for field in expected_fields:
                assert field in model.vector_fields, f"Expected field {field} not in vector_fields"
            
            test_results["ml_models"]["passed"] += 1
        except Exception as e:
            test_results["ml_models"]["failed"] += 1
            test_results["ml_models"]["errors"].append(f"Biodiversity vector fields check failed: {e}")


class TestRESMModelDetailed:
    """Detailed tests for RESM model."""
    
    def test_resm_prediction_with_sample_data(self):
        """Test RESM model prediction with sample features."""
        try:
            from ai.models.resm import RESMEnsemble, RESMConfig
            
            config = RESMConfig(use_pretrained=True)
            model = RESMEnsemble(config=config)
            
            # Sample features
            features = {
                "aoi_area_ha": 100.0,
                "natural_habitat_ratio": 0.5,
                "impervious_surface_ratio": 0.2,
                "agricultural_ratio": 0.3,
                "solar_ghi_kwh_m2_day": 4.5,
                "wind_speed_100m_ms": 7.0,
            }
            
            # Fill missing features
            for field in model.vector_fields:
                if field not in features:
                    features[field] = 0.0
            
            prediction = model.predict(features)
            assert prediction is not None
            
            # RESM should return a score (0-100)
            if isinstance(prediction, dict):
                assert "score" in prediction or "prediction" in prediction
                if "score" in prediction:
                    score = prediction["score"]
                    assert isinstance(score, (int, float))
                    assert 0 <= score <= 100, f"RESM score {score} should be between 0 and 100"
            
            test_results["ml_models"]["passed"] += 1
        except Exception as e:
            test_results["ml_models"]["failed"] += 1
            test_results["ml_models"]["errors"].append(f"RESM prediction failed: {e}")
