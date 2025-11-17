"""Geometry helpers for AOI loading, validation, and buffering."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import geopandas as gpd
from shapely import wkt


def _load_vector(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(f"AOI file not found: {path}")
    gdf = gpd.read_file(path)
    if gdf.empty:
        raise ValueError(f"AOI file {path} contains no features.")
    if gdf.crs is None:
        raise ValueError(f"AOI file {path} has no CRS defined.")
    return gdf


def _load_wkt(text: str) -> gpd.GeoDataFrame:
    geometry = wkt.loads(text)
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[geometry], crs="EPSG:4326")
    return gdf


def load_aoi(aoi_input: str, target_crs: str) -> gpd.GeoDataFrame:
    path = Path(aoi_input)
    if path.exists():
        gdf = _load_vector(path)
    else:
        gdf = _load_wkt(aoi_input)

    gdf = gdf.explode(index_parts=False).reset_index(drop=True)
    gdf = gdf.to_crs(target_crs)
    gdf["geometry"] = gdf.geometry.buffer(0)
    gdf = gdf[gdf.is_valid]
    if gdf.empty:
        raise ValueError("AOI geometries are invalid or empty after cleaning.")
    gdf["geometry"] = gdf.geometry.apply(lambda geom: geom if geom.area > 0 else None)
    gdf = gdf.dropna(subset=["geometry"])
    if gdf.empty:
        raise ValueError("AOI geometries have zero area.")
    return gdf


def buffer_aoi(aoi: gpd.GeoDataFrame, buffer_km: float) -> gpd.GeoDataFrame:
    if buffer_km <= 0:
        return aoi
    buffered = aoi.copy()
    buffered["geometry"] = buffered.geometry.buffer(buffer_km * 1000)
    return buffered


def dissolve_geometries(geoms: Iterable) -> gpd.GeoDataFrame:
    gdf = gpd.GeoDataFrame(geometry=list(geoms), crs="EPSG:4326")
    dissolved = gdf.dissolve().reset_index(drop=True)
    return dissolved


def save_geojson(gdf: gpd.GeoDataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, driver="GeoJSON")

