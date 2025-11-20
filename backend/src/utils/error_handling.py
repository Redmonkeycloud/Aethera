"""Enhanced error handling utilities for dataset loading and analysis."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, TypeVar

from ..logging_utils import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def safe_dataset_load(
    dataset_name: str,
    loader_func: Callable[[], T],
    default: T | None = None,
    required: bool = False,
) -> T | None:
    """
    Safely load a dataset with comprehensive error handling.

    Args:
        dataset_name: Name of the dataset for logging
        loader_func: Function that loads the dataset
        default: Default value to return on error (if not required)
        required: If True, raises exception on failure; if False, returns default

    Returns:
        Loaded dataset or default value

    Raises:
        FileNotFoundError: If dataset is required but not found
        Exception: If dataset is required and loading fails
    """
    try:
        result = loader_func()
        if result is None:
            if required:
                raise FileNotFoundError(f"Required dataset '{dataset_name}' not found")
            logger.debug("Optional dataset '%s' not available", dataset_name)
            return default
        logger.info("Successfully loaded dataset '%s'", dataset_name)
        return result
    except FileNotFoundError as exc:
        if required:
            logger.error("Required dataset '%s' not found: %s", dataset_name, exc)
            raise
        logger.debug("Optional dataset '%s' not found: %s", dataset_name, exc)
        return default
    except Exception as exc:
        if required:
            logger.error("Failed to load required dataset '%s': %s", dataset_name, exc, exc_info=True)
            raise
        logger.warning("Failed to load optional dataset '%s': %s", dataset_name, exc)
        return default


@contextmanager
def dataset_load_context(dataset_name: str, required: bool = False):
    """
    Context manager for dataset loading with automatic error handling.

    Usage:
        with dataset_load_context("CORINE", required=True) as corine_path:
            if corine_path:
                # Use dataset
                pass
    """
    dataset_path = None
    error = None

    try:
        yield dataset_path
    except FileNotFoundError as exc:
        error = exc
        if required:
            logger.error("Required dataset '%s' not found: %s", dataset_name, exc)
            raise
        logger.debug("Optional dataset '%s' not found: %s", dataset_name, exc)
    except Exception as exc:
        error = exc
        if required:
            logger.error("Failed to load required dataset '%s': %s", dataset_name, exc, exc_info=True)
            raise
        logger.warning("Failed to load optional dataset '%s': %s", dataset_name, exc)
    finally:
        if error and not required:
            logger.debug("Continuing without dataset '%s'", dataset_name)


def check_dataset_availability(
    dataset_path: Path | None,
    dataset_name: str,
    required: bool = False,
) -> bool:
    """
    Check if a dataset is available and log appropriately.

    Args:
        dataset_path: Path to the dataset file
        dataset_name: Name of the dataset for logging
        required: Whether the dataset is required

    Returns:
        True if dataset is available, False otherwise
    """
    if dataset_path is None:
        if required:
            logger.error("Required dataset '%s' not found", dataset_name)
            return False
        logger.debug("Optional dataset '%s' not available", dataset_name)
        return False

    if not dataset_path.exists():
        if required:
            logger.error("Required dataset '%s' file does not exist: %s", dataset_name, dataset_path)
            return False
        logger.debug("Optional dataset '%s' file does not exist: %s", dataset_name, dataset_path)
        return False

    if not dataset_path.is_file():
        if required:
            logger.error("Required dataset '%s' path is not a file: %s", dataset_name, dataset_path)
            return False
        logger.debug("Optional dataset '%s' path is not a file: %s", dataset_name, dataset_path)
        return False

    logger.debug("Dataset '%s' is available at %s", dataset_name, dataset_path)
    return True


def validate_dataset_format(
    dataset_path: Path,
    dataset_name: str,
    valid_extensions: list[str] | None = None,
) -> bool:
    """
    Validate that a dataset file has a valid format.

    Args:
        dataset_path: Path to the dataset file
        dataset_name: Name of the dataset for logging
        valid_extensions: List of valid file extensions (e.g., ['.gpkg', '.shp'])

    Returns:
        True if format is valid, False otherwise
    """
    if valid_extensions is None:
        valid_extensions = [".gpkg", ".shp", ".geojson", ".json"]

    extension = dataset_path.suffix.lower()
    if extension not in valid_extensions:
        logger.warning(
            "Dataset '%s' has unsupported format '%s'. Valid formats: %s",
            dataset_name,
            extension,
            valid_extensions,
        )
        return False

    return True

