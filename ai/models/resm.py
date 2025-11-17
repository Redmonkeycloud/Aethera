"""Renewable/Resilience Environmental Suitability Model (RESM)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


logger = logging.getLogger(__name__)

# Suitability score labels (0-100 scale)
SUITABILITY_LABELS = ["very_low", "low", "moderate", "high", "very_high"]


@dataclass
class RESMConfig:
    """Configuration for RESM model."""

    name: str = "resm"
    version: str = "0.1.0"
    features: list[str] | None = None
    training_data_path: str | None = None


class RESMEnsemble:
    """Ensemble model for renewable energy suitability assessment."""

    def __init__(self, config: RESMConfig | None = None) -> None:
        self.config = config or RESMConfig()
        self.vector_fields = self.config.features or [
            "aoi_area_ha",
            "natural_habitat_ratio",
            "impervious_surface_ratio",
            "agricultural_ratio",
            "distance_to_protected_km",
            "protected_area_overlap_pct",
            "habitat_fragmentation_index",
            "connectivity_index",
            "ecosystem_service_value",
            "soil_erosion_risk",
            "distance_to_settlement_km",
            "resource_efficiency_index",
            "project_type_solar",
            "project_type_wind",
        ]
        self.training_data_path = (
            Path(self.config.training_data_path) if self.config.training_data_path else None
        )
        self._models = self._train_models()

    @staticmethod
    def _generate_training_data(n: int = 2000) -> tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data for RESM."""
        rng = np.random.default_rng(42)

        # Generate realistic feature distributions
        aoi_area_ha = rng.uniform(10, 10000, size=n)
        natural_habitat_ratio = rng.uniform(0, 1, size=n)
        impervious_ratio = rng.uniform(0, 0.8, size=n)
        agri_ratio = rng.uniform(0, 1, size=n)
        distance_to_protected_km = rng.exponential(5, size=n)
        protected_overlap_pct = rng.uniform(0, 50, size=n)
        fragmentation_index = rng.uniform(0, 1, size=n)
        connectivity_index = rng.uniform(0, 1, size=n)
        ecosystem_service_value = rng.uniform(0, 1, size=n)
        soil_erosion_risk = rng.uniform(0, 1, size=n)
        distance_to_settlement_km = rng.exponential(10, size=n)
        resource_efficiency = rng.uniform(0, 1, size=n)
        project_type_solar = rng.integers(0, 2, size=n)
        project_type_wind = 1 - project_type_solar

        X = np.column_stack(
            [
                aoi_area_ha,
                natural_habitat_ratio,
                impervious_ratio,
                agri_ratio,
                distance_to_protected_km,
                protected_overlap_pct,
                fragmentation_index,
                connectivity_index,
                ecosystem_service_value,
                soil_erosion_risk,
                distance_to_settlement_km,
                resource_efficiency,
                project_type_solar,
                project_type_wind,
            ]
        )

        # Suitability score (0-100): higher for agricultural land, lower for protected areas
        suitability = (
            agri_ratio * 40  # Agricultural land is suitable
            + (1.0 - natural_habitat_ratio) * 30  # Less natural = more suitable
            - protected_overlap_pct * 0.5  # Protected areas are constraints
            - distance_to_protected_km * 0.2  # Closer to protected = less suitable
            + (1.0 - impervious_ratio) * 20  # Less urban = more suitable
            + resource_efficiency * 15  # Higher efficiency = more suitable
            - soil_erosion_risk * 10  # Lower erosion risk = more suitable
            + (1.0 - fragmentation_index) * 5  # Less fragmented = more suitable
        )

        # Normalize to 0-100 range
        suitability = np.clip(suitability, 0, 100)

        return X, suitability

    def _load_external_training_data(self) -> tuple[np.ndarray, np.ndarray] | None:
        """Load external training data if available."""
        if not self.training_data_path:
            return None
        path = self.training_data_path
        if not path.exists():
            logger.warning("RESM training data path %s not found. Falling back to synthetic data.", path)
            return None
        try:
            if path.suffix == ".parquet":
                df = pd.read_parquet(path)
            elif path.suffix in {".csv", ".tsv"}:
                df = pd.read_csv(path)
            else:
                logger.warning("Unsupported RESM training format %s. Falling back to synthetic.", path.suffix)
                return None
        except Exception as exc:
            logger.warning("Failed to load RESM training data: %s", exc)
            return None

        missing = [col for col in self.vector_fields if col not in df.columns]
        if missing:
            logger.warning("Training data missing columns %s. Falling back to synthetic data.", missing)
            return None

        label_column = None
        for candidate in ("suitability_score", "label", "target", "score"):
            if candidate in df.columns:
                label_column = candidate
                break

        if not label_column:
            logger.warning("Training data lacks label column. Falling back to synthetic data.")
            return None

        y = df[label_column].to_numpy()
        if np.isnan(y).any() or (y < 0).any() or (y > 100).any():
            logger.warning("Training labels contain invalid values. Falling back to synthetic data.")
            return None

        X = df[self.vector_fields].to_numpy()
        return X, y.astype(float)

    def _train_models(self) -> list[tuple[str, Any]]:
        """Train ensemble of regression models."""
        external = self._load_external_training_data()
        if external:
            X, y = external
            logger.info("Loaded RESM training data from %s", self.training_data_path)
            dataset_source = str(self.training_data_path)
        else:
            X, y = self._generate_training_data()
            dataset_source = "synthetic"
        self.dataset_source = dataset_source

        models: list[tuple[str, Any]] = []

        # Ridge Regression (linear baseline)
        ridge_pipeline = Pipeline([("scaler", StandardScaler()), ("reg", Ridge(alpha=1.0))])
        ridge_pipeline.fit(X, y)
        models.append(("ridge_regression", ridge_pipeline))

        # Random Forest
        rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=7)
        rf.fit(X, y)
        models.append(("random_forest", rf))

        # Gradient Boosting
        gb = GradientBoostingRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.1, random_state=21
        )
        gb.fit(X, y)
        models.append(("gradient_boosting", gb))

        return models

    def _vectorize(self, features: dict[str, float]) -> np.ndarray:
        """Convert feature dictionary to vector."""
        return np.array([float(features.get(field, 0.0)) for field in self.vector_fields])

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        """
        Predict renewable energy suitability score.

        Returns:
            Dictionary with suitability score (0-100), category, confidence, and model details
        """
        x = self._vectorize(features)
        predictions: list[float] = []
        details: list[dict[str, Any]] = []

        for name, model in self._models:
            pred = model.predict([x])[0]
            pred = float(np.clip(pred, 0, 100))  # Ensure 0-100 range
            predictions.append(pred)

            # Calculate confidence based on prediction variance (simplified)
            confidence = 0.8 if hasattr(model, "feature_importances_") else 0.7

            details.append(
                {
                    "model": name,
                    "prediction": pred,
                    "confidence": confidence,
                }
            )

        # Ensemble prediction (average)
        final_score = float(np.mean(predictions))
        final_confidence = float(np.mean([d["confidence"] for d in details]))

        # Categorize suitability
        if final_score < 20:
            category = "very_low"
        elif final_score < 40:
            category = "low"
        elif final_score < 60:
            category = "moderate"
        elif final_score < 80:
            category = "high"
        else:
            category = "very_high"

        # Key drivers (simplified - would use SHAP values in production)
        drivers = []
        if features.get("agricultural_ratio", 0) > 0.5:
            drivers.append("High agricultural land ratio (suitable for development)")
        if features.get("distance_to_protected_km", 999) > 10:
            drivers.append("Sufficient distance from protected areas")
        if features.get("soil_erosion_risk", 1) < 0.3:
            drivers.append("Low soil erosion risk")
        if not drivers:
            drivers.append("Moderate suitability based on land use characteristics")

        return {
            "score": final_score,
            "category": category,
            "confidence": final_confidence,
            "model_details": details,
            "features": features,
            "drivers": drivers,
            "dataset_source": getattr(self, "dataset_source", "synthetic"),
        }


class RESMModel:
    """Main RESM model interface."""

    def __init__(self, config: RESMConfig | None = None) -> None:
        self.config = config or RESMConfig()

    @cached_property
    def ensemble(self) -> RESMEnsemble:
        """Lazy-load ensemble model."""
        return RESMEnsemble(self.config)

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        """Predict suitability score."""
        return self.ensemble.predict(features)
