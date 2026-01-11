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
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    KFold,
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)

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
        """Calculate regression metrics including MAPE and Median Absolute Error."""
        mse = float(mean_squared_error(y_true, y_pred))
        mae = float(mean_absolute_error(y_true, y_pred))
        r2 = float(r2_score(y_true, y_pred))
        rmse = float(np.sqrt(mse))
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        # Avoid division by zero
        non_zero_mask = y_true != 0
        if np.any(non_zero_mask):
            mape = float(np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100)
        else:
            mape = float('inf') if np.any(y_pred != y_true) else 0.0
        
        # Calculate Median Absolute Error
        median_ae = float(np.median(np.abs(y_true - y_pred)))
        
        # Calculate Adjusted R²
        n = len(y_true)
        if n > 1:
            adjusted_r2 = 1 - (1 - r2) * (n - 1) / (n - 1 - 1)  # Assuming p=1 feature
        else:
            adjusted_r2 = r2

        metrics = {
            f"{prefix}mse": mse,
            f"{prefix}mae": mae,
            f"{prefix}rmse": rmse,
            f"{prefix}r2": r2,
            f"{prefix}adjusted_r2": adjusted_r2,
            f"{prefix}mape": mape,
            f"{prefix}median_ae": median_ae,
        }
        return metrics

    def evaluate_classification(
        self, y_true: np.ndarray, y_pred: np.ndarray, labels: list[str] | None = None, prefix: str = ""
    ) -> dict[str, float]:
        """Calculate classification metrics including F1, confusion matrix, and ROC AUC."""
        accuracy = float(accuracy_score(y_true, y_pred))
        # Convert string labels to indices if needed
        label_indices: list[int] | None = None
        if labels:
            label_indices = list(range(len(labels)))
        report = classification_report(y_true, y_pred, labels=label_indices, output_dict=True, zero_division=0)

        metrics = {f"{prefix}accuracy": accuracy}

        # Add per-class metrics with F1 prominently
        for label, scores in report.items():
            if isinstance(scores, dict) and "precision" in scores:
                metrics[f"{prefix}{label}_precision"] = float(scores["precision"])
                metrics[f"{prefix}{label}_recall"] = float(scores["recall"])
                f1 = float(scores["f1-score"])
                metrics[f"{prefix}{label}_f1"] = f1
                # Also store as "f1" for prominent display
                if label != "macro avg" and label != "weighted avg":
                    metrics[f"{prefix}{label}_f1_score"] = f1  # Alternative key for easy lookup

        # Add macro and weighted averages with F1 prominently
        if "macro avg" in report:
            metrics[f"{prefix}macro_avg_precision"] = float(report["macro avg"]["precision"])
            metrics[f"{prefix}macro_avg_recall"] = float(report["macro avg"]["recall"])
            macro_f1 = float(report["macro avg"]["f1-score"])
            metrics[f"{prefix}macro_avg_f1"] = macro_f1
            metrics[f"{prefix}macro_f1"] = macro_f1  # Alternative key for easy lookup

        if "weighted avg" in report:
            metrics[f"{prefix}weighted_avg_precision"] = float(report["weighted avg"]["precision"])
            metrics[f"{prefix}weighted_avg_recall"] = float(report["weighted avg"]["recall"])
            weighted_f1 = float(report["weighted avg"]["f1-score"])
            metrics[f"{prefix}weighted_avg_f1"] = weighted_f1
            metrics[f"{prefix}weighted_f1"] = weighted_f1  # Alternative key for easy lookup

        # Add overall F1 (macro average as primary)
        metrics[f"{prefix}f1"] = metrics.get(f"{prefix}macro_avg_f1", metrics.get(f"{prefix}weighted_avg_f1", 0.0))
        
        # Add confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=label_indices)
        metrics[f"{prefix}confusion_matrix"] = cm.tolist()
        
        # Add ROC AUC for binary classification (if only 2 classes)
        unique_classes = np.unique(y_true)
        if len(unique_classes) == 2:
            try:
                # For binary classification, use the positive class
                roc_auc = float(roc_auc_score(y_true, y_pred))
                metrics[f"{prefix}roc_auc"] = roc_auc
            except Exception:
                pass  # ROC AUC may fail if classes are not properly encoded
        
        # Add F1 score prominently (macro average)
        metrics[f"{prefix}f1_score"] = metrics[f"{prefix}f1"]

        return metrics
    
    def evaluate_with_cross_validation(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        cv_folds: int = 5,
        scoring: str = "f1_weighted",
        model_type: str = "classification",
    ) -> dict[str, float]:
        """Perform cross-validation and return metrics."""
        if model_type == "classification":
            cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=self.config.random_state)
            # For classification, use f1_macro or f1_weighted
            if scoring == "f1":
                scoring = "f1_macro"
        else:
            cv = KFold(n_splits=cv_folds, shuffle=True, random_state=self.config.random_state)
            # For regression, use r2 or neg_mean_squared_error
            if scoring == "f1":
                scoring = "r2"
        
        try:
            scores = cross_val_score(model, X, y, cv=cv, scoring=scoring, n_jobs=-1)
            
            cv_metrics = {
                "cv_mean": float(np.mean(scores)),
                "cv_std": float(np.std(scores)),
                "cv_min": float(np.min(scores)),
                "cv_max": float(np.max(scores)),
                "cv_folds": cv_folds,
                "cv_scoring": scoring,
            }
            return cv_metrics
        except Exception as e:
            logger.warning(f"Cross-validation failed: {e}")
            return {}

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

