"""Biodiversity AI ensemble (mandatory component)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import logging
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


CLASS_LABELS = ["low", "moderate", "high", "very_high"]
logger = logging.getLogger(__name__)


@dataclass
class BiodiversityConfig:
    name: str = "biodiversity"
    version: str = "0.1.0"
    overlay_features: list[str] | None = None
    ml_features: list[str] | None = None
    candidate_models: list[str] | None = None
    thresholds: dict | None = None
    vector_fields: list[str] | None = None
    training_data_path: Optional[str] = None


class BiodiversityEnsemble:
    def __init__(self, config: BiodiversityConfig | None = None) -> None:
        self.config = config or BiodiversityConfig()
        self.vector_fields = self.config.vector_fields or [
            "protected_overlap_pct",
            "fragmentation_index",
            "forest_ratio",
            "protected_site_count",
            "protected_overlap_ha",
            "aoi_area_ha",
        ]
        self.training_data_path = Path(self.config.training_data_path) if self.config.training_data_path else None
        self._models = self._train_models()

    @staticmethod
    def _generate_training_data(n: int = 1500) -> Tuple[np.ndarray, np.ndarray]:
        rng = np.random.default_rng(42)
        protected_overlap_pct = rng.uniform(0, 60, size=n)
        fragmentation_index = rng.uniform(0, 1, size=n)
        forest_ratio = rng.uniform(0, 1, size=n)
        protected_site_count = rng.integers(0, 30, size=n)
        protected_overlap_ha = rng.uniform(0, 2000, size=n)
        aoi_area_ha = rng.uniform(10, 8000, size=n)

        X = np.column_stack(
            [
                protected_overlap_pct,
                fragmentation_index,
                forest_ratio,
                protected_site_count,
                protected_overlap_ha,
                aoi_area_ha,
            ]
        )

        severity = (
            protected_overlap_pct * 1.4
            + fragmentation_index * 40
            + forest_ratio * 20
            + protected_site_count * 1.5
            + (protected_overlap_ha / np.maximum(aoi_area_ha, 1)) * 80
        )
        bins = [-np.inf, 30, 60, 90, np.inf]
        y = np.digitize(severity, bins) - 1
        return X, y

    def _load_external_training_data(self) -> Tuple[np.ndarray, np.ndarray] | None:
        if not self.training_data_path:
            return None
        path = self.training_data_path
        if not path.exists():
            logger.warning("Biodiversity training data path %s not found. Falling back to synthetic data.", path)
            return None
        try:
            if path.suffix == ".parquet":
                df = pd.read_parquet(path)
            elif path.suffix in {".csv", ".tsv"}:
                df = pd.read_csv(path)
            else:
                logger.warning("Unsupported biodiversity training format %s. Falling back to synthetic.", path.suffix)
                return None
        except Exception as exc:
            logger.warning("Failed to load biodiversity training data: %s", exc)
            return None

        missing = [col for col in self.vector_fields if col not in df.columns]
        if missing:
            logger.warning("Training data missing columns %s. Falling back to synthetic data.", missing)
            return None

        label_column = None
        for candidate in ("label", "sensitivity", "target"):
            if candidate in df.columns:
                label_column = candidate
                break

        if not label_column:
            logger.warning("Training data lacks label column. Falling back to synthetic data.")
            return None

        label_map = {label: idx for idx, label in enumerate(CLASS_LABELS)}
        y = df[label_column].map(label_map).to_numpy()
        if np.isnan(y).any():
            logger.warning("Training labels contain unknown classes. Falling back to synthetic data.")
            return None

        X = df[self.vector_fields].to_numpy()
        return X, y.astype(int)

    def _train_models(self) -> List[Tuple[str, Any]]:
        external = self._load_external_training_data()
        if external:
            X, y = external
            logger.info("Loaded biodiversity training data from %s", self.training_data_path)
            dataset_source = str(self.training_data_path)
        else:
            X, y = self._generate_training_data()
            dataset_source = "synthetic"
        self.dataset_source = dataset_source

        models: List[Tuple[str, Any]] = []

        lr_pipeline = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=500, multi_class="multinomial")),
            ]
        )
        lr_pipeline.fit(X, y)
        models.append(("logistic_regression", lr_pipeline))

        rf = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=7)
        rf.fit(X, y)
        models.append(("random_forest", rf))

        gb = GradientBoostingClassifier(max_depth=3, random_state=21)
        gb.fit(X, y)
        models.append(("gradient_boosting", gb))

        return models

    def _vectorize(self, features: Dict[str, float]) -> np.ndarray:
        return np.array([float(features.get(field, 0.0)) for field in self.vector_fields])

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        x = self._vectorize(features)
        probabilities: List[np.ndarray] = []
        details: List[Dict[str, Any]] = []

        for name, model in self._models:
            proba = model.predict_proba([x])[0]
            probabilities.append(proba)
            pred_idx = int(np.argmax(proba))
            details.append(
                {
                    "model": name,
                    "prediction": CLASS_LABELS[pred_idx],
                    "confidence": float(proba[pred_idx]),
                }
            )

        avg_prob = np.mean(probabilities, axis=0)
        final_idx = int(np.argmax(avg_prob))
        score = float(np.dot(avg_prob, np.array([20, 50, 75, 95])))

        explanation = [
            f"Protected overlap {features.get('protected_overlap_pct', 0.0):.1f}%",
            f"Fragmentation index {features.get('fragmentation_index', 0.0):.2f}",
            f"Forest ratio {features.get('forest_ratio', 0.0):.2f}",
        ]

        return {
            "score": score,
            "sensitivity": CLASS_LABELS[final_idx],
            "confidence": float(avg_prob[final_idx]),
            "model_details": details,
            "features": features,
            "drivers": explanation,
            "dataset_source": getattr(self, "dataset_source", "synthetic"),
        }


class BiodiversityModel:
    def __init__(self, config: BiodiversityConfig | None = None) -> None:
        self.config = config or BiodiversityConfig()

    @cached_property
    def ensemble(self) -> BiodiversityEnsemble:
        return BiodiversityEnsemble(self.config)

    def predict(self, features: dict[str, float]) -> dict:
        return self.ensemble.predict(features)
