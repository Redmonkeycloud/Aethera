"""Cumulative Impact Model (CIM) - integrates RESM, AHSM, and biodiversity scores."""

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

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    xgb = None  # type: ignore[assignment, misc]

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    lgb = None  # type: ignore[assignment, misc]

from .pretrained import load_pretrained_bundle


logger = logging.getLogger(__name__)

# Cumulative impact level labels
IMPACT_LABELS = ["negligible", "low", "moderate", "high", "very_high"]


@dataclass
class CIMConfig:
    """Configuration for CIM model."""

    name: str = "cim"
    version: str = "0.1.0"
    inputs: list[str] | None = None
    training_data_path: str | None = None
    use_pretrained: bool = True


class CIMEnsemble:
    """Ensemble model for cumulative impact assessment."""

    def __init__(self, config: CIMConfig | None = None) -> None:
        self.config = config or CIMConfig()
        self.vector_fields = self.config.inputs or [
            "resm_score",
            "ahsm_score",
            "biodiversity_score",
            "distance_to_protected_km",
            "protected_overlap_pct",
            "habitat_fragmentation_index",
            "connectivity_index",
            "ecosystem_service_value",
            "ghg_emissions_intensity",
            "net_carbon_balance",
            "land_use_efficiency",
            "natural_habitat_ratio",
            "soil_erosion_risk",
            "water_regulation_capacity",
        ]
        self.training_data_path = (
            Path(self.config.training_data_path) if self.config.training_data_path else None
        )
        self._models = self._load_or_train_models()

    def _load_or_train_models(self) -> list[tuple[str, Any]]:
        if self.config.use_pretrained:
            bundle = load_pretrained_bundle(self.config.name, here_file=__file__)
            if bundle is not None:
                if bundle.vector_fields:
                    self.vector_fields = bundle.vector_fields
                trained_on = bundle.dataset_source or "unknown"
                self.dataset_source = f"pretrained:{bundle.model_path} (trained_on={trained_on})"
                return bundle.models
        return self._train_models()

    @staticmethod
    def _generate_training_data(n: int = 2500) -> tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data for CIM."""
        rng = np.random.default_rng(42)

        # Generate realistic feature distributions
        resm_score = rng.uniform(0, 100, size=n)
        ahsm_score = rng.uniform(0, 100, size=n)
        biodiversity_score = rng.uniform(0, 100, size=n)
        distance_to_protected_km = rng.exponential(5, size=n)
        protected_overlap_pct = rng.uniform(0, 50, size=n)
        fragmentation_index = rng.uniform(0, 1, size=n)
        connectivity_index = rng.uniform(0, 1, size=n)
        ecosystem_service_value = rng.uniform(0, 1, size=n)
        ghg_intensity = rng.uniform(0, 500, size=n)
        net_carbon_balance = rng.uniform(-1000, 1000, size=n)
        land_use_efficiency = rng.uniform(0, 10, size=n)
        natural_habitat_ratio = rng.uniform(0, 1, size=n)
        soil_erosion_risk = rng.uniform(0, 1, size=n)
        water_regulation = rng.uniform(0, 1, size=n)

        X = np.column_stack(
            [
                resm_score,
                ahsm_score,
                biodiversity_score,
                distance_to_protected_km,
                protected_overlap_pct,
                fragmentation_index,
                connectivity_index,
                ecosystem_service_value,
                ghg_intensity,
                net_carbon_balance,
                land_use_efficiency,
                natural_habitat_ratio,
                soil_erosion_risk,
                water_regulation,
            ]
        )

        # Cumulative impact: higher when multiple stressors are high
        impact_score = (
            (100 - biodiversity_score) * 0.3  # Low biodiversity = high impact
            + ahsm_score * 0.25  # High hazard risk = high impact
            + protected_overlap_pct * 0.2  # Protected area overlap = high impact
            + (1.0 - connectivity_index) * 0.15  # Low connectivity = high impact
            + fragmentation_index * 0.1  # High fragmentation = impact
            + (ghg_intensity / 10) * 0.1  # High emissions = impact
            - (ecosystem_service_value * 20)  # High service value = lower impact
        )

        # Normalize and categorize
        impact_score = np.clip(impact_score, 0, 100)
        bins = [0, 20, 40, 60, 80, 100]
        y = np.digitize(impact_score, bins) - 1

        return X, y

    def _load_external_training_data(self) -> tuple[np.ndarray, np.ndarray] | None:
        """Load external training data if available."""
        if not self.training_data_path:
            return None
        path = self.training_data_path
        if not path.exists():
            logger.warning("CIM training data path %s not found. Falling back to synthetic data.", path)
            return None
        try:
            if path.suffix == ".parquet":
                df = pd.read_parquet(path)
            elif path.suffix in {".csv", ".tsv"}:
                df = pd.read_csv(path)
            else:
                logger.warning("Unsupported CIM training format %s. Falling back to synthetic.", path.suffix)
                return None
        except Exception as exc:
            logger.warning("Failed to load CIM training data: %s", exc)
            return None

        missing = [col for col in self.vector_fields if col not in df.columns]
        if missing:
            logger.warning("Training data missing columns %s. Falling back to synthetic data.", missing)
            return None

        label_column = None
        for candidate in ("cumulative_impact_class", "impact_level", "label", "target"):
            if candidate in df.columns:
                label_column = candidate
                break

        if not label_column:
            logger.warning("Training data lacks label column. Falling back to synthetic data.")
            return None

        label_map = {label: idx for idx, label in enumerate(IMPACT_LABELS)}
        if df[label_column].dtype == "object":
            y = df[label_column].map(label_map).to_numpy()
        else:
            y = df[label_column].to_numpy()

        if np.isnan(y).any() or (y < 0).any() or (y >= len(IMPACT_LABELS)).any():
            logger.warning("Training labels contain invalid values. Falling back to synthetic data.")
            return None

        X = df[self.vector_fields].to_numpy()
        return X, y.astype(int)

    def _train_models(self) -> list[tuple[str, Any]]:
        """Train ensemble of classification models."""
        external = self._load_external_training_data()
        if external:
            X, y = external
            logger.info("Loaded CIM training data from %s", self.training_data_path)
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

        # XGBoost (if available)
        if XGBOOST_AVAILABLE:
            try:
                n_classes = len(np.unique(y))
                xgb_objective = "binary:logistic" if n_classes == 2 else "multi:softprob"
                xgb_model = xgb.XGBClassifier(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    objective=xgb_objective,
                    random_state=21,
                    n_jobs=-1,
                    eval_metric="mlogloss" if n_classes > 2 else "logloss",
                )
                xgb_model.fit(X, y)
                models.append(("xgboost", xgb_model))
                logger.info("XGBoost model added to ensemble")
            except Exception as e:
                logger.warning(f"Failed to train XGBoost model: {e}")
        else:
            logger.debug("XGBoost not available. Install with: pip install xgboost")

        # LightGBM (if available)
        if LIGHTGBM_AVAILABLE:
            try:
                n_classes = len(np.unique(y))
                lgb_objective = "binary" if n_classes == 2 else "multiclass"
                lgb_metric = "binary_logloss" if n_classes == 2 else "multi_logloss"
                lgb_model = lgb.LGBMClassifier(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    objective=lgb_objective,
                    metric=lgb_metric,
                    random_state=21,
                    n_jobs=-1,
                    verbose=-1,
                )
                lgb_model.fit(X, y)
                models.append(("lightgbm", lgb_model))
                logger.info("LightGBM model added to ensemble")
            except Exception as e:
                logger.warning(f"Failed to train LightGBM model: {e}")
        else:
            logger.debug("LightGBM not available. Install with: pip install lightgbm")

        return models

    def _vectorize(self, features: dict[str, float]) -> np.ndarray:
        """Convert feature dictionary to vector."""
        return np.array([float(features.get(field, 0.0)) for field in self.vector_fields])

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        """
        Predict cumulative impact level.

        Returns:
            Dictionary with impact score (0-100), category, confidence, and model details
        """
        x = self._vectorize(features)
        probabilities: list[np.ndarray] = []
        details: list[dict[str, Any]] = []

        for name, model in self._models:
            proba = model.predict_proba([x])[0]
            probabilities.append(proba)
            pred_idx = int(np.argmax(proba))
            # Map prediction index to label (handle case where model has different number of classes)
            if pred_idx < len(IMPACT_LABELS):
                pred_label = IMPACT_LABELS[pred_idx]
            else:
                pred_label = f"class_{pred_idx}"  # Fallback label
            details.append(
                {
                    "model": name,
                    "prediction": pred_label,
                    "confidence": float(proba[pred_idx]),
                }
            )

        # Ensemble prediction (average probabilities)
        avg_prob = np.mean(probabilities, axis=0)
        final_idx = int(np.argmax(avg_prob))
        # Score array must match number of classes in IMPACT_LABELS (5 classes)
        score_values = np.array([10, 30, 50, 75, 95])
        if len(avg_prob) != len(score_values):
            # Adjust score_values to match actual number of classes
            n_classes = len(avg_prob)
            score_values = np.linspace(10, 95, n_classes)
        impact_score = float(np.dot(avg_prob, score_values))

        # Key drivers
        drivers = []
        if features.get("biodiversity_score", 100) < 40:
            drivers.append("High biodiversity sensitivity")
        if features.get("ahsm_score", 0) > 70:
            drivers.append("High hazard susceptibility")
        if features.get("protected_overlap_pct", 0) > 10:
            drivers.append("Significant protected area overlap")
        if features.get("ghg_emissions_intensity", 0) > 200:
            drivers.append("High GHG emissions intensity")
        if features.get("connectivity_index", 1) < 0.3:
            drivers.append("Low ecological connectivity")
        if not drivers:
            drivers.append("Moderate cumulative impact based on multiple factors")

        # Map category index to label (handle case where model has different number of classes)
        if final_idx < len(IMPACT_LABELS):
            category = IMPACT_LABELS[final_idx]
        else:
            # Fallback if index is out of bounds
            category = IMPACT_LABELS[-1] if IMPACT_LABELS else "unknown"
            logger.warning("CIM prediction index %d out of bounds for IMPACT_LABELS. Using fallback.", final_idx)
        
        return {
            "score": impact_score,
            "category": category,
            "confidence": float(avg_prob[final_idx]),
            "model_details": details,
            "features": features,
            "drivers": drivers,
            "dataset_source": getattr(self, "dataset_source", "synthetic"),
        }


class CIMModel:
    """Main CIM model interface."""

    def __init__(self, config: CIMConfig | None = None) -> None:
        self.config = config or CIMConfig()

    @cached_property
    def ensemble(self) -> CIMEnsemble:
        """Lazy-load ensemble model."""
        return CIMEnsemble(self.config)

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        """Predict cumulative impact."""
        return self.ensemble.predict(features)
