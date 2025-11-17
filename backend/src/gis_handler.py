"""Geospatial processing utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import geopandas as gpd
from geopandas import GeoDataFrame

from .logging_utils import get_logger


logger = get_logger(__name__)


class GISHandler:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def clip_vector(self, dataset_path: Path, aoi: GeoDataFrame, output_name: str) -> GeoDataFrame:
        logger.info("Clipping dataset %s", dataset_path)
        bbox = tuple(aoi.total_bounds.tolist())
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

    def save_vector(self, gdf: GeoDataFrame, output_name: str, driver: Optional[str] = None) -> Optional[Path]:
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
        import json

        output_path = self.output_dir / file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info("Summary file written to %s", output_path)
        return output_path

