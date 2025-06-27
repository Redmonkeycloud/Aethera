# ai/config/resm_config.py

import os

# Project base directory (adjust if needed)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to training data
TRAIN_DATA_PATH = os.path.join(BASE_DIR, "data_preprocessing", "resm_training_data.csv")

# Path where trained model will be saved
MODEL_OUTPUT_PATH = os.path.join(BASE_DIR, "models", "resm_model.pkl")

# Features used in training (update based on your dataset)
RESM_FEATURES = [
    "avg_wind_speed",      # in m/s
    "solar_radiation",     # in kWh/m²/day
    "land_slope",          # in degrees
    "proximity_to_grid",   # in meters
    "elevation",           # in meters
    "protected_area",      # binary 0/1
    "land_cover_code",     # encoded CLC or similar
    "population_density"   # persons per km²
]

# Target variable
RESM_TARGET = "suitability_score"

# Model hyperparameters (for RandomForest, XGBoost, etc.)
RESM_MODEL_PARAMS = {
    "n_estimators": 100,
    "max_depth": 10,
    "random_state": 42,
    "n_jobs": -1
}

# Scoring metric to evaluate performance
SCORING_METRIC = "r2"  # Alternatives: "neg_mean_squared_error", "mae", etc.

# Whether to enable logging (for debugging)
DEBUG_MODE = True
