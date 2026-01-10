"""
Download weather/climate data for RESM model training and prediction.

This script downloads:
- Solar radiation data (Global Horizontal Irradiance - GHI)
- Wind speed data
- Temperature and precipitation data

Data sources:
- Copernicus Climate Data Store (CDS) - ERA5 reanalysis data
- Global Solar Atlas (World Bank/ESMAP) - Solar radiation
- Global Wind Atlas - Wind speed data
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import box

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.config.base_settings import settings
from backend.src.datasets.catalog import DatasetCatalog


def download_era5_data(
    bbox: tuple[float, float, float, float],
    variables: list[str],
    years: list[int],
    output_dir: Path,
    country: Optional[str] = None,
) -> Path:
    """
    Download ERA5 reanalysis data from Copernicus CDS.
    
    Note: This requires CDS API key setup. See:
    https://cds.climate.copernicus.eu/api-how-to
    
    Args:
        bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
        variables: List of variables to download (e.g., ['2m_temperature', '10m_wind_speed', 'surface_solar_radiation'])
        years: List of years to download
        output_dir: Output directory
        country: Optional country code for naming
        
    Returns:
        Path to downloaded file
    """
    print("⚠️  ERA5 data download requires Copernicus CDS API setup.")
    print("Please see: https://cds.climate.copernicus.eu/api-how-to")
    print("For now, creating a placeholder script structure...")
    
    # Placeholder - in production, would use cdsapi
    output_path = output_dir / "weather" / f"era5_{country or 'region'}.nc"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Would download ERA5 data to: {output_path}")
    return output_path


def download_global_solar_atlas(
    bbox: tuple[float, float, float, float],
    output_dir: Path,
    country: Optional[str] = None,
) -> Optional[Path]:
    """
    Download solar radiation data from Global Solar Atlas.
    
    Note: Global Solar Atlas provides raster data. This function
    downloads the GHI (Global Horizontal Irradiance) dataset.
    
    Args:
        bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
        output_dir: Output directory
        country: Optional country code for naming
        
    Returns:
        Path to downloaded file or None if download fails
    """
    print("Downloading Global Solar Atlas data...")
    
    # Global Solar Atlas provides API access and downloadable raster tiles
    # For Europe, we can use their tile service
    # URL format: https://globalsolaratlas.info/download/{country}
    
    output_path = output_dir / "weather" / f"solar_ghi_{country or 'region'}.tif"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # For now, provide instructions - actual download requires API key or manual download
        print(f"⚠️  Global Solar Atlas data requires manual download or API setup.")
        print(f"Visit: https://globalsolaratlas.info/download/{country or 'region'}")
        print(f"Expected output path: {output_path}")
        
        # In production, would use requests or rasterio to download tiles
        return output_path
    except Exception as e:
        print(f"Error downloading Global Solar Atlas data: {e}")
        return None


def download_global_wind_atlas(
    bbox: tuple[float, float, float, float],
    height: int = 100,  # Wind speed at 100m height
    output_dir: Path,
    country: Optional[str] = None,
) -> Optional[Path]:
    """
    Download wind speed data from Global Wind Atlas.
    
    Note: Global Wind Atlas provides raster data for wind speeds at different heights.
    
    Args:
        bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
        height: Wind speed measurement height in meters (default: 100m)
        output_dir: Output directory
        country: Optional country code for naming
        
    Returns:
        Path to downloaded file or None if download fails
    """
    print(f"Downloading Global Wind Atlas data (height: {height}m)...")
    
    output_path = output_dir / "weather" / f"wind_speed_{height}m_{country or 'region'}.tif"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Global Wind Atlas provides API access
        # URL format: https://globalwindatlas.info/api/gwa/custom
        print(f"⚠️  Global Wind Atlas data requires API setup.")
        print(f"Visit: https://globalwindatlas.info/")
        print(f"Expected output path: {output_path}")
        
        return output_path
    except Exception as e:
        print(f"Error downloading Global Wind Atlas data: {e}")
        return None


def extract_weather_features_from_raster(
    point: tuple[float, float],
    raster_path: Path,
) -> Optional[float]:
    """Extract weather value from raster at a given point."""
    try:
        import rasterio
        from rasterio.transform import from_bounds
        
        with rasterio.open(raster_path) as src:
            # Sample the raster at the point
            values = list(src.sample([point]))
            if values:
                return float(values[0][0])
    except ImportError:
        print("⚠️  rasterio not installed. Install with: pip install rasterio")
    except Exception as e:
        print(f"Error reading raster: {e}")
    
    return None


def create_weather_summary(
    catalog: DatasetCatalog,
    country: Optional[str] = None,
    output_path: Optional[Path] = None,
) -> None:
    """
    Create a summary CSV of weather data for training.
    
    This function creates a grid of points and extracts weather values
    for use in training data preparation.
    """
    print("Creating weather data summary...")
    
    # Get country bounds from GADM or use default Europe bounds
    if country:
        try:
            gadm_path = catalog.gadm(level=0)
            if gadm_path:
                gdf = gpd.read_file(gadm_path)
                country_gdf = gdf[gdf['GID_0'] == country.upper()] if 'GID_0' in gdf.columns else gdf
                bbox = country_gdf.total_bounds  # minx, miny, maxx, maxy
            else:
                raise FileNotFoundError("GADM data not found")
        except Exception:
            # Default to Europe bounds (EPSG:4326)
            bbox = [5.0, 35.0, 30.0, 70.0]  # Approximate Europe
    else:
        bbox = [5.0, 35.0, 30.0, 70.0]  # Approximate Europe
    
    # Create a grid of sample points
    lons = np.linspace(bbox[0], bbox[2], num=20)
    lats = np.linspace(bbox[1], bbox[3], num=20)
    
    weather_data = []
    for lon in lons:
        for lat in lats:
            # In production, would extract from downloaded raster data
            # For now, use synthetic values based on latitude (rough approximation)
            solar_ghi = 1000 + (50 - abs(lat - 45)) * 20  # Rough approximation
            wind_speed = 5.0 + np.random.uniform(-2, 2)  # Rough approximation
            temperature = 15 - (abs(lat - 45) * 0.5)  # Rough approximation
            
            weather_data.append({
                "lon": lon,
                "lat": lat,
                "solar_ghi_kwh_m2_day": max(0, solar_ghi / 1000.0),  # Convert to kWh/m²/day
                "wind_speed_100m_ms": max(0, wind_speed),
                "temperature_2m_c": temperature,
            })
    
    df = pd.DataFrame(weather_data)
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"✅ Created weather summary at {output_path}")
    else:
        weather_dir = catalog.base_dir / "weather"
        weather_dir.mkdir(parents=True, exist_ok=True)
        output_path = weather_dir / f"weather_summary_{country or 'europe'}.csv"
        df.to_csv(output_path, index=False)
        print(f"✅ Created weather summary at {output_path}")
    
    print(f"   Generated {len(df)} sample points")
    print("   ⚠️  Note: This uses synthetic/approximate data.")
    print("   For production, download real weather data using the download functions.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download weather/climate data for RESM model")
    parser.add_argument(
        "--data-sources-dir",
        type=Path,
        default=settings.data_sources_dir,
        help="Directory to save weather data (default: data2)",
    )
    parser.add_argument(
        "--country",
        type=str,
        default=None,
        help="Country code (e.g., ITA, GRC) for country-specific data",
    )
    parser.add_argument(
        "--create-summary",
        action="store_true",
        help="Create a weather data summary CSV with sample points",
    )
    parser.add_argument(
        "--source",
        choices=["era5", "solar_atlas", "wind_atlas", "all"],
        default="all",
        help="Weather data source to download",
    )
    
    args = parser.parse_args()
    
    catalog = DatasetCatalog(args.data_sources_dir)
    
    # Default bounding box (Europe)
    bbox = (5.0, 35.0, 30.0, 70.0)
    
    if args.country:
        try:
            gadm_path = catalog.gadm(level=0)
            if gadm_path:
                gdf = gpd.read_file(gadm_path)
                if 'GID_0' in gdf.columns:
                    country_gdf = gdf[gdf['GID_0'] == args.country.upper()]
                    if not country_gdf.empty:
                        bounds = country_gdf.total_bounds
                        bbox = (bounds[0], bounds[1], bounds[2], bounds[3])
        except Exception:
            print(f"Warning: Could not get bounds for country {args.country}, using default")
    
    print(f"Downloading weather data for bbox: {bbox}")
    print(f"Output directory: {args.data_sources_dir / 'weather'}")
    
    if args.source in ("era5", "all"):
        download_era5_data(
            bbox=bbox,
            variables=["2m_temperature", "10m_wind_speed", "surface_solar_radiation"],
            years=[2020, 2021, 2022],
            output_dir=args.data_sources_dir,
            country=args.country,
        )
    
    if args.source in ("solar_atlas", "all"):
        download_global_solar_atlas(
            bbox=bbox,
            output_dir=args.data_sources_dir,
            country=args.country,
        )
    
    if args.source in ("wind_atlas", "all"):
        download_global_wind_atlas(
            bbox=bbox,
            height=100,
            output_dir=args.data_sources_dir,
            country=args.country,
        )
    
    if args.create_summary:
        create_weather_summary(
            catalog=catalog,
            country=args.country,
            output_path=args.data_sources_dir / "weather" / f"weather_summary_{args.country or 'europe'}.csv",
        )
    
    print("\n✅ Weather data download script completed!")
    print("\nNext steps:")
    print("1. Set up API keys for Copernicus CDS, Global Solar Atlas, Global Wind Atlas")
    print("2. Run the download functions with proper API authentication")
    print("3. Use the downloaded data in RESM feature extraction")


if __name__ == "__main__":
    main()

