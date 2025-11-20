"""Validation Metrics Tracker: Track model performance metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

import numpy as np
from psycopg.types.json import Jsonb
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

from ..db.client import DatabaseClient


class MetricType(str, Enum):
    """Types of metrics."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    ENSEMBLE = "ensemble"


@dataclass
class ValidationMetric:
    """Represents a validation metric for a model."""

    model_name: str
    model_version: str
    metric_name: str
    metric_value: float
    metric_type: MetricType
    dataset_split: str | None = None
    metadata: dict[str, Any] | None = None
    evaluated_at: datetime | None = None
    id: UUID | None = None
    model_registry_id: UUID | None = None


class ValidationMetricsTracker:
    """Tracks validation metrics for model versions."""

    def __init__(self, db_client: DatabaseClient) -> None:
        """Initialize validation metrics tracker.

        Args:
            db_client: Database client for persistence
        """
        self.db_client = db_client

    def log_metric(
        self,
        model_name: str,
        model_version: str,
        metric_name: str,
        metric_value: float,
        metric_type: MetricType | str,
        dataset_split: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ValidationMetric:
        """Log a validation metric.

        Args:
            model_name: Model name
            model_version: Model version
            metric_name: Name of the metric (e.g., 'accuracy', 'f1', 'r2', 'mae')
            metric_value: Metric value
            metric_type: Type of metric
            dataset_split: Dataset split (e.g., 'train', 'validation', 'test')
            metadata: Additional metadata

        Returns:
            Logged validation metric
        """
        if isinstance(metric_type, str):
            metric_type = MetricType(metric_type)

        metric = ValidationMetric(
            model_name=model_name,
            model_version=model_version,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_type=metric_type,
            dataset_split=dataset_split,
            metadata=metadata,
            evaluated_at=datetime.now(timezone.utc),
        )

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Get model registry ID if available
                cur.execute(
                    "SELECT id FROM model_registry WHERE model_name = %s AND version = %s",
                    (model_name, model_version),
                )
                registry_row = cur.fetchone()
                registry_id = registry_row[0] if registry_row else None
                metric.model_registry_id = registry_id

                # Insert or update metric
                cur.execute(
                    """
                    INSERT INTO model_validation_metrics (
                        model_registry_id, model_name, model_version, metric_name,
                        metric_value, metric_type, dataset_split, metadata, evaluated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (model_registry_id, metric_name, dataset_split)
                    DO UPDATE SET
                        metric_value = EXCLUDED.metric_value,
                        metadata = EXCLUDED.metadata,
                        evaluated_at = EXCLUDED.evaluated_at
                    RETURNING id, evaluated_at
                    """,
                    (
                        registry_id,
                        metric.model_name,
                        metric.model_version,
                        metric.metric_name,
                        metric.metric_value,
                        metric_type.value,
                        metric.dataset_split,
                        Jsonb(metric.metadata) if metric.metadata else None,
                        metric.evaluated_at,
                    ),
                )
                row = cur.fetchone()
                metric.id = row[0]
                metric.evaluated_at = row[1]

        return metric

    def evaluate_classification(
        self,
        model_name: str,
        model_version: str,
        y_true: np.ndarray | list[int],
        y_pred: np.ndarray | list[int],
        dataset_split: str = "test",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, ValidationMetric]:
        """Evaluate classification metrics.

        Args:
            model_name: Model name
            model_version: Model version
            y_true: True labels
            y_pred: Predicted labels
            dataset_split: Dataset split
            metadata: Additional metadata

        Returns:
            Dictionary of logged metrics
        """
        y_true_array = np.array(y_true)
        y_pred_array = np.array(y_pred)

        metrics: dict[str, ValidationMetric] = {}

        # Calculate metrics
        accuracy = accuracy_score(y_true_array, y_pred_array)
        precision = precision_score(y_true_array, y_pred_array, average="weighted", zero_division=0)
        recall = recall_score(y_true_array, y_pred_array, average="weighted", zero_division=0)
        f1 = f1_score(y_true_array, y_pred_array, average="weighted", zero_division=0)

        # Log metrics
        metrics["accuracy"] = self.log_metric(
            model_name,
            model_version,
            "accuracy",
            float(accuracy),
            MetricType.CLASSIFICATION,
            dataset_split,
            metadata,
        )

        metrics["precision"] = self.log_metric(
            model_name,
            model_version,
            "precision",
            float(precision),
            MetricType.CLASSIFICATION,
            dataset_split,
            metadata,
        )

        metrics["recall"] = self.log_metric(
            model_name,
            model_version,
            "recall",
            float(recall),
            MetricType.CLASSIFICATION,
            dataset_split,
            metadata,
        )

        metrics["f1"] = self.log_metric(
            model_name,
            model_version,
            "f1",
            float(f1),
            MetricType.CLASSIFICATION,
            dataset_split,
            metadata,
        )

        return metrics

    def evaluate_regression(
        self,
        model_name: str,
        model_version: str,
        y_true: np.ndarray | list[float],
        y_pred: np.ndarray | list[float],
        dataset_split: str = "test",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, ValidationMetric]:
        """Evaluate regression metrics.

        Args:
            model_name: Model name
            model_version: Model version
            y_true: True values
            y_pred: Predicted values
            dataset_split: Dataset split
            metadata: Additional metadata

        Returns:
            Dictionary of logged metrics
        """
        y_true_array = np.array(y_true)
        y_pred_array = np.array(y_pred)

        metrics: dict[str, ValidationMetric] = {}

        # Calculate metrics
        mae = mean_absolute_error(y_true_array, y_pred_array)
        mse = mean_squared_error(y_true_array, y_pred_array)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true_array, y_pred_array)

        # Log metrics
        metrics["mae"] = self.log_metric(
            model_name,
            model_version,
            "mae",
            float(mae),
            MetricType.REGRESSION,
            dataset_split,
            metadata,
        )

        metrics["mse"] = self.log_metric(
            model_name,
            model_version,
            "mse",
            float(mse),
            MetricType.REGRESSION,
            dataset_split,
            metadata,
        )

        metrics["rmse"] = self.log_metric(
            model_name,
            model_version,
            "rmse",
            float(rmse),
            MetricType.REGRESSION,
            dataset_split,
            metadata,
        )

        metrics["r2"] = self.log_metric(
            model_name,
            model_version,
            "r2",
            float(r2),
            MetricType.REGRESSION,
            dataset_split,
            metadata,
        )

        return metrics

    def get_metrics(
        self,
        model_name: str,
        model_version: str | None = None,
        metric_name: str | None = None,
        dataset_split: str | None = None,
    ) -> list[ValidationMetric]:
        """Get validation metrics.

        Args:
            model_name: Model name
            model_version: Optional model version filter
            metric_name: Optional metric name filter
            dataset_split: Optional dataset split filter

        Returns:
            List of validation metrics
        """
        conditions = ["model_name = %s"]
        params: list[Any] = [model_name]

        if model_version:
            conditions.append("model_version = %s")
            params.append(model_version)

        if metric_name:
            conditions.append("metric_name = %s")
            params.append(metric_name)

        if dataset_split:
            conditions.append("dataset_split = %s")
            params.append(dataset_split)

        where_clause = "WHERE " + " AND ".join(conditions)

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, model_registry_id, model_name, model_version, metric_name,
                           metric_value, metric_type, dataset_split, metadata, evaluated_at
                    FROM model_validation_metrics
                    {where_clause}
                    ORDER BY evaluated_at DESC
                    """,
                    tuple(params),
                )
                rows = cur.fetchall()
                return [self._row_to_metric(row) for row in rows]

    def _row_to_metric(self, row: tuple) -> ValidationMetric:
        """Convert database row to ValidationMetric."""
        return ValidationMetric(
            id=row[0],
            model_registry_id=row[1],
            model_name=row[2],
            model_version=row[3],
            metric_name=row[4],
            metric_value=float(row[5]),
            metric_type=MetricType(row[6]),
            dataset_split=row[7],
            metadata=dict(row[8]) if row[8] else None,
            evaluated_at=row[9],
        )

