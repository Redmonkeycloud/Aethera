# aoi_landcover_analysis.py

import os
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional, Tuple, Dict, Any
from core.emissions_api import estimate_from_corine_summary

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# CORINE code-to-label mapping (expand as you go)
CORINE_CODES = {
    111: "Continuous Urban Fabric",
    112: "Discontinuous Urban Fabric",
    121: "Industrial or Commercial Units",
    131: "Mineral Extraction Sites",
    211: "Non-Irrigated Arable Land",
    231: "Pastures",
    311: "Broad-leaved Forest",
    312: "Coniferous Forest",
    313: "Mixed Forest",
    321: "Natural Grasslands",
    411: "Inland Marshes",
    511: "Water Courses",
    512: "Water Bodies",
}

# Optional: fixed palette to keep colors stable across runs
COLOR_MAP = {
    "Continuous Urban Fabric": "#b2182b",
    "Discontinuous Urban Fabric": "#ef8a62",
    "Industrial or Commercial Units": "#d6604d",
    "Mineral Extraction Sites": "#fddbc7",
    "Non-Irrigated Arable Land": "#d9ef8b",
    "Pastures": "#a6d96a",
    "Broad-leaved Forest": "#1b7837",
    "Coniferous Forest": "#4dac26",
    "Mixed Forest": "#80cdc1",
    "Natural Grasslands": "#5ab4ac",
    "Inland Marshes": "#c7eae5",
    "Water Courses": "#2166ac",
    "Water Bodies": "#67a9cf",
    "Unknown": "#cccccc",
}

def _pick_corine_code_column(gdf: gpd.GeoDataFrame) -> str:
    """
    Try a few common CORINE code column names and return the one that exists.
    Raises KeyError if none found.
    """
    cols_lower = {c.lower(): c for c in gdf.columns}
    for candidate in ("code_18", "code18", "code", "clc_code", "code_12"):  # add more if needed
        if candidate in cols_lower:
            return cols_lower[candidate]
    # last resort: try case-sensitive common names
    for candidate in ("Code_18", "CODE_18"):
        if candidate in gdf.columns:
            return candidate
    raise KeyError("Could not find CORINE land-cover code column (e.g., 'Code_18').")

def intersect_aoi_with_corine(
    aoi_gdf: gpd.GeoDataFrame,
    corine_shapefile_path: str,
    logger: Optional[Any] = None
) -> Tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """
    Intersect AOI with CORINE, compute per-class areas, and return:
      - clipped GeoDataFrame (with 'area_ha' and 'land_cover_label')
      - summary DataFrame (corine_code, land_cover, area_hectares, pct_of_aoi)
    """
    if logger: logger.info(f"[CORINE] Reading: {corine_shapefile_path}")
    corine = gpd.read_file(corine_shapefile_path)

    # Align CRS for topological operations
    if corine.crs != aoi_gdf.crs:
        if logger: logger.debug("[CORINE] Reprojecting AOI to CORINE CRS for overlay")
        aoi_gdf = aoi_gdf.to_crs(corine.crs)

    # Clip with overlay (exact geometry)
    if logger: logger.info("[CORINE] Intersecting AOI with CORINE (overlay)...")
    clipped = gpd.overlay(corine, aoi_gdf, how="intersection")
    if clipped.empty:
        if logger: logger.warning("[CORINE] No overlap found between AOI and CORINE.")
        # return empty structures with expected columns
        return clipped, pd.DataFrame(columns=["corine_code", "land_cover", "area_hectares", "pct_of_aoi"])

    # Compute area in EPSG:3035 (EU metric)
    if clipped.crs is None or clipped.crs.to_string().lower() != "epsg:3035":
        if logger: logger.debug("[CORINE] Reprojecting clipped layer to EPSG:3035 for area (ha)")
        clipped = clipped.to_crs("EPSG:3035")
    clipped["area_ha"] = clipped.geometry.area / 10_000.0

    # Try to keep just the essentials to reduce memory footprint
    # (keep any code/name columns you care about)
    try:
        code_col = _pick_corine_code_column(clipped)
    except KeyError as e:
        if logger: logger.exception("[CORINE] Missing code column in CORINE layer.")
        raise

    # Map codes to labels
    def _map_label(v):
        try:
            return CORINE_CODES.get(int(v), "Unknown")
        except Exception:
            return "Unknown"

    clipped["land_cover_label"] = clipped[code_col].apply(_map_label)

    # AOI area (for % calculation)
    aoi_for_area = aoi_gdf.to_crs("EPSG:3035")
    aoi_area_ha = float(aoi_for_area.geometry.area.sum() / 10_000.0)

    # Summary table
    summary = (
        clipped
        .groupby([code_col, "land_cover_label"], dropna=False)["area_ha"]
        .sum()
        .reset_index()
        .rename(columns={code_col: "corine_code", "land_cover_label": "land_cover", "area_ha": "area_hectares"})
        .sort_values("area_hectares", ascending=False)
    )
    if aoi_area_ha > 0:
        summary["pct_of_aoi"] = (summary["area_hectares"] / aoi_area_ha) * 100.0
    else:
        summary["pct_of_aoi"] = 0.0

    if logger:
        logger.info(f"[CORINE] Classes found: {summary.shape[0]}; AOI area: {aoi_area_ha:.1f} ha")

    return clipped, summary

def _plot_landcover(
    clipped_gdf: gpd.GeoDataFrame,
    country_code: str,
    out_png: str,
    logger: Optional[Any] = None
):
    """Plot land cover classes with a stable color palette."""
    if clipped_gdf.empty:
        if logger: logger.warning("[PLOT] Nothing to plot (empty clipped layer).")
        return

    # Build color series matching labels
    labels = clipped_gdf["land_cover_label"].fillna("Unknown")
    colors = labels.map(lambda lbl: COLOR_MAP.get(lbl, COLOR_MAP["Unknown"]))

    fig, ax = plt.subplots(figsize=(12, 10))
    clipped_gdf.plot(ax=ax, color=colors, edgecolor="black", linewidth=0.2)
    ax.set_title(f"Land Cover Classes - {country_code}", fontsize=14)
    ax.set_axis_off()

    # Simple legend (unique labels)
    uniq = pd.Series(labels.unique())
    # Create basic legend patches
    from matplotlib.patches import Patch
    patches = [Patch(facecolor=COLOR_MAP.get(lbl, "#cccccc"), label=lbl) for lbl in uniq]
    ax.legend(handles=patches, loc="lower left", fontsize=8, frameon=True)

    plt.tight_layout()
    plt.savefig(out_png, dpi=180)
    plt.close()
    if logger: logger.info(f"[PLOT] Saved land cover map to {out_png}")

def run_full_analysis(
    aoi_gdf: gpd.GeoDataFrame,
    country_code: str,
    corine_shapefile_path: str,
    logger: Optional[Any] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, str]]:
    """
    Full AOI analysis:
      1) Intersect AOI with CORINE
      2) Summarize by class (ha, % of AOI)
      3) Estimate emissions (uses land_cover_label → emissions_api factors)
      4) Export GeoJSON + PNG map

    Returns:
      - landcover_summary (DataFrame)
      - emissions_summary (DataFrame)
      - artifacts (dict with paths to 'clipped_geojson' and 'plot_png')
    """
    clipped_gdf, landcover_summary = intersect_aoi_with_corine(aoi_gdf, corine_shapefile_path, logger=logger)

    landcover_summary_df = landcover_summary  # what you already computed
    emissions_summary = estimate_from_corine_summary(
                        landcover_summary_df, country=country_code, years=1
                        )

    # Save clipped GeoJSON
    clipped_geojson = os.path.join(OUTPUT_DIR, f"clipped_landcover_{country_code}.geojson")
    if not clipped_gdf.empty:
        # keep only essential columns to keep file size sane
        essential_cols = ["land_cover_label", "area_ha"]
        keep = [c for c in essential_cols if c in clipped_gdf.columns]
        out_gdf = clipped_gdf[keep + ["geometry"]] if keep else clipped_gdf[["geometry"]]
        out_gdf.to_file(clipped_geojson, driver="GeoJSON")
        if logger: logger.info(f"[OUTPUT] Saved clipped land cover GeoJSON to {clipped_geojson}")
    else:
        clipped_geojson = ""

    # Save plot PNG
    plot_png = os.path.join(OUTPUT_DIR, f"land_cover_map_{country_code}.png")
    _plot_landcover(clipped_gdf, country_code, plot_png, logger=logger)

    artifacts = {"clipped_geojson": clipped_geojson, "plot_png": plot_png}
    return landcover_summary, emissions_summary, artifacts


if __name__ == "__main__":
    print("[ERROR] Please run this module via 'main_controller.py'.")
