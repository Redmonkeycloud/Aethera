"""Optimize hyperparameters using Optuna for all models."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.models import BiodiversityEnsemble, RESMEnsemble, AHSMEnsemble, CIMEnsemble
from ai.utils.model_selection import OptunaHyperparameterOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def optimize_biodiversity(n_trials: int = 100, timeout: int | None = None):
    """Optimize Biodiversity model hyperparameters."""
    logger.info("=" * 80)
    logger.info("Optimizing Biodiversity Model Hyperparameters")
    logger.info("=" * 80)
    
    # Generate training data (static method, no need to instantiate)
    X, y = BiodiversityEnsemble._generate_training_data(n=1000)
    
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Classes: {len(np.unique(y))}")
    
    results = {}
    
    # Optimize XGBoost
    try:
        optimizer = OptunaHyperparameterOptimizer(
            X, y, model_type="classification", n_trials=n_trials, timeout=timeout
        )
        xgb_params = optimizer.optimize_xgboost()
        results["xgboost"] = {
            "best_params": xgb_params,
            "best_score": optimizer.best_score,
        }
        logger.info(f"XGBoost best CV score: {optimizer.best_score:.4f}")
    except Exception as e:
        logger.error(f"XGBoost optimization failed: {e}")
        results["xgboost"] = {"error": str(e)}
    
    # Optimize LightGBM
    try:
        optimizer = OptunaHyperparameterOptimizer(
            X, y, model_type="classification", n_trials=n_trials, timeout=timeout
        )
        lgb_params = optimizer.optimize_lightgbm()
        results["lightgbm"] = {
            "best_params": lgb_params,
            "best_score": optimizer.best_score,
        }
        logger.info(f"LightGBM best CV score: {optimizer.best_score:.4f}")
    except Exception as e:
        logger.error(f"LightGBM optimization failed: {e}")
        results["lightgbm"] = {"error": str(e)}
    
    return results


def optimize_resm(n_trials: int = 100, timeout: int | None = None):
    """Optimize RESM model hyperparameters."""
    logger.info("\n" + "=" * 80)
    logger.info("Optimizing RESM Model Hyperparameters")
    logger.info("=" * 80)
    
    # Generate training data (static method, no need to instantiate)
    X, y = RESMEnsemble._generate_training_data(n=1000)
    
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    
    results = {}
    
    # Optimize XGBoost
    try:
        optimizer = OptunaHyperparameterOptimizer(
            X, y, model_type="regression", n_trials=n_trials, timeout=timeout
        )
        xgb_params = optimizer.optimize_xgboost()
        results["xgboost"] = {
            "best_params": xgb_params,
            "best_score": optimizer.best_score,
        }
        logger.info(f"XGBoost best CV score (R²): {optimizer.best_score:.4f}")
    except Exception as e:
        logger.error(f"XGBoost optimization failed: {e}")
        results["xgboost"] = {"error": str(e)}
    
    # Optimize LightGBM
    try:
        optimizer = OptunaHyperparameterOptimizer(
            X, y, model_type="regression", n_trials=n_trials, timeout=timeout
        )
        lgb_params = optimizer.optimize_lightgbm()
        results["lightgbm"] = {
            "best_params": lgb_params,
            "best_score": optimizer.best_score,
        }
        logger.info(f"LightGBM best CV score (R²): {optimizer.best_score:.4f}")
    except Exception as e:
        logger.error(f"LightGBM optimization failed: {e}")
        results["lightgbm"] = {"error": str(e)}
    
    return results


def optimize_ahsm(n_trials: int = 100, timeout: int | None = None):
    """Optimize AHSM model hyperparameters."""
    logger.info("\n" + "=" * 80)
    logger.info("Optimizing AHSM Model Hyperparameters")
    logger.info("=" * 80)
    
    # Generate training data (static method, no need to instantiate)
    X, y = AHSMEnsemble._generate_training_data(n=1000)
    
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Classes: {len(np.unique(y))}")
    
    results = {}
    
    # Optimize XGBoost
    try:
        optimizer = OptunaHyperparameterOptimizer(
            X, y, model_type="classification", n_trials=n_trials, timeout=timeout
        )
        xgb_params = optimizer.optimize_xgboost()
        results["xgboost"] = {
            "best_params": xgb_params,
            "best_score": optimizer.best_score,
        }
        logger.info(f"XGBoost best CV score: {optimizer.best_score:.4f}")
    except Exception as e:
        logger.error(f"XGBoost optimization failed: {e}")
        results["xgboost"] = {"error": str(e)}
    
    # Optimize LightGBM
    try:
        optimizer = OptunaHyperparameterOptimizer(
            X, y, model_type="classification", n_trials=n_trials, timeout=timeout
        )
        lgb_params = optimizer.optimize_lightgbm()
        results["lightgbm"] = {
            "best_params": lgb_params,
            "best_score": optimizer.best_score,
        }
        logger.info(f"LightGBM best CV score: {optimizer.best_score:.4f}")
    except Exception as e:
        logger.error(f"LightGBM optimization failed: {e}")
        results["lightgbm"] = {"error": str(e)}
    
    return results


def optimize_cim(n_trials: int = 100, timeout: int | None = None):
    """Optimize CIM model hyperparameters."""
    logger.info("\n" + "=" * 80)
    logger.info("Optimizing CIM Model Hyperparameters")
    logger.info("=" * 80)
    
    # Generate training data (static method, no need to instantiate)
    X, y = CIMEnsemble._generate_training_data(n=1000)
    
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Classes: {len(np.unique(y))}")
    
    results = {}
    
    # Optimize XGBoost
    try:
        optimizer = OptunaHyperparameterOptimizer(
            X, y, model_type="classification", n_trials=n_trials, timeout=timeout
        )
        xgb_params = optimizer.optimize_xgboost()
        results["xgboost"] = {
            "best_params": xgb_params,
            "best_score": optimizer.best_score,
        }
        logger.info(f"XGBoost best CV score: {optimizer.best_score:.4f}")
    except Exception as e:
        logger.error(f"XGBoost optimization failed: {e}")
        results["xgboost"] = {"error": str(e)}
    
    # Optimize LightGBM
    try:
        optimizer = OptunaHyperparameterOptimizer(
            X, y, model_type="classification", n_trials=n_trials, timeout=timeout
        )
        lgb_params = optimizer.optimize_lightgbm()
        results["lightgbm"] = {
            "best_params": lgb_params,
            "best_score": optimizer.best_score,
        }
        logger.info(f"LightGBM best CV score: {optimizer.best_score:.4f}")
    except Exception as e:
        logger.error(f"LightGBM optimization failed: {e}")
        results["lightgbm"] = {"error": str(e)}
    
    return results


def main():
    """Run hyperparameter optimization for all models."""
    parser = argparse.ArgumentParser(description="Optimize hyperparameters for all ML models")
    parser.add_argument("--model", choices=["biodiversity", "resm", "ahsm", "cim", "all"], default="all")
    parser.add_argument("--n-trials", type=int, default=100, help="Number of Optuna trials")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")
    parser.add_argument("--output", type=str, help="Output JSON file for results")
    args = parser.parse_args()
    
    all_results = {}
    
    try:
        if args.model in ["biodiversity", "all"]:
            all_results["biodiversity"] = optimize_biodiversity(args.n_trials, args.timeout)
        
        if args.model in ["resm", "all"]:
            all_results["resm"] = optimize_resm(args.n_trials, args.timeout)
        
        if args.model in ["ahsm", "all"]:
            all_results["ahsm"] = optimize_ahsm(args.n_trials, args.timeout)
        
        if args.model in ["cim", "all"]:
            all_results["cim"] = optimize_cim(args.n_trials, args.timeout)
        
        # Save results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(all_results, f, indent=2)
            logger.info(f"\nResults saved to {args.output}")
        
        logger.info("\n" + "=" * 80)
        logger.info("Hyperparameter Optimization Complete!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
