"""Asset Hazard Susceptibility Model (AHSM)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


logger = logging.getLogger(__name__)

# Risk level labels
RISK_LABELS = ["very_low", "low", "moderate", "high", "very_high"]


@dataclass
class AHSMConfig:
    """Configuration for AHSM model."""

    name: str = "ahsm"
    version: str = "0.1.0"
    hazard_types: list[str] | None = None
    training_data_path: str | None = None


class AHSMEnsemble:
    """Ensemble model for hazard susceptibility assessment."""

    def __init__(self, config: AHSMConfig | None = None) -> None:
        self.config = config or AHSMConfig()
        self.hazard_types = self.config.hazard_types or ["flood", "wildfire", "landslide"]
        self.vector_fields = [
            "aoi_area_ha",
            "forest_ratio",
            "water_ratio",
            "impervious_ratio",
            "agricultural_ratio",
            "habitat_fragmentation_index",
            "edge_density",
            "patch_density",
            "water_regulation_capacity",
            "soil_erosion_risk",
            "distance_to_water_km",
            "ecosystem_service_value",
            "connectivity_index",
        ]
        self.training_data_path = (
            Path(self.config.training_data_path) if self.config.training_data_path else None
        )
        self._models = self._train_models()

    @staticmethod
    def _generate_training_data(n: int = 2000) -> tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data for AHSM."""
        rng = np.random.default_rng(42)

        # Generate realistic feature distributions
        aoi_area_ha = rng.uniform(10, 10000, size=n)
        forest_ratio = rng.uniform(0, 1, size=n)
        water_ratio = rng.uniform(0, 0.5, size=n)
        impervious_ratio = rng.uniform(0, 0.8, size=n)
        agri_ratio = rng.uniform(0, 1, size=n)
        fragmentation_index = rng.uniform(0, 1, size=n)
        edge_density = rng.uniform(0, 500, size=n)
        patch_density = rng.uniform(0, 50, size=n)
        water_regulation = rng.uniform(0, 1, size=n)
        soil_erosion_risk = rng.uniform(0, 1, size=n)
        distance_to_water_km = rng.exponential(5, size=n)
        ecosystem_service_value = rng.uniform(0, 1, size=n)
        connectivity_index = rng.uniform(0, 1, size=n)

        X = np.column_stack(
            [
                aoi_area_ha,
                forest_ratio,
                water_ratio,
                impervious_ratio,
                agri_ratio,
                fragmentation_index,
                edge_density,
                patch_density,
                water_regulation,
                soil_erosion_risk,
                distance_to_water_km,
                ecosystem_service_value,
                connectivity_index,
            ]
        )

        # Risk score: higher for areas with high water ratio, erosion risk, low regulation
        risk_score = (
            water_ratio * 30  # High water = flood risk
            + soil_erosion_risk * 25  # High erosion = landslide risk
            + (1.0 - water_regulation) * 20  # Low regulation = flood risk
            + impervious_ratio * 15  # High impervious = runoff/flood risk
            + forest_ratio * 10  # Forests = wildfire risk (moderate)
            - connectivity_index * 5  # Low connectivity = higher vulnerability
            + (distance_to_water_km < 1.0) * 15  # Very close to water = flood risk
        )

        # Normalize and categorize
        risk_score = np.clip(risk_score, 0, 100)
        bins = [0, 20, 40, 60, 80, 100]
        y = np.digitize(risk_score, bins) - 1

        return X, y

    def _load_external_training_data(self) -> tuple[np.ndarray, np.ndarray] | None:
        """Load external training data if available."""
        if not self.training_data_path:
            return None
        path = self.training_data_path
        if not path.exists():
            logger.warning("AHSM training data path %s not found. Falling back to synthetic data.", path)
            return None
        try:
            if path.suffix == ".parquet":
                df = pd.read_parquet(path)
            elif path.suffix in {".csv", ".tsv"}:
                df = pd.read_csv(path)
            else:
                logger.warning("Unsupported AHSM training format %s. Falling back to synthetic.", path.suffix)
                return None
        except Exception as exc:
            logger.warning("Failed to load AHSM training data: %s", exc)
            return None

        missing = [col for col in self.vector_fields if col not in df.columns]
        if missing:
            logger.warning("Training data missing columns %s. Falling back to synthetic data.", missing)
            return None

        label_column = None
        for candidate in ("hazard_risk", "risk_level", "label", "target"):
            if candidate in df.columns:
                label_column = candidate
                break

        if not label_column:
            logger.warning("Training data lacks label column. Falling back to synthetic data.")
            return None

        label_map = {label: idx for idx, label in enumerate(RISK_LABELS)}
        if df[label_column].dtype == "object":
            y = df[label_column].map(label_map).to_numpy()
        else:
            y = df[label_column].to_numpy()

        if np.isnan(y).any() or (y < 0).any() or (y >= len(RISK_LABELS)).any():
            logger.warning("Training labels contain invalid values. Falling back to synthetic data.")
            return None

        X = df[self.vector_fields].to_numpy()
        return X, y.astype(int)

    def _train_models(self) -> list[tuple[str, Any]]:
        """Train ensemble of classification models."""
        external = self._load_external_training_data()
        if external:
            X, y = external
            logger.info("Loaded AHSM training data from %s", self.training_data_path)
            dataset_source = str(self.training_data_path)
        else:
            X, y = self._generate_training_data()
            dataset_source = "synthetic"
        self.dataset_source = dataset_source

        # Check that we have at least 2 classes
        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            logger.warning(
                "Training data contains only %d class(es): %s. Using synthetic data instead.",
                len(unique_classes), unique_classes
            )
            X, y = self._generate_training_data()
            dataset_source = "synthetic (fallback)"
            self.dataset_source = dataset_source

        models: list[tuple[str, Any]] = []

        # Logistic Regression
        lr_pipeline = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=500)),
            ]
        )
        lr_pipeline.fit(X, y)
        models.append(("logistic_regression", lr_pipeline))

        # Random Forest
        rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=7)
        rf.fit(X, y)
        models.append(("random_forest", rf))

        # Gradient Boosting
        gb = GradientBoostingClassifier(
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
        Predict hazard susceptibility risk level.

        Returns:
            Dictionary with risk score (0-100), category, confidence, and model details
        """
        x = self._vectorize(features)
        probabilities: list[np.ndarray] = []
        details: list[dict[str, Any]] = []

        for name, model in self._models:
            proba = model.predict_proba([x])[0]
            probabilities.append(proba)
            pred_idx = int(np.argmax(proba))
            details.append(
                {
                    "model": name,
                    "prediction": RISK_LABELS[pred_idx],
                    "confidence": float(proba[pred_idx]),
                }
            )

        # Ensemble prediction (average probabilities)
        avg_prob = np.mean(probabilities, axis=0)
        final_idx = int(np.argmax(avg_prob))
        risk_score = float(np.dot(avg_prob, np.array([10, 30, 50, 75, 95])))

        # Key drivers
        drivers = []
        if features.get("water_ratio", 0) > 0.2:
            drivers.append("High water body ratio (flood risk)")
        if features.get("soil_erosion_risk", 0) > 0.6:
            drivers.append("High soil erosion risk (landslide susceptibility)")
        if features.get("water_regulation_capacity", 1) < 0.4:
            drivers.append("Low water regulation capacity (flood vulnerability)")
        if features.get("impervious_ratio", 0) > 0.5:
            drivers.append("High impervious surface ratio (runoff/flood risk)")
        if not drivers:
            drivers.append("Moderate hazard susceptibility based on land characteristics")

        return {
            "score": risk_score,
            "category": RISK_LABELS[final_idx],
            "confidence": float(avg_prob[final_idx]),
            "model_details": details,
            "features": features,
            "drivers": drivers,
            "hazard_types": self.hazard_types,
            "dataset_source": getattr(self, "dataset_source", "synthetic"),
        }


class AHSMModel:
    """Main AHSM model interface."""

    def __init__(self, config: AHSMConfig | None = None) -> None:
        self.config = config or AHSMConfig()

    @cached_property
    def ensemble(self) -> AHSMEnsemble:
        """Lazy-load ensemble model."""
        return AHSMEnsemble(self.config)

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        """Predict hazard susceptibility."""
        return self.ensemble.predict(features)
