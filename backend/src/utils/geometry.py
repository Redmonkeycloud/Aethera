"""Geometry helpers for AOI loading, validation, and buffering."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import geopandas as gpd
from shapely import wkt
from shapely.geometry import (
    GeometryCollection,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from ..logging_utils import get_logger


logger = get_logger(__name__)


def _load_vector(path: Path) -> gpd.GeoDataFrame:
    """Load a vector file (GeoJSON, Shapefile, GeoPackage, etc.)."""
    if not path.exists():
        raise FileNotFoundError(f"AOI file not found: {path}")
    gdf = gpd.read_file(path)
    if gdf.empty:
        raise ValueError(f"AOI file {path} contains no features.")
    if gdf.crs is None:
        raise ValueError(f"AOI file {path} has no CRS defined.")
    return gdf


def _load_wkt_string(text: str) -> gpd.GeoDataFrame:
    """
    Load WKT (Well-Known Text) string into a GeoDataFrame.

    Supports:
    - Single geometries: POINT, LINESTRING, POLYGON
    - Multi geometries: MULTIPOINT, MULTILINESTRING, MULTIPOLYGON
    - Geometry collections: GEOMETRYCOLLECTION

    Args:
        text: WKT string

    Returns:
        GeoDataFrame with geometries
    """
    try:
        geometry = wkt.loads(text.strip())
    except Exception as e:
        raise ValueError(f"Invalid WKT format: {e}") from e

    if geometry is None:
        raise ValueError("WKT string resulted in None geometry")

    # Handle different geometry types
    geometries = []
    ids = []

    if isinstance(geometry, GeometryCollection):
        # Extract all geometries from collection
        for idx, geom in enumerate(geometry.geoms):
            if geom is not None and not geom.is_empty:
                geometries.append(geom)
                ids.append(idx)
    elif isinstance(
        geometry, (MultiPoint, MultiLineString, MultiPolygon)
    ):
        # Extract individual geometries from multi-geometry
        for idx, geom in enumerate(geometry.geoms):
            if geom is not None and not geom.is_empty:
                geometries.append(geom)
                ids.append(idx)
    elif isinstance(geometry, (Point, Polygon)) or hasattr(geometry, "geom_type"):
        # Single geometry
        if not geometry.is_empty:
            geometries.append(geometry)
            ids.append(0)
    else:
        raise ValueError(f"Unsupported geometry type: {type(geometry)}")

    if not geometries:
        raise ValueError("WKT string contains no valid geometries")

    gdf = gpd.GeoDataFrame({"id": ids}, geometry=geometries, crs="EPSG:4326")
    logger.info("Loaded %d geometry(ies) from WKT string", len(gdf))
    return gdf


def _load_wkt_file(path: Path) -> gpd.GeoDataFrame:
    """
    Load WKT from a file.

    Supports:
    - Single WKT string per line
    - Multiple geometries (one per line)

    Args:
        path: Path to WKT file

    Returns:
        GeoDataFrame with geometries
    """
    if not path.exists():
        raise FileNotFoundError(f"WKT file not found: {path}")

    geometries = []
    ids = []

    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                geom = wkt.loads(line)
                if geom is not None and not geom.is_empty:
                    geometries.append(geom)
                    ids.append(line_num)
            except Exception as e:
                logger.warning(
                    "Skipping invalid WKT on line %d: %s", line_num, e
                )
                continue

    if not geometries:
        raise ValueError(f"WKT file {path} contains no valid geometries")

    gdf = gpd.GeoDataFrame({"id": ids}, geometry=geometries, crs="EPSG:4326")
    logger.info("Loaded %d geometry(ies) from WKT file %s", len(gdf), path.name)
    return gdf


def _is_wkt_string(text: str) -> bool:
    """Check if a string looks like WKT."""
    text = text.strip().upper()
    wkt_types = [
        "POINT",
        "LINESTRING",
        "POLYGON",
        "MULTIPOINT",
        "MULTILINESTRING",
        "MULTIPOLYGON",
        "GEOMETRYCOLLECTION",
    ]
    return any(text.startswith(wkt_type) for wkt_type in wkt_types)


def load_aoi(aoi_input: str, target_crs: str) -> gpd.GeoDataFrame:
    """
    Load an AOI from various input formats.

    Supports:
    - Vector files: GeoJSON, Shapefile, GeoPackage, etc.
    - WKT strings: Direct WKT text
    - WKT files: Files containing WKT (.wkt, .txt with WKT content)

    Args:
        aoi_input: Path to file or WKT string
        target_crs: Target CRS for the output (e.g., "EPSG:3035")

    Returns:
        GeoDataFrame in target CRS
    """
    path = Path(aoi_input)

    # Check if it's a file path
    if path.exists():
        # Check if it's a WKT file
        if path.suffix.lower() in (".wkt", ".txt"):
            # Try to read as WKT file
            try:
                gdf = _load_wkt_file(path)
            except Exception:
                # Fall back to regular vector file loading
                gdf = _load_vector(path)
        else:
            # Regular vector file
            gdf = _load_vector(path)
    elif _is_wkt_string(aoi_input):
        # WKT string
        gdf = _load_wkt_string(aoi_input)
    else:
        # Try as file path that doesn't exist, or invalid input
        raise FileNotFoundError(
            f"AOI input not found as file and doesn't appear to be WKT: {aoi_input}"
        )

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

