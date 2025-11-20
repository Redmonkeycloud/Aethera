# Model Governance

Comprehensive model governance system for tracking, validating, and managing ML models throughout their lifecycle.

## Overview

The Model Governance system provides:
- **Model Registry**: Centralized versioning and lifecycle management
- **Drift Detection**: Monitor data and concept drift
- **A/B Testing**: Compare model versions statistically
- **Validation Metrics**: Track model performance over time

## Model Registry

### Registering Models

Register a new model version with metadata:

```python
from backend.src.governance import ModelRegistry
from backend.src.governance.registry import ModelStage
from backend.src.db.client import DatabaseClient

db_client = DatabaseClient(settings.postgres_dsn)
registry = ModelRegistry(db_client)

entry = registry.register_model(
    model_name="biodiversity_ensemble",
    version="0.2.0",
    stage=ModelStage.DEVELOPMENT,
    description="Improved biodiversity model with new features",
    model_path="/models/biodiversity_v0.2.0.pkl",
    training_data_path="/data/training_biodiversity_v2.csv",
    hyperparameters={
        "learning_rate": 0.01,
        "n_estimators": 100,
    },
    training_metadata={
        "training_date": "2024-01-15",
        "dataset_size": 10000,
    },
    created_by="data_scientist",
)
```

### Model Stages

Models progress through stages:
- **development**: Initial development and testing
- **staging**: Pre-production validation
- **production**: Live deployment
- **archived**: Deprecated models

### Promoting Models

Promote a model to production:

```python
promoted = registry.promote_model(
    model_name="biodiversity_ensemble",
    version="0.2.0",
    target_stage=ModelStage.PRODUCTION,
    approved_by="ml_lead",
)
```

### Retrieving Models

```python
# Get specific version
model = registry.get_model("biodiversity_ensemble", "0.2.0")

# Get latest version
latest = registry.get_latest_version("biodiversity_ensemble", stage=ModelStage.PRODUCTION)

# List all models
all_models = registry.list_models(model_name="biodiversity_ensemble", limit=10)
```

## Validation Metrics

### Logging Metrics

Track model performance metrics:

```python
from backend.src.governance import ValidationMetricsTracker
from backend.src.governance.validation import MetricType

tracker = ValidationMetricsTracker(db_client)

# Log individual metric
tracker.log_metric(
    model_name="biodiversity_ensemble",
    model_version="0.2.0",
    metric_name="accuracy",
    metric_value=0.95,
    metric_type=MetricType.CLASSIFICATION,
    dataset_split="test",
)
```

### Classification Metrics

Automatically calculate and log classification metrics:

```python
y_true = [0, 1, 0, 1, 1, 0]
y_pred = [0, 1, 0, 1, 0, 0]

metrics = tracker.evaluate_classification(
    model_name="biodiversity_ensemble",
    model_version="0.2.0",
    y_true=y_true,
    y_pred=y_pred,
    dataset_split="test",
)

# Returns: accuracy, precision, recall, f1
```

### Regression Metrics

Automatically calculate and log regression metrics:

```python
y_true = [1.0, 2.0, 3.0, 4.0]
y_pred = [1.1, 2.1, 2.9, 4.2]

metrics = tracker.evaluate_regression(
    model_name="resm_ensemble",
    model_version="0.1.0",
    y_true=y_true,
    y_pred=y_pred,
    dataset_split="validation",
)

# Returns: mae, mse, rmse, r2
```

### Retrieving Metrics

```python
# Get all metrics for a model
metrics = tracker.get_metrics(
    model_name="biodiversity_ensemble",
    model_version="0.2.0",
    dataset_split="test",
)
```

## Drift Detection

### Data Drift

Detect distribution shifts in input features:

```python
from backend.src.governance import DriftDetector
import pandas as pd
import numpy as np

detector = DriftDetector(db_client)

# Reference data (baseline)
reference_data = pd.DataFrame({
    "feature1": np.random.normal(0, 1, 1000),
    "feature2": np.random.normal(5, 2, 1000),
})

# Current data
current_data = pd.DataFrame({
    "feature1": np.random.normal(2, 1, 1000),  # Shifted
    "feature2": np.random.normal(5, 2, 1000),
})

alerts = detector.detect_data_drift(
    model_name="biodiversity_ensemble",
    model_version="0.2.0",
    reference_data=reference_data,
    current_data=current_data,
    threshold=0.2,  # Alert if drift > 0.2
    method="ks_test",  # Kolmogorov-Smirnov test
)
```

### Prediction Drift

Detect shifts in model predictions:

```python
reference_predictions = np.random.normal(50, 10, 1000)
current_predictions = np.random.normal(60, 10, 1000)

alert = detector.detect_prediction_drift(
    model_name="biodiversity_ensemble",
    model_version="0.2.0",
    reference_predictions=reference_predictions,
    current_predictions=current_predictions,
    threshold=0.2,
)
```

### Detection Methods

- **ks_test**: Kolmogorov-Smirnov test (default)
- **psi**: Population Stability Index
- **chi_square**: Chi-square test (for categorical data)

### Retrieving Alerts

```python
# Get all alerts
alerts = detector.get_drift_alerts(
    model_name="biodiversity_ensemble",
    is_alert=True,  # Only active alerts
    limit=100,
)

# Acknowledge an alert
detector.acknowledge_alert(alert_id=alert.id, acknowledged_by="data_scientist")
```

## A/B Testing

### Creating an A/B Test

Compare two model versions:

```python
from backend.src.governance import ABTestManager

manager = ABTestManager(db_client)

test = manager.create_test(
    test_name="biodiversity_v2_vs_v1",
    model_a_name="biodiversity_ensemble",
    model_a_version="0.1.0",  # Control
    model_b_name="biodiversity_ensemble",
    model_b_version="0.2.0",  # Treatment
    success_metric="accuracy",
    traffic_split=0.5,  # 50% to model B
    min_samples=100,  # Minimum samples before evaluation
    success_threshold=0.02,  # 2% improvement required
    statistical_test="t_test",
    significance_level=0.05,
    created_by="ml_engineer",
)
```

### Running the Test

```python
# Start the test
test = manager.start_test(test.id)

# Collect results (in production, this would be done automatically)
model_a_results = [0.85, 0.87, 0.86, ...]  # Accuracy scores
model_b_results = [0.90, 0.91, 0.89, ...]

# Evaluate
result = manager.evaluate_test(
    test_id=test.id,
    model_a_results=model_a_results,
    model_b_results=model_b_results,
)

print(f"Model B improvement: {result.relative_improvement}%")
print(f"Statistically significant: {result.is_significant}")
print(f"P-value: {result.p_value}")
```

### Retrieving Test Results

```python
# Get test details
test = manager.get_test(test_id)

# Get results
results = manager.get_test_results(test_id)

# List all tests
tests = manager.list_tests(status=ABTestStatus.RUNNING)
```

## API Endpoints

### Model Registry

- `POST /governance/models/register` - Register a new model
- `GET /governance/models` - List models
- `GET /governance/models/{model_name}/{version}` - Get specific model
- `GET /governance/models/{model_name}/latest` - Get latest version
- `POST /governance/models/{model_name}/{version}/promote` - Promote model

### Validation Metrics

- `POST /governance/models/{model_name}/{version}/metrics` - Log metric
- `GET /governance/models/{model_name}/{version}/metrics` - Get metrics

### Drift Detection

- `GET /governance/drift/alerts` - Get drift alerts
- `POST /governance/drift/alerts/{alert_id}/acknowledge` - Acknowledge alert

### A/B Testing

- `POST /governance/ab-tests` - Create A/B test
- `POST /governance/ab-tests/{test_id}/start` - Start test
- `GET /governance/ab-tests` - List tests
- `GET /governance/ab-tests/{test_id}` - Get test details
- `GET /governance/ab-tests/{test_id}/results` - Get test results

## Configuration

Configure model governance in `base_settings.py`:

```python
# Model Governance configuration
enable_model_registry: bool = True
enable_drift_detection: bool = True
drift_threshold: float = 0.2
drift_detection_method: str = "ks_test"
```

## Integration with Existing Pipeline

The model governance system integrates with the existing model logging in `main_controller.py`. Models are automatically registered when they are used in analysis runs.

## Best Practices

1. **Register models early**: Register models as soon as they are trained
2. **Track all metrics**: Log validation metrics for all dataset splits
3. **Monitor drift regularly**: Set up scheduled drift detection
4. **Use A/B tests**: Compare new models before promoting to production
5. **Document changes**: Include descriptions when registering new versions
6. **Approve promotions**: Require approval for production promotions

## Database Schema

The governance system uses the following tables:
- `model_registry`: Model versions and metadata
- `model_validation_metrics`: Performance metrics
- `model_drift_detection`: Drift alerts
- `model_ab_tests`: A/B test configurations
- `model_ab_test_results`: A/B test results

See `backend/src/db/schema.sql` for full schema definitions.

