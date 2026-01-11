"""Benchmark all models and compare performance."""

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
from ai.utils.model_selection import ModelBenchmarker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def benchmark_biodiversity():
    """Benchmark Biodiversity model."""
    logger.info("=" * 80)
    logger.info("Benchmarking Biodiversity Model")
    logger.info("=" * 80)
    
    model = BiodiversityEnsemble()
    
    # Generate training data
    X, y = model._generate_training_data(n=1000)
    
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Classes: {len(np.unique(y))}")
    
    # Create benchmarker
    benchmarker = ModelBenchmarker(X, y, test_size=0.2, random_state=42)
    
    # Benchmark each model type
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    
    # Logistic Regression
    lr = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=500))])
    benchmarker.benchmark_model(lr, "Logistic Regression", scoring="accuracy")
    
    # Random Forest
    rf = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=7)
    benchmarker.benchmark_model(rf, "Random Forest", scoring="accuracy")
    
    # Gradient Boosting
    gb = GradientBoostingClassifier(max_depth=3, random_state=21)
    benchmarker.benchmark_model(gb, "Gradient Boosting", scoring="accuracy")
    
    # XGBoost
    try:
        import xgboost as xgb
        n_classes = len(np.unique(y))
        xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective="binary:logistic" if n_classes == 2 else "multi:softprob",
            random_state=21,
            n_jobs=-1,
        )
        benchmarker.benchmark_model(xgb_model, "XGBoost", scoring="accuracy")
    except ImportError:
        logger.warning("XGBoost not available")
    
    # LightGBM
    try:
        import lightgbm as lgb
        n_classes = len(np.unique(y))
        lgb_model = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective="binary" if n_classes == 2 else "multiclass",
            random_state=21,
            n_jobs=-1,
            verbose=-1,
        )
        benchmarker.benchmark_model(lgb_model, "LightGBM", scoring="accuracy")
    except ImportError:
        logger.warning("LightGBM not available")
    
    # Print summary
    summary = benchmarker.get_summary()
    logger.info("\n" + "=" * 80)
    logger.info("Biodiversity Model Benchmark Summary")
    logger.info("=" * 80)
    logger.info(f"Best Accuracy: {summary.get('best_accuracy', 'N/A')}")
    logger.info(f"Fastest Training: {summary.get('fastest_training', 'N/A')}")
    logger.info(f"Fastest Inference: {summary.get('fastest_inference', 'N/A')}")
    logger.info(f"Best CV: {summary.get('best_cv', 'N/A')}")
    
    return summary


def benchmark_resm():
    """Benchmark RESM model."""
    logger.info("\n" + "=" * 80)
    logger.info("Benchmarking RESM Model")
    logger.info("=" * 80)
    
    model = RESMEnsemble()
    
    # Generate training data
    X, y = model._generate_training_data(n=1000)
    
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    
    # Create benchmarker
    benchmarker = ModelBenchmarker(X, y, test_size=0.2, random_state=42)
    
    # Benchmark each model type
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    
    # Ridge Regression
    ridge = Pipeline([("scaler", StandardScaler()), ("reg", Ridge(alpha=1.0))])
    benchmarker.benchmark_model(ridge, "Ridge Regression", scoring="r2")
    
    # Random Forest
    rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=7)
    benchmarker.benchmark_model(rf, "Random Forest", scoring="r2")
    
    # Gradient Boosting
    gb = GradientBoostingRegressor(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=21)
    benchmarker.benchmark_model(gb, "Gradient Boosting", scoring="r2")
    
    # XGBoost
    try:
        import xgboost as xgb
        xgb_model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective="reg:squarederror",
            random_state=21,
            n_jobs=-1,
        )
        benchmarker.benchmark_model(xgb_model, "XGBoost", scoring="r2")
    except ImportError:
        logger.warning("XGBoost not available")
    
    # LightGBM
    try:
        import lightgbm as lgb
        lgb_model = lgb.LGBMRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective="regression",
            random_state=21,
            n_jobs=-1,
            verbose=-1,
        )
        benchmarker.benchmark_model(lgb_model, "LightGBM", scoring="r2")
    except ImportError:
        logger.warning("LightGBM not available")
    
    # Print summary
    summary = benchmarker.get_summary()
    logger.info("\n" + "=" * 80)
    logger.info("RESM Model Benchmark Summary")
    logger.info("=" * 80)
    logger.info(f"Best R²: {summary.get('best_accuracy', 'N/A')}")
    logger.info(f"Fastest Training: {summary.get('fastest_training', 'N/A')}")
    logger.info(f"Fastest Inference: {summary.get('fastest_inference', 'N/A')}")
    logger.info(f"Best CV: {summary.get('best_cv', 'N/A')}")
    
    return summary


def benchmark_ahsm():
    """Benchmark AHSM model."""
    logger.info("\n" + "=" * 80)
    logger.info("Benchmarking AHSM Model")
    logger.info("=" * 80)
    
    model = AHSMEnsemble()
    
    # Generate training data
    X, y = model._generate_training_data(n=1000)
    
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Classes: {len(np.unique(y))}")
    
    # Create benchmarker
    benchmarker = ModelBenchmarker(X, y, test_size=0.2, random_state=42)
    
    # Benchmark each model type (similar to biodiversity)
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    
    # Logistic Regression
    lr = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=500))])
    benchmarker.benchmark_model(lr, "Logistic Regression", scoring="accuracy")
    
    # Random Forest
    rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=7)
    benchmarker.benchmark_model(rf, "Random Forest", scoring="accuracy")
    
    # Gradient Boosting
    gb = GradientBoostingClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=21)
    benchmarker.benchmark_model(gb, "Gradient Boosting", scoring="accuracy")
    
    # XGBoost
    try:
        import xgboost as xgb
        n_classes = len(np.unique(y))
        xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective="binary:logistic" if n_classes == 2 else "multi:softprob",
            random_state=21,
            n_jobs=-1,
        )
        benchmarker.benchmark_model(xgb_model, "XGBoost", scoring="accuracy")
    except ImportError:
        logger.warning("XGBoost not available")
    
    # LightGBM
    try:
        import lightgbm as lgb
        n_classes = len(np.unique(y))
        lgb_model = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective="binary" if n_classes == 2 else "multiclass",
            random_state=21,
            n_jobs=-1,
            verbose=-1,
        )
        benchmarker.benchmark_model(lgb_model, "LightGBM", scoring="accuracy")
    except ImportError:
        logger.warning("LightGBM not available")
    
    # Print summary
    summary = benchmarker.get_summary()
    logger.info("\n" + "=" * 80)
    logger.info("AHSM Model Benchmark Summary")
    logger.info("=" * 80)
    logger.info(f"Best Accuracy: {summary.get('best_accuracy', 'N/A')}")
    logger.info(f"Fastest Training: {summary.get('fastest_training', 'N/A')}")
    logger.info(f"Fastest Inference: {summary.get('fastest_inference', 'N/A')}")
    logger.info(f"Best CV: {summary.get('best_cv', 'N/A')}")
    
    return summary


def benchmark_cim():
    """Benchmark CIM model."""
    logger.info("\n" + "=" * 80)
    logger.info("Benchmarking CIM Model")
    logger.info("=" * 80)
    
    model = CIMEnsemble()
    
    # Generate training data
    X, y = model._generate_training_data(n=1000)
    
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Classes: {len(np.unique(y))}")
    
    # Create benchmarker
    benchmarker = ModelBenchmarker(X, y, test_size=0.2, random_state=42)
    
    # Benchmark each model type (similar to biodiversity)
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    
    # Logistic Regression
    lr = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=500))])
    benchmarker.benchmark_model(lr, "Logistic Regression", scoring="accuracy")
    
    # Random Forest
    rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=7)
    benchmarker.benchmark_model(rf, "Random Forest", scoring="accuracy")
    
    # Gradient Boosting
    gb = GradientBoostingClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=21)
    benchmarker.benchmark_model(gb, "Gradient Boosting", scoring="accuracy")
    
    # XGBoost
    try:
        import xgboost as xgb
        n_classes = len(np.unique(y))
        xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective="binary:logistic" if n_classes == 2 else "multi:softprob",
            random_state=21,
            n_jobs=-1,
        )
        benchmarker.benchmark_model(xgb_model, "XGBoost", scoring="accuracy")
    except ImportError:
        logger.warning("XGBoost not available")
    
    # LightGBM
    try:
        import lightgbm as lgb
        n_classes = len(np.unique(y))
        lgb_model = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective="binary" if n_classes == 2 else "multiclass",
            random_state=21,
            n_jobs=-1,
            verbose=-1,
        )
        benchmarker.benchmark_model(lgb_model, "LightGBM", scoring="accuracy")
    except ImportError:
        logger.warning("LightGBM not available")
    
    # Print summary
    summary = benchmarker.get_summary()
    logger.info("\n" + "=" * 80)
    logger.info("CIM Model Benchmark Summary")
    logger.info("=" * 80)
    logger.info(f"Best Accuracy: {summary.get('best_accuracy', 'N/A')}")
    logger.info(f"Fastest Training: {summary.get('fastest_training', 'N/A')}")
    logger.info(f"Fastest Inference: {summary.get('fastest_inference', 'N/A')}")
    logger.info(f"Best CV: {summary.get('best_cv', 'N/A')}")
    
    return summary


def main():
    """Run benchmarks for all models."""
    parser = argparse.ArgumentParser(description="Benchmark all ML models")
    parser.add_argument("--model", choices=["biodiversity", "resm", "ahsm", "cim", "all"], default="all")
    parser.add_argument("--output", type=str, help="Output JSON file for results")
    args = parser.parse_args()
    
    results = {}
    
    try:
        if args.model in ["biodiversity", "all"]:
            results["biodiversity"] = benchmark_biodiversity()
        
        if args.model in ["resm", "all"]:
            results["resm"] = benchmark_resm()
        
        if args.model in ["ahsm", "all"]:
            results["ahsm"] = benchmark_ahsm()
        
        if args.model in ["cim", "all"]:
            results["cim"] = benchmark_cim()
        
        # Save results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"\nResults saved to {args.output}")
        
        logger.info("\n" + "=" * 80)
        logger.info("Benchmarking Complete!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Benchmarking failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
