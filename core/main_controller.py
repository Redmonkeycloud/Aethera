# core/main_controller.py

import os
import argparse
import pandas as pd
import geopandas as gpd
from core import gis_handler
from core import aoi_landcover_analysis

def ensure_directories():
    """Create necessary base folders if missing."""
    base_folders = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    ]
    for folder in base_folders:
        os.makedirs(folder, exist_ok=True)
    print("[INIT] Folder structure ensured.")

def ensure_base_datasets():
    """Check and download datasets if missing."""
    print("[INIT] Checking base datasets...")
    
    natural_earth_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "natural_earth")
    gadm_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gadm")
    eurostat_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "eurostat")
    corine_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "corine")

    if not os.path.exists(natural_earth_path) or len(os.listdir(natural_earth_path)) == 0:
        gis_handler.download_natural_earth()

    if not os.path.exists(gadm_path) or len(os.listdir(gadm_path)) == 0:
        gis_handler.download_gadm()

    if not os.path.exists(eurostat_path) or len(os.listdir(eurostat_path)) == 0:
        gis_handler.download_eurostat()

    # CORINE vector is downloaded manually for now
    if not os.path.exists(corine_path):
        os.makedirs(corine_path)
        print("[CORINE] Please manually download and place the CORINE GPKG into /data/corine/")

    print("[INIT] All base datasets ready.")

def load_country_aoi(country_code):
    """Load AOI geometry from GADM for a given ISO country code."""
    gadm_shapefile = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gadm", "gadm41_0.shp")
    if not os.path.exists(gadm_shapefile):
        raise FileNotFoundError("GADM shapefile not found. Please ensure it is downloaded.")

    gadm = gpd.read_file(gadm_shapefile)
    if "GID_0" not in gadm.columns:
        raise ValueError("GADM shapefile missing 'GID_0' country code column.")

    aoi_gdf = gadm[gadm["GID_0"] == country_code.upper()]
    if aoi_gdf.empty:
        raise ValueError(f"Country code '{country_code}' not found in GADM data.")

    print(f"[AOI] Selected country: {country_code} - {aoi_gdf.iloc[0]['NAME_0']}")
    return aoi_gdf

def ensure_country_corine_layer(country_code, aoi_gdf):
    """Ensure a country-specific CORINE shapefile exists; extract if needed."""
    country_shapefile = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "corine",
        f"corine_{country_code}.shp"
    )

    if os.path.exists(country_shapefile):
        print(f"[CORINE] Country CORINE shapefile already exists: {country_shapefile}")
        return country_shapefile

    print(f"[CORINE] Extracting {country_code} from full GPKG...")
    gpkg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "corine", "u2018_clc2018_v2020_20u1_geoPackage.gpkg")
    
    if not os.path.exists(gpkg_path):
        raise FileNotFoundError(f"GPKG file not found: {gpkg_path}")

    # Load full GPKG (large file)
    full_gdf = gpd.read_file(gpkg_path)

    # Reproject AOI to match CORINE CRS if necessary
    if full_gdf.crs != aoi_gdf.crs:
        aoi_gdf = aoi_gdf.to_crs(full_gdf.crs)

    # Clip CORINE to AOI
    clipped_gdf = gpd.overlay(full_gdf, aoi_gdf, how="intersection")

    if clipped_gdf.empty:
        raise ValueError(f"No CORINE land cover found for country {country_code}.")

    # Save country-specific CORINE shapefile
    clipped_gdf.to_file(country_shapefile)
    print(f"[CORINE] Saved extracted CORINE shapefile: {country_shapefile}")

    return country_shapefile

def run_aoi_analysis(country_code):
    """Run the full AOI land cover and emissions analysis."""
    print(f"[RUN] Running full analysis for {country_code}...")

    # Load AOI
    aoi_gdf = load_country_aoi(country_code)

    # Ensure extracted country-specific CORINE layer
    country_corine_shapefile = ensure_country_corine_layer(country_code, aoi_gdf)

    # Run full land cover + emissions analysis
    landcover_summary, emissions_summary = aoi_landcover_analysis.run_full_analysis(
        aoi_gdf, country_code, country_corine_shapefile
    )

    # Save results to Excel
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    excel_path = os.path.join(output_dir, f"analysis_summary_{country_code}.xlsx")

    with pd.ExcelWriter(excel_path) as writer:
        landcover_summary.to_excel(writer, sheet_name="Land Cover Summary", index=False)
        emissions_summary.to_excel(writer, sheet_name="Emissions Summary", index=False)

    print(f"[OUTPUT] Results saved to: {excel_path}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AETHERA: EIA Automated Analysis")
    parser.add_argument("--country", type=str, required=True, help="ISO3 country code (e.g., GRC, ESP, ITA)")
    args = parser.parse_args()

    print("\n--- AETHERA: EIA Automated Analysis ---\n")
    ensure_directories()
    ensure_base_datasets()
    run_aoi_analysis(args.country.upper())
    print("\n--- AETHERA: All processes completed successfully ---\n")

if __name__ == "__main__":
    main()
