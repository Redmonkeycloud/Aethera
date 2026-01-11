"""
Copernicus CDS API client for ERA5 historical weather data.

This module provides utilities for downloading ERA5 reanalysis data
from the Copernicus Climate Data Store (CDS).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import cdsapi
    CDSAPI_AVAILABLE = True
except ImportError:
    CDSAPI_AVAILABLE = False
    cdsapi = None  # type: ignore[assignment, misc]


class ERA5Client:
    """Client for downloading ERA5 reanalysis data from Copernicus CDS."""

    def __init__(self, cds_api_key: Optional[str] = None, cds_api_url: Optional[str] = None) -> None:
        """
        Initialize ERA5 client.

        Args:
            cds_api_key: Copernicus CDS API key (or set CDS_API_KEY env var)
            cds_api_url: Copernicus CDS API URL (or set CDS_API_URL env var)
        """
        if not CDSAPI_AVAILABLE:
            logger.warning("cdsapi not installed. Install with: pip install cdsapi")
            self.client = None
            return

        api_key = cds_api_key or os.getenv("CDS_API_KEY")
        api_url = cds_api_url or os.getenv("CDS_API_URL", "https://cds.climate.copernicus.eu/api/v2")

        if not api_key:
            logger.warning("CDS_API_KEY not set. ERA5 downloads will be disabled.")
            self.client = None
            return

        try:
            self.client = cdsapi.Client(url=api_url, key=api_key)
            logger.info("ERA5 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ERA5 client: {e}")
            self.client = None

    def download_hourly_data(
        self,
        bbox: tuple[float, float, float, float],  # (north, west, south, east)
        start_date: datetime,
        end_date: datetime,
        output_path: Path,
        variables: Optional[list[str]] = None,
    ) -> Optional[Path]:
        """
        Download ERA5 hourly reanalysis data for a bounding box.

        Args:
            bbox: Bounding box (north, west, south, east) in degrees
            start_date: Start date for data
            end_date: End date for data
            output_path: Path to save the downloaded NetCDF file
            variables: List of variables to download (default: surface variables)

        Returns:
            Path to downloaded file, or None if download failed
        """
        if not self.client:
            logger.error("ERA5 client not initialized. Cannot download data.")
            return None

        if variables is None:
            variables = [
                "2m_temperature",
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
                "surface_solar_radiation_downwards",
                "total_precipitation",
            ]

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Format dates for CDS API
        date_range = pd.date_range(start_date.date(), end_date.date(), freq="D")
        dates = [d.strftime("%Y-%m-%d") for d in date_range]

        try:
            logger.info(f"Downloading ERA5 data for {len(dates)} days from {start_date} to {end_date}")
            logger.info(f"Bounding box: {bbox}")
            logger.info(f"Variables: {variables}")

            request_params = {
                "product_type": "reanalysis",
                "variable": variables,
                "year": list(set([d[:4] for d in dates])),
                "month": list(set([d[5:7] for d in dates])),
                "day": list(set([d[8:10] for d in dates])),
                "time": [f"{h:02d}:00" for h in range(24)],
                "area": [bbox[0], bbox[1], bbox[2], bbox[3]],  # north, west, south, east
                "format": "netcdf",
            }

            self.client.retrieve(
                "reanalysis-era5-single-levels",
                request_params,
                str(output_path),
            )

            logger.info(f"ERA5 data downloaded successfully to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to download ERA5 data: {e}")
            return None

    def extract_temporal_series(
        self,
        netcdf_path: Path,
        lon: float,
        lat: float,
        variables: Optional[list[str]] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Extract temporal series from ERA5 NetCDF file for a specific point.

        Args:
            netcdf_path: Path to ERA5 NetCDF file
            lon: Longitude of point
            lat: Latitude of point
            variables: Variables to extract (default: all available)

        Returns:
            DataFrame with temporal series, or None if extraction failed
        """
        try:
            import xarray as xr

            ds = xr.open_dataset(netcdf_path)

            # Select nearest point
            point_data = ds.sel(longitude=lon, latitude=lat, method="nearest")

            # Convert to DataFrame
            df = point_data.to_dataframe().reset_index()

            # Clean up column names
            df.columns = [col.replace(" ", "_").lower() for col in df.columns]

            # Select specific variables if requested
            if variables:
                available_vars = [v for v in variables if v in df.columns]
                if available_vars:
                    df = df[["time"] + available_vars]

            ds.close()
            return df

        except ImportError:
            logger.error("xarray not installed. Install with: pip install xarray")
            return None
        except Exception as e:
            logger.error(f"Failed to extract temporal series from {netcdf_path}: {e}")
            return None

    def get_climatology(
        self,
        bbox: tuple[float, float, float, float],
        output_dir: Path,
        years: Optional[list[int]] = None,
    ) -> Optional[Path]:
        """
        Download ERA5 climatology (monthly averages) for historical analysis.

        Args:
            bbox: Bounding box (north, west, south, east) in degrees
            output_dir: Directory to save downloaded files
            years: List of years to download (default: last 5 years)

        Returns:
            Path to downloaded file, or None if download failed
        """
        if not self.client:
            logger.error("ERA5 client not initialized. Cannot download data.")
            return None

        if years is None:
            current_year = datetime.now().year
            years = list(range(current_year - 5, current_year))

        output_path = output_dir / f"era5_climatology_{years[0]}_{years[-1]}.nc"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Downloading ERA5 climatology for years {years}")

            request_params = {
                "product_type": "monthly_averaged_reanalysis",
                "variable": [
                    "2m_temperature",
                    "10m_u_component_of_wind",
                    "10m_v_component_of_wind",
                    "surface_solar_radiation_downwards",
                ],
                "year": [str(y) for y in years],
                "month": [f"{m:02d}" for m in range(1, 13)],
                "area": [bbox[0], bbox[1], bbox[2], bbox[3]],
                "format": "netcdf",
                "time": "00:00",
            }

            self.client.retrieve(
                "reanalysis-era5-single-levels-monthly-means",
                request_params,
                str(output_path),
            )

            logger.info(f"ERA5 climatology downloaded successfully to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to download ERA5 climatology: {e}")
            return None
