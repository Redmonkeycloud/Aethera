"""Dataset discovery utilities."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatasetCatalog:
    base_dir: Path

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
        return self._search(
            "biodiversity", ["training.parquet", "training.csv", "*.parquet", "*.csv"]
        )

