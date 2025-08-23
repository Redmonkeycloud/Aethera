# core/buffer_analysis.py

import os
import pandas as pd
import geopandas as gpd
from shapely import STRtree
from __future__ import annotations
from shapely.geometry import base as shapely_base
from typing import Iterable, Dict, Any, Optional, List, Tuple

# ---------------------------
# Helpers
# ---------------------------

def _ensure_metric_crs(
    gdf: gpd.GeoDataFrame,
    prefer: str = "EPSG:3035",
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

    # Already projected; keep as‑is
    return gdf

def load_vector_data(path: str) -> gpd.GeoDataFrame:
    """Load shapefile/GeoJSON/GPKG/etc. as GeoDataFrame (CRS must be present)."""
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        raise ValueError(f"Loaded data at {path} has no CRS; set it before running analysis.")
    return gdf

def _build_strtree(geoms: Iterable[shapely_base.BaseGeometry]) -> Tuple[STRtree, List[shapely_base.BaseGeometry]]:
    """
    Build an STRtree from an iterable of geometries and return (tree, geom_list).
    Keep a list reference so indices returned by tree map to original geometries.
    """
    geom_list = [g for g in geoms if g is not None]
    if not geom_list:
        raise ValueError("No valid geometries to index in STRtree.")
    tree = STRtree(geom_list)
    return tree, geom_list

# ---------------------------
# Core proximity functions
# ---------------------------

def calculate_min_distance_fast(
    aoi_gdf: gpd.GeoDataFrame,
    features_gdf: gpd.GeoDataFrame,
    features_label: str,
    logger: Optional[Any] = None,
) -> gpd.GeoDataFrame:
    """
    Compute minimum distance from each AOI geometry to the nearest feature geometry
    using Shapely 2.0 STRtree.nearest (fast, memory‑friendly).

    Returns a copy of AOI with a new column: f"min_dist_to_{features_label}" (meters).
    """
    aoi = _ensure_metric_crs(aoi_gdf, logger=logger).copy()
    feats = _ensure_metric_crs(features_gdf, logger=logger)

    if logger: logger.info(f"[PROX] Building spatial index for features: {features_label}")
    tree, feat_list = _build_strtree(feats.geometry)

    out_col = f"min_dist_to_{features_label}"
    dists: List[float] = []

    for idx, geom in aoi.geometry.items():
        if geom is None or geom.is_empty:
            dists.append(float("nan"))
            continue
        try:
            nearest_geom = tree.nearest(geom)  # returns a shapely geometry
            d = geom.distance(nearest_geom)
        except Exception:
            # Fallback: if something odd happens, compute dense distance (slower)
            d = feats.distance(geom).min()
        dists.append(float(d))

    aoi[out_col] = dists
    return aoi

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

def summarize_distance_stats(aoi_with_dist: gpd.GeoDataFrame, features_label: str) -> Dict[str, float]:
    """
    Summary statistics over distance column for AOI.
    Returns mean/min/max and p50/p95 (meters).
    """
    col = f"min_dist_to_{features_label}"
    s = aoi_with_dist[col].dropna()
    if s.empty:
        return {"mean_m": None, "min_m": None, "p50_m": None, "p95_m": None, "max_m": None}
    return {
        "mean_m": float(s.mean()),
        "min_m": float(s.min()),
        "p50_m": float(s.quantile(0.50)),
        "p95_m": float(s.quantile(0.95)),
        "max_m": float(s.max()),
    }

def intersect_aoi_with_buffers(
    aoi_gdf: gpd.GeoDataFrame,
    buffers: Dict[str, gpd.GeoDataFrame],
    logger: Optional[Any] = None,
) -> pd.DataFrame:
    """
    Intersect AOI with a dict of buffers and return a tidy table:
    columns = [buffer_label, overlap_ha, pct_of_aoi]
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
# Optional “one‑shot” runner
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
    Convenience wrapper:
      1) min distance per AOI
      2) multi-buffer generation + AOI overlap summary
    Returns dict with:
      - aoi_with_dist (GeoDataFrame)
      - buffer_overlap (DataFrame)
      - buffers (Dict[str, GeoDataFrame])
      - distance_stats (Dict)
    """
    # 1) distances
    aoi_with_dist = calculate_min_distance_fast(aoi_gdf, features_gdf, features_label, logger=logger)
    stats = summarize_distance_stats(aoi_with_dist, features_label)

    # 2) buffers + overlap
    buffers = buffer_features(features_gdf, buffer_distances_m, dissolve=dissolve_buffers, logger=logger)
    overlap_tbl = intersect_aoi_with_buffers(aoi_with_dist, buffers, logger=logger)

    return {
        "aoi_with_dist": aoi_with_dist,
        "buffer_overlap": overlap_tbl,
        "buffers": buffers,
        "distance_stats": stats,
    }
