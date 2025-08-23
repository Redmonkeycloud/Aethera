# core/buffer_analysis.py
from __future__ import annotations

import os
from typing import Iterable, Dict, Any, Optional, List, Tuple

import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.strtree import STRtree  # Correct for Shapely >= 2.0


DEFAULT_METRIC_CRS = "EPSG:3035"  # LAEA Europe recommended for meters


# ---------------------------
# CRS & Core Helpers
# ---------------------------

def _ensure_metric_crs(
    gdf: gpd.GeoDataFrame,
    prefer: str = DEFAULT_METRIC_CRS,
    fallback: str = "EPSG:3857",
    logger: Optional[Any] = None,
) -> gpd.GeoDataFrame:
    """
    Ensure GeoDataFrame is in a projected metric CRS for distance/area ops.
    Prefers EPSG:3035 (EU LAEA); falls back to EPSG:3857 if reprojection fails.
    """
    if gdf.crs is None:
        raise ValueError("Input GeoDataFrame has no CRS. Please set a valid CRS before calling proximity functions.")

    if gdf.crs.is_geographic:
        try:
            if logger: logger.debug(f"[CRS] Reprojecting to {prefer} for metric distances.")
            return gdf.to_crs(prefer)
        except Exception:
            if logger: logger.warning(f"[CRS] Failed to project to {prefer}; falling back to {fallback}")
            return gdf.to_crs(fallback)

    # Already projected; keep as-is
    return gdf


def load_vector_data(path: str) -> gpd.GeoDataFrame:
    """Load shapefile/GeoJSON/GPKG/etc. as GeoDataFrame (CRS must be present)."""
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        raise ValueError(f"Loaded data at {path} has no CRS; set it before running analysis.")
    return gdf


def clip_to_aoi_bbox(
    features_gdf: gpd.GeoDataFrame,
    aoi_gdf: gpd.GeoDataFrame,
    expand_m: float = 5000.0,
    logger: Optional[Any] = None
) -> gpd.GeoDataFrame:
    """
    Clip features to an expanded AOI bounding box in metric CRS for performance.
    """
    aoi_m = _ensure_metric_crs(aoi_gdf, logger=logger)
    feat_m = _ensure_metric_crs(features_gdf, logger=logger)

    minx, miny, maxx, maxy = aoi_m.total_bounds
    minx -= expand_m; miny -= expand_m; maxx += expand_m; maxy += expand_m
    bbox_poly = gpd.GeoDataFrame(
        geometry=[Polygon.from_bounds(minx, miny, maxx, maxy)],
        crs=aoi_m.crs
    )
    try:
        clipped = gpd.overlay(feat_m, bbox_poly, how="intersection")
        if logger:
            logger.info(f"[CLIP] Features clipped to expanded AOI bbox; remaining={len(clipped)}")
        return clipped
    except Exception as e:
        if logger:
            logger.warning(f"[CLIP] Overlay failed; using bbox filter only: {e}")
        # Fallback bbox spatial filter
        return feat_m.cx[minx:maxx, miny:maxy]


# ---------------------------
# Distance / Proximity
# ---------------------------

def nearest_distance_table(
    aoi_gdf: gpd.GeoDataFrame,
    features_gdf: gpd.GeoDataFrame,
    label: str,
    k: int = 1,
    return_geometry: bool = False,
    logger: Optional[Any] = None
) -> gpd.GeoDataFrame:
    """
    Compute nearest distance from each AOI geometry to the nearest feature (meters).
    Uses GeoPandas Spatial Index (sindex.nearest) with candidate reduction.

    Returns a DataFrame (or GeoDataFrame if return_geometry=True) with columns:
    - aoi_index
    - min_dist_to_{label}_m
    """
    aoi_m = _ensure_metric_crs(aoi_gdf, logger=logger)
    feat_m = _ensure_metric_crs(features_gdf, logger=logger)

    # Build spatial index
    _ = feat_m.sindex  # triggers building sindex

    results = []
    for idx, geom in aoi_m.geometry.items():
        if geom is None or geom.is_empty:
            results.append({"aoi_index": idx, f"min_dist_to_{label}_m": float("nan")})
            continue

        try:
            # Get candidate nearest indices based on bounds
            # In newer GeoPandas, you can use sindex.nearest with a geometry and max_results
            cand_idx = list(feat_m.sindex.nearest(geom.bounds, num_results=max(10, k * 10)))
            candidates = feat_m.iloc[cand_idx]
            if candidates.empty:
                mind = float("nan")
            else:
                dists = candidates.distance(geom)
                mind = float(dists.min())
        except Exception:
            # Fallback: brute distance (slower)
            mind = float(feat_m.distance(geom).min())

        results.append({"aoi_index": idx, f"min_dist_to_{label}_m": mind})

    out = pd.DataFrame(results)
    if return_geometry:
        out_gdf = aoi_m.reset_index().merge(out, left_index=True, right_on="aoi_index")
        return gpd.GeoDataFrame(out_gdf, geometry="geometry", crs=aoi_m.crs)
    return out


def calculate_min_distance_fast(
    aoi_gdf: gpd.GeoDataFrame,
    features_gdf: gpd.GeoDataFrame,
    features_label: str,
    logger: Optional[Any] = None,
) -> gpd.GeoDataFrame:
    """
    Alternative approach using Shapely STRtree.nearest (requires Shapely 2.0+).
    Adds column f"min_dist_to_{features_label}" in meters to a copy of AOI.
    """
    aoi = _ensure_metric_crs(aoi_gdf, logger=logger).copy()
    feats = _ensure_metric_crs(features_gdf, logger=logger)

    if logger: logger.info(f"[PROX] Building STRtree for features: {features_label}")
    try:
        tree = STRtree(feats.geometry)
    except Exception as e:
        if logger:
            logger.warning(f"[PROX] STRtree failed ({e}); falling back to nearest_distance_table().")
        # Fallback to nearest_distance_table, then merge result back
        tbl = nearest_distance_table(aoi_gdf, features_gdf, label=features_label, return_geometry=False, logger=logger)
        aoi = aoi.reset_index().merge(tbl, left_index=True, right_on="aoi_index", how="left")
        aoi = gpd.GeoDataFrame(aoi, geometry="geometry", crs=aoi.crs)
        return aoi

    out_col = f"min_dist_to_{features_label}"
    dists: List[float] = []
    for idx, geom in aoi.geometry.items():
        if geom is None or geom.is_empty:
            dists.append(float("nan"))
            continue
        try:
            nearest_geom = tree.nearest(geom)
            d = geom.distance(nearest_geom)
        except Exception:
            d = feats.distance(geom).min()
        dists.append(float(d))

    aoi[out_col] = dists
    return aoi


def summarize_distance_stats(distance_df: pd.DataFrame, label: str) -> pd.DataFrame:
    """
    Create a summary DataFrame with stats of distance column min_dist_to_{label}_m.
    Returns DataFrame with columns: label, mean_m, min_m, max_m, p50_m, p95_m
    """
    col = f"min_dist_to_{label}_m"
    s = pd.to_numeric(distance_df[col], errors="coerce").dropna()

    if s.empty:
        return pd.DataFrame([{
            "label": label,
            "mean_m": None, "min_m": None, "max_m": None, "p50_m": None, "p95_m": None
        }])

    return pd.DataFrame([{
        "label": label,
        "mean_m": float(s.mean()),
        "min_m": float(s.min()),
        "max_m": float(s.max()),
        "p50_m": float(s.quantile(0.50)),
        "p95_m": float(s.quantile(0.95))
    }])


# ---------------------------
# Buffers & Overlap
# ---------------------------

def buffer_features(
    features_gdf: gpd.GeoDataFrame,
    distances_m: Iterable[int] | Iterable[float],
    dissolve: bool = False,
    logger: Optional[Any] = None,
) -> Dict[str, gpd.GeoDataFrame]:
    """
    Create one or more buffer polygons around features (in meters).
    Returns a dict { "<N>m": GeoDataFrame }.

    If dissolve=True, returns a single multipart geometry per distance (faster for overlay).
    """
    feats = _ensure_metric_crs(features_gdf, logger=logger)
    buffers: Dict[str, gpd.GeoDataFrame] = {}

    for d in distances_m:
        label = f"{int(d)}m"
        if logger: logger.debug(f"[BUFFER] Building {label} buffer")
        buf = feats.copy()
        buf["geometry"] = buf.geometry.buffer(float(d))
        if dissolve:
            # dissolve to a single geometry row
            buf = gpd.GeoDataFrame(geometry=[buf.unary_union], crs=feats.crs)
        buffers[label] = buf

    return buffers


def intersect_aoi_with_buffers(
    aoi_gdf: gpd.GeoDataFrame,
    buffers: Dict[str, gpd.GeoDataFrame],
    logger: Optional[Any] = None,
) -> pd.DataFrame:
    """
    Intersect AOI with a dict of buffers and return a tidy table:
    columns = [buffer, overlap_ha, pct_of_aoi]
    """
    aoi_metric = _ensure_metric_crs(aoi_gdf, logger=logger)
    aoi_area_ha = float(aoi_metric.geometry.area.sum() / 10_000.0)
    rows = []

    for label, buf_gdf in buffers.items():
        if buf_gdf.crs != aoi_metric.crs:
            buf_gdf = buf_gdf.to_crs(aoi_metric.crs)
        inter = gpd.overlay(aoi_metric, buf_gdf, how="intersection")
        overlap_ha = float(inter.geometry.area.sum() / 10_000.0) if not inter.empty else 0.0
        pct = (overlap_ha / aoi_area_ha * 100.0) if aoi_area_ha > 0 else 0.0
        rows.append({"buffer": label, "overlap_ha": overlap_ha, "pct_of_aoi": pct})

    return pd.DataFrame(rows).sort_values("overlap_ha", ascending=False)


# ---------------------------
# Rivers Loader (HydroRIVERS)
# ---------------------------

def load_rivers(
    hydro_path: str,
    aoi_gdf: Optional[gpd.GeoDataFrame] = None,
    logger: Optional[Any] = None
) -> gpd.GeoDataFrame:
    """
    Load HydroRIVERS shapefile and optionally clip to AOI bounding box in EPSG:3035.
    """
    if not os.path.exists(hydro_path):
        raise FileNotFoundError(f"HydroRIVERS file not found: {hydro_path}")

    rivers = gpd.read_file(hydro_path)
    if rivers.crs is None:
        # HydroRIVERS uses EPSG:4326 typically
        rivers = rivers.set_crs("EPSG:4326")

    rivers_m = rivers.to_crs(DEFAULT_METRIC_CRS)

    if aoi_gdf is not None:
        try:
            rivers_m = clip_to_aoi_bbox(rivers_m, aoi_gdf, expand_m=5000.0, logger=logger)
            if logger:
                logger.info(f"[RIVERS] Clipped HydroRIVERS to AOI bbox; features={len(rivers_m)}")
        except Exception as e:
            if logger:
                logger.warning(f"[RIVERS] AOI clipping failed: {e}. Proceeding without clip.")

    return rivers_m


# ---------------------------
# One-shot Proximity Suite
# ---------------------------

def run_proximity_suite(
    aoi_gdf: gpd.GeoDataFrame,
    features_gdf: gpd.GeoDataFrame,
    features_label: str,
    buffer_distances_m: Iterable[int] | Iterable[float] = (100, 250, 500, 1000),
    dissolve_buffers: bool = True,
    logger: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Convenience runner:
      1) nearest distance table
      2) multi-buffer generation
      3) AOI-buffer overlap summary

    Returns dict with:
      - aoi_dist_table (DataFrame)              # columns: aoi_index, min_dist_to_{label}_m
      - distance_stats (DataFrame)              # summary stats
      - buffer_overlap (DataFrame)              # tidy buffer-overlap table
      - buffers (Dict[str, GeoDataFrame])       # buffers per distance
    """
    # (1) Distance table
    dist_tbl = nearest_distance_table(aoi_gdf, features_gdf, label=features_label, return_geometry=False, logger=logger)
    stats_df = summarize_distance_stats(dist_tbl, label=features_label)

    # (2) Buffers + overlap
    buffers = buffer_features(features_gdf, buffer_distances_m, dissolve=dissolve_buffers, logger=logger)
    # For overlap, pass original AOI (geometry)—not the distance table
    overlap_tbl = intersect_aoi_with_buffers(aoi_gdf, buffers, logger=logger)

    return {
        "aoi_dist_table": dist_tbl,
        "distance_stats": stats_df,
        "buffer_overlap": overlap_tbl,
        "buffers": buffers,
    }
