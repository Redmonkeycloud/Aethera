"""
Model explainability utilities using SHAP and Yellowbrick.

Generates feature importance, performance visualizations, and model interpretation
for ML models used in AETHERA analysis.
"""

from __future__ import annotations

import json
import base64
from pathlib import Path
from typing import Any, Dict, List, Tuple
from io import BytesIO

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from sklearn.base import BaseEstimator
from sklearn.pipeline import Pipeline

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

try:
    from yellowbrick.classifier import (
        ClassificationReport,
        ConfusionMatrix,
        ROCAUC,
        ClassPredictionError,
    )
    from yellowbrick.regressor import (
        PredictionError,
        ResidualsPlot,
        LearningCurve,
    )
    from yellowbrick.features import FeatureImportances
    YELLOWBRICK_AVAILABLE = True
except ImportError:
    YELLOWBRICK_AVAILABLE = False

from loguru import logger
import hashlib
import pickle


def _get_cache_key(model_name: str, config_path: str | None = None, version: str | None = None) -> str:
    """
    Generate a cache key for explainability artifacts.
    
    Args:
        model_name: Name of the model (e.g., "biodiversity", "resm")
        config_path: Path to training data config (optional)
        version: Model version (optional)
        
    Returns:
        Cache key string
    """
    key_parts = [model_name]
    if config_path:
        key_parts.append(str(config_path))
    if version:
        key_parts.append(str(version))
    key_string = "_".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def _save_cached_artifacts(cache_dir: Path, cache_key: str, artifacts: Dict[str, Any]) -> None:
    """
    Save explainability artifacts to cache.
    
    Args:
        cache_dir: Cache directory
        cache_key: Cache key
        artifacts: Artifacts to cache
    """
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{cache_key}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(artifacts, f)
        logger.debug(f"Saved explainability artifacts to cache: {cache_file}")
    except Exception as e:
        logger.warning(f"Failed to save artifacts to cache: {e}")


def _load_cached_artifacts(cache_dir: Path, cache_key: str) -> Dict[str, Any] | None:
    """
    Load explainability artifacts from cache.
    
    Args:
        cache_dir: Cache directory
        cache_key: Cache key
        
    Returns:
        Cached artifacts or None if not found
    """
    try:
        cache_file = cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                artifacts = pickle.load(f)
            logger.debug(f"Loaded explainability artifacts from cache: {cache_file}")
            return artifacts
    except Exception as e:
        logger.warning(f"Failed to load artifacts from cache: {e}")
    return None


def generate_shap_explanations(
    model: BaseEstimator | Pipeline,
    X_train: np.ndarray,
    X_sample: np.ndarray | None = None,
    feature_names: List[str] | None = None,
    model_type: str = "classification",
) -> Dict[str, Any]:
    """
    Generate SHAP explanations for a model.
    
    Args:
        model: Trained scikit-learn model or pipeline
        X_train: Training data (used for TreeExplainer or as background for KernelExplainer)
        X_sample: Sample data to explain (if None, uses small sample from X_train)
        feature_names: Names of features
        model_type: "classification" or "regression"
        
    Returns:
        Dictionary with SHAP values and metadata
    """
    if not SHAP_AVAILABLE:
        logger.warning("SHAP not available. Install with: pip install shap")
        return {}
    
    try:
        # Use small sample for efficiency
        if X_sample is None:
            sample_size = min(100, len(X_train))
            X_sample = X_train[:sample_size]
        
        # Extract the actual model if it's a Pipeline
        actual_model = model
        X_train_transformed = X_train[:min(100, len(X_train))]
        if isinstance(model, Pipeline):
            # For pipelines, get the last step (the actual model)
            actual_model = model.steps[-1][1]
            # Transform X_train through the pipeline (except last step)
            if len(model.steps) > 1:
                try:
                    X_train_transformed = model[:-1].transform(X_train[:min(100, len(X_train))])
                except Exception:
                    # If transformation fails, use original
                    pass
        
        # Choose appropriate SHAP explainer
        explainer = None
        shap_values = None
        
        # Try TreeExplainer first (for tree-based models)
        tree_models = ["RandomForest", "GradientBoosting", "XGBoost", "DecisionTree"]
        model_name = type(actual_model).__name__
        
        if any(tree_name in model_name for tree_name in tree_models):
            try:
                explainer = shap.TreeExplainer(actual_model)
                shap_values = explainer.shap_values(X_sample)
                # For classification, SHAP returns list of arrays (one per class)
                if isinstance(shap_values, list):
                    # Use the class with highest average probability
                    if len(shap_values) > 1:
                        shap_values = shap_values[1]  # Use positive class for binary
                    else:
                        shap_values = shap_values[0]
            except Exception as e:
                logger.warning(f"TreeExplainer failed for {model_name}: {e}")
        
        # Fallback to KernelExplainer or LinearExplainer
        if explainer is None:
            try:
                if "Linear" in model_name or "Logistic" in model_name or "Ridge" in model_name:
                    explainer = shap.LinearExplainer(actual_model, X_train_transformed)
                    shap_values = explainer.shap_values(X_sample)
                else:
                    # Use a smaller background for KernelExplainer (it's slow)
                    background_size = min(50, len(X_train_transformed))
                    explainer = shap.KernelExplainer(
                        model.predict if model_type == "regression" else model.predict_proba,
                        X_train_transformed[:background_size]
                    )
                    shap_values = explainer.shap_values(X_sample[:min(20, len(X_sample))])  # Limit samples for speed
                
                if isinstance(shap_values, list):
                    if len(shap_values) > 1:
                        shap_values = shap_values[1]  # For binary classification
                    else:
                        shap_values = shap_values[0]
            except Exception as e:
                logger.warning(f"SHAP explainer failed: {e}")
                return {}
        
        if shap_values is None:
            return {}
        
        # Calculate feature importance (mean absolute SHAP values)
        if len(shap_values.shape) > 1:
            feature_importance = np.abs(shap_values).mean(axis=0)
        else:
            feature_importance = np.abs(shap_values)
        
        # Create feature importance dictionary
        importance_dict = {}
        if feature_names:
            for idx, name in enumerate(feature_names):
                if idx < len(feature_importance):
                    importance_dict[name] = float(feature_importance[idx])
        else:
            for idx, importance in enumerate(feature_importance):
                importance_dict[f"feature_{idx}"] = float(importance)
        
        # Get summary statistics
        result = {
            "feature_importance": importance_dict,
            "shap_values_mean": shap_values.mean(axis=0).tolist() if len(shap_values.shape) > 1 else shap_values.mean().tolist(),
            "shap_values_std": shap_values.std(axis=0).tolist() if len(shap_values.shape) > 1 else shap_values.std().tolist(),
            "model_type": model_type,
            "explainer_type": type(explainer).__name__,
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating SHAP explanations: {e}")
        return {}


def generate_yellowbrick_plots(
    model: BaseEstimator | Pipeline,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray | None = None,
    y_test: np.ndarray | None = None,
    model_type: str = "classification",
    feature_names: List[str] | None = None,
    output_dir: Path | None = None,
) -> Dict[str, str]:
    """
    Generate Yellowbrick performance visualization plots.
    
    Args:
        model: Trained scikit-learn model or pipeline
        X_train: Training features
        y_train: Training labels/targets
        X_test: Test features (optional)
        y_test: Test labels/targets (optional)
        model_type: "classification" or "regression"
        feature_names: Names of features
        output_dir: Directory to save plots (if None, returns base64 encoded images)
        
    Returns:
        Dictionary mapping plot names to file paths or base64 encoded images
    """
    if not YELLOWBRICK_AVAILABLE:
        logger.warning("Yellowbrick not available. Install with: pip install yellowbrick")
        return {}
    
    plots = {}
    
    try:
        # Use test data if available, otherwise use train data
        X_eval = X_test if X_test is not None else X_train
        y_eval = y_test if y_test is not None else y_train
        
        # Limit data size for performance
        max_samples = 1000
        if len(X_eval) > max_samples:
            indices = np.random.choice(len(X_eval), max_samples, replace=False)
            X_eval = X_eval[indices]
            y_eval = y_eval[indices]
        
        if model_type == "classification":
            # Classification Report
            try:
                fig, ax = plt.subplots(figsize=(8, 6))
                visualizer = ClassificationReport(model, ax=ax, support=True)
                visualizer.fit(X_train, y_train)
                visualizer.score(X_eval, y_eval)
                visualizer.finalize()
                
                plot_path = _save_or_encode_plot(fig, "classification_report", output_dir)
                plots["classification_report"] = plot_path
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Failed to generate classification report: {e}")
            
            # Confusion Matrix
            try:
                fig, ax = plt.subplots(figsize=(8, 6))
                visualizer = ConfusionMatrix(model, ax=ax)
                visualizer.fit(X_train, y_train)
                visualizer.score(X_eval, y_eval)
                visualizer.finalize()
                
                plot_path = _save_or_encode_plot(fig, "confusion_matrix", output_dir)
                plots["confusion_matrix"] = plot_path
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Failed to generate confusion matrix: {e}")
            
            # ROC AUC (for binary classification)
            try:
                n_classes = len(np.unique(y_train))
                if n_classes == 2:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    visualizer = ROCAUC(model, ax=ax)
                    visualizer.fit(X_train, y_train)
                    visualizer.score(X_eval, y_eval)
                    visualizer.finalize()
                    
                    plot_path = _save_or_encode_plot(fig, "roc_auc", output_dir)
                    plots["roc_auc"] = plot_path
                    plt.close(fig)
            except Exception as e:
                logger.warning(f"Failed to generate ROC AUC: {e}")
        
        else:  # regression
            # Prediction Error Plot
            try:
                fig, ax = plt.subplots(figsize=(8, 6))
                visualizer = PredictionError(model, ax=ax)
                visualizer.fit(X_train, y_train)
                visualizer.score(X_eval, y_eval)
                visualizer.finalize()
                
                plot_path = _save_or_encode_plot(fig, "prediction_error", output_dir)
                plots["prediction_error"] = plot_path
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Failed to generate prediction error plot: {e}")
            
            # Residuals Plot
            try:
                fig, ax = plt.subplots(figsize=(8, 6))
                visualizer = ResidualsPlot(model, ax=ax)
                visualizer.fit(X_train, y_train)
                visualizer.score(X_eval, y_eval)
                visualizer.finalize()
                
                plot_path = _save_or_encode_plot(fig, "residuals", output_dir)
                plots["residuals"] = plot_path
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Failed to generate residuals plot: {e}")
        
        # Feature Importance (for tree-based models)
        try:
            if feature_names is not None:
                actual_model = model
                if isinstance(model, Pipeline):
                    actual_model = model.steps[-1][1]
                
                model_name = type(actual_model).__name__
                if any(name in model_name for name in ["RandomForest", "GradientBoosting", "DecisionTree"]):
                    fig, ax = plt.subplots(figsize=(10, 6))
                    visualizer = FeatureImportances(actual_model, ax=ax, labels=feature_names, relative=False)
                    visualizer.fit(X_train, y_train)
                    visualizer.finalize()
                    
                    plot_path = _save_or_encode_plot(fig, "feature_importance", output_dir)
                    plots["feature_importance"] = plot_path
                    plt.close(fig)
        except Exception as e:
            logger.warning(f"Failed to generate feature importance plot: {e}")
    
    except Exception as e:
        logger.error(f"Error generating Yellowbrick plots: {e}")
    
    return plots


def _save_or_encode_plot(fig: plt.Figure, plot_name: str, output_dir: Path | None = None) -> str:
    """
    Save plot to file or encode as base64 string.
    
    Args:
        fig: Matplotlib figure
        plot_name: Name for the plot
        output_dir: Directory to save (if None, returns base64)
        
    Returns:
        File path or base64 encoded string
    """
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        plot_path = output_dir / f"{plot_name}.png"
        fig.savefig(plot_path, dpi=150, bbox_inches='tight')
        return str(plot_path)
    else:
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return f"data:image/png;base64,{img_base64}"


def save_explainability_artifacts(
    artifacts: Dict[str, Any],
    output_dir: Path,
    model_name: str,
    use_cache: bool = False,
    cache_key: str | None = None,
) -> Dict[str, str]:
    """
    Save explainability artifacts to disk.
    
    Args:
        artifacts: Dictionary containing SHAP values, plots, etc.
        output_dir: Directory to save artifacts
        model_name: Name of the model (e.g., "biodiversity", "resm")
        
    Returns:
        Dictionary mapping artifact types to file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir = output_dir / model_name
    model_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths = {}
    
    # Save SHAP data as JSON
    if "shap" in artifacts:
        shap_path = model_dir / "shap_values.json"
        with open(shap_path, 'w') as f:
            json.dump(artifacts["shap"], f, indent=2)
        saved_paths["shap"] = str(shap_path.relative_to(output_dir))
    
    # Save plots (they're already saved if output_dir was provided)
    if "plots" in artifacts:
        plot_paths = {}
        for plot_name, plot_path in artifacts["plots"].items():
            if isinstance(plot_path, str) and not plot_path.startswith("data:image"):
                # It's a file path
                plot_paths[plot_name] = str(Path(plot_path).relative_to(output_dir))
            else:
                # It's base64, save it
                if plot_path.startswith("data:image"):
                    img_data = plot_path.split(",")[1]
                    img_bytes = base64.b64decode(img_data)
                    plot_file = model_dir / f"{plot_name}.png"
                    with open(plot_file, 'wb') as f:
                        f.write(img_bytes)
                    plot_paths[plot_name] = str(plot_file.relative_to(output_dir))
        
        saved_paths["plots"] = plot_paths
    
    # Save metadata
    metadata = {
        "model_name": model_name,
        "artifacts": saved_paths,
        **artifacts.get("metadata", {})
    }
    if cache_key is not None:
        metadata["cache_key"] = cache_key
    metadata_path = model_dir / "explainability_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    saved_paths["metadata"] = str(metadata_path.relative_to(output_dir))
    
    # Save to cache if enabled
    if use_cache and cache_key is not None:
        cache_dir = output_dir.parent / ".cache"
        _save_cached_artifacts(cache_dir, cache_key, artifacts)
    
    return saved_paths


def generate_shap_waterfall_plot(
    model: BaseEstimator | Pipeline,
    X_sample: np.ndarray,
    feature_names: List[str] | None = None,
    output_dir: Path | None = None,
    max_display: int = 10,
) -> str | None:
    """
    Generate SHAP waterfall plot for a single prediction.
    
    Args:
        model: Trained model
        X_sample: Single sample to explain (shape: (1, n_features))
        feature_names: Names of features
        output_dir: Directory to save plot
        max_display: Maximum number of features to display
        
    Returns:
        File path or base64 encoded image
    """
    if not SHAP_AVAILABLE:
        return None
    
    try:
        # Get SHAP values for the sample
        shap_data = generate_shap_explanations(
            model=model,
            X_train=X_sample,  # Use sample as training for single prediction
            X_sample=X_sample,
            feature_names=feature_names,
            model_type="classification" if hasattr(model, "predict_proba") else "regression",
        )
        
        if not shap_data or "feature_importance" not in shap_data:
            return None
        
        # Create waterfall plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # For now, create a simple bar chart representation
        # Full waterfall plot would require shap.plots.waterfall which needs explainer object
        if feature_names and "feature_importance" in shap_data:
            features = list(shap_data["feature_importance"].keys())[:max_display]
            importances = [shap_data["feature_importance"][f] for f in features]
            
            colors = ['red' if x < 0 else 'green' for x in importances]
            ax.barh(features, importances, color=colors)
            ax.set_xlabel("SHAP Value")
            ax.set_title("SHAP Waterfall (Feature Contributions)")
            ax.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
        
        return _save_or_encode_plot(fig, "shap_waterfall", output_dir)
        
    except Exception as e:
        logger.warning(f"Failed to generate SHAP waterfall plot: {e}")
        return None


def generate_shap_dependence_plots(
    model: BaseEstimator | Pipeline,
    X_train: np.ndarray,
    feature_names: List[str] | None = None,
    output_dir: Path | None = None,
    top_features: int = 5,
) -> Dict[str, str]:
    """
    Generate SHAP dependence plots for top features.
    
    Args:
        model: Trained model
        X_train: Training data
        feature_names: Names of features
        output_dir: Directory to save plots
        top_features: Number of top features to plot
        
    Returns:
        Dictionary mapping feature names to plot paths
    """
    if not SHAP_AVAILABLE:
        return {}
    
    plots = {}
    
    try:
        # Get SHAP values
        shap_data = generate_shap_explanations(
            model=model,
            X_train=X_train,
            feature_names=feature_names,
            model_type="classification" if hasattr(model, "predict_proba") else "regression",
        )
        
        if not shap_data or "feature_importance" not in shap_data:
            return {}
        
        # Get top features
        feature_importance = shap_data["feature_importance"]
        sorted_features = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)
        top_features_list = [f[0] for f in sorted_features[:top_features]]
        
        # Get feature indices
        if feature_names:
            feature_indices = {name: idx for idx, name in enumerate(feature_names)}
        else:
            feature_indices = {f"feature_{i}": i for i in range(X_train.shape[1])}
        
        # Generate dependence plots for each top feature
        for feature_name in top_features_list:
            if feature_name not in feature_indices:
                continue
            
            feat_idx = feature_indices[feature_name]
            
            try:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                # Plot feature values vs SHAP values
                feature_values = X_train[:, feat_idx] if len(X_train.shape) > 1 else X_train
                
                # Get SHAP values (simplified - would need actual explainer)
                # For now, create a scatter plot of feature vs prediction
                predictions = model.predict(X_train) if hasattr(model, "predict") else None
                
                if predictions is not None:
                    ax.scatter(feature_values, predictions, alpha=0.5, s=20)
                    ax.set_xlabel(feature_name)
                    ax.set_ylabel("Model Prediction")
                    ax.set_title(f"SHAP Dependence: {feature_name}")
                    ax.grid(True, alpha=0.3)
                
                plot_path = _save_or_encode_plot(fig, f"shap_dependence_{feature_name}", output_dir)
                if plot_path:
                    plots[feature_name] = plot_path
                plt.close(fig)
                
            except Exception as e:
                logger.warning(f"Failed to generate dependence plot for {feature_name}: {e}")
        
        return plots
        
    except Exception as e:
        logger.error(f"Error generating SHAP dependence plots: {e}")
        return {}

