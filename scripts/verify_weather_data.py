"""
Verify that weather data files are properly detected and readable.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.datasets.catalog import DatasetCatalog
from backend.src.config.base_settings import settings


def verify_weather_data() -> None:
    """Check if weather data files are detected."""
    catalog = DatasetCatalog(settings.data_sources_dir)
    
    print("Checking for weather data files...")
    print(f"Data directory: {settings.data_sources_dir}")
    print(f"Weather directory: {settings.data_sources_dir / 'weather'}")
    print()
    
    # Check solar GHI data
    solar_path = catalog.weather_solar_ghi()
    if solar_path:
        print(f"✅ Solar GHI data found: {solar_path}")
        
        # Try to read basic info
        try:
            import rasterio
            with rasterio.open(solar_path) as src:
                print(f"   - CRS: {src.crs}")
                print(f"   - Bounds: {src.bounds}")
                print(f"   - Width: {src.width}, Height: {src.height}")
                print(f"   - Data type: {src.dtypes[0]}")
                print(f"   - No data value: {src.nodata}")
                # Read a sample value
                sample_value = src.read(1, window=((src.height//2, src.height//2+1), (src.width//2, src.width//2+1)))
                if sample_value.size > 0:
                    print(f"   - Sample value (center): {sample_value[0,0]}")
        except ImportError:
            print("   ⚠️  rasterio not available - cannot verify file contents")
        except Exception as e:
            print(f"   ⚠️  Error reading file: {e}")
    else:
        print("❌ Solar GHI data not found")
        print(f"   Expected location: {settings.data_sources_dir / 'weather'}")
        print(f"   Expected pattern: solar_ghi*.tif or solar_ghi*.nc")
    
    print()
    
    # Check wind data
    wind_path = catalog.weather_wind_speed()
    if wind_path:
        print(f"✅ Wind speed data found: {wind_path}")
    else:
        print("⚠️  Wind speed data not found (optional)")
    
    print()
    
    # Check weather summary
    summary_path = catalog.weather_summary()
    if summary_path:
        print(f"✅ Weather summary CSV found: {summary_path}")
    else:
        print("⚠️  Weather summary CSV not found (optional, can be generated)")
    
    print()
    print("=" * 60)
    if solar_path:
        print("✅ Weather data setup looks good!")
        print("\nNext steps:")
        print("1. Run an analysis to test weather feature extraction")
        print("2. (Optional) Download wind speed data from Global Wind Atlas")
        print("3. (Optional) Generate training data with weather features")
    else:
        print("❌ Weather data not detected")
        print("\nPlease ensure:")
        print(f"1. File is saved to: {settings.data_sources_dir / 'weather'}")
        print("2. File is named: solar_ghi_europe.tif (or matches solar_ghi*.tif)")
        print("3. File is in GeoTIFF format (.tif or .tiff extension)")


if __name__ == "__main__":
    verify_weather_data()

