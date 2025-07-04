# suitability_model

import os
import logging
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from ai.config.resm_config import RESM_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RESM")

class RESMModel:
    def __init__(self, config=None):
        self.config = config or RESM_CONFIG
        self.model_type = self.config["model_type"]
        self.hyperparams = self.config["hyperparameters"]
        self.model = self._get_model()

    def _get_model(self):
        if self.model_type == "RandomForest":
            return RandomForestRegressor(**self.hyperparams)
        elif self.model_type == "GradientBoosting":
            return GradientBoostingRegressor(**self.hyperparams)
        elif self.model_type == "XGBoost":
            return XGBRegressor(**self.hyperparams)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def train(self, X, y):
        logger.info(f"Training {self.model_type} model on {X.shape[0]} samples...")
        self.model.fit(X, y)

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        logger.info(f"Model saved to: {path}")

    def load(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        self.model = joblib.load(path)
        logger.info(f"Model loaded from: {path}")

    def predict(self, X):
        return self.model.predict(X)
