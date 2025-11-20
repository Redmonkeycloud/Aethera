"""Tiling and chunking utilities for large AOIs."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import geopandas as gpd
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import box

from ..config.base_settings import settings
from ..logging_utils import get_logger
from ..observability.metrics import record_geospatial_operation
from ..observability.performance import measure_operation

logger = get_logger(__name__)


def create_tiles(
    aoi: GeoDataFrame,
    tile_size_km: float | None = None,
    overlap_km: float = 0.0,
) -> Generator[GeoDataFrame, None, None]:
    """
    Create tiles from an AOI for chunked processing.

    Args:
        aoi: Area of Interest GeoDataFrame
        tile_size_km: Size of each tile in kilometers (defaults to settings.tile_size_km)
        overlap_km: Overlap between tiles in kilometers (to avoid edge effects)

    Yields:
        GeoDataFrame tiles that intersect with the AOI
    """
    with measure_operation("create_tiles") as monitor:
        if tile_size_km is None:
            tile_size_km = settings.tile_size_km

        # Get AOI bounds
        bounds = aoi.total_bounds
        minx, miny, maxx, maxy = bounds

    # Convert tile size from km to meters (assuming CRS is in meters)
    # For EPSG:3035 (ETRS89), 1 degree ≈ 111 km, but we'll use the CRS units
    # Most projected CRS use meters, so we'll assume meters
    tile_size_m = tile_size_km * 1000
    overlap_m = overlap_km * 1000

    # Calculate number of tiles
    width = maxx - minx
    height = maxy - miny
    n_tiles_x = int(np.ceil(width / tile_size_m)) + 1
    n_tiles_y = int(np.ceil(height / tile_size_m)) + 1

    logger.info(
        "Creating %d x %d tiles (total: %d) for AOI of size %.2f km²",
        n_tiles_x,
        n_tiles_y,
        n_tiles_x * n_tiles_y,
        (width * height) / 1_000_000,  # Convert m² to km²
    )

    tile_count = 0
    for i in range(n_tiles_x):
        for j in range(n_tiles_y):
            # Calculate tile bounds with overlap
            tile_minx = minx + (i * tile_size_m) - overlap_m
            tile_miny = miny + (j * tile_size_m) - overlap_m
            tile_maxx = minx + ((i + 1) * tile_size_m) + overlap_m
            tile_maxy = miny + ((j + 1) * tile_size_m) + overlap_m

            # Create tile geometry
            tile_geom = box(tile_minx, tile_miny, tile_maxx, tile_maxy)
            tile_gdf = gpd.GeoDataFrame(geometry=[tile_geom], crs=aoi.crs)

            # Clip AOI to tile
            clipped = gpd.clip(aoi, tile_gdf)
            if not clipped.empty:
                tile_count += 1
                clipped["tile_id"] = f"{i}_{j}"
                clipped["tile_x"] = i
                clipped["tile_y"] = j
                yield clipped

        logger.info("Generated %d non-empty tiles", tile_count)
        monitor.record_metric("tiles_generated", tile_count)
        monitor.record_metric("tile_size_km", tile_size_km)
        record_geospatial_operation("create_tiles", monitor.get_duration())


def should_tile(aoi: GeoDataFrame) -> bool:
    """
    Determine if an AOI should be tiled based on size threshold.

    Args:
        aoi: Area of Interest GeoDataFrame

    Returns:
        True if AOI should be tiled, False otherwise
    """
    if not settings.enable_tiling:
        return False

    # Calculate AOI area in km²
    area_m2 = aoi.geometry.area.sum()
    area_km2 = area_m2 / 1_000_000

    threshold = settings.aoi_size_threshold_km2
    should = area_km2 > threshold

    if should:
        logger.info(
            "AOI size (%.2f km²) exceeds threshold (%.2f km²), tiling enabled",
            area_km2,
            threshold,
        )
    else:
        logger.debug(
            "AOI size (%.2f km²) below threshold (%.2f km²), tiling not needed",
            area_km2,
            threshold,
        )

    return should


def process_tiles(
    aoi: GeoDataFrame,
    process_func: callable,
    tile_size_km: float | None = None,
    overlap_km: float = 0.0,
    merge_results: bool = True,
    **kwargs,
) -> GeoDataFrame | list[GeoDataFrame]:
    """
    Process an AOI in tiles and optionally merge results.

    Args:
        aoi: Area of Interest GeoDataFrame
        process_func: Function to process each tile (takes tile_gdf, **kwargs, returns GeoDataFrame)
        tile_size_km: Size of each tile in kilometers
        overlap_km: Overlap between tiles in kilometers
        merge_results: If True, merge all tile results into single GeoDataFrame
        **kwargs: Additional arguments to pass to process_func

    Returns:
        Merged GeoDataFrame if merge_results=True, otherwise list of tile results
    """
    tiles = list(create_tiles(aoi, tile_size_km, overlap_km))
    if not tiles:
        logger.warning("No tiles generated from AOI")
        return gpd.GeoDataFrame(geometry=[], crs=aoi.crs) if merge_results else []

    logger.info("Processing %d tiles", len(tiles))
    results = []

    for idx, tile in enumerate(tiles):
        logger.debug("Processing tile %d/%d (tile_id: %s)", idx + 1, len(tiles), tile["tile_id"].iloc[0] if not tile.empty else "unknown")
        try:
            result = process_func(tile, **kwargs)
            if not result.empty:
                # Preserve tile metadata if present
                if "tile_id" in tile.columns:
                    result["tile_id"] = tile["tile_id"].iloc[0]
                results.append(result)
        except Exception as e:
            logger.error("Error processing tile %d: %s", idx, e, exc_info=True)
            continue

    if not results:
        logger.warning("No results from tile processing")
        return gpd.GeoDataFrame(geometry=[], crs=aoi.crs) if merge_results else []

    if merge_results:
        # Merge all tile results
        merged = gpd.GeoDataFrame(pd.concat(results, ignore_index=True))
        # Remove duplicates that may occur due to overlap
        if "tile_id" in merged.columns:
            # For overlapping tiles, keep only one copy
            merged = merged.drop_duplicates(subset=["geometry"], keep="first")
        logger.info("Merged %d tile results into single GeoDataFrame", len(results))
        return merged

    return results


def clip_vector_tiled(
    dataset_path: Path,
    aoi: GeoDataFrame,
    tile_size_km: float | None = None,
    overlap_km: float = 1.0,
) -> GeoDataFrame:
    """
    Clip a vector dataset to an AOI using tiling for large datasets.

    Args:
        dataset_path: Path to the dataset file
        aoi: Area of Interest GeoDataFrame
        tile_size_km: Size of each tile in kilometers
        overlap_km: Overlap between tiles in kilometers

    Returns:
        Clipped GeoDataFrame
    """
    def process_tile(tile_gdf: GeoDataFrame) -> GeoDataFrame:
        """Process a single tile."""
        bbox = tuple(tile_gdf.total_bounds.tolist())
        gdf = gpd.read_file(dataset_path, bbox=bbox)
        if gdf.empty:
            return gdf
        gdf = gdf.to_crs(aoi.crs)
        clipped = gpd.clip(gdf, tile_gdf)
        return clipped

    return process_tiles(
        aoi,
        process_tile,
        tile_size_km=tile_size_km,
        overlap_km=overlap_km,
        merge_results=True,
    )

