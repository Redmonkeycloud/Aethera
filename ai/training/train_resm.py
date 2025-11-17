"""Training pipeline for RESM (Renewable/Resilience Suitability Model)."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ..models.resm import RESMEnsemble
from .base import BaseTrainer, TrainingConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_training_data(data_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load training data from CSV or Parquet."""
    if data_path.suffix == ".parquet":
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)

    # Find label column
    label_column = None
    for candidate in ("suitability_score", "label", "target", "score"):
        if candidate in df.columns:
            label_column = candidate
            break

    if not label_column:
        raise ValueError(f"No label column found in {data_path}")

    y = df[label_column].to_numpy()

    # Get feature columns
    feature_columns = [
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
    X = df[[col for col in feature_columns if col in df.columns]].to_numpy()

    return X, y


def train_resm(
    training_data_path: str | None = None,
    output_dir: str | None = None,
    use_mlflow: bool = True,
    use_wandb: bool = False,
    mlflow_tracking_uri: str | None = None,
) -> None:
    """Train RESM ensemble model."""
    config = TrainingConfig(
        model_name="resm",
        model_version="0.1.0",
        training_data_path=training_data_path,
        output_dir=Path(output_dir) if output_dir else Path("models/resm"),
        use_mlflow=use_mlflow,
        use_wandb=use_wandb,
        mlflow_tracking_uri=mlflow_tracking_uri,
    )

    trainer = BaseTrainer(config)
    trainer.setup_tracking()

    # Load or generate training data
    if training_data_path and Path(training_data_path).exists():
        logger.info("Loading training data from %s", training_data_path)
        X, y = load_training_data(Path(training_data_path))
        trainer.log_params({"dataset_source": training_data_path, "dataset_size": len(X)})
    else:
        logger.info("Generating synthetic training data")
        ensemble = RESMEnsemble()
        X, y = ensemble._generate_training_data(n=2000)
        trainer.log_params({"dataset_source": "synthetic", "dataset_size": len(X)})

    # Split data
    X_train, X_val, X_test, y_train, y_val, y_test = trainer.split_data(X, y)
    trainer.log_params({"train_size": len(X_train), "val_size": len(X_val), "test_size": len(X_test)})

    # Train models
    models: list[tuple[str, Any]] = []
    model_configs = {
        "ridge_regression": {"alpha": 1.0},
        "random_forest": {"n_estimators": 200, "max_depth": 10, "random_state": 7},
        "gradient_boosting": {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.1, "random_state": 21},
    }

    for model_name, model_params in model_configs.items():
        logger.info("Training %s...", model_name)
        trainer.log_params({f"{model_name}_{k}": v for k, v in model_params.items()})

        if model_name == "ridge_regression":
            pipeline = Pipeline([("scaler", StandardScaler()), ("reg", Ridge(**model_params))])
        elif model_name == "random_forest":
            pipeline = RandomForestRegressor(**model_params)
        else:  # gradient_boosting
            pipeline = GradientBoostingRegressor(**model_params)

        pipeline.fit(X_train, y_train)
        models.append((model_name, pipeline))

        # Evaluate on validation set
        y_val_pred = pipeline.predict(X_val)
        val_metrics = trainer.evaluate_regression(y_val, y_val_pred, prefix=f"{model_name}_val_")
        trainer.log_metrics(val_metrics)

        logger.info("%s validation R²: %.4f", model_name, val_metrics[f"{model_name}_val_r2"])

    # Evaluate ensemble on test set
    logger.info("Evaluating ensemble on test set...")
    ensemble_predictions = []
    for name, model in models:
        pred = model.predict(X_test)
        ensemble_predictions.append(pred)

    ensemble_pred = np.mean(ensemble_predictions, axis=0)

    test_metrics = trainer.evaluate_regression(y_test, ensemble_pred, prefix="ensemble_test_")
    trainer.log_metrics(test_metrics)
    logger.info("Ensemble test R²: %.4f", test_metrics["ensemble_test_r2"])

    # Save models
    if config.save_model:
        for name, model in models:
            trainer.save_model(model, name, metadata={"model_name": name, "version": config.model_version})

    trainer.finish_tracking()
    logger.info("Training complete!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train RESM model")
    parser.add_argument("--training-data", type=str, help="Path to training data (CSV/Parquet)")
    parser.add_argument("--output-dir", type=str, help="Output directory for models")
    parser.add_argument("--no-mlflow", action="store_true", help="Disable MLflow tracking")
    parser.add_argument("--wandb", action="store_true", help="Enable W&B tracking")
    parser.add_argument("--mlflow-uri", type=str, help="MLflow tracking URI")
    args = parser.parse_args()

    train_resm(
        training_data_path=args.training_data,
        output_dir=args.output_dir,
        use_mlflow=not args.no_mlflow,
        use_wandb=args.wandb,
        mlflow_tracking_uri=args.mlflow_uri,
    )


if __name__ == "__main__":
    main()
