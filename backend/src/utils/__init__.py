"""Utility modules for AETHERA."""

from .dataset_checker import DatasetAvailabilityChecker, DatasetAvailabilityReport
from .error_handling import (
    check_dataset_availability,
    dataset_load_context,
    safe_dataset_load,
    validate_dataset_format,
)
from .geometry import buffer_aoi, dissolve_geometries, load_aoi, save_geojson
from .tiling import create_tiles, process_tiles, should_tile

__all__ = [
    "load_aoi",
    "buffer_aoi",
    "dissolve_geometries",
    "save_geojson",
    "create_tiles",
    "process_tiles",
    "should_tile",
    "DatasetAvailabilityChecker",
    "DatasetAvailabilityReport",
    "check_dataset_availability",
    "dataset_load_context",
    "safe_dataset_load",
    "validate_dataset_format",
]

