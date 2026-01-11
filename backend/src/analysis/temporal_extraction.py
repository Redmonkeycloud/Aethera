"""
Temporal data extraction pipeline for AOI coordinates.

Extracts historical weather data from ERA5 for analysis runs
and prepares it for forecasting.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import geopandas as gpd
import pandas as pd

from ..config.base_settings import settings
from ..logging_utils import get_logger
from .era5_client import ERA5Client

logger = get_logger(__name__)


def extract_aoi_bbox(aoi: gpd.GeoDataFrame) -> Tuple[float, float, float, float]:
    """
    Extract bounding box from AOI GeoDataFrame.

    Args:
        aoi: GeoDataFrame with AOI geometry

    Returns:
        Tuple of (north, west, south, east) in degrees
    """
    # Convert to WGS84 if needed
    if aoi.crs != "EPSG:4326":
        aoi_wgs84 = aoi.to_crs("EPSG:4326")
    else:
        aoi_wgs84 = aoi

    bounds = aoi_wgs84.total_bounds
    # bounds is [minx, miny, maxx, maxy] (west, south, east, north)
    west, south, east, north = bounds

    return (north, west, south, east)


def extract_aoi_centroid(aoi: gpd.GeoDataFrame) -> Tuple[float, float]:
    """
    Extract centroid from AOI GeoDataFrame.

    Args:
        aoi: GeoDataFrame with AOI geometry

    Returns:
        Tuple of (longitude, latitude) in degrees
    """
    # Convert to WGS84 if needed
    if aoi.crs != "EPSG:4326":
        aoi_wgs84 = aoi.to_crs("EPSG:4326")
    else:
        aoi_wgs84 = aoi

    # Calculate centroid
    centroid = aoi_wgs84.geometry.unary_union.centroid

    return (centroid.x, centroid.y)


def extract_temporal_data_for_aoi(
    aoi: gpd.GeoDataFrame,
    run_dir: Path,
    era5_client: Optional[ERA5Client] = None,
    years_back: int = 5,
    variables: Optional[List[str]] = None,
) -> Dict[str, Optional[Path]]:
    """
    Extract temporal weather data for an AOI.

    Downloads ERA5 data if not already available and extracts
    temporal series for the AOI centroid.

    Args:
        aoi: GeoDataFrame with AOI geometry
        run_dir: Directory for this analysis run
        era5_client: Optional ERA5 client (creates new if None)
        years_back: Number of years of historical data to fetch
        variables: List of variables to extract (default: standard set)

    Returns:
        Dictionary with paths to extracted temporal data files
    """
    if variables is None:
        variables = [
            "2m_temperature",
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "surface_solar_radiation_downwards",
        ]

    client = era5_client or ERA5Client()
    temporal_dir = run_dir / "processed" / "temporal"
    temporal_dir.mkdir(parents=True, exist_ok=True)

    # Extract AOI bounds and centroid
    bbox = extract_aoi_bbox(aoi)
    lon, lat = extract_aoi_centroid(aoi)

    logger.info(f"Extracting temporal data for AOI at ({lon:.4f}, {lat:.4f})")
    logger.info(f"Bounding box: {bbox}")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years_back * 365)

    # Download ERA5 climatology (monthly averages are faster)
    climatology_path = temporal_dir / f"era5_climatology_{start_date.year}_{end_date.year}.nc"

    results: Dict[str, Optional[Path]] = {}

    if not climatology_path.exists():
        if client.client:
            logger.info("Downloading ERA5 climatology data...")
            downloaded_path = client.get_climatology(
                bbox=bbox,
                output_dir=temporal_dir,
                years=list(range(start_date.year, end_date.year + 1)),
            )
            if downloaded_path:
                climatology_path = downloaded_path
        else:
            logger.warning("ERA5 client not available. Skipping temporal data download.")
            return results

    # Extract temporal series for centroid
    if climatology_path.exists():
        logger.info(f"Extracting temporal series from {climatology_path}")
        temporal_df = client.extract_temporal_series(
            netcdf_path=climatology_path,
            lon=lon,
            lat=lat,
            variables=variables,
        )

        if temporal_df is not None and not temporal_df.empty:
            # Save as CSV for easy access
            csv_path = temporal_dir / "temporal_series.csv"
            temporal_df.to_csv(csv_path, index=False)
            results["temporal_series"] = csv_path

            # Create separate files for each variable
            for var in variables:
                if var in temporal_df.columns:
                    var_df = temporal_df[["time", var]].copy()
                    var_df.columns = ["timestamp", "value"]
                    var_df["variable"] = var
                    var_path = temporal_dir / f"{var}_series.csv"
                    var_df.to_csv(var_path, index=False)
                    results[var] = var_path

            logger.info(f"Temporal series extracted and saved to {temporal_dir}")
        else:
            logger.warning("Failed to extract temporal series from ERA5 data")
    else:
        logger.warning(f"ERA5 climatology file not found: {climatology_path}")

    return results


def load_temporal_series(file_path: Path, variable: Optional[str] = None) -> pd.DataFrame:
    """
    Load temporal series from CSV file.

    Args:
        file_path: Path to CSV file with temporal data
        variable: Optional variable name to filter

    Returns:
        DataFrame with temporal series
    """
    df = pd.read_csv(file_path)

    # Ensure timestamp column is datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    elif "time" in df.columns:
        df["timestamp"] = pd.to_datetime(df["time"])

    # Filter by variable if specified
    if variable and "variable" in df.columns:
        df = df[df["variable"] == variable]

    return df
