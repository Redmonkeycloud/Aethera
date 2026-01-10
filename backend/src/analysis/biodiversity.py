"""Biodiversity preprocessing and feature engineering."""

from __future__ import annotations

from typing import Dict, Tuple, List

import geopandas as gpd

FOREST_CLASSES = {"311", "312", "313"}


def compute_overlap_metrics(
    aoi: gpd.GeoDataFrame, protected_areas: gpd.GeoDataFrame
) -> Tuple[Dict[str, float], gpd.GeoDataFrame]:
    """Return area/percentage overlap metrics and the overlapping GeoDataFrame."""
    if protected_areas.empty:
        return {
            "protected_overlap_ha": 0.0,
            "protected_overlap_pct": 0.0,
            "protected_site_count": 0,
            "fragmentation_index": 0.0,
        }, protected_areas

    overlap = gpd.overlay(protected_areas, aoi, how="intersection", keep_geom_type=True)
    if overlap.empty:
        return {
            "protected_overlap_ha": 0.0,
            "protected_overlap_pct": 0.0,
            "protected_site_count": 0,
            "fragmentation_index": 0.0,
        }, overlap

    # NOTE: Protected areas may overlap each other; summing polygon areas can exceed AOI area.
    # Use a unioned area estimate and cap overlap_pct to [0, 100].
    try:
        overlap_area = overlap.geometry.union_all().area  # shapely >= 2
    except Exception:
        overlap_area = overlap.unary_union.area
    aoi_area = aoi.geometry.area.sum()

    overlap_ha = overlap_area / 10_000
    aoi_ha = aoi_area / 10_000 if aoi_area > 0 else 1
    overlap_pct = min(100.0, (overlap_ha / aoi_ha) * 100)

    # Fragmentation: normalize by a reasonable max number of sites (heuristic).
    # The previous implementation effectively saturated to 1.0 for any overlap when AOI is a single polygon.
    site_count = overlap.shape[0]
    if site_count:
        fragmentation_index = min(1.0, site_count / 20.0)
    else:
        fragmentation_index = 0.0

    return {
        "protected_overlap_ha": overlap_ha,
        "protected_overlap_pct": overlap_pct,
        "protected_site_count": site_count,
        "fragmentation_index": fragmentation_index,
    }, overlap


def forest_ratio(land_cover_summary: List[Dict]) -> float:
    total_area = sum(float(row.get("total_area_ha", 0)) for row in land_cover_summary)
    if total_area <= 0:
        return 0.0
    forest_area = sum(
        float(row.get("total_area_ha", 0))
        for row in land_cover_summary
        if str(row.get("class_code")) in FOREST_CLASSES
    )
    return forest_area / total_area


def build_biodiversity_features(
    aoi: gpd.GeoDataFrame,
    land_cover_summary: List[Dict],
    overlap_metrics: Dict[str, float],
) -> Dict[str, float]:
    aoi_area_ha = aoi.geometry.area.sum() / 10_000
    features = {
        "aoi_area_ha": aoi_area_ha,
        "protected_overlap_ha": overlap_metrics["protected_overlap_ha"],
        "protected_overlap_pct": overlap_metrics["protected_overlap_pct"],
        "protected_site_count": overlap_metrics["protected_site_count"],
        "fragmentation_index": overlap_metrics["fragmentation_index"],
        "forest_ratio": forest_ratio(land_cover_summary),
    }
    return features

