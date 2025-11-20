"""Geospatial processing utilities."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
from geopandas import GeoDataFrame

from ..config.base_settings import settings
from ..utils.dask_geopandas import get_dask_wrapper
from ..utils.tiling import clip_vector_tiled, should_tile
from .logging_utils import get_logger


logger = get_logger(__name__)


class GISHandler:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def clip_vector(
        self,
        dataset_path: Path,
        aoi: GeoDataFrame,
        output_name: str,
        use_cache: bool = True,
    ) -> GeoDataFrame:
        """
        Clip a vector dataset to the AOI.

        Uses tiling for large AOIs and Dask-Geopandas for parallel processing if enabled.

        Args:
            dataset_path: Path to the dataset file
            aoi: Area of interest GeoDataFrame
            output_name: Name for the output file
            use_cache: Whether to use dataset cache if available

        Returns:
            Clipped GeoDataFrame
        """
        logger.info("Clipping dataset %s", dataset_path)

        # Check if we should use tiling
        use_tiling = should_tile(aoi)

        # Try Dask-Geopandas first if enabled
        dask_wrapper = get_dask_wrapper()
        if dask_wrapper and not use_tiling:
            try:
                with dask_wrapper:
                    clipped = dask_wrapper.clip_parallel(dataset_path, aoi)
                    if not clipped.empty:
                        output_path = self.output_dir / output_name
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        clipped.to_file(output_path)
                        logger.info("Saved clipped dataset (Dask) to %s", output_path)
                        return clipped
            except Exception as e:
                logger.warning("Dask clip failed, falling back to standard clip: %s", e)

        # Use tiling for large AOIs
        if use_tiling:
            try:
                clipped = clip_vector_tiled(dataset_path, aoi)
                if not clipped.empty:
                    output_path = self.output_dir / output_name
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    clipped.to_file(output_path)
                    logger.info("Saved clipped dataset (tiled) to %s", output_path)
                    return clipped
            except Exception as e:
                logger.warning("Tiled clip failed, falling back to standard clip: %s", e)

        # Standard clipping approach
        bbox = tuple(aoi.total_bounds.tolist())

        # Try to use cache if available and enabled
        if use_cache:
            from ..datasets.catalog import DatasetCatalog

            catalog = DatasetCatalog(settings.data_sources_dir)
            if catalog.cache:
                try:
                    # Generate a cache key that includes bbox
                    gdf = catalog.cache.get(
                        dataset_path,
                        lambda p, **kw: gpd.read_file(p, bbox=bbox),
                        bbox=bbox,
                    )
                except Exception as exc:
                    logger.warning("Cache load failed, falling back to direct read: %s", exc)
                    gdf = gpd.read_file(dataset_path, bbox=bbox)
            else:
                gdf = gpd.read_file(dataset_path, bbox=bbox)
        else:
            gdf = gpd.read_file(dataset_path, bbox=bbox)
        if gdf.empty:
            logger.warning("Dataset %s returned no features within AOI bbox.", dataset_path)
            return gdf
        gdf = gdf.to_crs(aoi.crs)
        clipped = gpd.clip(gdf, aoi)
        if clipped.empty:
            logger.warning("No intersection found between AOI and %s.", dataset_path)
            return clipped
        output_path = self.output_dir / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        clipped.to_file(output_path)
        logger.info("Saved clipped dataset to %s", output_path)
        return clipped

    def save_vector(
        self, gdf: GeoDataFrame, output_name: str, driver: str | None = None
    ) -> Path | None:
        if gdf.empty:
            logger.warning("Requested to save %s but GeoDataFrame is empty.", output_name)
            return None
        output_path = self.output_dir / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if driver:
            gdf.to_file(output_path, driver=driver)
        else:
            gdf.to_file(output_path)
        logger.info("Vector layer written to %s", output_path)
        return output_path

    def save_summary(self, data: list[dict], file_name: str) -> Path:
        output_path = self.output_dir / file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info("Summary file written to %s", output_path)
        return output_path

