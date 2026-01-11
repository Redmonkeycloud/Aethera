"""Model selection utilities with hyperparameter optimization and benchmarking."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from sklearn.base import BaseEstimator
from sklearn.model_selection import cross_val_score, train_test_split

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    optuna = None  # type: ignore[assignment, misc]

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

logger = logging.getLogger(__name__)


@dataclass
class ModelBenchmarkResult:
    """Result of model benchmarking."""
    
    model_name: str
    accuracy: float
    training_time: float
    inference_time: float
    memory_mb: float | None = None
    params: dict[str, Any] | None = None
    cv_scores: list[float] | None = None
    cv_mean: float | None = None
    cv_std: float | None = None


class ModelBenchmarker:
    """Benchmark different models for performance comparison."""
    
    def __init__(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42,
        cv_folds: int = 5,
    ) -> None:
        """
        Initialize benchmarker.
        
        Args:
            X: Feature matrix
            y: Target vector
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility
            cv_folds: Number of CV folds
        """
        self.X = X
        self.y = y
        self.test_size = test_size
        self.random_state = random_state
        self.cv_folds = cv_folds
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        self.results: list[ModelBenchmarkResult] = []
    
    def benchmark_model(
        self,
        model: BaseEstimator,
        model_name: str,
        scoring: str = "accuracy",
        measure_memory: bool = False,
    ) -> ModelBenchmarkResult:
        """
        Benchmark a single model.
        
        Args:
            model: Scikit-learn compatible model
            model_name: Name of the model
            scoring: Scoring metric for CV
            measure_memory: Whether to measure memory usage (requires memory_profiler)
            
        Returns:
            ModelBenchmarkResult with performance metrics
        """
        logger.info(f"Benchmarking {model_name}...")
        
        # Training time
        start_time = time.time()
        model.fit(self.X_train, self.y_train)
        training_time = time.time() - start_time
        
        # Inference time (on test set)
        start_time = time.time()
        predictions = model.predict(self.X_test)
        inference_time = (time.time() - start_time) / len(self.X_test)  # Per sample
        
        # Accuracy/R²
        if hasattr(model, "score"):
            accuracy = float(model.score(self.X_test, self.y_test))
        else:
            # Fallback: calculate manually
            if scoring == "accuracy":
                from sklearn.metrics import accuracy_score
                accuracy = float(accuracy_score(self.y_test, predictions))
            elif scoring == "r2":
                from sklearn.metrics import r2_score
                accuracy = float(r2_score(self.y_test, predictions))
            else:
                accuracy = 0.0
        
        # Cross-validation
        try:
            cv_scores = cross_val_score(
                model, self.X_train, self.y_train, cv=self.cv_folds, scoring=scoring, n_jobs=-1
            )
            cv_mean = float(np.mean(cv_scores))
            cv_std = float(np.std(cv_scores))
        except Exception as e:
            logger.warning(f"CV failed for {model_name}: {e}")
            cv_scores = None
            cv_mean = None
            cv_std = None
        
        # Memory (optional)
        memory_mb = None
        if measure_memory:
            try:
                import sys
                memory_mb = sys.getsizeof(model) / (1024 * 1024)  # Rough estimate
            except Exception:
                pass
        
        # Get parameters
        params = model.get_params() if hasattr(model, "get_params") else None
        
        result = ModelBenchmarkResult(
            model_name=model_name,
            accuracy=accuracy,
            training_time=training_time,
            inference_time=inference_time,
            memory_mb=memory_mb,
            params=params,
            cv_scores=cv_scores.tolist() if cv_scores is not None else None,
            cv_mean=cv_mean,
            cv_std=cv_std,
        )
        
        self.results.append(result)
        logger.info(
            f"{model_name}: Accuracy={accuracy:.4f}, Train={training_time:.3f}s, "
            f"Infer={inference_time*1000:.3f}ms/sample, CV={cv_mean:.4f}±{cv_std:.4f}"
        )
        
        return result
    
    def get_best_model(self, metric: str = "accuracy") -> ModelBenchmarkResult | None:
        """
        Get the best model based on a metric.
        
        Args:
            metric: Metric to use ("accuracy", "training_time", "inference_time")
            
        Returns:
            Best ModelBenchmarkResult or None
        """
        if not self.results:
            return None
        
        if metric == "accuracy":
            return max(self.results, key=lambda r: r.accuracy)
        elif metric == "training_time":
            return min(self.results, key=lambda r: r.training_time)
        elif metric == "inference_time":
            return min(self.results, key=lambda r: r.inference_time)
        elif metric == "cv_mean":
            return max(self.results, key=lambda r: r.cv_mean or 0.0)
        else:
            return self.results[0]
    
    def get_summary(self) -> dict[str, Any]:
        """Get summary of all benchmark results."""
        if not self.results:
            return {}
        
        return {
            "n_models": len(self.results),
            "results": [
                {
                    "model_name": r.model_name,
                    "accuracy": r.accuracy,
                    "training_time": r.training_time,
                    "inference_time": r.inference_time,
                    "cv_mean": r.cv_mean,
                    "cv_std": r.cv_std,
                }
                for r in self.results
            ],
            "best_accuracy": self.get_best_model("accuracy").model_name if self.get_best_model("accuracy") else None,
            "fastest_training": self.get_best_model("training_time").model_name if self.get_best_model("training_time") else None,
            "fastest_inference": self.get_best_model("inference_time").model_name if self.get_best_model("inference_time") else None,
            "best_cv": self.get_best_model("cv_mean").model_name if self.get_best_model("cv_mean") else None,
        }


class OptunaHyperparameterOptimizer:
    """Hyperparameter optimization using Optuna."""
    
    def __init__(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        model_type: str = "classification",
        n_trials: int = 100,
        cv_folds: int = 5,
        random_state: int = 42,
        timeout: int | None = None,
    ) -> None:
        """
        Initialize optimizer.
        
        Args:
            X_train: Training features
            y_train: Training targets
            model_type: "classification" or "regression"
            n_trials: Number of Optuna trials
            cv_folds: Number of CV folds
            random_state: Random seed
            timeout: Timeout in seconds (None for no timeout)
        """
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna not available. Install with: pip install optuna")
        
        self.X_train = X_train
        self.y_train = y_train
        self.model_type = model_type
        self.n_trials = n_trials
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.timeout = timeout
        
        self.study: optuna.Study | None = None
        self.best_params: dict[str, Any] | None = None
        self.best_score: float | None = None
    
    def optimize_xgboost(
        self,
        objective: str | None = None,
    ) -> dict[str, Any]:
        """
        Optimize XGBoost hyperparameters.
        
        Args:
            objective: XGBoost objective function
            
        Returns:
            Best hyperparameters
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost not available. Install with: pip install xgboost")
        
        if self.model_type == "classification":
            n_classes = len(np.unique(self.y_train))
            if n_classes == 2:
                objective = "binary:logistic"
            else:
                objective = "multi:softprob"
        else:
            objective = "reg:squarederror"
        
        def objective_func(trial: optuna.Trial) -> float:
            params = {
                "objective": objective,
                "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 7),
                "gamma": trial.suggest_float("gamma", 0.0, 0.5),
                "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
                "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 1.0),
                "random_state": self.random_state,
                "n_jobs": -1,
            }
            
            if self.model_type == "classification":
                if n_classes == 2:
                    model = xgb.XGBClassifier(**params)
                    scoring = "accuracy"
                else:
                    model = xgb.XGBClassifier(**params)
                    scoring = "f1_macro"
            else:
                model = xgb.XGBRegressor(**params)
                scoring = "r2"
            
            scores = cross_val_score(
                model, self.X_train, self.y_train, cv=self.cv_folds, scoring=scoring, n_jobs=-1
            )
            return float(np.mean(scores))
        
        self.study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=self.random_state))
        self.study.optimize(objective_func, n_trials=self.n_trials, timeout=self.timeout, show_progress_bar=True)
        
        self.best_params = self.study.best_params.copy()
        self.best_params["objective"] = objective
        self.best_params["random_state"] = self.random_state
        self.best_params["n_jobs"] = -1
        self.best_score = self.study.best_value
        
        logger.info(f"XGBoost optimization complete. Best CV score: {self.best_score:.4f}")
        logger.info(f"Best parameters: {self.best_params}")
        
        return self.best_params
    
    def optimize_lightgbm(
        self,
        objective: str | None = None,
    ) -> dict[str, Any]:
        """
        Optimize LightGBM hyperparameters.
        
        Args:
            objective: LightGBM objective function
            
        Returns:
            Best hyperparameters
        """
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM not available. Install with: pip install lightgbm")
        
        if self.model_type == "classification":
            n_classes = len(np.unique(self.y_train))
            if n_classes == 2:
                objective = "binary"
                metric = "binary_logloss"
            else:
                objective = "multiclass"
                metric = "multi_logloss"
        else:
            objective = "regression"
            metric = "rmse"
        
        def objective_func(trial: optuna.Trial) -> float:
            params = {
                "objective": objective,
                "metric": metric,
                "boosting_type": "gbdt",
                "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
                "num_leaves": trial.suggest_int("num_leaves", 20, 300),
                "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
                "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 1.0),
                "random_state": self.random_state,
                "n_jobs": -1,
                "verbose": -1,
            }
            
            if self.model_type == "classification":
                if n_classes == 2:
                    model = lgb.LGBMClassifier(**params)
                    scoring = "accuracy"
                else:
                    model = lgb.LGBMClassifier(**params)
                    scoring = "f1_macro"
            else:
                model = lgb.LGBMRegressor(**params)
                scoring = "r2"
            
            scores = cross_val_score(
                model, self.X_train, self.y_train, cv=self.cv_folds, scoring=scoring, n_jobs=-1
            )
            return float(np.mean(scores))
        
        self.study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=self.random_state))
        self.study.optimize(objective_func, n_trials=self.n_trials, timeout=self.timeout, show_progress_bar=True)
        
        self.best_params = self.study.best_params.copy()
        self.best_params["objective"] = objective
        self.best_params["metric"] = metric
        self.best_params["boosting_type"] = "gbdt"
        self.best_params["random_state"] = self.random_state
        self.best_params["n_jobs"] = -1
        self.best_params["verbose"] = -1
        self.best_score = self.study.best_value
        
        logger.info(f"LightGBM optimization complete. Best CV score: {self.best_score:.4f}")
        logger.info(f"Best parameters: {self.best_params}")
        
        return self.best_params
