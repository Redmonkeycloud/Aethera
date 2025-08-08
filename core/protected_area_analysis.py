# protected_area_analysis.py
"""
Protected Area analysis utilities for AETHERA.

Features:
- Load Natura 2000 polygons (EEA) from the project data folder.
- Optional fallback to WDPA if Natura 2000 layer is missing.
- Intersect AOI with protected areas and compute overlap area (hectares).
- Summarize overlaps by site name and designation for reporting.
- Optional exporters for clipped outputs.

Assumptions:
- Natura 2000 dataset is a shapefile bundle stored at:
  data/protected_areas/natura2000/Natura2000_end2021_rev1_epsg3035.shp
  (and its .shx/.dbf/.prj/.cpg siblings in the same folder)

- CRS:
  * Natura 2000 file is EPSG:3035 (meters) — great for area calculations.
  * AOI can be in any CRS; functions will reproject as needed.
"""

from __future__ import annotations

import os
import geopandas as gpd
import pandas as pd
from typing import Optional, Tuple

# ---------------------------------------------------------------------
# Default paths (relative to project root)
# ---------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

NATURA_SHAPEFILE = os.path.join(
    BASE_DIR,
    "data",
    "protected_areas",
    "natura2000",
    "Natura2000_end2021_rev1_epsg3035.shp",
)

# If you also download WDPA, set the path here (optional fallback)
WDPA_SHP = os.path.join(
    BASE_DIR,
    "data",
    "protected_areas",
    "wdpa",
    "WDPA_Public.shp",  # adjust to your actual filename if you add WDPA
)

# Designation columns in WDPA that may indicate Natura-like sites (fallback filter)
WDPA_DESIG_COLS = ["DESIG_ENG", "DESIG", "INT_DESIG", "DESIG_TYPE"]
WDPA_NATURA_HINTS = [
    "natura 2000",
    "special protection area",
    "special area of conservation",
    "site of community importance",
    "birds directive",
    "habitats directive",
    "spa",
    "sac",
    "sci",
]

# ---------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------

def load_natura2000() -> gpd.GeoDataFrame:
    """
    Load Natura 2000 polygons (EEA shapefile). Raises if file is missing.

    Returns
    -------
    GeoDataFrame
        Natura 2000 polygon layer (expected EPSG:3035).
    """
    if not os.path.exists(NATURA_SHAPEFILE):
        raise FileNotFoundError(
            f"Natura 2000 shapefile not found:\n  {NATURA_SHAPEFILE}\n"
            "Ensure all shapefile components (.shp/.shx/.dbf/.prj/.cpg) are in the same folder."
        )
    gdf = gpd.read_file(NATURA_SHAPEFILE)
    # Ensure CRS is set (EEA file should be EPSG:3035)
    if gdf.crs is None:
        gdf.set_crs("EPSG:3035", inplace=True)
    return gdf


def load_wdpa_filtered_to_natura(wdpa_path: Optional[str] = None) -> gpd.GeoDataFrame:
    """
    OPTIONAL fallback: load WDPA shapefile and keep entries that look like Natura 2000.
    If WDPA not found, raises FileNotFoundError.

    Parameters
    ----------
    wdpa_path : str, optional
        Path to WDPA shapefile; defaults to WDPA_SHP.

    Returns
    -------
    GeoDataFrame
        Filtered WDPA layer (may be empty if no hints are found).
    """
    path = wdpa_path or WDPA_SHP
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"WDPA shapefile not found at:\n  {path}\n"
            "Place WDPA under data/protected_areas/wdpa/ or disable fallback."
        )
    wdpa = gpd.read_file(path)
    if wdpa.crs is None:
        # WDPA is often EPSG:4326, but set if missing
        wdpa.set_crs("EPSG:4326", inplace=True)

    # Try filtering by designation text
    mask = pd.Series(False, index=wdpa.index)
    for col in WDPA_DESIG_COLS:
        if col in wdpa.columns:
            colvals = wdpa[col].astype(str).str.lower()
            for hint in WDPA_NATURA_HINTS:
                mask |= colvals.str.contains(hint, na=False)

    filtered = wdpa[mask]
    return filtered if not filtered.empty else wdpa  # if no hints, return all WDPA to avoid false negatives


def load_protected_areas(prefer: str = "natura", use_wdpa_fallback: bool = True) -> Tuple[gpd.GeoDataFrame, str]:
    """
    Load protected areas:
      - If prefer='natura': try Natura 2000 first, else fallback to WDPA (if enabled).
      - If prefer='wdpa' : load WDPA immediately.

    Returns
    -------
    (GeoDataFrame, str)
        The PA layer and a label of the source: 'NATURA2000', 'WDPA_NATURA_FILTERED' or 'WDPA_ALL'.
    """
    if prefer.lower() == "wdpa":
        gdf = load_wdpa_filtered_to_natura()
        src = "WDPA_NATURA_FILTERED" if "DESIG" in gdf.columns else "WDPA_ALL"
        return gdf, src

    # prefer Natura
    try:
        gdf = load_natura2000()
        return gdf, "NATURA2000"
    except FileNotFoundError:
        if not use_wdpa_fallback:
            raise
        gdf = load_wdpa_filtered_to_natura()
        src = "WDPA_NATURA_FILTERED" if "DESIG" in gdf.columns else "WDPA_ALL"
        return gdf, src

# ---------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------

def intersect_aoi_with_protected(
    aoi_gdf: gpd.GeoDataFrame,
    pa_gdf: gpd.GeoDataFrame,
    area_crs: str = "EPSG:3035",
) -> Tuple[gpd.GeoDataFrame, float]:
    """
    Intersect AOI with protected areas and compute overlap in hectares.

    Notes:
    - Reprojects to a metric CRS (default EPSG:3035) for accurate area.
    - Returns both the clipped layer and total overlap (ha).

    Parameters
    ----------
    aoi_gdf : GeoDataFrame
        AOI polygons.
    pa_gdf : GeoDataFrame
        Protected area polygons (Natura/WDPA).
    area_crs : str
        CRS used to compute area in meters.

    Returns
    -------
    (GeoDataFrame, float)
        Clipped GeoDataFrame with 'overlap_ha', total overlap in hectares.
    """
    # Harmonize before overlay (use PA CRS for topological overlay)
    if aoi_gdf.crs != pa_gdf.crs:
        aoi_aligned = aoi_gdf.to_crs(pa_gdf.crs)
    else:
        aoi_aligned = aoi_gdf

    clipped = gpd.overlay(pa_gdf, aoi_aligned, how="intersection")
    if clipped.empty:
        return clipped, 0.0

    # Area calc in a metric CRS
    if clipped.crs is None or clipped.crs.is_geographic:
        clipped = clipped.to_crs(area_crs)
    elif clipped.crs.to_string().lower() != area_crs.lower():
        clipped = clipped.to_crs(area_crs)

    clipped["overlap_ha"] = (clipped.geometry.area / 10000.0).astype(float)
    total_overlap = float(clipped["overlap_ha"].sum())
    return clipped, total_overlap


def summarize_overlap_table(
    clipped_gdf: gpd.GeoDataFrame,
    name_fields: tuple = ("SITENAME", "NAME", "SITE_NAME", "SITECODE"),
    desig_fields: tuple = ("DESIG_ENG", "DESIG", "DESIG_TYPE"),
) -> pd.DataFrame:
    """
    Build a tidy summary table: site_name, designation, overlap_ha (descending).

    Parameters
    ----------
    clipped_gdf : GeoDataFrame
        Result of intersect_aoi_with_protected.
    name_fields : tuple
        Candidate columns for site name.
    desig_fields : tuple
        Candidate columns for designation.

    Returns
    -------
    DataFrame
        Columns: ['site_name', 'designation', 'overlap_ha']
    """
    if clipped_gdf.empty:
        return pd.DataFrame(columns=["site_name", "designation", "overlap_ha"])

    site_name_col = next((c for c in name_fields if c in clipped_gdf.columns), None)
    desig_col = next((c for c in desig_fields if c in clipped_gdf.columns), None)

    out = clipped_gdf.copy()
    out["site_name"] = out[site_name_col] if site_name_col else "Unknown"
    out["designation"] = out[desig_col] if desig_col else "Unknown"

    tbl = (
        out.groupby(["site_name", "designation"], dropna=False)["overlap_ha"]
          .sum()
          .reset_index()
          .sort_values("overlap_ha", ascending=False)
    )
    return tbl

# ---------------------------------------------------------------------
# Optional exporters (use from main if you want to persist)
# ---------------------------------------------------------------------

def save_clipped_as_geojson(clipped_gdf: gpd.GeoDataFrame, out_path: str) -> str:
    """
    Save clipped protected areas as GeoJSON for web/inspection.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    clipped_gdf.to_file(out_path, driver="GeoJSON")
    return out_path


def save_clipped_as_shapefile(clipped_gdf: gpd.GeoDataFrame, out_path: str) -> str:
    """
    Save clipped protected areas as Shapefile (folder must be writable).
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    clipped_gdf.to_file(out_path)
    return out_path
