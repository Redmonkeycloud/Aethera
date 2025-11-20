"""Drift Detection: Monitor data and concept drift for ML models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

import numpy as np
import pandas as pd
from psycopg.types.json import Jsonb
from scipy import stats

from ..db.client import DatabaseClient


class DriftType(str, Enum):
    """Types of drift to detect."""

    DATA_DRIFT = "data_drift"  # Distribution shift in input features
    CONCEPT_DRIFT = "concept_drift"  # Relationship between features and target changes
    PREDICTION_DRIFT = "prediction_drift"  # Distribution shift in predictions


@dataclass
class DriftAlert:
    """Represents a drift detection alert."""

    model_name: str
    model_version: str
    drift_type: DriftType
    feature_name: str | None
    drift_score: float
    threshold: float
    is_alert: bool
    reference_statistics: dict[str, Any]
    current_statistics: dict[str, Any]
    detection_method: str
    sample_size: int
    detected_at: datetime
    id: UUID | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None


class DriftDetector:
    """Detects data and concept drift for ML models."""

    def __init__(self, db_client: DatabaseClient) -> None:
        """Initialize drift detector.

        Args:
            db_client: Database client for persistence
        """
        self.db_client = db_client

    def detect_data_drift(
        self,
        model_name: str,
        model_version: str,
        reference_data: pd.DataFrame | dict[str, Any],
        current_data: pd.DataFrame | dict[str, Any],
        threshold: float = 0.2,
        method: str = "ks_test",
    ) -> list[DriftAlert]:
        """Detect data drift in input features.

        Args:
            model_name: Model name
            model_version: Model version
            reference_data: Baseline/reference data (DataFrame or dict of feature arrays)
            current_data: Current data to compare
            threshold: Alert threshold (0-1)
            method: Detection method ('ks_test', 'psi', 'chi_square')

        Returns:
            List of drift alerts (one per feature if drift detected)
        """
        alerts: list[DriftAlert] = []

        # Convert dict to DataFrame if needed
        if isinstance(reference_data, dict):
            reference_df = pd.DataFrame(reference_data)
        else:
            reference_df = reference_data

        if isinstance(current_data, dict):
            current_df = pd.DataFrame(current_data)
        else:
            current_df = current_data

        # Detect drift for each feature
        for feature in reference_df.columns:
            if feature not in current_df.columns:
                continue

            ref_values = reference_df[feature].dropna()
            curr_values = current_df[feature].dropna()

            if len(ref_values) == 0 or len(curr_values) == 0:
                continue

            # Calculate drift score based on method
            drift_score = self._calculate_drift_score(ref_values, curr_values, method)

            # Calculate statistics
            ref_stats = self._calculate_statistics(ref_values)
            curr_stats = self._calculate_statistics(curr_values)

            is_alert = drift_score > threshold

            alert = DriftAlert(
                model_name=model_name,
                model_version=model_version,
                drift_type=DriftType.DATA_DRIFT,
                feature_name=feature,
                drift_score=float(drift_score),
                threshold=threshold,
                is_alert=is_alert,
                reference_statistics=ref_stats,
                current_statistics=curr_stats,
                detection_method=method,
                sample_size=len(curr_values),
                detected_at=datetime.now(timezone.utc),
            )

            alerts.append(alert)

            # Persist to database
            self._save_drift_alert(alert)

        return alerts

    def detect_prediction_drift(
        self,
        model_name: str,
        model_version: str,
        reference_predictions: np.ndarray | list[float],
        current_predictions: np.ndarray | list[float],
        threshold: float = 0.2,
        method: str = "ks_test",
    ) -> DriftAlert | None:
        """Detect drift in model predictions.

        Args:
            model_name: Model name
            model_version: Model version
            reference_predictions: Baseline predictions
            current_predictions: Current predictions
            threshold: Alert threshold
            method: Detection method

        Returns:
            Drift alert if drift detected, None otherwise
        """
        ref_array = np.array(reference_predictions)
        curr_array = np.array(current_predictions)

        if len(ref_array) == 0 or len(curr_array) == 0:
            return None

        drift_score = self._calculate_drift_score(ref_array, curr_array, method)
        ref_stats = self._calculate_statistics(ref_array)
        curr_stats = self._calculate_statistics(curr_array)

        is_alert = drift_score > threshold

        alert = DriftAlert(
            model_name=model_name,
            model_version=model_version,
            drift_type=DriftType.PREDICTION_DRIFT,
            feature_name=None,
            drift_score=float(drift_score),
            threshold=threshold,
            is_alert=is_alert,
            reference_statistics=ref_stats,
            current_statistics=curr_stats,
            detection_method=method,
            sample_size=len(curr_array),
            detected_at=datetime.now(timezone.utc),
        )

        self._save_drift_alert(alert)
        return alert if is_alert else None

    def get_drift_alerts(
        self,
        model_name: str | None = None,
        model_version: str | None = None,
        drift_type: DriftType | str | None = None,
        is_alert: bool | None = None,
        limit: int = 100,
    ) -> list[DriftAlert]:
        """Get drift alerts from database.

        Args:
            model_name: Filter by model name
            model_version: Filter by model version
            drift_type: Filter by drift type
            is_alert: Filter by alert status
            limit: Maximum number of results

        Returns:
            List of drift alerts
        """
        conditions = []
        params: list[Any] = []

        if model_name:
            conditions.append("model_name = %s")
            params.append(model_name)

        if model_version:
            conditions.append("model_version = %s")
            params.append(model_version)

        if drift_type:
            drift_type_value = drift_type.value if isinstance(drift_type, DriftType) else drift_type
            conditions.append("drift_type = %s")
            params.append(drift_type_value)

        if is_alert is not None:
            conditions.append("is_alert = %s")
            params.append(is_alert)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        params.append(limit)

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, model_name, model_version, drift_type, feature_name,
                           drift_score, threshold, is_alert, reference_statistics,
                           current_statistics, detection_method, sample_size,
                           detected_at, acknowledged_at, acknowledged_by
                    FROM model_drift_detection
                    {where_clause}
                    ORDER BY detected_at DESC
                    LIMIT %s
                    """,
                    tuple(params),
                )
                rows = cur.fetchall()
                return [self._row_to_alert(row) for row in rows]

    def acknowledge_alert(self, alert_id: UUID, acknowledged_by: str) -> None:
        """Acknowledge a drift alert.

        Args:
            alert_id: Alert ID
            acknowledged_by: User acknowledging the alert
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE model_drift_detection
                    SET acknowledged_at = %s, acknowledged_by = %s
                    WHERE id = %s
                    """,
                    (datetime.now(timezone.utc), acknowledged_by, alert_id),
                )

    def _calculate_drift_score(
        self,
        reference: np.ndarray | pd.Series,
        current: np.ndarray | pd.Series,
        method: str,
    ) -> float:
        """Calculate drift score between reference and current distributions.

        Args:
            reference: Reference data
            current: Current data
            method: Detection method

        Returns:
            Drift score (0-1, higher = more drift)
        """
        if method == "ks_test":
            # Kolmogorov-Smirnov test statistic
            statistic, _ = stats.ks_2samp(reference, current)
            return float(statistic)

        elif method == "psi":
            # Population Stability Index
            return self._calculate_psi(reference, current)

        elif method == "chi_square":
            # Chi-square test (for categorical data)
            if isinstance(reference, pd.Series):
                ref_counts = reference.value_counts()
                curr_counts = current.value_counts()
            else:
                ref_counts = pd.Series(reference).value_counts()
                curr_counts = pd.Series(current).value_counts()

            # Align indices
            all_categories = ref_counts.index.union(curr_counts.index)
            ref_counts = ref_counts.reindex(all_categories, fill_value=0)
            curr_counts = curr_counts.reindex(all_categories, fill_value=0)

            # Chi-square test
            chi2, _ = stats.chisquare(curr_counts, ref_counts)
            # Normalize to 0-1 range (approximate)
            return min(1.0, float(chi2) / 100.0)

        else:
            raise ValueError(f"Unknown drift detection method: {method}")

    @staticmethod
    def _calculate_psi(reference: np.ndarray | pd.Series, current: np.ndarray | pd.Series) -> float:
        """Calculate Population Stability Index (PSI).

        Args:
            reference: Reference data
            current: Current data

        Returns:
            PSI value (higher = more drift, typically > 0.2 indicates drift)
        """
        # Create bins based on reference data
        _, bin_edges = np.histogram(reference, bins=10)
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf

        # Calculate distributions
        ref_counts, _ = np.histogram(reference, bins=bin_edges)
        curr_counts, _ = np.histogram(current, bins=bin_edges)

        # Normalize to probabilities
        ref_probs = ref_counts / len(reference)
        curr_probs = curr_counts / len(current)

        # Avoid division by zero
        ref_probs = np.where(ref_probs == 0, 0.0001, ref_probs)
        curr_probs = np.where(curr_probs == 0, 0.0001, curr_probs)

        # Calculate PSI
        psi = np.sum((curr_probs - ref_probs) * np.log(curr_probs / ref_probs))
        return float(psi)

    @staticmethod
    def _calculate_statistics(data: np.ndarray | pd.Series) -> dict[str, Any]:
        """Calculate summary statistics for data.

        Args:
            data: Data array or series

        Returns:
            Dictionary of statistics
        """
        if isinstance(data, pd.Series):
            array = data.values
        else:
            array = data

        return {
            "mean": float(np.mean(array)),
            "std": float(np.std(array)),
            "min": float(np.min(array)),
            "max": float(np.max(array)),
            "median": float(np.median(array)),
            "q25": float(np.percentile(array, 25)),
            "q75": float(np.percentile(array, 75)),
            "count": int(len(array)),
        }

    def _save_drift_alert(self, alert: DriftAlert) -> None:
        """Save drift alert to database."""
        # Get model_registry_id if available
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Try to find model registry ID
                cur.execute(
                    "SELECT id FROM model_registry WHERE model_name = %s AND version = %s",
                    (alert.model_name, alert.model_version),
                )
                registry_row = cur.fetchone()
                registry_id = registry_row[0] if registry_row else None

                # Insert drift alert
                cur.execute(
                    """
                    INSERT INTO model_drift_detection (
                        id, model_registry_id, model_name, model_version, drift_type,
                        feature_name, drift_score, threshold, is_alert,
                        reference_statistics, current_statistics, detection_method,
                        sample_size, detected_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                    """,
                    (
                        alert.id if alert.id else None,
                        registry_id,
                        alert.model_name,
                        alert.model_version,
                        alert.drift_type.value,
                        alert.feature_name,
                        alert.drift_score,
                        alert.threshold,
                        alert.is_alert,
                        Jsonb(alert.reference_statistics),
                        Jsonb(alert.current_statistics),
                        alert.detection_method,
                        alert.sample_size,
                        alert.detected_at,
                    ),
                )
                row = cur.fetchone()
                alert.id = row[0]

    def _row_to_alert(self, row: tuple) -> DriftAlert:
        """Convert database row to DriftAlert."""
        return DriftAlert(
            id=row[0],
            model_name=row[1],
            model_version=row[2],
            drift_type=DriftType(row[3]),
            feature_name=row[4],
            drift_score=float(row[5]),
            threshold=float(row[6]),
            is_alert=bool(row[7]),
            reference_statistics=dict(row[8]) if row[8] else {},
            current_statistics=dict(row[9]) if row[9] else {},
            detection_method=row[10],
            sample_size=int(row[11]),
            detected_at=row[12],
            acknowledged_at=row[13],
            acknowledged_by=row[14],
        )

