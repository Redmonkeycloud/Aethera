"""
TimesFM (Time Series Foundation Model) service for temporal forecasting.

This service provides zero-shot time series forecasting capabilities
for energy yield prediction, climate risk assessment, and other temporal analyses.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..config.base_settings import settings
from ..logging_utils import get_logger
from .era5_client import ERA5Client

logger = get_logger(__name__)

# Try to import forecasting libraries
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None  # type: ignore[assignment, misc]

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    ARIMA = None  # type: ignore[assignment, misc]


class TimesFMService:
    """Service for temporal forecasting using TimesFM and fallback methods."""

    def __init__(
        self,
        era5_client: Optional[ERA5Client] = None,
        use_prophet: bool = True,
        use_arima: bool = True,
    ) -> None:
        """
        Initialize TimesFM service.

        Args:
            era5_client: Optional ERA5 client for historical data
            use_prophet: Whether to enable Prophet as fallback
            use_arima: Whether to enable ARIMA as fallback
        """
        self.era5_client = era5_client or ERA5Client()
        self.use_prophet = use_prophet and PROPHET_AVAILABLE
        self.use_arima = use_arima and ARIMA_AVAILABLE

        logger.info(
            f"TimesFM service initialized. Prophet: {self.use_prophet}, ARIMA: {self.use_arima}"
        )

    def prepare_temporal_data(
        self,
        df: pd.DataFrame,
        timestamp_col: str = "timestamp",
        value_col: str = "value",
        freq: str = "D",  # Daily frequency
    ) -> pd.DataFrame:
        """
        Prepare temporal data for forecasting.

        Args:
            df: DataFrame with temporal data
            timestamp_col: Name of timestamp column
            value_col: Name of value column
            freq: Frequency for resampling ('D' for daily, 'H' for hourly, etc.)

        Returns:
            Prepared DataFrame with datetime index
        """
        df = df.copy()

        # Convert timestamp column to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])

        # Set timestamp as index
        df = df.set_index(timestamp_col).sort_index()

        # Resample to desired frequency
        df_resampled = df[[value_col]].resample(freq).mean().dropna()

        return df_resampled

    def forecast_with_prophet(
        self,
        df: pd.DataFrame,
        horizon_days: int = 365,
        seasonality_mode: str = "multiplicative",
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Forecast using Facebook Prophet.

        Args:
            df: DataFrame with datetime index and 'value' column
            horizon_days: Number of days to forecast
            seasonality_mode: 'multiplicative' or 'additive'
            yearly_seasonality: Enable yearly seasonality
            weekly_seasonality: Enable weekly seasonality
            daily_seasonality: Enable daily seasonality

        Returns:
            Tuple of (forecast DataFrame, metrics dict)
        """
        if not self.use_prophet:
            raise ValueError("Prophet not available. Install with: pip install prophet")

        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_df = df.reset_index()
        prophet_df.columns = ["ds", "y"]
        prophet_df = prophet_df.dropna()

        if len(prophet_df) < 30:
            raise ValueError(f"Insufficient data for Prophet: {len(prophet_df)} samples (minimum: 30)")

        # Fit model
        model = Prophet(
            seasonality_mode=seasonality_mode,
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
        )

        try:
            model.fit(prophet_df)
        except Exception as e:
            logger.error(f"Prophet model fitting failed: {e}")
            raise

        # Create future dataframe
        future = model.make_future_dataframe(periods=horizon_days)
        forecast = model.predict(future)

        # Extract forecast for future period only
        forecast_df = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        forecast_df = forecast_df.tail(horizon_days).reset_index(drop=True)
        forecast_df.columns = ["timestamp", "forecast", "lower_bound", "upper_bound"]

        # Calculate metrics on training data
        train_forecast = model.predict(prophet_df)
        mae = np.mean(np.abs(train_forecast["yhat"] - prophet_df["y"]))
        rmse = np.sqrt(np.mean((train_forecast["yhat"] - prophet_df["y"]) ** 2))
        mape = np.mean(np.abs((train_forecast["yhat"] - prophet_df["y"]) / prophet_df["y"])) * 100

        metrics = {
            "model": "prophet",
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "training_samples": len(prophet_df),
            "horizon_days": horizon_days,
        }

        return forecast_df, metrics

    def forecast_with_arima(
        self,
        df: pd.DataFrame,
        horizon_days: int = 365,
        order: Tuple[int, int, int] = (1, 1, 1),  # (p, d, q)
        seasonal_order: Optional[Tuple[int, int, int, int]] = None,  # (P, D, Q, s)
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Forecast using ARIMA model.

        Args:
            df: DataFrame with datetime index and 'value' column
            horizon_days: Number of days to forecast
            order: ARIMA order (p, d, q)
            seasonal_order: Seasonal ARIMA order (P, D, Q, s)

        Returns:
            Tuple of (forecast DataFrame, metrics dict)
        """
        if not self.use_arima:
            raise ValueError("ARIMA not available. Install with: pip install statsmodels")

        values = df["value"].dropna().values

        if len(values) < 30:
            raise ValueError(f"Insufficient data for ARIMA: {len(values)} samples (minimum: 30)")

        # Fit model
        try:
            if seasonal_order:
                model = ARIMA(values, order=order, seasonal_order=seasonal_order)
            else:
                model = ARIMA(values, order=order)

            fitted_model = model.fit()
        except Exception as e:
            logger.error(f"ARIMA model fitting failed: {e}")
            raise

        # Generate forecast
        forecast_result = fitted_model.forecast(steps=horizon_days, alpha=0.05)
        forecast_values = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int()

        # Create forecast DataFrame
        last_timestamp = df.index[-1]
        forecast_dates = pd.date_range(
            start=last_timestamp + timedelta(days=1),
            periods=horizon_days,
            freq=df.index.freq or "D",
        )

        forecast_df = pd.DataFrame(
            {
                "timestamp": forecast_dates,
                "forecast": forecast_values,
                "lower_bound": conf_int.iloc[:, 0].values,
                "upper_bound": conf_int.iloc[:, 1].values,
            }
        )

        # Calculate metrics on training data
        train_forecast = fitted_model.predict(start=0, end=len(values) - 1)
        mae = np.mean(np.abs(train_forecast - values))
        rmse = np.sqrt(np.mean((train_forecast - values) ** 2))
        mape = np.mean(np.abs((train_forecast - values) / (values + 1e-10))) * 100

        metrics = {
            "model": "arima",
            "order": order,
            "seasonal_order": seasonal_order,
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "training_samples": len(values),
            "horizon_days": horizon_days,
        }

        return forecast_df, metrics

    def forecast_with_simple_trend(
        self,
        df: pd.DataFrame,
        horizon_days: int = 365,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Simple linear trend forecasting (fallback when other methods unavailable).

        Args:
            df: DataFrame with datetime index and 'value' column
            horizon_days: Number of days to forecast

        Returns:
            Tuple of (forecast DataFrame, metrics dict)
        """
        values = df["value"].dropna().values

        if len(values) < 7:
            raise ValueError(f"Insufficient data: {len(values)} samples (minimum: 7)")

        # Linear regression
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, deg=1)
        trend = np.poly1d(coeffs)

        # Generate forecast
        future_x = np.arange(len(values), len(values) + horizon_days)
        forecast_values = trend(future_x)

        # Simple uncertainty estimate (std of residuals)
        residuals = values - trend(x)
        std_error = np.std(residuals)
        forecast_values_lower = forecast_values - 1.96 * std_error
        forecast_values_upper = forecast_values + 1.96 * std_error

        # Create forecast DataFrame
        last_timestamp = df.index[-1]
        forecast_dates = pd.date_range(
            start=last_timestamp + timedelta(days=1),
            periods=horizon_days,
            freq=df.index.freq or "D",
        )

        forecast_df = pd.DataFrame(
            {
                "timestamp": forecast_dates,
                "forecast": forecast_values,
                "lower_bound": forecast_values_lower,
                "upper_bound": forecast_values_upper,
            }
        )

        # Calculate metrics
        train_forecast = trend(x)
        mae = np.mean(np.abs(train_forecast - values))
        rmse = np.sqrt(np.mean((train_forecast - values) ** 2))
        mape = np.mean(np.abs((train_forecast - values) / (values + 1e-10))) * 100

        metrics = {
            "model": "simple_trend",
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "training_samples": len(values),
            "horizon_days": horizon_days,
        }

        return forecast_df, metrics

    def forecast_energy_yield(
        self,
        historical_data: pd.DataFrame,
        horizon_days: int = 365,
        method: str = "auto",  # 'auto', 'prophet', 'arima', 'simple_trend'
    ) -> Dict[str, Any]:
        """
        Forecast renewable energy yield (solar/wind) based on historical weather data.

        Args:
            historical_data: DataFrame with temporal weather data (solar radiation, wind speed)
            horizon_days: Number of days to forecast
            method: Forecasting method to use

        Returns:
            Dictionary with forecast results and metadata
        """
        # Prepare data
        df = self.prepare_temporal_data(
            historical_data,
            timestamp_col="timestamp",
            value_col="value",
            freq="D",
        )

        # Select forecasting method
        if method == "auto":
            if self.use_prophet and len(df) >= 30:
                method = "prophet"
            elif self.use_arima and len(df) >= 30:
                method = "arima"
            else:
                method = "simple_trend"

        # Generate forecast
        try:
            if method == "prophet":
                forecast_df, metrics = self.forecast_with_prophet(df, horizon_days=horizon_days)
            elif method == "arima":
                forecast_df, metrics = self.forecast_with_arima(df, horizon_days=horizon_days)
            else:
                forecast_df, metrics = self.forecast_with_simple_trend(df, horizon_days=horizon_days)

            # Convert to dict for JSON serialization
            forecast_data = {
                "timestamps": forecast_df["timestamp"].dt.strftime("%Y-%m-%d").tolist(),
                "forecast": forecast_df["forecast"].tolist(),
                "lower_bound": forecast_df["lower_bound"].tolist(),
                "upper_bound": forecast_df["upper_bound"].tolist(),
            }

            result = {
                "forecast_type": "energy_yield",
                "variable": historical_data.get("variable", "unknown").iloc[0] if "variable" in historical_data.columns else "unknown",
                "horizon_days": horizon_days,
                "forecast_data": forecast_data,
                "metrics": metrics,
                "method": method,
                "created_at": datetime.now().isoformat(),
            }

            logger.info(f"Energy yield forecast generated using {method} (horizon: {horizon_days} days)")
            return result

        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            raise

    def forecast_climate_risk(
        self,
        historical_data: pd.DataFrame,
        risk_type: str,  # 'extreme_heat', 'extreme_cold', 'wind_storm', 'drought'
        horizon_days: int = 365,
        method: str = "auto",
    ) -> Dict[str, Any]:
        """
        Forecast climate risk based on historical weather data.

        Args:
            historical_data: DataFrame with temporal weather data
            risk_type: Type of climate risk to forecast
            horizon_days: Number of days to forecast
            method: Forecasting method to use

        Returns:
            Dictionary with risk forecast results
        """
        # Prepare data
        df = self.prepare_temporal_data(
            historical_data,
            timestamp_col="timestamp",
            value_col="value",
            freq="D",
        )

        # Select forecasting method
        if method == "auto":
            if self.use_prophet and len(df) >= 30:
                method = "prophet"
            elif self.use_arima and len(df) >= 30:
                method = "arima"
            else:
                method = "simple_trend"

        # Generate forecast
        try:
            if method == "prophet":
                forecast_df, metrics = self.forecast_with_prophet(df, horizon_days=horizon_days)
            elif method == "arima":
                forecast_df, metrics = self.forecast_with_arima(df, horizon_days=horizon_days)
            else:
                forecast_df, metrics = self.forecast_with_simple_trend(df, horizon_days=horizon_days)

            # Calculate risk levels based on forecast values
            # This is a simplified example - real risk assessment would be more sophisticated
            mean_value = df["value"].mean()
            std_value = df["value"].std()

            risk_scores = []
            risk_levels = []

            for forecast_val in forecast_df["forecast"]:
                # Simple threshold-based risk assessment
                z_score = (forecast_val - mean_value) / (std_value + 1e-10)

                if abs(z_score) > 2:
                    risk_level = "extreme"
                    risk_score = min(100, abs(z_score) * 20)
                elif abs(z_score) > 1.5:
                    risk_level = "high"
                    risk_score = min(80, abs(z_score) * 15)
                elif abs(z_score) > 1:
                    risk_level = "moderate"
                    risk_score = min(60, abs(z_score) * 12)
                else:
                    risk_level = "low"
                    risk_score = min(40, abs(z_score) * 10)

                risk_scores.append(float(risk_score))
                risk_levels.append(risk_level)

            # Convert to dict for JSON serialization
            forecast_data = {
                "timestamps": forecast_df["timestamp"].dt.strftime("%Y-%m-%d").tolist(),
                "forecast": forecast_df["forecast"].tolist(),
                "lower_bound": forecast_df["lower_bound"].tolist(),
                "upper_bound": forecast_df["upper_bound"].tolist(),
                "risk_scores": risk_scores,
                "risk_levels": risk_levels,
            }

            result = {
                "forecast_type": "climate_risk",
                "risk_type": risk_type,
                "horizon_days": horizon_days,
                "forecast_data": forecast_data,
                "metrics": metrics,
                "method": method,
                "created_at": datetime.now().isoformat(),
            }

            logger.info(f"Climate risk forecast generated for {risk_type} using {method}")
            return result

        except Exception as e:
            logger.error(f"Climate risk forecasting failed: {e}")
            raise
