"""Base training infrastructure with MLflow and W&B integration."""

from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    wandb = None  # type: ignore[assignment, misc]


logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for training runs."""

    model_name: str
    model_version: str
    training_data_path: str | None = None
    output_dir: Path | None = None
    test_size: float = 0.2
    validation_size: float = 0.1
    random_state: int = 42
    use_mlflow: bool = True
    use_wandb: bool = False
    mlflow_tracking_uri: str | None = None
    wandb_project: str = "aethera"
    wandb_entity: str | None = None
    save_model: bool = True


class BaseTrainer:
    """Base class for model training with MLflow/W&B integration."""

    def __init__(self, config: TrainingConfig) -> None:
        self.config = config
        self.output_dir = config.output_dir or Path("models")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mlflow_run: mlflow.ActiveRun | None = None
        self.wandb_run: Any = None

    def setup_tracking(self) -> None:
        """Initialize MLflow and/or W&B tracking."""
        if self.config.use_mlflow:
            if self.config.mlflow_tracking_uri:
                mlflow.set_tracking_uri(self.config.mlflow_tracking_uri)
            mlflow.set_experiment(self.config.model_name)
            self.mlflow_run = mlflow.start_run(run_name=f"{self.config.model_name}_{self.config.model_version}")
            logger.info("Started MLflow run: %s", self.mlflow_run.info.run_id)

        if self.config.use_wandb and WANDB_AVAILABLE:
            wandb.init(
                project=self.config.wandb_project,
                entity=self.config.wandb_entity,
                name=f"{self.config.model_name}_{self.config.model_version}",
                config={
                    "model_name": self.config.model_name,
                    "model_version": self.config.model_version,
                    "test_size": self.config.test_size,
                    "validation_size": self.config.validation_size,
                    "random_state": self.config.random_state,
                },
            )
            self.wandb_run = wandb.run
            logger.info("Started W&B run: %s", wandb.run.id if wandb.run else None)
        elif self.config.use_wandb and not WANDB_AVAILABLE:
            logger.warning("W&B requested but not installed. Install with: pip install wandb")

    def log_params(self, params: dict[str, Any]) -> None:
        """Log parameters to MLflow and/or W&B."""
        if self.mlflow_run:
            mlflow.log_params(params)
        if self.wandb_run:
            wandb.config.update(params)

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Log metrics to MLflow and/or W&B."""
        if self.mlflow_run:
            mlflow.log_metrics(metrics, step=step)
        if self.wandb_run:
            wandb.log(metrics, step=step)

    def log_artifact(self, local_path: str | Path, artifact_path: str | None = None) -> None:
        """Log artifacts to MLflow and/or W&B."""
        if self.mlflow_run:
            mlflow.log_artifact(str(local_path), artifact_path=artifact_path)
        if self.wandb_run:
            wandb.save(str(local_path))

    def split_data(
        self, X: np.ndarray, y: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data into train, validation, and test sets."""
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=(self.config.test_size + self.config.validation_size), random_state=self.config.random_state
        )
        val_size = self.config.validation_size / (self.config.test_size + self.config.validation_size)
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=(1 - val_size), random_state=self.config.random_state
        )
        return X_train, X_val, X_test, y_train, y_val, y_test

    def evaluate_regression(
        self, y_true: np.ndarray, y_pred: np.ndarray, prefix: str = ""
    ) -> dict[str, float]:
        """Calculate regression metrics."""
        mse = float(mean_squared_error(y_true, y_pred))
        mae = float(mean_absolute_error(y_true, y_pred))
        r2 = float(r2_score(y_true, y_pred))
        rmse = float(np.sqrt(mse))

        metrics = {
            f"{prefix}mse": mse,
            f"{prefix}mae": mae,
            f"{prefix}rmse": rmse,
            f"{prefix}r2": r2,
        }
        return metrics

    def evaluate_classification(
        self, y_true: np.ndarray, y_pred: np.ndarray, labels: list[str] | None = None, prefix: str = ""
    ) -> dict[str, float]:
        """Calculate classification metrics."""
        accuracy = float(accuracy_score(y_true, y_pred))
        # Convert string labels to indices if needed
        label_indices: list[int] | None = None
        if labels:
            label_indices = list(range(len(labels)))
        report = classification_report(y_true, y_pred, labels=label_indices, output_dict=True, zero_division=0)

        metrics = {f"{prefix}accuracy": accuracy}

        # Add per-class metrics
        for label, scores in report.items():
            if isinstance(scores, dict) and "precision" in scores:
                metrics[f"{prefix}{label}_precision"] = float(scores["precision"])
                metrics[f"{prefix}{label}_recall"] = float(scores["recall"])
                metrics[f"{prefix}{label}_f1"] = float(scores["f1-score"])

        # Add macro and weighted averages
        if "macro avg" in report:
            metrics[f"{prefix}macro_avg_precision"] = float(report["macro avg"]["precision"])
            metrics[f"{prefix}macro_avg_recall"] = float(report["macro avg"]["recall"])
            metrics[f"{prefix}macro_avg_f1"] = float(report["macro avg"]["f1-score"])

        if "weighted avg" in report:
            metrics[f"{prefix}weighted_avg_precision"] = float(report["weighted avg"]["precision"])
            metrics[f"{prefix}weighted_avg_recall"] = float(report["weighted avg"]["recall"])
            metrics[f"{prefix}weighted_avg_f1"] = float(report["weighted avg"]["f1-score"])

        return metrics

    def save_model(self, model: Any, model_name: str, metadata: dict[str, Any] | None = None) -> Path:
        """Save model to disk and log to MLflow/W&B."""
        model_path = self.output_dir / f"{model_name}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump({"model": model, "metadata": metadata or {}}, f)

        if self.mlflow_run:
            mlflow.sklearn.log_model(model, model_name)
            if metadata:
                mlflow.log_dict(metadata, f"{model_name}_metadata.json")

        if self.wandb_run:
            wandb.save(str(model_path))

        logger.info("Saved model to %s", model_path)
        return model_path

    def finish_tracking(self) -> None:
        """Close MLflow and/or W&B runs."""
        if self.mlflow_run:
            mlflow.end_run()
            logger.info("Ended MLflow run")
        if self.wandb_run:
            wandb.finish()
            logger.info("Ended W&B run")

