# core/buffer_analysis.py
from __future__ import annotations
import os
from typing import Iterable, Dict, Any, Optional, List, Tuple

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt

from shapely.ops import nearest_points
from shapely import STRtree
from shapely.geometry import LineString
from shapely.geometry import base as shapely_base


def _ensure_metric_crs(
    gdf: gpd.GeoDataFrame,
    prefer: str = "EPSG:3035",
    fallback: str = "EPSG:3857",
    logger: Optional[Any] = None,
) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError("Input GeoDataFrame has no CRS. Please set a CRS.")
    if gdf.crs.is_geographic:
        try:
            if logger: logger.debug(f"[CRS] Reprojecting to {prefer} for metric distances.")
            return gdf.to_crs(prefer)
        except Exception:
            if logger: logger.warning(f"[CRS] Failed to project to {prefer}; falling back to {fallback}")
            return gdf.to_crs(fallback)
    return gdf


def load_vector_data(path: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        raise ValueError(f"Loaded data at {path} has no CRS; set CRS before analyzing.")
    return gdf


def _build_strtree(geoms: Iterable[shapely_base.BaseGeometry]) -> Tuple[STRtree, List[shapely_base.BaseGeometry]]:
    geom_list = [g for g in geoms if g is not None and not g.is_empty]
    if not geom_list:
        raise ValueError("No valid geometries to index in STRtree.")
    tree = STRtree(geom_list)
    return tree, geom_list


def nearest_distance_table(
    aoi_gdf: gpd.GeoDataFrame,
    features_gdf: gpd.GeoDataFrame,
    label: str,
    k: int = 1,  # for possible future extension to multiple nearest
    return_geometry: bool = True,
    chunksize: int = 5000,
    logger: Optional[Any] = None
) -> gpd.GeoDataFrame:
    """
    Compute nearest distance from each AOI geometry to the features layer using STRtree.
    If return_geometry=True, returns line segments connecting AOI to nearest feature.
    For large AOIs, process in chunks.

    Returns GeoDataFrame with columns:
      - f"dist_to_{label}_m": float
      - geometry: AOI geometry OR connecting line (if return_geometry)
    """
    aoi = _ensure_metric_crs(aoi_gdf, logger=logger).copy()
    feats = _ensure_metric_crs(features_gdf, logger=logger)

    if logger: logger.info(f"[PROX] Indexing features for nearest search: {label}")
    tree, feat_list = _build_strtree(feats.geometry)

    # Prepare output
    distances: List[float] = []
    out_geoms: List[shapely_base.BaseGeometry] = []

    aoi_indices = aoi.index.to_list()
    aoi_geoms = aoi.geometry.values

    def process_slice(geom_slice, label_inner) -> Tuple[List[float], List[shapely_base.BaseGeometry]]:
        dists_local = []
        geoms_local = []
        for geom in geom_slice:
            if geom is None or geom.is_empty:
                dists_local.append(np.nan)
                geoms_local.append(None)
                continue
            nearest_geom = tree.nearest(geom)
            d = geom.distance(nearest_geom)
            dists_local.append(float(d))
            if return_geometry:
                p1, p2 = nearest_points(geom, nearest_geom)
                geoms_local.append(LineString([p1, p2]))
            else:
                geoms_local.append(geom)
        return dists_local, geoms_local

    # Chunked processing
    for start in range(0, len(aoi_geoms), chunksize):
        end = min(start + chunksize, len(aoi_geoms))
        chunk = aoi_geoms[start:end]
        d_local, g_local = process_slice(chunk, label)
        distances.extend(d_local)
        out_geoms.extend(g_local)

    out = gpd.GeoDataFrame(
        data={f"dist_to_{label}_m": distances},
        geometry=out_geoms if return_geometry else aoi.geometry,
        crs=aoi.crs
    )
    out.index = aoi.index  # align to AOI index if useful
    return out


def summarize_distance_stats(aoi_or_table_gdf: gpd.GeoDataFrame, label: str) -> pd.DataFrame:
    col = f"dist_to_{label}_m"
    s = aoi_or_table_gdf[col].dropna()
    if s.empty:
        return pd.DataFrame([{"metric": "empty", "value": None}])
    return pd.DataFrame([
        {"metric": "mean_m", "value": float(s.mean())},
        {"metric": "min_m", "value": float(s.min())},
        {"metric": "p50_m", "value": float(s.quantile(0.50))},
        {"metric": "p95_m", "value": float(s.quantile(0.95))},
        {"metric": "max_m", "value": float(s.max())},
    ])


def buffer_features(
    features_gdf: gpd.GeoDataFrame,
    distances_m: Iterable[int] | Iterable[float],
    dissolve: bool = False,
    logger: Optional[Any] = None,
) -> Dict[str, gpd.GeoDataFrame]:
    feats = _ensure_metric_crs(features_gdf, logger=logger)
    buffers: Dict[str, gpd.GeoDataFrame] = {}
    for d in distances_m:
        label = f"{int(d)}m"
        if logger: logger.debug(f"[BUFFER] Building {label} buffer")
        buf = feats.copy()
        buf["geometry"] = buf.geometry.buffer(float(d))
        if dissolve:
            buf = gpd.GeoDataFrame(geometry=[buf.unary_union], crs=feats.crs)
        buffers[label] = buf
    return buffers


def intersect_aoi_with_buffers(
    aoi_gdf: gpd.GeoDataFrame,
    buffers: Dict[str, gpd.GeoDataFrame],
    logger: Optional[Any] = None,
) -> pd.DataFrame:
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


def load_rivers(rivers_shp: str, aoi_gdf: gpd.GeoDataFrame, logger: Optional[Any] = None) -> gpd.GeoDataFrame:
    if not os.path.exists(rivers_shp):
        raise FileNotFoundError(f"Rivers shapefile not found: {rivers_shp}")
    r = gpd.read_file(rivers_shp)
    if r.crs is None:
        raise ValueError(f"Rivers file {rivers_shp} has no CRS.")
    aoi = _ensure_metric_crs(aoi_gdf, logger=logger)
    r = r.to_crs(aoi.crs)
    bbox = aoi.total_bounds
    r = r.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
    if logger: logger.info(f"[RIVERS] Loaded rivers, clipped to AOI bounds: {len(r)} lines")
    return r


# ----------------------------
# Plot: Save Proximity Map PNG
# ----------------------------
def plot_proximity_map(
    aoi_gdf: gpd.GeoDataFrame,
    features_gdf: gpd.GeoDataFrame,
    nearest_lines_gdf: Optional[gpd.GeoDataFrame] = None,
    buffers: Optional[Dict[str, gpd.GeoDataFrame]] = None,
    outfile: str = None,
    title: str = "Proximity Map",
    logger: Optional[Any] = None
):
    """
    Plot AOI, features, optional connecting lines to nearest features,
    and optional buffers around features. Saves as PNG.
    """
    aoi = _ensure_metric_crs(aoi_gdf, logger=logger)
    feats = _ensure_metric_crs(features_gdf, logger=logger)

    fig, ax = plt.subplots(figsize=(10, 8))
    aoi.boundary.plot(ax=ax, color="black", linewidth=1.2, label="AOI")
    feats.plot(ax=ax, color="#1f77b4", linewidth=1, alpha=0.7, label="Features")

    if buffers:
        for label, buf in buffers.items():
            buf = buf.to_crs(aoi.crs) if buf.crs != aoi.crs else buf
            buf.boundary.plot(ax=ax, linestyle="--", alpha=0.5, label=f"Buffer {label}")

    if nearest_lines_gdf is not None and not nearest_lines_gdf.empty:
        nearest_lines = nearest_lines_gdf.to_crs(aoi.crs) if nearest_lines_gdf.crs != aoi.crs else nearest_lines_gdf
        nearest_lines.plot(ax=ax, color="red", linewidth=1.2, alpha=0.8, label="AOI → Nearest Feature")

    ax.set_title(title)
    ax.set_axis_off()
    ax.legend(loc="upper right")
    plt.tight_layout()

    if outfile:
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        plt.savefig(outfile, dpi=180)
        if logger: logger.info(f"[PLOT] Saved proximity map to {outfile}")
    plt.close()
