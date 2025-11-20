"""Dataset availability checker for pre-analysis validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..datasets.catalog import DatasetCatalog
from ..logging_utils import get_logger
from .error_handling import check_dataset_availability, validate_dataset_format

logger = get_logger(__name__)


@dataclass
class DatasetAvailability:
    """Dataset availability status."""

    name: str
    available: bool
    path: Path | None = None
    required: bool = False
    error: str | None = None


@dataclass
class DatasetAvailabilityReport:
    """Report of dataset availability for analysis."""

    required_datasets: list[DatasetAvailability]
    optional_datasets: list[DatasetAvailability]
    all_available: bool
    missing_required: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "all_required_available": self.all_available,
            "missing_required": self.missing_required,
            "required_datasets": [
                {
                    "name": ds.name,
                    "available": ds.available,
                    "path": str(ds.path) if ds.path else None,
                    "error": ds.error,
                }
                for ds in self.required_datasets
            ],
            "optional_datasets": [
                {
                    "name": ds.name,
                    "available": ds.available,
                    "path": str(ds.path) if ds.path else None,
                    "error": ds.error,
                }
                for ds in self.optional_datasets
            ],
        }


class DatasetAvailabilityChecker:
    """Check dataset availability before running analysis."""

    def __init__(self, catalog: DatasetCatalog) -> None:
        """
        Initialize checker with dataset catalog.

        Args:
            catalog: DatasetCatalog instance
        """
        self.catalog = catalog

    def check_all(self) -> DatasetAvailabilityReport:
        """
        Check availability of all datasets.

        Returns:
            DatasetAvailabilityReport with status of all datasets
        """
        required: list[DatasetAvailability] = []
        optional: list[DatasetAvailability] = []

        # Required datasets
        required.append(self._check_dataset("CORINE", self.catalog.corine, required=True))

        # Optional datasets
        optional.append(self._check_dataset("Natura 2000", self.catalog.natura2000, required=False))
        optional.append(self._check_dataset("WDPA", self.catalog.wdpa, required=False))
        optional.append(self._check_dataset("Rivers", self.catalog.rivers, required=False))
        optional.append(self._check_dataset("Roads", self.catalog.roads, required=False))
        optional.append(self._check_dataset("GADM Level 0", lambda: self.catalog.gadm(level=0), required=False))
        optional.append(self._check_dataset("GADM Level 1", lambda: self.catalog.gadm(level=1), required=False))
        optional.append(self._check_dataset("Eurostat NUTS", self.catalog.eurostat_nuts, required=False))
        optional.append(
            self._check_dataset("Natural Earth", self.catalog.natural_earth_admin, required=False)
        )
        optional.append(
            self._check_dataset("Biodiversity Training", self.catalog.biodiversity_training, required=False)
        )

        missing_required = [ds.name for ds in required if not ds.available]
        all_available = len(missing_required) == 0

        return DatasetAvailabilityReport(
            required_datasets=required,
            optional_datasets=optional,
            all_available=all_available,
            missing_required=missing_required,
        )

    def _check_dataset(
        self,
        name: str,
        loader_func: callable,
        required: bool = False,
    ) -> DatasetAvailability:
        """
        Check availability of a single dataset.

        Args:
            name: Dataset name
            loader_func: Function that returns dataset path
            required: Whether dataset is required

        Returns:
            DatasetAvailability status
        """
        try:
            path = loader_func()
            if path is None:
                return DatasetAvailability(
                    name=name,
                    available=False,
                    path=None,
                    required=required,
                    error="Dataset not found in catalog",
                )

            if not check_dataset_availability(path, name, required=required):
                return DatasetAvailability(
                    name=name,
                    available=False,
                    path=path,
                    required=required,
                    error="Dataset file does not exist or is not accessible",
                )

            if not validate_dataset_format(path, name):
                return DatasetAvailability(
                    name=name,
                    available=False,
                    path=path,
                    required=required,
                    error="Dataset format is not supported",
                )

            return DatasetAvailability(
                name=name,
                available=True,
                path=path,
                required=required,
            )

        except FileNotFoundError as exc:
            return DatasetAvailability(
                name=name,
                available=False,
                path=None,
                required=required,
                error=f"File not found: {exc}",
            )
        except Exception as exc:
            return DatasetAvailability(
                name=name,
                available=False,
                path=None,
                required=required,
                error=f"Error checking dataset: {exc}",
            )

    def check_required_only(self) -> bool:
        """
        Check if all required datasets are available.

        Returns:
            True if all required datasets are available, False otherwise
        """
        report = self.check_all()
        return report.all_available

