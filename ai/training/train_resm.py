# ai/training/train_resm.py

import os
import sys
import yaml
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from ai.models.suitability_model import RESMModel
from utils.logging_utils import setup_logger, log_step, log_exception

# --- Load config ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'resm_config.yaml')

with open(CONFIG_PATH, 'r') as file:
    config = yaml.safe_load(file)

# --- Setup logger ---
logger = setup_logger("RESM_Training", "RESM")

try:
    log_step(logger, "Started RESM training pipeline.")

    # --- Load data ---
    data_path = config['data']['path']
    df = pd.read_csv(data_path)
    log_step(logger, f"Loaded dataset from {data_path} with shape {df.shape}")

    target_column = config['data']['target_column']
    feature_columns = config['data']['features']

    X = df[feature_columns]
    y = df[target_column]

    # --- Split data ---
    test_size = config['training']['test_size']
    random_state = config['training'].get('random_state', 42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    log_step(logger, f"Split data: train={X_train.shape[0]} rows, test={X_test.shape[0]} rows")

    # --- Train model ---
    model_params = config['model']
    model = RESMModel(**model_params)
    model.train(X_train, y_train)

    log_step(logger, "Model training completed.")

    # --- Evaluate ---
    predictions = model.predict(X_test)
    rmse = mean_squared_error(y_test, predictions, squared=False)
    r2 = r2_score(y_test, predictions)

    log_step(logger, f"Evaluation - RMSE: {rmse:.3f}, R²: {r2:.3f}")

    # --- Save model ---
    output_dir = config['output']['model_dir']
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "resm_model.pkl")
    joblib.dump(model.model, model_path)

    log_step(logger, f"Saved trained model to {model_path}")
    log_step(logger, "RESM training pipeline finished successfully.")

except Exception as e:
    log_exception(logger, "Unhandled exception during RESM training pipeline", e)
    sys.exit(1)
