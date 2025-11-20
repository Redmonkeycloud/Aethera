"""Run a full country-wide analysis using GADM boundaries."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_SOURCES = BASE_DIR / "data2"
BACKEND_DIR = BASE_DIR / "backend"


def get_country_aoi_path(country_code: str) -> Path:
    """Get the path to a country's GADM level 0 boundary."""
    gadm_dir = DATA_SOURCES / "gadm"
    country_code_upper = country_code.upper()
    
    # Try different directory name patterns
    patterns = [
        f"gadm41_{country_code_upper}_shp",
        f"gadm41_{country_code_upper}",
    ]
    
    for pattern in patterns:
        country_dir = gadm_dir / pattern
        if country_dir.exists() and country_dir.is_dir():
            # Try multiple formats
            for ext in [".shp", ".geojson", ".json"]:
                level0_file = country_dir / f"gadm41_{country_code_upper}_0{ext}"
                if level0_file.exists():
                    return level0_file
    
    # If not found, list available countries
    available = []
    for country_dir in gadm_dir.iterdir():
        if country_dir.is_dir() and country_dir.name.startswith("gadm41_"):
            parts = country_dir.name.split("_")
            if len(parts) >= 2:
                available.append(parts[1])
    
    raise FileNotFoundError(
        f"GADM data not found for country {country_code}. "
        f"Available countries: {', '.join(available)}"
    )


def convert_to_geojson(input_path: Path, output_path: Path) -> None:
    """Convert shapefile or GeoJSON to GeoJSON (if needed)."""
    import geopandas as gpd
    
    # If already GeoJSON, just copy/use it
    if input_path.suffix.lower() in [".geojson", ".json"]:
        gdf = gpd.read_file(input_path)
        # Ensure WGS84
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        gdf.to_file(output_path, driver="GeoJSON")
        print(f"Using {input_path.name} (already GeoJSON format)")
    else:
        # Convert from shapefile
        gdf = gpd.read_file(input_path)
        # Convert to WGS84 for GeoJSON
        gdf = gdf.to_crs("EPSG:4326")
        gdf.to_file(output_path, driver="GeoJSON")
        print(f"Converted {input_path.name} to {output_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run country-wide analysis.")
    parser.add_argument("country_code", help="ISO country code (e.g., ITA, GRC)")
    parser.add_argument("--project-type", default="solar_farm", help="Project type")
    args = parser.parse_args()
    
    country_code = args.country_code.upper()
    
    # Get country boundary
    try:
        country_shp = get_country_aoi_path(country_code)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Convert to GeoJSON for the analysis
    temp_geojson = BASE_DIR / f"temp_country_{country_code}.geojson"
    convert_to_geojson(country_shp, temp_geojson)
    
    # Run the analysis
    print(f"\nRunning analysis for {country_code}...")
    cmd = [
        sys.executable,
        "-m", "src.main_controller",
        "--aoi", str(temp_geojson),
        "--project-type", args.project_type
    ]
    
    result = subprocess.run(cmd, cwd=BACKEND_DIR, capture_output=False)
    
    # Clean up temp file
    if temp_geojson.exists():
        temp_geojson.unlink()
    
    if result.returncode == 0:
        print(f"\n[SUCCESS] Analysis complete for {country_code}!")
    else:
        print(f"\n[ERROR] Analysis failed for {country_code}")
        sys.exit(1)


if __name__ == "__main__":
    main()

