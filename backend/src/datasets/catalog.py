"""Dataset discovery utilities."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd

from ..config.base_settings import settings
from ..logging_utils import get_logger
from .cache import DatasetCache


logger = get_logger(__name__)


@dataclass
class DatasetCatalog:
    """Catalog for discovering and loading geospatial datasets with caching."""

    base_dir: Path
    cache: DatasetCache | None = None

    def __post_init__(self) -> None:
        """Initialize cache if enabled."""
        if settings.dataset_cache_enabled:
            cache_dir = (
                settings.dataset_cache_dir
                if settings.dataset_cache_dir.is_absolute()
                else Path(__file__).resolve().parents[3] / settings.dataset_cache_dir
            )
            self.cache = DatasetCache(
                max_memory_size_mb=settings.dataset_cache_max_mb,
                cache_dir=cache_dir,
                ttl_hours=settings.dataset_cache_ttl_hours,
            )
            logger.info("Dataset cache enabled (max: %d MB)", settings.dataset_cache_max_mb)
        else:
            logger.debug("Dataset cache disabled")

    def _search(self, relative: str, patterns: Iterable[str]) -> Path | None:
        root = self.base_dir / relative
        if not root.exists():
            return None
        for pattern in patterns:
            matches = sorted(root.rglob(pattern))
            if matches:
                return matches[0]
        return None

    def corine(self) -> Path:
        path = self._search("corine", ["*.gpkg", "*.shp"])
        if not path:
            raise FileNotFoundError("No CORINE dataset found under data source directory.")
        return path

    def natura2000(self) -> Path | None:
        return self._search("protected_areas/natura2000", ["*.gpkg", "*.shp"])

    def gadm(self, level: int = 2) -> Path | None:
        pattern = f"*_{level}.shp"
        return self._search("gadm", [pattern])

    def eurostat_nuts(self) -> Path | None:
        return self._search("eurostat", ["*.shp", "*.gpkg"])

    def natural_earth_admin(self) -> Path | None:
        return self._search(
            "natural_earth", ["ne_10m_admin_0_countries.*", "*.shp", "*.gpkg"]
        )

    def biodiversity_training(self) -> Path | None:
        """
        Find biodiversity training dataset.
        
        Searches in order:
        1. Main training files (training.parquet, training.csv) in biodiversity/ root
        2. Any parquet/csv files in biodiversity/ root
        3. External datasets in biodiversity/external/ (owid, gbif, etc.)
        """
        # First try main training files
        main_training = self._search(
            "biodiversity", ["training.parquet", "training.csv"]
        )
        if main_training:
            return main_training
        
        # Then try any parquet/csv in root
        any_training = self._search(
            "biodiversity", ["*.parquet", "*.csv"]
        )
        if any_training:
            return any_training
        
        # Finally try external datasets (prefer parquet, then csv)
        external_training = self._search(
            "biodiversity/external", ["*.parquet", "*.csv"]
        )
        return external_training

    def rivers(self) -> Path | None:
        """Find HydroRIVERS dataset (prefer EU subset if available)."""
        # Try EU subset first (smaller, faster)
        eu_path = self._search("rivers/HydroRIVERS_v10_eu_shp", ["*.shp"])
        if eu_path:
            return eu_path
        # Fall back to global dataset
        return self._search("rivers/HydroRIVERS_v10_shp", ["*.shp"])

    def wdpa(self) -> Path | None:
        """Find WDPA (World Database on Protected Areas) dataset."""
        return self._search("protected_areas/wdpa", ["*.gpkg", "*.shp"])

    def roads(self) -> Path | None:
        """
        Find roads dataset.
        
        Note: OSM PBF files require conversion to GeoJSON/Shapefile first.
        This method looks for already-converted files (GeoJSON, Shapefile, GPKG).
        For OSM PBF files, use external tools (osmium-tool, pyosmium) to convert first.
        """
        # Look for converted formats first (preferred)
        converted = self._search("roads", ["*.gpkg", "*.geojson", "*.shp"])
        if converted:
            return converted
        # Note: OSM PBF files (.osm.pbf) are not directly readable by GeoPandas
        # They need to be converted using tools like osmium-tool or pyosmium
        return None

    def load_dataset(
        self,
        dataset_name: str,
        bbox: tuple[float, float, float, float] | None = None,
        **kwargs: Any,
    ) -> gpd.GeoDataFrame:
        """
        Load a dataset with optional caching and bounding box filtering.

        Args:
            dataset_name: Name of the dataset method (e.g., 'corine', 'natura2000')
            bbox: Optional bounding box (minx, miny, maxx, maxy) for spatial filtering
            **kwargs: Additional arguments for dataset loading

        Returns:
            Loaded GeoDataFrame
        """
        # Get the dataset path
        method = getattr(self, dataset_name, None)
        if not method or not callable(method):
            raise ValueError(f"Unknown dataset: {dataset_name}")

        path = method(**kwargs)
        if path is None:
            raise FileNotFoundError(f"Dataset {dataset_name} not found")

        # Define loader function
        def loader(file_path: Path, **load_kwargs: Any) -> gpd.GeoDataFrame:
            if bbox:
                return gpd.read_file(file_path, bbox=bbox)
            return gpd.read_file(file_path, **load_kwargs)

        # Use cache if available
        if self.cache:
            return self.cache.get(path, loader, **kwargs)

        # Direct load without cache
        return loader(path, **kwargs)

    def get_cache_stats(self) -> dict[str, Any] | None:
        """Get cache statistics if caching is enabled."""
        if self.cache:
            return self.cache.get_stats()
        return None

    def clear_cache(self, memory_only: bool = False) -> None:
        """Clear the dataset cache."""
        if self.cache:
            self.cache.clear(memory_only=memory_only)
            logger.info("Dataset cache cleared")
        else:
            logger.warning("Cache not enabled, nothing to clear")

