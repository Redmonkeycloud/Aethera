"""
Weather/climate feature extraction for RESM model.

Extracts solar radiation, wind speed, and temperature data from raster files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def extract_raster_value_at_point(
    point: tuple[float, float],
    raster_path: Path,
    band: int = 1,
) -> Optional[float]:
    """
    Extract raster value at a given point (lon, lat).
    
    Args:
        point: Tuple of (longitude, latitude) in EPSG:4326
        raster_path: Path to raster file (GeoTIFF or NetCDF)
        band: Band number to read (default: 1)
        
    Returns:
        Raster value at the point, or None if extraction fails
    """
    try:
        import rasterio
        from rasterio.warp import transform_geom
        
        with rasterio.open(raster_path) as src:
            # Transform point to raster CRS
            geom = {"type": "Point", "coordinates": point}
            geom_transformed = transform_geom("EPSG:4326", src.crs, geom)
            lon, lat = geom_transformed["coordinates"]
            
            # Sample the raster at the point
            values = list(src.sample([(lon, lat)], indexes=[band]))
            if values and not np.isnan(values[0][0]):
                return float(values[0][0])
    except ImportError:
        logger.warning("rasterio not installed. Weather data extraction disabled.")
    except Exception as e:
        logger.warning(f"Failed to extract value from {raster_path}: {e}")
    
    return None


def extract_weather_from_summary(
    point: tuple[float, float],
    summary_path: Path,
) -> dict[str, Optional[float]]:
    """
    Extract weather data from summary CSV by finding nearest point.
    
    Args:
        point: Tuple of (longitude, latitude)
        summary_path: Path to weather summary CSV
        
    Returns:
        Dictionary with weather features
    """
    try:
        df = pd.read_csv(summary_path)
        
        if "lon" not in df.columns or "lat" not in df.columns:
            logger.warning("Weather summary CSV missing lon/lat columns")
            return {}
        
        # Find nearest point using Euclidean distance
        distances = np.sqrt(
            (df["lon"] - point[0]) ** 2 + (df["lat"] - point[1]) ** 2
        )
        nearest_idx = distances.idxmin()
        nearest_row = df.iloc[nearest_idx]
        
        weather_features = {}
        if "solar_ghi_kwh_m2_day" in df.columns:
            weather_features["solar_ghi_kwh_m2_day"] = float(nearest_row["solar_ghi_kwh_m2_day"])
        if "wind_speed_100m_ms" in df.columns:
            weather_features["wind_speed_100m_ms"] = float(nearest_row["wind_speed_100m_ms"])
        if "temperature_2m_c" in df.columns:
            weather_features["temperature_2m_c"] = float(nearest_row["temperature_2m_c"])
        
        return weather_features
    except Exception as e:
        logger.warning(f"Failed to extract weather from summary {summary_path}: {e}")
        return {}


def extract_weather_features(
    aoi: gpd.GeoDataFrame,
    solar_raster_path: Optional[Path] = None,
    wind_raster_path: Optional[Path] = None,
    weather_summary_path: Optional[Path] = None,
) -> dict[str, float]:
    """
    Extract weather features for an AOI.
    
    Args:
        aoi: Area of Interest GeoDataFrame (must have CRS)
        solar_raster_path: Path to solar radiation raster (optional)
        wind_raster_path: Path to wind speed raster (optional)
        weather_summary_path: Path to weather summary CSV (optional, used as fallback)
        
    Returns:
        Dictionary with weather features:
        - solar_ghi_kwh_m2_day: Global Horizontal Irradiance (kWh/m²/day)
        - wind_speed_100m_ms: Wind speed at 100m height (m/s)
        - temperature_2m_c: Temperature at 2m height (°C)
    """
    # Get centroid of AOI in a projected CRS first (for accurate calculation), then convert to EPSG:4326
    # Use EPSG:3857 (Web Mercator) or the original CRS if it's projected
    if aoi.crs and aoi.crs.is_geographic:
        # If AOI is in geographic CRS, use Web Mercator for centroid calculation
        aoi_projected = aoi.to_crs("EPSG:3857")
        centroid_proj = aoi_projected.geometry.centroid.iloc[0]
        # Convert back to EPSG:4326 for the point tuple
        from shapely.geometry import Point
        point_geom = Point(centroid_proj.x, centroid_proj.y)
        point_gdf_proj = gpd.GeoDataFrame(geometry=[point_geom], crs="EPSG:3857")
        point_gdf_4326 = point_gdf_proj.to_crs("EPSG:4326")
        centroid_4326 = point_gdf_4326.geometry.iloc[0]
        point = (centroid_4326.x, centroid_4326.y)
    else:
        # AOI is already in projected CRS, calculate centroid then convert
        centroid_proj = aoi.geometry.centroid.iloc[0]
        from shapely.geometry import Point
        point_geom = Point(centroid_proj.x, centroid_proj.y)
        point_gdf_proj = gpd.GeoDataFrame(geometry=[point_geom], crs=aoi.crs)
        point_gdf_4326 = point_gdf_proj.to_crs("EPSG:4326")
        centroid_4326 = point_gdf_4326.geometry.iloc[0]
        point = (centroid_4326.x, centroid_4326.y)
    
    weather_features: dict[str, Optional[float]] = {}
    
    # Try to extract from raster files
    if solar_raster_path and solar_raster_path.exists():
        solar_value = extract_raster_value_at_point(point, solar_raster_path)
        if solar_value is not None:
            # Convert W/m² to kWh/m²/day if needed (typical conversion factor)
            weather_features["solar_ghi_kwh_m2_day"] = solar_value / 1000.0 if solar_value > 10 else solar_value
    
    if wind_raster_path and wind_raster_path.exists():
        wind_value = extract_raster_value_at_point(point, wind_raster_path)
        if wind_value is not None:
            weather_features["wind_speed_100m_ms"] = wind_value
    
    # Fallback to summary CSV if rasters not available
    if weather_summary_path and weather_summary_path.exists():
        summary_features = extract_weather_from_summary(point, weather_summary_path)
        for key, value in summary_features.items():
            if key not in weather_features or weather_features[key] is None:
                weather_features[key] = value
    
    # Set defaults if values are missing
    result = {
        "solar_ghi_kwh_m2_day": weather_features.get("solar_ghi_kwh_m2_day", 4.0),  # Default: 4 kWh/m²/day (moderate)
        "wind_speed_100m_ms": weather_features.get("wind_speed_100m_ms", 6.0),  # Default: 6 m/s (moderate)
        "temperature_2m_c": weather_features.get("temperature_2m_c", 15.0),  # Default: 15°C (moderate)
    }
    
    return result

