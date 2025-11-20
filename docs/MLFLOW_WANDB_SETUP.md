# MLflow and Weights & Biases Integration

This document explains how to set up and use MLflow and Weights & Biases (W&B) for experiment tracking and model management in AETHERA.

## Overview

AETHERA integrates both **MLflow** and **Weights & Biases** for:
- **Experiment Tracking**: Log parameters, metrics, and artifacts
- **Model Registry**: Version and manage trained models
- **Reproducibility**: Track dataset versions, code versions, and hyperparameters
- **Visualization**: Compare model performance across runs

## MLflow Setup

### Installation

MLflow is already included in the project dependencies. If needed:

```bash
pip install mlflow
```

### Local MLflow Server

Start a local MLflow tracking server:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns
```

This starts the MLflow UI at `http://localhost:5000`.

### Remote MLflow Server

For production, use a remote MLflow server:

```bash
# Set tracking URI
export MLFLOW_TRACKING_URI=http://your-mlflow-server:5000

# Or in Python
import mlflow
mlflow.set_tracking_uri("http://your-mlflow-server:5000")
```

### Using MLflow in Training

MLflow is enabled by default in all training scripts:

```bash
# Train with MLflow (default)
python -m ai.training.train_biodiversity --training-data data2/biodiversity/training.csv

# Disable MLflow
python -m ai.training.train_biodiversity --no-mlflow --training-data data2/biodiversity/training.csv

# Use custom MLflow URI
python -m ai.training.train_biodiversity --mlflow-uri http://localhost:5000 --training-data data2/biodiversity/training.csv
```

## Weights & Biases Setup

### Installation

W&B is included in dependencies. Install separately if needed:

```bash
pip install wandb
```

### Authentication

1. **Create account**: Sign up at https://wandb.ai
2. **Login**: Run `wandb login` and enter your API key
3. **Configure**: Set project name and entity (optional)

```bash
wandb login
```

### Using W&B in Training

Enable W&B tracking with the `--wandb` flag:

```bash
# Train with W&B
python -m ai.training.train_biodiversity --wandb --training-data data2/biodiversity/training.csv

# Train with both MLflow and W&B
python -m ai.training.train_biodiversity --wandb --training-data data2/biodiversity/training.csv
```

### W&B Configuration

Set environment variables for W&B:

```bash
export WANDB_PROJECT=aethera
export WANDB_ENTITY=your-entity  # Optional
```

Or configure in code:

```python
import wandb
wandb.init(project="aethera", entity="your-entity")
```

## Training Scripts

### Individual Models

Train each model separately:

```bash
# Biodiversity AI
python -m ai.training.train_biodiversity --training-data data2/biodiversity/training.csv

# RESM
python -m ai.training.train_resm --training-data data2/resm/training.csv

# AHSM
python -m ai.training.train_ahsm --training-data data2/ahsm/training.csv

# CIM
python -m ai.training.train_cim --training-data data2/cim/training.csv
```

### Train All Models

Train all models in sequence:

```bash
python -m ai.training.train_all --training-data-dir data2
```

## What Gets Logged

### Parameters
- Model configuration (hyperparameters)
- Dataset source and size
- Training/validation/test split sizes
- Random seed

### Metrics
- **Classification models** (Biodiversity, AHSM, CIM):
  - Accuracy
  - Precision, Recall, F1-score (per class and macro/weighted averages)
- **Regression models** (RESM):
  - MSE, MAE, RMSE
  - R² score

### Artifacts
- Trained models (saved as pickle files)
- Model metadata (JSON)
- Training logs

## Model Registry

### MLflow Model Registry

Register models in MLflow:

```python
import mlflow

# After training, register the best model
mlflow.register_model(
    model_uri=f"runs:/{run_id}/model",
    name="biodiversity_ensemble"
)
```

### Loading Registered Models

```python
import mlflow

# Load from registry
model = mlflow.sklearn.load_model("models:/biodiversity_ensemble/Production")
```

## Best Practices

1. **Use consistent naming**: Use model name and version in run names
2. **Log dataset versions**: Include dataset source and hash in parameters
3. **Compare runs**: Use MLflow UI or W&B dashboard to compare experiments
4. **Tag important runs**: Mark production-ready models with tags
5. **Version control**: Commit code before training to track code versions

## Example Workflow

```bash
# 1. Start MLflow server (optional, uses local file storage by default)
mlflow ui

# 2. Train models with tracking
python -m ai.training.train_all --training-data-dir data2 --wandb

# 3. View results
# - MLflow: http://localhost:5000
# - W&B: https://wandb.ai/your-entity/aethera

# 4. Compare runs and select best models
# 5. Register best models in MLflow registry
# 6. Deploy registered models to production
```

## Troubleshooting

### MLflow Issues

**"MLflow tracking URI not set"**
- MLflow uses local file storage by default (`./mlruns`)
- Set `MLFLOW_TRACKING_URI` environment variable if using remote server

**"Permission denied"**
- Check write permissions for `./mlruns` directory
- Use `--mlflow-uri` to specify different location

### W&B Issues

**"Not logged in"**
- Run `wandb login` to authenticate
- Check API key is valid

**"Project not found"**
- W&B will create project automatically
- Or create project manually at https://wandb.ai

## Integration with Main Pipeline

Models trained with MLflow/W&B can be loaded in the main pipeline:

```python
import mlflow

# Load model from MLflow
model = mlflow.sklearn.load_model("models:/biodiversity_ensemble/latest")

# Use in prediction
prediction = model.predict(features)
```

The main controller automatically logs model metadata to the `model_runs` database table, which can be cross-referenced with MLflow/W&B runs using the run ID.

## References

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Weights & Biases Documentation](https://docs.wandb.ai/)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)

