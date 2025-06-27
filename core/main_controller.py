# core/main_controller.py

import os
import argparse
import pandas as pd
import geopandas as gpd
from core import gis_handler
from core import aoi_landcover_analysis

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def ensure_directories():
    """Create necessary base folders if missing."""
    for folder in ["data", "outputs"]:
        os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)
    print("[INIT] Folder structure ensured.")

def ensure_base_datasets(country_code):
    """Check and download required base datasets if missing."""
    print("[INIT] Checking base datasets...")

    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    NATURAL_EARTH_DIR = os.path.join(DATA_DIR, "natural_earth")
    GADM_DIR = os.path.join(DATA_DIR, "gadm")
    EUROSTAT_DIR = os.path.join(DATA_DIR, "eurostat")
    CORINE_DIR = os.path.join(DATA_DIR, "corine")

    # Ensure data directories exist
    for folder in [NATURAL_EARTH_DIR, GADM_DIR, EUROSTAT_DIR, CORINE_DIR]:
        os.makedirs(folder, exist_ok=True)

    # Check and download Natural Earth
    if not os.listdir(NATURAL_EARTH_DIR):
        gis_handler.download_natural_earth()

    # Check and download GADM
    gadm_file_path = os.path.join(GADM_DIR, f"gadm41_{country_code}_0.shp")
    if not os.path.exists(gadm_file_path):
        gis_handler.download_gadm(country_code)

    # Check and download Eurostat
    if not os.listdir(EUROSTAT_DIR):
        gis_handler.download_eurostat()

    # CORINE (manual)
    if not os.path.exists(CORINE_DIR):
        os.makedirs(CORINE_DIR)
        print("[CORINE] Please manually place the CORINE GPKG into /data/corine/")
    else:
        gpkg_found = any(f.endswith(".gpkg") for f in os.listdir(CORINE_DIR))
        if not gpkg_found:
            print("[CORINE] Please manually place the CORINE GPKG into /data/corine/")

    print("[INIT] All base datasets ready.")

def load_country_aoi(country_code):
    """Load country geometry from GADM."""
    gadm_path = os.path.join(BASE_DIR, "data", "gadm", f"gadm41_{country_code}_shp", f"gadm41_{country_code}_0.shp")
    if not os.path.exists(gadm_path):
        raise FileNotFoundError(f"GADM shapefile not found: {gadm_path}")

    gadm = gpd.read_file(gadm_path)
    print(f"[DEBUG] GADM columns: {gadm.columns.tolist()}")

    if "GID_0" not in gadm.columns:
        raise ValueError("Expected 'GID_0' column not found in GADM file.")

    aoi_gdf = gadm[gadm["GID_0"] == country_code]
    if aoi_gdf.empty:
        raise ValueError(f"Country code {country_code} not found in GADM data.")

    name_col = "COUNTRY" if "COUNTRY" in aoi_gdf.columns else "NAME_0" if "NAME_0" in aoi_gdf.columns else "Unknown"
    print(f"[AOI] Selected country: {country_code} - {aoi_gdf.iloc[0].get(name_col, 'Unknown')}")
    return aoi_gdf

def ensure_country_corine_layer(country_code, aoi_gdf):
    """
    Ensure a country-specific CORINE shapefile exists; extract if needed.
    Clips the full CORINE GPKG to the country's AOI and saves a smaller file.
    """
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    corine_dir = os.path.join(BASE_DIR, "data", "corine")
    corine_layer_name = "U2018_CLC2018_V2020_20u1"
    gpkg_path = os.path.join(corine_dir, f"{corine_layer_name}.gpkg")

    # Output path for the clipped version
    country_shapefile = os.path.join(corine_dir, f"corine_{country_code}.shp")

    if os.path.exists(country_shapefile):
        print(f"[CORINE] Country CORINE shapefile already exists: {country_shapefile}")
        return country_shapefile

    if not os.path.exists(gpkg_path):
        raise FileNotFoundError(f"[ERROR] GPKG file not found: {gpkg_path}")

    print(f"[CORINE] Extracting {country_code} from full GPKG...")
    print("[INFO] Using pyogrio for efficient spatial read...")

    # Ensure CRS match
    bbox = aoi_gdf.to_crs("EPSG:3035").total_bounds  # CORINE usually in EPSG:3035

    # Load only features within AOI bbox
    try:
        full_gdf = gpd.read_file(gpkg_path, layer=corine_layer_name, bbox=tuple(bbox))
    except Exception as e:
        raise RuntimeError(f"[ERROR] Failed to load CORINE layer: {e}")

    if full_gdf.empty:
        raise ValueError(f"[ERROR] No CORINE data found in bounding box for {country_code}.")

    # Reproject AOI to match CORINE layer
    if full_gdf.crs != aoi_gdf.crs:
        aoi_gdf = aoi_gdf.to_crs(full_gdf.crs)

    # Clip precisely
    clipped = gpd.overlay(full_gdf, aoi_gdf, how="intersection")

    if clipped.empty:
        raise ValueError(f"[ERROR] No CORINE features intersect with AOI for {country_code}.")

    # Save clipped shapefile
    clipped.to_file(country_shapefile)
    print(f"[CORINE] Saved clipped CORINE data to: {country_shapefile}")

    return country_shapefile

def run_aoi_analysis(country_code):
    """Run the full analysis pipeline for a country."""
    aoi_gdf = load_country_aoi(country_code)
    corine_path = ensure_country_corine_layer(country_code, aoi_gdf)

    landcover_summary, emissions_summary = aoi_landcover_analysis.run_full_analysis(
        aoi_gdf, country_code, corine_path
    )

    output_xlsx = os.path.join(BASE_DIR, "outputs", f"analysis_summary_{country_code}.xlsx")
    with pd.ExcelWriter(output_xlsx) as writer:
        landcover_summary.to_excel(writer, sheet_name="Land Cover Summary", index=False)
        emissions_summary.to_excel(writer, sheet_name="Emissions Summary", index=False)

    print(f"[OUTPUT] Results saved to: {output_xlsx}")

def main():
    parser = argparse.ArgumentParser(description="AETHERA: EIA Automated Analysis")
    parser.add_argument("--country", type=str, required=True, help="ISO3 country code (e.g., GRC, ITA)")
    args = parser.parse_args()

    print("\n--- AETHERA: EIA Automated Analysis ---\n")
    ensure_directories()
    ensure_base_datasets(args.country.upper())
    run_aoi_analysis(args.country.upper())
    print("\n--- AETHERA: All processes completed successfully ---\n")

if __name__ == "__main__":
    main()
