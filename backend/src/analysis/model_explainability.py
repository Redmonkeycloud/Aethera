"""
Helper module to generate explainability artifacts for ML models.

This module provides functions to generate SHAP and Yellowbrick visualizations
for the AETHERA ML models.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

# Add repo root to path for model imports
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from loguru import logger

# Import explainability functions
from backend.src.analysis.explainability import (
    generate_shap_explanations,
    generate_yellowbrick_plots,
    save_explainability_artifacts,
    generate_shap_waterfall_plot,
    generate_shap_dependence_plots,
    _get_cache_key,
    _load_cached_artifacts,
)


def generate_biodiversity_explainability(
    config_path: str | None = None,
    output_dir: Path | None = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Generate explainability artifacts for Biodiversity model."""
    try:
        from ai.models.biodiversity import BiodiversityConfig, BiodiversityEnsemble  # noqa: E402
        
        # Check cache first
        if use_cache and output_dir:
            cache_key = _get_cache_key("biodiversity", config_path, BiodiversityConfig().version)
            cache_dir = output_dir.parent / ".cache"
            cached = _load_cached_artifacts(cache_dir, cache_key)
            if cached:
                logger.info("Using cached biodiversity explainability artifacts")
                return cached
        
        config = BiodiversityConfig()
        if config_path:
            config.training_data_path = config_path
        
        ensemble = BiodiversityEnsemble(config)
        
        # Get training data (regenerate for explainability)
        external_data = ensemble._load_external_training_data()
        if external_data:
            X, y = external_data
        else:
            X, y = BiodiversityEnsemble._generate_training_data()
        
        feature_names = ensemble.vector_fields
        
        artifacts = {"shap": {}, "plots": {}, "metadata": {}}
        
        # Generate explainability for each model in ensemble
        for model_name, model in ensemble._models:
            try:
                # SHAP explanations
                shap_data = generate_shap_explanations(
                    model=model,
                    X_train=X,
                    feature_names=feature_names,
                    model_type="classification",
                )
                if shap_data:
                    artifacts["shap"][model_name] = shap_data
                
                # Yellowbrick plots (save to output_dir if provided)
                plots = generate_yellowbrick_plots(
                    model=model,
                    X_train=X,
                    y_train=y,
                    model_type="classification",
                    feature_names=feature_names,
                    output_dir=output_dir / model_name if output_dir else None,
                )
                if plots:
                    artifacts["plots"][model_name] = plots
                
                # Generate additional SHAP plots
                if output_dir:
                    waterfall = generate_shap_waterfall_plot(
                        model=model,
                        X_sample=X[:1],
                        feature_names=feature_names,
                        output_dir=output_dir / model_name,
                    )
                    if waterfall:
                        if "plots" not in artifacts:
                            artifacts["plots"] = {}
                        if model_name not in artifacts["plots"]:
                            artifacts["plots"][model_name] = {}
                        artifacts["plots"][model_name]["waterfall"] = waterfall
                    
                    dependence = generate_shap_dependence_plots(
                        model=model,
                        X_train=X,
                        feature_names=feature_names,
                        output_dir=output_dir / model_name,
                    )
                    if dependence:
                        if "plots" not in artifacts:
                            artifacts["plots"] = {}
                        if model_name not in artifacts["plots"]:
                            artifacts["plots"][model_name] = {}
                        artifacts["plots"][model_name].update(dependence)
                    
            except Exception as e:
                logger.warning(f"Failed to generate explainability for {model_name}: {e}")
        
        # Save to cache if enabled
        if use_cache and output_dir:
            cache_key = _get_cache_key("biodiversity", config_path, config.version)
            cache_dir = output_dir.parent / ".cache"
            from backend.src.analysis.explainability import _save_cached_artifacts
            _save_cached_artifacts(cache_dir, cache_key, artifacts)
        
        return artifacts
        
    except Exception as e:
        logger.error(f"Error generating biodiversity explainability: {e}")
        return {}


def generate_resm_explainability(
    config_path: str | None = None,
    output_dir: Path | None = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Generate explainability artifacts for RESM model."""
    try:
        from ai.models.resm import RESMConfig, RESMEnsemble  # noqa: E402
        
        # Check cache first
        if use_cache and output_dir:
            cache_key = _get_cache_key("resm", config_path, RESMConfig().version)
            cache_dir = output_dir.parent / ".cache"
            cached = _load_cached_artifacts(cache_dir, cache_key)
            if cached:
                logger.info("Using cached RESM explainability artifacts")
                return cached
        
        config = RESMConfig()
        if config_path:
            config.training_data_path = config_path
        
        ensemble = RESMEnsemble(config)
        
        # Get training data
        external_data = ensemble._load_external_training_data()
        if external_data:
            X, y = external_data
        else:
            X, y = RESMEnsemble._generate_training_data()
        
        feature_names = ensemble.vector_fields
        
        artifacts = {"shap": {}, "plots": {}, "metadata": {}}
        
        for model_name, model in ensemble._models:
            try:
                shap_data = generate_shap_explanations(
                    model=model,
                    X_train=X,
                    feature_names=feature_names,
                    model_type="regression",
                )
                if shap_data:
                    artifacts["shap"][model_name] = shap_data
                
                plots = generate_yellowbrick_plots(
                    model=model,
                    X_train=X,
                    y_train=y,
                    model_type="regression",
                    feature_names=feature_names,
                    output_dir=output_dir / model_name if output_dir else None,
                )
                if plots:
                    artifacts["plots"][model_name] = plots
                
                # Generate additional SHAP plots
                if output_dir:
                    dependence = generate_shap_dependence_plots(
                        model=model,
                        X_train=X,
                        feature_names=feature_names,
                        output_dir=output_dir / model_name,
                    )
                    if dependence:
                        if "plots" not in artifacts:
                            artifacts["plots"] = {}
                        if model_name not in artifacts["plots"]:
                            artifacts["plots"][model_name] = {}
                        artifacts["plots"][model_name].update(dependence)
                    
            except Exception as e:
                logger.warning(f"Failed to generate explainability for {model_name}: {e}")
        
        # Save to cache if enabled
        if use_cache and output_dir:
            cache_key = _get_cache_key("resm", config_path, config.version)
            cache_dir = output_dir.parent / ".cache"
            from backend.src.analysis.explainability import _save_cached_artifacts
            _save_cached_artifacts(cache_dir, cache_key, artifacts)
        
        return artifacts
        
    except Exception as e:
        logger.error(f"Error generating RESM explainability: {e}")
        return {}


def generate_ahsm_explainability(
    config_path: str | None = None,
    output_dir: Path | None = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Generate explainability artifacts for AHSM model."""
    try:
        from ai.models.ahsm import AHSMConfig, AHSMEnsemble  # noqa: E402
        
        # Check cache first
        if use_cache and output_dir:
            cache_key = _get_cache_key("ahsm", config_path, AHSMConfig().version)
            cache_dir = output_dir.parent / ".cache"
            cached = _load_cached_artifacts(cache_dir, cache_key)
            if cached:
                logger.info("Using cached AHSM explainability artifacts")
                return cached
        
        config = AHSMConfig()
        if config_path:
            config.training_data_path = config_path
        
        ensemble = AHSMEnsemble(config)
        
        external_data = ensemble._load_external_training_data()
        if external_data:
            X, y = external_data
        else:
            X, y = AHSMEnsemble._generate_training_data()
        
        feature_names = ensemble.vector_fields
        
        artifacts = {"shap": {}, "plots": {}, "metadata": {}}
        
        for model_name, model in ensemble._models:
            try:
                shap_data = generate_shap_explanations(
                    model=model,
                    X_train=X,
                    feature_names=feature_names,
                    model_type="classification",
                )
                if shap_data:
                    artifacts["shap"][model_name] = shap_data
                
                plots = generate_yellowbrick_plots(
                    model=model,
                    X_train=X,
                    y_train=y,
                    model_type="classification",
                    feature_names=feature_names,
                    output_dir=output_dir / model_name if output_dir else None,
                )
                if plots:
                    artifacts["plots"][model_name] = plots
                
                # Generate additional SHAP plots
                if output_dir:
                    waterfall = generate_shap_waterfall_plot(
                        model=model,
                        X_sample=X[:1],
                        feature_names=feature_names,
                        output_dir=output_dir / model_name,
                    )
                    if waterfall:
                        if "plots" not in artifacts:
                            artifacts["plots"] = {}
                        if model_name not in artifacts["plots"]:
                            artifacts["plots"][model_name] = {}
                        artifacts["plots"][model_name]["waterfall"] = waterfall
                    
                    dependence = generate_shap_dependence_plots(
                        model=model,
                        X_train=X,
                        feature_names=feature_names,
                        output_dir=output_dir / model_name,
                    )
                    if dependence:
                        if "plots" not in artifacts:
                            artifacts["plots"] = {}
                        if model_name not in artifacts["plots"]:
                            artifacts["plots"][model_name] = {}
                        artifacts["plots"][model_name].update(dependence)
                    
            except Exception as e:
                logger.warning(f"Failed to generate explainability for {model_name}: {e}")
        
        # Save to cache if enabled
        if use_cache and output_dir:
            cache_key = _get_cache_key("ahsm", config_path, config.version)
            cache_dir = output_dir.parent / ".cache"
            from backend.src.analysis.explainability import _save_cached_artifacts
            _save_cached_artifacts(cache_dir, cache_key, artifacts)
        
        return artifacts
        
    except Exception as e:
        logger.error(f"Error generating AHSM explainability: {e}")
        return {}


def generate_cim_explainability(
    config_path: str | None = None,
    output_dir: Path | None = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Generate explainability artifacts for CIM model."""
    try:
        from ai.models.cim import CIMConfig, CIMEnsemble  # noqa: E402
        
        # Check cache first
        if use_cache and output_dir:
            cache_key = _get_cache_key("cim", config_path, CIMConfig().version)
            cache_dir = output_dir.parent / ".cache"
            cached = _load_cached_artifacts(cache_dir, cache_key)
            if cached:
                logger.info("Using cached CIM explainability artifacts")
                return cached
        
        config = CIMConfig()
        if config_path:
            config.training_data_path = config_path
        
        ensemble = CIMEnsemble(config)
        
        external_data = ensemble._load_external_training_data()
        if external_data:
            X, y = external_data
        else:
            X, y = CIMEnsemble._generate_training_data()
        
        feature_names = ensemble.vector_fields
        
        artifacts = {"shap": {}, "plots": {}, "metadata": {}}
        
        for model_name, model in ensemble._models:
            try:
                shap_data = generate_shap_explanations(
                    model=model,
                    X_train=X,
                    feature_names=feature_names,
                    model_type="classification",
                )
                if shap_data:
                    artifacts["shap"][model_name] = shap_data
                
                plots = generate_yellowbrick_plots(
                    model=model,
                    X_train=X,
                    y_train=y,
                    model_type="classification",
                    feature_names=feature_names,
                    output_dir=output_dir / model_name if output_dir else None,
                )
                if plots:
                    artifacts["plots"][model_name] = plots
                
                # Generate additional SHAP plots
                if output_dir:
                    waterfall = generate_shap_waterfall_plot(
                        model=model,
                        X_sample=X[:1],
                        feature_names=feature_names,
                        output_dir=output_dir / model_name,
                    )
                    if waterfall:
                        if "plots" not in artifacts:
                            artifacts["plots"] = {}
                        if model_name not in artifacts["plots"]:
                            artifacts["plots"][model_name] = {}
                        artifacts["plots"][model_name]["waterfall"] = waterfall
                    
                    dependence = generate_shap_dependence_plots(
                        model=model,
                        X_train=X,
                        feature_names=feature_names,
                        output_dir=output_dir / model_name,
                    )
                    if dependence:
                        if "plots" not in artifacts:
                            artifacts["plots"] = {}
                        if model_name not in artifacts["plots"]:
                            artifacts["plots"][model_name] = {}
                        artifacts["plots"][model_name].update(dependence)
                    
            except Exception as e:
                logger.warning(f"Failed to generate explainability for {model_name}: {e}")
        
        # Save to cache if enabled
        if use_cache and output_dir:
            cache_key = _get_cache_key("cim", config_path, config.version)
            cache_dir = output_dir.parent / ".cache"
            from backend.src.analysis.explainability import _save_cached_artifacts
            _save_cached_artifacts(cache_dir, cache_key, artifacts)
        
        return artifacts
        
    except Exception as e:
        logger.error(f"Error generating CIM explainability: {e}")
        return {}

