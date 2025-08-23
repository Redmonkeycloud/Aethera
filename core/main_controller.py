# core/main_controller.py

import os
import sys
import argparse
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from core import gis_handler, aoi_landcover_analysis
from core import protected_area_analysis as paa
from core import buffer_analysis as buf
from core import osm_utils as osm
from core.emissions_api import from_corine_summary, monte_carlo_emissions
from utils.logging_utils import setup_logger, log_memory_usage, log_step, log_exception


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# -------------------------
# Helpers (local maps)
# -------------------------

def _plot_buffers_map(aoi_gdf, buffers_dict, title, out_png, logger=None):
    """
    Simple map export: AOI outline + dissolved buffers.
    buffers_dict: { "100m": GeoDataFrame, ... } typically with dissolve=True used.
    """
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        aoi_gdf.to_crs(epsg=3857).boundary.plot(ax=ax, color="black", linewidth=1.0)
        # Plot each buffer with an alpha
        for label, gdf in buffers_dict.items():
            gdf.to_crs(epsg=3857).plot(ax=ax, alpha=0.25, edgecolor="none", label=label)
        ax.set_title(title)
        ax.legend()
        ax.set_axis_off()
        plt.tight_layout()
        fig.savefig(out_png, dpi=200)
        plt.close(fig)
        if logger:
            logger.info(f"[MAP] Buffer map written: {out_png}")
    except Exception as e:
        if logger:
            logger.warning(f"[MAP] Failed to create buffer map: {e}")


def _plot_nearest_points_map(aoi_gdf, features_gdf, nearest_points_gdf, title, out_png, logger=None):
    """
    Simple map export: AOI boundary + features + nearest points locations (if available).
    """
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        aoi_gdf.to_crs(epsg=3857).boundary.plot(ax=ax, color="black", linewidth=1.0, label="AOI")
        # Features might be lines (roads/rivers)
        features_gdf.to_crs(epsg=3857).plot(ax=ax, color="#1f77b4", linewidth=0.8, alpha=0.8, label="Features")
        # If we have nearest points as a GeoDataFrame
        if nearest_points_gdf is not None and not nearest_points_gdf.empty:
            nearest_points_gdf.to_crs(epsg=3857).plot(ax=ax, color="red", markersize=10, label="Nearest Points")
        ax.set_title(title)
        ax.legend()
        ax.set_axis_off()
        plt.tight_layout()
        fig.savefig(out_png, dpi=200)
        plt.close(fig)
        if logger:
            logger.info(f"[MAP] Nearest points map written: {out_png}")
    except Exception as e:
        if logger:
            logger.warning(f"[MAP] Failed to create nearest points map: {e}")


# -------------------------
# Setup/Ensure Data
# -------------------------

def ensure_directories(logger):
    """Create necessary base folders if missing."""
    for folder in ["data", "outputs"]:
        os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)
    # Additional folders for proximity
    for folder in ["roads", "rivers", "grid", "protected_areas"]:
        os.makedirs(os.path.join(DATA_DIR, folder), exist_ok=True)
    log_step(logger, "[INIT] Folder structure ensured.")


def ensure_base_datasets(country_code, logger):
    """Check and download required base datasets if missing."""
    log_step(logger, "[INIT] Checking base datasets...")

    dirs = {
        "NATURAL_EARTH": os.path.join(DATA_DIR, "natural_earth"),
        "GADM": os.path.join(DATA_DIR, "gadm"),
        "EUROSTAT": os.path.join(DATA_DIR, "eurostat"),
        "CORINE": os.path.join(DATA_DIR, "corine"),
        "RIVERS": os.path.join(DATA_DIR, "rivers"),
        "ROADS": os.path.join(DATA_DIR, "roads"),
        "GRID": os.path.join(DATA_DIR, "grid"),
        "PROTECTED": os.path.join(DATA_DIR, "protected_areas"),
    }

    for path in dirs.values():
        os.makedirs(path, exist_ok=True)

    # Natural Earth (admin boundaries world)
    if not os.listdir(dirs["NATURAL_EARTH"]):
        gis_handler.download_natural_earth()

    # GADM (per country)
    gadm_file = os.path.join(dirs["GADM"], f"gadm41_{country_code}_0.shp")
    if not os.path.exists(gadm_file):
        gis_handler.download_gadm(country_code)

    # Eurostat NUTS
    if not os.listdir(dirs["EUROSTAT"]):
        gis_handler.download_eurostat()

    # CORINE (manual)
    corine_files = os.listdir(dirs["CORINE"])
    if not any(f.lower().endswith(".gpkg") for f in corine_files):
        logger.warning("[CORINE] Please manually place the CORINE GPKG into /data/corine/")

    # Rivers: HydroRIVERS expected manually
    if not any(f.lower().endswith(".shp") for f in os.listdir(dirs["RIVERS"])):
        logger.warning("[RIVERS] Place HydroRIVERS shapefile in /data/rivers (EU or global).")

    # Grid: optionally place your energy infra layers in /data/grid
    # e.g. 'grid.gpkg' or 'powerlines.shp' or 'substations.shp'
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


# -------------------------
# Main AOI Pipeline
# -------------------------

def run_aoi_analysis(country_code, logger):
    """
    Full AOI analysis:
      1) Load AOI
      2) Clip CORINE (cached)
      3) Protected Areas (Natura preferred; WDPA fallback)
      4) Land Cover & Emissions + Monte Carlo uncertainty
      4b) Proximity to Roads (OSMnx cached) and Rivers (HydroRIVERS)
      4c) (Optional) Distance-to-Grid (if present)
      5) Save outputs to Excel (+ maps)
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # (1) AOI
    aoi_gdf = load_country_aoi(country_code, logger)

    # (2) CORINE clip (cached)
    corine_path = ensure_country_corine_layer(country_code, aoi_gdf, logger)

    # (3) Protected Areas (Natura preferred; WDPA fallback)
    try:
        log_step(logger, "[PROTECTED] Loading protected area data (prefer=Natura2000)...")
        pa_gdf, pa_source = paa.load_protected_areas(prefer="natura", use_wdpa_fallback=True)
        log_step(logger, f"[PROTECTED] Source loaded: {pa_source} | features={len(pa_gdf)}")

        log_step(logger, "[PROTECTED] Computing AOI intersection with protected areas...")
        clipped_pa, total_pa_overlap = paa.intersect_aoi_with_protected(aoi_gdf, pa_gdf, area_crs="EPSG:3035")
        pa_summary_df = paa.summarize_overlap_table(clipped_pa)

        log_step(logger, f"[PROTECTED] Total overlap: {total_pa_overlap:.1f} ha | Sites overlapping: {len(pa_summary_df)}")

        # Optional: save clipped PA polygons for mapping
        paa.save_clipped_as_geojson(
            clipped_pa,
            os.path.join(OUTPUT_DIR, f"clipped_{pa_source}_{country_code}.geojson")
        )
    except Exception as e:
        logger.warning(f"[PROTECTED] Skipping protected areas due to error: {e}")
        clipped_pa = gpd.GeoDataFrame()
        pa_summary_df = pd.DataFrame(columns=["site_code", "site_name", "overlap_ha"])
        pa_source = "ProtectedAreas"

    # (4) Land cover & emissions
    log_step(logger, "[RUN] Running land cover & emissions analysis...")
    landcover_summary, emissions_summary = aoi_landcover_analysis.run_full_analysis(
        aoi_gdf, country_code, corine_path, logger=logger
    )

    # Emissions Uncertainty (Monte Carlo)
    try:
        log_step(logger, "[EMISSIONS] Computing uncertainty via Monte Carlo (n_sim=2000)...")
        cat_areas = from_corine_summary(landcover_summary)  # {category: area_ha}
        mc_df = monte_carlo_emissions(cat_areas, country=country_code, years=1, n_sim=2000)
    except Exception as e:
        mc_df = pd.DataFrame([{
            "n_sim": 0, "years": 1,
            "total_mean_tCO2e": None,
            "total_p05_tCO2e": None,
            "total_p50_tCO2e": None,
            "total_p95_tCO2e": None
        }])
        logger.warning(f"[EMISSIONS] Monte Carlo failed: {e}")

    # (4b) Proximity analysis — Roads (OSMnx cached)
    roads_dist_tbl = pd.DataFrame()
    roads_stats_df = pd.DataFrame()
    roads_overlap_df = pd.DataFrame()
    roads_buffers = {}

    try:
        log_step(logger, "[PROX] Ensuring cached roads layer via OSMnx...")
        roads_gpkg = osm.ensure_osmnx_cached(
            country_code=country_code,
            aoi_gdf=aoi_gdf,
            logger=logger,
            buffer_m=5000,
            force=False
        )
        roads_gdf = osm.load_roads_layer(roads_gpkg, logger=logger)

        # Clip to AOI bbox and run proximity suite
        roads_clipped = buf.clip_to_aoi_bbox(roads_gdf, aoi_gdf, expand_m=5000.0, logger=logger)
        roads_prox = buf.run_proximity_suite(
            aoi_gdf=aoi_gdf,
            features_gdf=roads_clipped,
            features_label="roads",
            buffer_distances_m=(100, 250, 500, 1000),
            dissolve_buffers=True,
            logger=logger
        )

        roads_dist_tbl = roads_prox["aoi_dist_table"]        # DataFrame: aoi_index, min_dist_to_roads_m
        roads_stats_df = roads_prox["distance_stats"]        # DataFrame: label, mean/min/max/p50/p95
        roads_overlap_df = roads_prox["buffer_overlap"]      # DataFrame: buffer, overlap_ha, pct_of_aoi
        roads_buffers = roads_prox["buffers"]

        # Optional: Save nearest roads per AOI
        roads_dist_tbl.to_csv(os.path.join(OUTPUT_DIR, f"aoi_nearest_roads_{country_code}.csv"), index=False)

        # Maps for roads
        _plot_buffers_map(aoi_gdf, roads_buffers, title="Roads Buffers", 
                          out_png=os.path.join(OUTPUT_DIR, f"roads_buffers_{country_code}.png"), logger=logger)
        # Note: If nearest points are needed visually, add return_geometry in buffer module and pass it here.

    except Exception as e:
        logger.warning(f"[PROX] Roads proximity step failed: {e}")

    # (4c) Proximity analysis — Rivers (HydroRIVERS)
    rivers_dist_tbl = pd.DataFrame()
    rivers_stats_df = pd.DataFrame()
    rivers_overlap_df = pd.DataFrame()
    rivers_buffers = {}

    try:
        river_dir = os.path.join(DATA_DIR, "rivers")
        possible_rivers = [
            os.path.join(river_dir, "HydroRIVERS_v10_eu.shp"),
            os.path.join(river_dir, "HydroRIVERS_v10.shp"),
        ]
        hydro_path = next((p for p in possible_rivers if os.path.exists(p)), None)
        if hydro_path:
            log_step(logger, "[PROX] Loading HydroRIVERS and clipping to AOI bounds...")
            rivers_gdf = buf.load_rivers(hydro_path, aoi_gdf=aoi_gdf, logger=logger)

            rivers_prox = buf.run_proximity_suite(
                aoi_gdf=aoi_gdf,
                features_gdf=rivers_gdf,
                features_label="rivers",
                buffer_distances_m=(100, 250, 500, 1000),
                dissolve_buffers=True,
                logger=logger
            )

            rivers_dist_tbl = rivers_prox["aoi_dist_table"]
            rivers_stats_df = rivers_prox["distance_stats"]
            rivers_overlap_df = rivers_prox["buffer_overlap"]
            rivers_buffers = rivers_prox["buffers"]

            # Save nearest rivers per AOI
            rivers_dist_tbl.to_csv(os.path.join(OUTPUT_DIR, f"aoi_nearest_rivers_{country_code}.csv"), index=False)

            _plot_buffers_map(aoi_gdf, rivers_buffers, title="Rivers Buffers", 
                              out_png=os.path.join(OUTPUT_DIR, f"rivers_buffers_{country_code}.png"), logger=logger)
        else:
            logger.warning("[PROX] No HydroRIVERS shapefile found — skipping rivers proximity.")
    except Exception as e:
        logger.warning(f"[PROX] Rivers proximity step failed: {e}")

    # (4d) OPTIONAL: Distance-to-grid (if present)
    grid_dist_tbl = pd.DataFrame()
    grid_stats_df = pd.DataFrame()
    grid_overlap_df = pd.DataFrame()
    grid_buffers = {}
    try:
        grid_dir = os.path.join(DATA_DIR, "grid")
        # Try a few layer name patterns:
        possible_grid_paths = [
            os.path.join(grid_dir, "grid.gpkg"),
            os.path.join(grid_dir, "powerlines.shp"),
            os.path.join(grid_dir, "substations.shp")
        ]
        grid_path = next((p for p in possible_grid_paths if os.path.exists(p)), None)
        if grid_path:
            log_step(logger, "[GRID] Found grid layer; computing proximity...")
            grid_gdf = gpd.read_file(grid_path)
            grid_gdf = grid_gdf.to_crs(aoi_gdf.crs)

            grid_clipped = buf.clip_to_aoi_bbox(grid_gdf, aoi_gdf, expand_m=5000.0, logger=logger)
            grid_prox = buf.run_proximity_suite(
                aoi_gdf=aoi_gdf,
                features_gdf=grid_clipped,
                features_label="grid",
                buffer_distances_m=(250, 500, 1000, 5000),
                dissolve_buffers=True,
                logger=logger
            )
            grid_dist_tbl = grid_prox["aoi_dist_table"]
            grid_stats_df = grid_prox["distance_stats"]
            grid_overlap_df = grid_prox["buffer_overlap"]
            grid_buffers = grid_prox["buffers"]

            grid_dist_tbl.to_csv(os.path.join(OUTPUT_DIR, f"aoi_nearest_grid_{country_code}.csv"), index=False)

            _plot_buffers_map(aoi_gdf, grid_buffers, title="Grid Buffers", 
                              out_png=os.path.join(OUTPUT_DIR, f"grid_buffers_{country_code}.png"), logger=logger)
        else:
            logger.info("[GRID] No grid layer found; skip grid proximity.")
    except Exception as e:
        logger.warning(f"[GRID] Grid proximity step failed: {e}")

    # (4e) Combined Proximity Summary
    combined_summary_rows = []
    # For each AOI index, record min distances to each category if available
    aoi_indices = list(aoi_gdf.index)

    for idx in aoi_indices:
        row = {"aoi_index": idx}

        if not roads_dist_tbl.empty:
            cols_road = [c for c in roads_dist_tbl.columns if "min_dist_to_roads" in c]
            row["min_dist_to_roads_m"] = float(roads_dist_tbl[roads_dist_tbl["aoi_index"] == idx][cols_road].min(axis=1).fillna(float("inf")).min()) if cols_road else None
        else:
            row["min_dist_to_roads_m"] = None

        if not rivers_dist_tbl.empty:
            cols_rivers = [c for c in rivers_dist_tbl.columns if "min_dist_to_rivers" in c]
            row["min_dist_to_rivers_m"] = float(rivers_dist_tbl[rivers_dist_tbl["aoi_index"] == idx][cols_rivers].min(axis=1).fillna(float("inf")).min()) if cols_rivers else None
        else:
            row["min_dist_to_rivers_m"] = None

        if not grid_dist_tbl.empty:
            cols_grid = [c for c in grid_dist_tbl.columns if "min_dist_to_grid" in c]
            row["min_dist_to_grid_m"] = float(grid_dist_tbl[grid_dist_tbl["aoi_index"] == idx][cols_grid].min(axis=1).fillna(float("inf")).min()) if cols_grid else None
        else:
            row["min_dist_to_grid_m"] = None

        combined_summary_rows.append(row)

    combined_proximity_df = pd.DataFrame(combined_summary_rows)

    # (5) Save outputs — Excel with all sheets
    output_xlsx = os.path.join(OUTPUT_DIR, f"analysis_summary_{country_code}.xlsx")
    with pd.ExcelWriter(output_xlsx, mode="w") as writer:
        # Land cover + emissions
        landcover_summary.to_excel(writer, sheet_name="Land Cover Summary", index=False)
        emissions_summary.to_excel(writer, sheet_name="Emissions Summary", index=False)
        mc_df.to_excel(writer, sheet_name="Emissions Uncertainty (MC)", index=False)

        # Protected areas
        pa_summary_df.to_excel(writer, sheet_name=f"{pa_source}_Overlap", index=False)

        # Proximity: Roads
        if not roads_stats_df.empty:
            roads_stats_df.to_excel(writer, sheet_name="Roads_Distance_Stats", index=False)
        if not roads_overlap_df.empty:
            roads_overlap_df.to_excel(writer, sheet_name="Roads_Buffer_Overlap", index=False)
        if not roads_dist_tbl.empty:
            roads_dist_tbl.to_excel(writer, sheet_name="Roads_Distance_PerAOI", index=False)

        # Proximity: Rivers
        if not rivers_stats_df.empty:
            rivers_stats_df.to_excel(writer, sheet_name="Rivers_Distance_Stats", index=False)
        if not rivers_overlap_df.empty:
            rivers_overlap_df.to_excel(writer, sheet_name="Rivers_Buffer_Overlap", index=False)
        if not rivers_dist_tbl.empty:
            rivers_dist_tbl.to_excel(writer, sheet_name="Rivers_Distance_PerAOI", index=False)

        # Proximity: Grid
        if not grid_stats_df.empty:
            grid_stats_df.to_excel(writer, sheet_name="Grid_Distance_Stats", index=False)
        if not grid_overlap_df.empty:
            grid_overlap_df.to_excel(writer, sheet_name="Grid_Buffer_Overlap", index=False)
        if not grid_dist_tbl.empty:
            grid_dist_tbl.to_excel(writer, sheet_name="Grid_Distance_PerAOI", index=False)

        # Combined summary
        if not combined_proximity_df.empty:
            combined_proximity_df.to_excel(writer, sheet_name="Combined_Proximity_Summary", index=False)

    log_step(logger, f"[OUTPUT] Summary written to {output_xlsx}")
    log_memory_usage(logger, "After full AOI analysis")


# -------------------------
# Entrypoint
# -------------------------

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
