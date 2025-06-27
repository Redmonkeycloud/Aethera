# ai/models/resm_model.py

import os
import logging
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor

from ai.config.resm_config import RESM_CONFIG

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RESM")

def get_model(model_type: str, hyperparams: dict):
    """Factory method to initialize model."""
    logger.info(f"Initializing model: {model_type}")
    if model_type == "RandomForest":
        return RandomForestRegressor(**hyperparams)
    elif model_type == "GradientBoosting":
        return GradientBoostingRegressor(**hyperparams)
    elif model_type == "XGBoost":
        return XGBRegressor(**hyperparams)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

def train_and_save_model(X, y, model_save_path):
    """Train the RESM model and persist it."""
    model_type = RESM_CONFIG["model_type"]
    hyperparams = RESM_CONFIG["hyperparameters"]
    model = get_model(model_type, hyperparams)

    logger.info(f"Training {model_type} model on {X.shape[0]} samples...")
    model.fit(X, y)
    
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    joblib.dump(model, model_save_path)
    logger.info(f"Model saved to: {model_save_path}")
    return model

def load_model(model_path):
    """Load a pre-trained RESM model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    logger.info(f"Loading model from {model_path}")
    return joblib.load(model_path)
