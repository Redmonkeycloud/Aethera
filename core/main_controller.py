# core/main_controller.py

import os
import sys
import argparse
import pandas as pd
import geopandas as gpd

from core import gis_handler, aoi_landcover_analysis
from core import protected_area_analysis as paa
# (Optional) proximity later:
# from core import buffer_analysis

from utils.logging_utils import setup_logger, log_memory_usage, log_step, log_exception

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def ensure_directories(logger):
    """Create necessary base folders if missing."""
    for folder in ["data", "outputs"]:
        os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)
    log_step(logger, "[INIT] Folder structure ensured.")


def ensure_base_datasets(country_code, logger):
    """Check and download required base datasets if missing."""
    log_step(logger, "[INIT] Checking base datasets...")

    dirs = {
        "NATURAL_EARTH": os.path.join(DATA_DIR, "natural_earth"),
        "GADM": os.path.join(DATA_DIR, "gadm"),
        "EUROSTAT": os.path.join(DATA_DIR, "eurostat"),
        "CORINE": os.path.join(DATA_DIR, "corine"),
        # Optional: where you place protected datasets
        "PA_NATURA": os.path.join(DATA_DIR, "protected_areas", "natura2000"),
        "PA_WDPA": os.path.join(DATA_DIR, "protected_areas", "wdpa"),
    }

    for path in dirs.values():
        os.makedirs(path, exist_ok=True)

    # Natural Earth (admin boundaries world)
    if not os.listdir(dirs["NATURAL_EARTH"]):
        gis_handler.download_natural_earth()

    # GADM (per country admin)
    gadm_file = os.path.join(dirs["GADM"], f"gadm41_{country_code}_0.shp")
    if not os.path.exists(gadm_file):
        gis_handler.download_gadm(country_code)

    # Eurostat NUTS (optional base layer)
    if not os.listdir(dirs["EUROSTAT"]):
        gis_handler.download_eurostat()

    # CORINE (manual GPKG expected)
    corine_files = os.listdir(dirs["CORINE"])
    if not any(f.lower().endswith(".gpkg") for f in corine_files):
        logger.warning("[CORINE] Please manually place the CORINE GPKG into /data/corine/")

    log_step(logger, "[INIT] All base datasets ready.")
    log_memory_usage(logger, "After base dataset check")


def load_country_aoi(country_code, logger):
    gadm_path = os.path.join(DATA_DIR, "gadm", f"gadm41_{country_code}_shp", f"gadm41_{country_code}_0.shp")
    if not os.path.exists(gadm_path):
        raise FileNotFoundError(f"GADM shapefile not found: {gadm_path}")

    gadm = gpd.read_file(gadm_path)
    logger.debug(f"[DEBUG] GADM columns: {gadm.columns.tolist()}")

    if "GID_0" not in gadm.columns:
        raise ValueError("Expected 'GID_0' column not found in GADM file.")

    aoi = gadm[gadm["GID_0"] == country_code]
    if aoi.empty:
        raise ValueError(f"Country code {country_code} not found in GADM data.")

    name_col = "COUNTRY" if "COUNTRY" in aoi.columns else "NAME_0" if "NAME_0" in aoi.columns else None
    nice_name = aoi.iloc[0][name_col] if name_col else country_code
    log_step(logger, f"[AOI] Selected country: {country_code} - {nice_name}")
    return aoi


def ensure_country_corine_layer(country_code, aoi_gdf, logger):
    """
    Clip the full CORINE GPKG to the AOI and save a country-specific shapefile once.
    """
    corine_dir = os.path.join(DATA_DIR, "corine")
    layer = "U2018_CLC2018_V2020_20u1"
    gpkg_path = os.path.join(corine_dir, f"{layer}.gpkg")
    output_path = os.path.join(corine_dir, f"corine_{country_code}.shp")

    if os.path.exists(output_path):
        log_step(logger, f"[CORINE] Using cached clipped file: {output_path}")
        return output_path

    if not os.path.exists(gpkg_path):
        raise FileNotFoundError(f"Missing CORINE GPKG: {gpkg_path}")

    log_step(logger, f"[CORINE] Clipping country {country_code} from CORINE GPKG...")
    bbox = aoi_gdf.to_crs("EPSG:3035").total_bounds
    full_gdf = gpd.read_file(gpkg_path, layer=layer, bbox=tuple(bbox))

    if full_gdf.empty:
        raise ValueError(f"[ERROR] No CORINE data in bbox for {country_code}.")

    if full_gdf.crs != aoi_gdf.crs:
        aoi_gdf = aoi_gdf.to_crs(full_gdf.crs)

    clipped = gpd.overlay(full_gdf, aoi_gdf, how="intersection")
    if clipped.empty:
        raise ValueError(f"[ERROR] No intersection between CORINE and AOI for {country_code}.")

    clipped.to_file(output_path)
    log_step(logger, f"[CORINE] Saved clipped layer to {output_path}")
    return output_path


def run_aoi_analysis(country_code, logger):
    # (1) AOI
    aoi_gdf = load_country_aoi(country_code, logger)

    # (2) CORINE clip (cached)
    corine_path = ensure_country_corine_layer(country_code, aoi_gdf, logger)

    # (3) Protected Areas (Natura preferred, WDPA fallback optional)
    log_step(logger, "[PROTECTED] Loading protected area data (prefer=Natura2000)...")
    pa_gdf, pa_source = paa.load_protected_areas(prefer="natura", use_wdpa_fallback=True)
    log_step(logger, f"[PROTECTED] Source loaded: {pa_source} | features={len(pa_gdf)}")

    log_step(logger, "[PROTECTED] Computing AOI intersection with protected areas...")
    clipped_pa, total_pa_overlap = paa.intersect_aoi_with_protected(aoi_gdf, pa_gdf, area_crs="EPSG:3035")
    pa_summary_df = paa.summarize_overlap_table(clipped_pa)

    log_step(logger, f"[PROTECTED] Total overlap: {total_pa_overlap:.1f} ha | Sites in overlap: {len(pa_summary_df)}")

    # (Optional) Save the clipped protected polygons for mapping
    # paa.save_clipped_as_geojson(clipped_pa, os.path.join(BASE_DIR, "outputs", f"clipped_{pa_source}_{country_code}.geojson"))

    # (4) Land cover & emissions
    log_step(logger, "[RUN] Running land cover & emissions analysis...")
    landcover_summary, emissions_summary = aoi_landcover_analysis.run_full_analysis(
        aoi_gdf, country_code, corine_path
    )

    # (5) Save outputs
    output_xlsx = os.path.join(BASE_DIR, "outputs", f"analysis_summary_{country_code}.xlsx")
    with pd.ExcelWriter(output_xlsx, mode="w") as writer:
        landcover_summary.to_excel(writer, sheet_name="Land Cover Summary", index=False)
        emissions_summary.to_excel(writer, sheet_name="Emissions Summary", index=False)
        pa_summary_df.to_excel(writer, sheet_name=f"{pa_source}_Overlap", index=False)

    log_step(logger, f"[OUTPUT] Summary written to {output_xlsx}")
    log_memory_usage(logger, "After full AOI analysis")


def main():
    parser = argparse.ArgumentParser(description="AETHERA: EIA Automated Analysis")
    parser.add_argument("--country", type=str, required=True, help="ISO3 country code (e.g., GRC, ITA)")
    args = parser.parse_args()
    country_code = args.country.upper()

    print("\n--- AETHERA: EIA Automated Analysis ---\n")

    # Initialize logger *after* getting country code
    logger = setup_logger("AETHERA", country_code)

    try:
        log_step(logger, "Starting folder checks and setup...")
        ensure_directories(logger)
        ensure_base_datasets(country_code, logger)

        log_step(logger, f"Running AOI analysis for {country_code}...")
        run_aoi_analysis(country_code, logger)

        log_step(logger, "All processes completed successfully.")
        print("\n--- AETHERA: All processes completed successfully ---\n")
    except Exception as e:
        log_exception(logger, "Unhandled exception in AETHERA main pipeline", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
