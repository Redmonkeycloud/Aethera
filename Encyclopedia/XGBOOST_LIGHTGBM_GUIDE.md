# XGBoost/LightGBM Implementation Guide

**Last Updated**: 2026-01-10

## Overview

XGBoost and LightGBM have been successfully integrated into all AETHERA ML models (Biodiversity, RESM, AHSM, CIM). These models are now automatically included in the ensemble when dependencies are installed.

## Installation

The dependencies are already added to `backend/pyproject.toml`. Install them with:

```bash
pip install xgboost lightgbm optuna
```

Or if using the project dependencies:

```bash
cd backend
pip install -e .
```

## Features

### 1. Automatic Integration

XGBoost and LightGBM models are **automatically** added to all ensemble models when dependencies are installed:

- **Biodiversity Model**: XGBoost and LightGBM classifiers
- **RESM Model**: XGBoost and LightGBM regressors
- **AHSM Model**: XGBoost and LightGBM classifiers
- **CIM Model**: XGBoost and LightGBM classifiers

The models automatically:
- Select the correct objective function (binary/multi-class/regression)
- Fit with appropriate parameters
- Participate in ensemble averaging
- Fall back gracefully if dependencies are not installed

### 2. Model Benchmarking

Compare performance across all model types:

```bash
# Benchmark all models
python scripts/benchmark_models.py --model all --output benchmarks.json

# Benchmark specific model
python scripts/benchmark_models.py --model biodiversity --output biodiversity_benchmarks.json
```

**Metrics Reported:**
- Accuracy/R² Score
- Training Time
- Inference Time (per sample)
- Cross-Validation Scores (mean, std, min, max)

**Example Output:**
```
Biodiversity Model Benchmark Summary
================================================================================
Best Accuracy: XGBoost
Fastest Training: Logistic Regression
Fastest Inference: LightGBM
Best CV: XGBoost
```

### 3. Hyperparameter Optimization

Optimize XGBoost and LightGBM hyperparameters using Optuna:

```bash
# Optimize all models (100 trials)
python scripts/optimize_hyperparameters.py --model all --n-trials 100 --output optimized_params.json

# Optimize specific model with timeout
python scripts/optimize_hyperparameters.py --model resm --n-trials 200 --timeout 3600 --output resm_optimized.json
```

**Optimized Parameters:**
- XGBoost: `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`, `min_child_weight`, `gamma`, `reg_alpha`, `reg_lambda`
- LightGBM: `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`, `min_child_samples`, `num_leaves`, `reg_alpha`, `reg_lambda`

**Results Saved:**
- Best hyperparameters for each model
- Best cross-validation score achieved
- JSON format for easy integration

### 4. Model Selection Pipeline

The `ModelBenchmarker` class provides a flexible model selection pipeline:

```python
from ai.utils.model_selection import ModelBenchmarker
import numpy as np

# Create benchmarker
benchmarker = ModelBenchmarker(X, y, test_size=0.2, random_state=42)

# Benchmark models
benchmarker.benchmark_model(model1, "Random Forest")
benchmarker.benchmark_model(model2, "XGBoost")
benchmarker.benchmark_model(model3, "LightGBM")

# Get best model by metric
best_model = benchmarker.get_best_model("accuracy")
fastest_model = benchmarker.get_best_model("inference_time")

# Get summary
summary = benchmarker.get_summary()
```

## Usage in Production

### Automatic Usage

When you run an analysis, XGBoost and LightGBM models are **automatically** included if dependencies are installed. No configuration needed!

### Manual Configuration

To use optimized hyperparameters, you can load them from the optimization results:

```python
import json
import xgboost as xgb

# Load optimized parameters
with open("optimized_params.json") as f:
    results = json.load(f)

xgb_params = results["biodiversity"]["xgboost"]["best_params"]

# Create model with optimized parameters
model = xgb.XGBClassifier(**xgb_params)
```

## Performance Comparison

### Expected Performance (Typical Results)

| Model Type | XGBoost | LightGBM | Gradient Boosting | Random Forest |
|------------|---------|----------|-------------------|---------------|
| **Accuracy/R²** | High | High | Medium-High | Medium |
| **Training Time** | Medium | Fast | Slow | Medium |
| **Inference Time** | Fast | Very Fast | Medium | Medium |
| **Memory Usage** | Low | Very Low | Medium | High |

**Notes:**
- XGBoost typically achieves the best accuracy but is slower to train
- LightGBM is fastest for training and inference with competitive accuracy
- Gradient Boosting (scikit-learn) is a good baseline
- Random Forest provides interpretability but uses more memory

## Troubleshooting

### XGBoost/LightGBM Not Included in Ensemble

**Check if dependencies are installed:**
```bash
python -c "import xgboost; import lightgbm; print('OK')"
```

**Check model logs:**
- Look for "XGBoost model added to ensemble" messages
- Check for "XGBoost not available" warnings

### Import Errors

If you see import errors, install dependencies:
```bash
pip install xgboost lightgbm optuna
```

### Performance Issues

If optimization is slow:
- Reduce `--n-trials` (e.g., 50 instead of 100)
- Set `--timeout` to limit execution time
- Use fewer CV folds in `OptunaHyperparameterOptimizer`

## Best Practices

1. **Benchmark First**: Run benchmarks to understand baseline performance
2. **Optimize Selectively**: Focus optimization on models that show promise
3. **Validate Results**: Always validate optimized parameters on a holdout set
4. **Monitor Performance**: Track model performance over time using metrics API

## Integration with Existing Code

XGBoost and LightGBM are **seamlessly integrated**:

- ✅ Models automatically included in `_train_models()` methods
- ✅ Participate in ensemble averaging in `predict()` methods
- ✅ Work with existing explainability (SHAP, Yellowbrick)
- ✅ Compatible with pretrained model loading
- ✅ Support all existing training data formats

## Next Steps

1. **Run Benchmarks**: Compare XGBoost/LightGBM vs. current models
   ```bash
   python scripts/benchmark_models.py --model all --output benchmarks.json
   ```

2. **Optimize Hyperparameters**: Find best parameters for your data
   ```bash
   python scripts/optimize_hyperparameters.py --model all --n-trials 100
   ```

3. **Integrate Optimized Parameters**: Use optimized parameters in model training (future enhancement)

4. **Monitor Performance**: Use metrics API to track model performance over time

## Related Files

- **Model Implementation**: `ai/models/*.py` (biodiversity.py, resm.py, ahsm.py, cim.py)
- **Model Selection Utilities**: `ai/utils/model_selection.py`
- **Benchmarking Script**: `scripts/benchmark_models.py`
- **Optimization Script**: `scripts/optimize_hyperparameters.py`
- **Dependencies**: `backend/pyproject.toml`

## Support

For issues or questions:
1. Check logs for error messages
2. Verify dependencies are installed
3. Review benchmark results for performance insights
4. Consult Optuna documentation for optimization parameters

---

**Status**: ✅ **COMPLETE** (2026-01-10)
All XGBoost/LightGBM features are implemented and ready to use!
