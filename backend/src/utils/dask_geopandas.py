"""Dask-Geopandas integration for parallel geospatial processing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import geopandas as gpd
from geopandas import GeoDataFrame

from ..config.base_settings import settings
from ..logging_utils import get_logger
from ..observability.metrics import record_geospatial_operation
from ..observability.performance import measure_operation

logger = get_logger(__name__)

# Try to import dask-geopandas, but make it optional
try:
    import dask
    import dask_geopandas as dgpd
    from dask.distributed import Client, LocalCluster

    DASK_AVAILABLE = True
except ImportError:
    DASK_AVAILABLE = False
    dask = None  # type: ignore
    dgpd = None  # type: ignore
    Client = None  # type: ignore
    LocalCluster = None  # type: ignore


class DaskGeoPandasWrapper:
    """Wrapper for Dask-Geopandas operations."""

    def __init__(self, n_workers: int | None = None) -> None:
        """
        Initialize Dask-Geopandas wrapper.

        Args:
            n_workers: Number of Dask workers (None = auto-detect)
        """
        self.client: Client | None = None
        self.n_workers = n_workers or settings.dask_workers
        self._cluster: LocalCluster | None = None

    def __enter__(self) -> "DaskGeoPandasWrapper":
        """Context manager entry."""
        if not DASK_AVAILABLE:
            logger.warning("Dask-Geopandas not available. Install with: pip install dask-geopandas")
            return self

        if not settings.enable_dask:
            logger.debug("Dask is disabled in settings")
            return self

        try:
            # Create local cluster
            self._cluster = LocalCluster(
                n_workers=self.n_workers,
                threads_per_worker=1,  # Geopandas operations are CPU-bound
                processes=True,
                silence_logs=30,  # Reduce Dask logging noise
            )
            self.client = Client(self._cluster)
            worker_count = len(self.client.scheduler_info()["workers"])
            logger.info("Dask cluster started with %d workers", worker_count)
            record_geospatial_operation("dask_cluster_start", 0.0)  # Duration tracked separately
        except Exception as e:
            logger.warning("Failed to start Dask cluster: %s", e)
            self.client = None

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.warning("Error closing Dask client: %s", e)
        if self._cluster:
            try:
                self._cluster.close()
            except Exception as e:
                logger.warning("Error closing Dask cluster: %s", e)

    def is_available(self) -> bool:
        """Check if Dask-Geopandas is available and enabled."""
        return DASK_AVAILABLE and settings.enable_dask and self.client is not None

    def to_dask_geodataframe(
        self, gdf: GeoDataFrame, npartitions: int | None = None
    ) -> Any:
        """
        Convert GeoDataFrame to Dask-GeoDataFrame.

        Args:
            gdf: GeoDataFrame to convert
            npartitions: Number of partitions (None = auto)

        Returns:
            Dask-GeoDataFrame or original GeoDataFrame if Dask unavailable
        """
        if not self.is_available():
            logger.debug("Dask not available, returning original GeoDataFrame")
            return gdf

        try:
            if npartitions is None:
                # Auto-determine partitions based on size
                npartitions = max(1, len(gdf) // 10000)  # ~10k features per partition

            dgdf = dgpd.from_geopandas(gdf, npartitions=npartitions)
            logger.debug("Converted GeoDataFrame to Dask-GeoDataFrame with %d partitions", npartitions)
            return dgdf
        except Exception as e:
            logger.warning("Failed to convert to Dask-GeoDataFrame: %s", e)
            return gdf

    def clip_parallel(
        self,
        dataset_path: Path,
        aoi: GeoDataFrame,
        npartitions: int | None = None,
    ) -> GeoDataFrame:
        """
        Clip a vector dataset to AOI using parallel processing.

        Args:
            dataset_path: Path to the dataset file
            aoi: Area of Interest GeoDataFrame
            npartitions: Number of partitions for reading dataset

        Returns:
            Clipped GeoDataFrame
        """
        if not self.is_available():
            logger.debug("Dask not available, using standard clip")
            bbox = tuple(aoi.total_bounds.tolist())
            gdf = gpd.read_file(dataset_path, bbox=bbox)
            if gdf.empty:
                return gdf
            gdf = gdf.to_crs(aoi.crs)
            return gpd.clip(gdf, aoi)

        with measure_operation("dask_clip_parallel") as monitor:
            try:
                # Read dataset with Dask
                if npartitions is None:
                    # Estimate partitions based on file size
                    file_size_mb = dataset_path.stat().st_size / (1024 * 1024)
                    npartitions = max(1, int(file_size_mb / 100))  # ~100MB per partition

                logger.info("Reading dataset with Dask using %d partitions", npartitions)
                dgdf = dgpd.read_file(dataset_path, npartitions=npartitions)

                # Convert AOI to Dask-GeoDataFrame
                aoi_dgdf = dgpd.from_geopandas(aoi, npartitions=1)

                # Reproject if needed
                if dgdf.crs != aoi.crs:
                    dgdf = dgdf.to_crs(aoi.crs)

                # Clip using Dask
                clipped_dgdf = dgpd.clip(dgdf, aoi_dgdf)

                # Compute result
                clipped = clipped_dgdf.compute()
                logger.info("Parallel clip completed, result has %d features", len(clipped))
                monitor.record_metric("features", len(clipped))
                monitor.record_metric("partitions", npartitions)
                record_geospatial_operation("dask_clip_parallel", monitor.get_duration())
                return clipped

            except Exception as e:
                logger.warning("Dask clip failed, falling back to standard clip: %s", e)
                bbox = tuple(aoi.total_bounds.tolist())
                gdf = gpd.read_file(dataset_path, bbox=bbox)
                if gdf.empty:
                    return gdf
                gdf = gdf.to_crs(aoi.crs)
                return gpd.clip(gdf, aoi)

    def apply_parallel(
        self,
        gdf: GeoDataFrame,
        func: Callable[[GeoDataFrame], GeoDataFrame],
        npartitions: int | None = None,
    ) -> GeoDataFrame:
        """
        Apply a function to GeoDataFrame partitions in parallel.

        Args:
            gdf: GeoDataFrame to process
            func: Function to apply to each partition
            npartitions: Number of partitions

        Returns:
            Processed GeoDataFrame
        """
        if not self.is_available():
            logger.debug("Dask not available, using standard apply")
            return func(gdf)

        try:
            dgdf = self.to_dask_geodataframe(gdf, npartitions=npartitions)
            if isinstance(dgdf, GeoDataFrame):
                # Conversion failed, use standard apply
                return func(gdf)

            # Apply function to each partition
            result_dgdf = dgdf.map_partitions(func, meta=gdf.head(0))
            result = result_dgdf.compute()
            logger.debug("Parallel apply completed")
            return result

        except Exception as e:
            logger.warning("Dask apply failed, falling back to standard apply: %s", e)
            return func(gdf)


def get_dask_wrapper() -> DaskGeoPandasWrapper | None:
    """
    Get a Dask-Geopandas wrapper instance.

    Returns:
        DaskGeoPandasWrapper if available and enabled, None otherwise
    """
    if not DASK_AVAILABLE:
        return None
    if not settings.enable_dask:
        return None
    return DaskGeoPandasWrapper()

