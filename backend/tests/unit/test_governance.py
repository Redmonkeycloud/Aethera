"""Unit tests for Model Governance."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

import numpy as np
import pandas as pd

from backend.src.db.client import DatabaseClient
from backend.src.governance import (
    ABTestManager,
    DriftDetector,
    ModelRegistry,
    ValidationMetricsTracker,
)
from backend.src.governance.registry import ModelStage
from backend.src.governance.drift import DriftType
from backend.src.governance.validation import MetricType
from backend.src.governance.ab_testing import ABTestStatus


@pytest.fixture
def db_client(test_db_dsn):
    """Database client fixture."""
    return DatabaseClient(test_db_dsn)


@pytest.fixture
def model_registry(db_client):
    """Model registry fixture."""
    return ModelRegistry(db_client)


@pytest.fixture
def drift_detector(db_client):
    """Drift detector fixture."""
    return DriftDetector(db_client)


@pytest.fixture
def validation_tracker(db_client):
    """Validation metrics tracker fixture."""
    return ValidationMetricsTracker(db_client)


@pytest.fixture
def ab_test_manager(db_client):
    """A/B test manager fixture."""
    return ABTestManager(db_client)


class TestModelRegistry:
    """Tests for Model Registry."""

    def test_register_model(self, model_registry):
        """Test registering a model."""
        entry = model_registry.register_model(
            model_name="test_model",
            version="0.1.0",
            stage=ModelStage.DEVELOPMENT,
            description="Test model",
            hyperparameters={"learning_rate": 0.01},
            created_by="test_user",
        )

        assert entry.model_name == "test_model"
        assert entry.version == "0.1.0"
        assert entry.stage == ModelStage.DEVELOPMENT
        assert entry.id is not None

    def test_get_model(self, model_registry):
        """Test retrieving a model."""
        # Register first
        entry = model_registry.register_model(
            model_name="test_model",
            version="0.2.0",
            created_by="test_user",
        )

        # Retrieve
        retrieved = model_registry.get_model("test_model", "0.2.0")
        assert retrieved is not None
        assert retrieved.model_name == "test_model"
        assert retrieved.version == "0.2.0"

    def test_list_models(self, model_registry):
        """Test listing models."""
        # Register multiple models
        model_registry.register_model("model_a", "1.0.0", created_by="test")
        model_registry.register_model("model_a", "1.1.0", created_by="test")
        model_registry.register_model("model_b", "1.0.0", created_by="test")

        # List all
        all_models = model_registry.list_models()
        assert len(all_models) >= 3

        # Filter by name
        model_a_versions = model_registry.list_models(model_name="model_a")
        assert len(model_a_versions) >= 2
        assert all(m.model_name == "model_a" for m in model_a_versions)

    def test_get_latest_version(self, model_registry):
        """Test getting latest version."""
        model_registry.register_model("latest_test", "1.0.0", created_by="test")
        model_registry.register_model("latest_test", "1.1.0", created_by="test")

        latest = model_registry.get_latest_version("latest_test")
        assert latest is not None
        assert latest.version == "1.1.0"

    def test_promote_model(self, model_registry):
        """Test promoting a model."""
        entry = model_registry.register_model(
            "promote_test",
            "1.0.0",
            stage=ModelStage.DEVELOPMENT,
            created_by="test",
        )

        promoted = model_registry.promote_model(
            "promote_test",
            "1.0.0",
            ModelStage.PRODUCTION,
            "admin",
        )

        assert promoted.stage == ModelStage.PRODUCTION
        assert promoted.approved_by == "admin"
        assert promoted.approved_at is not None


class TestDriftDetector:
    """Tests for Drift Detection."""

    def test_detect_data_drift(self, drift_detector):
        """Test data drift detection."""
        # Create reference and current data with drift
        reference_data = pd.DataFrame({
            "feature1": np.random.normal(0, 1, 1000),
            "feature2": np.random.normal(5, 2, 1000),
        })

        # Current data with shifted distribution
        current_data = pd.DataFrame({
            "feature1": np.random.normal(2, 1, 1000),  # Shifted mean
            "feature2": np.random.normal(5, 2, 1000),  # Same distribution
        })

        alerts = drift_detector.detect_data_drift(
            model_name="test_model",
            model_version="0.1.0",
            reference_data=reference_data,
            current_data=current_data,
            threshold=0.1,
        )

        assert len(alerts) == 2
        # feature1 should have higher drift score
        feature1_alert = next(a for a in alerts if a.feature_name == "feature1")
        assert feature1_alert.drift_score > 0.1

    def test_detect_prediction_drift(self, drift_detector):
        """Test prediction drift detection."""
        reference = np.random.normal(50, 10, 1000)
        current = np.random.normal(60, 10, 1000)  # Shifted

        alert = drift_detector.detect_prediction_drift(
            model_name="test_model",
            model_version="0.1.0",
            reference_predictions=reference,
            current_predictions=current,
            threshold=0.1,
        )

        assert alert is not None
        assert alert.drift_type == DriftType.PREDICTION_DRIFT
        assert alert.drift_score > 0.1

    def test_get_drift_alerts(self, drift_detector):
        """Test retrieving drift alerts."""
        # Create some alerts first
        reference = pd.DataFrame({"feature": np.random.normal(0, 1, 100)})
        current = pd.DataFrame({"feature": np.random.normal(2, 1, 100)})

        drift_detector.detect_data_drift(
            "test_model",
            "0.1.0",
            reference,
            current,
            threshold=0.1,
        )

        # Retrieve alerts
        alerts = drift_detector.get_drift_alerts(
            model_name="test_model",
            limit=10,
        )

        assert len(alerts) > 0


class TestValidationMetricsTracker:
    """Tests for Validation Metrics Tracker."""

    def test_log_metric(self, validation_tracker):
        """Test logging a metric."""
        metric = validation_tracker.log_metric(
            model_name="test_model",
            model_version="0.1.0",
            metric_name="accuracy",
            metric_value=0.95,
            metric_type=MetricType.CLASSIFICATION,
            dataset_split="test",
        )

        assert metric.metric_name == "accuracy"
        assert metric.metric_value == 0.95
        assert metric.id is not None

    def test_evaluate_classification(self, validation_tracker):
        """Test classification metrics evaluation."""
        y_true = [0, 1, 0, 1, 1, 0, 1, 0]
        y_pred = [0, 1, 0, 1, 0, 0, 1, 0]

        metrics = validation_tracker.evaluate_classification(
            "test_model",
            "0.1.0",
            y_true,
            y_pred,
            dataset_split="test",
        )

        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics
        assert metrics["accuracy"].metric_value > 0

    def test_evaluate_regression(self, validation_tracker):
        """Test regression metrics evaluation."""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.1, 2.1, 2.9, 4.2, 4.8]

        metrics = validation_tracker.evaluate_regression(
            "test_model",
            "0.1.0",
            y_true,
            y_pred,
            dataset_split="test",
        )

        assert "mae" in metrics
        assert "mse" in metrics
        assert "rmse" in metrics
        assert "r2" in metrics

    def test_get_metrics(self, validation_tracker):
        """Test retrieving metrics."""
        # Log some metrics first
        validation_tracker.log_metric(
            "test_model",
            "0.1.0",
            "accuracy",
            0.95,
            MetricType.CLASSIFICATION,
        )

        metrics = validation_tracker.get_metrics("test_model", model_version="0.1.0")
        assert len(metrics) > 0
        assert any(m.metric_name == "accuracy" for m in metrics)


class TestABTestManager:
    """Tests for A/B Testing."""

    def test_create_test(self, ab_test_manager):
        """Test creating an A/B test."""
        test = ab_test_manager.create_test(
            test_name="test_ab_1",
            model_a_name="model_a",
            model_a_version="1.0.0",
            model_b_name="model_b",
            model_b_version="1.1.0",
            success_metric="accuracy",
            created_by="test_user",
        )

        assert test.test_name == "test_ab_1"
        assert test.status == ABTestStatus.DRAFT
        assert test.id is not None

    def test_start_test(self, ab_test_manager):
        """Test starting an A/B test."""
        test = ab_test_manager.create_test(
            test_name="test_start",
            model_a_name="model_a",
            model_a_version="1.0.0",
            model_b_name="model_b",
            model_b_version="1.1.0",
            success_metric="accuracy",
        )

        started = ab_test_manager.start_test(test.id)
        assert started.status == ABTestStatus.RUNNING
        assert started.start_date is not None

    def test_evaluate_test(self, ab_test_manager):
        """Test evaluating A/B test results."""
        test = ab_test_manager.create_test(
            test_name="test_eval",
            model_a_name="model_a",
            model_a_version="1.0.0",
            model_b_name="model_b",
            model_b_version="1.1.0",
            success_metric="accuracy",
        )

        # Simulate results
        model_a_results = np.random.normal(0.85, 0.05, 100)
        model_b_results = np.random.normal(0.90, 0.05, 100)

        result = ab_test_manager.evaluate_test(
            test.id,
            model_a_results,
            model_b_results,
        )

        assert result.model_a_value < result.model_b_value
        assert result.difference > 0
        assert result.p_value is not None

    def test_list_tests(self, ab_test_manager):
        """Test listing A/B tests."""
        # Create some tests
        ab_test_manager.create_test(
            "test_1",
            "model_a", "1.0.0",
            "model_b", "1.1.0",
            "accuracy",
        )

        tests = ab_test_manager.list_tests()
        assert len(tests) > 0

