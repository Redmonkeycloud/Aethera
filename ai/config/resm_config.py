# resm_config.py

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RESM_CONFIG = {
    "train_data_path": os.path.join(BASE_DIR, "data_preprocessing", "resm_training_data.csv"),
    "model_output_path": os.path.join(BASE_DIR, "models", "suitability_model.pkl"),
    "features": [
        "avg_wind_speed", "solar_radiation", "land_slope",
        "proximity_to_grid", "elevation", "protected_area",
        "land_cover_code", "population_density"
    ],
    "target": "suitability_score",
    "model_type": "RandomForest",
    "hyperparameters": {
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": 42,
        "n_jobs": -1
    },
    # MULTI-METRIC SUPPORT
    "metrics": [
        "r2",                  # Coefficient of determination
        "neg_mean_squared_error",
        "neg_mean_absolute_error",
        "explained_variance"
    ],
    "debug": True
}
