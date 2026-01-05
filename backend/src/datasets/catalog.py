"""Dataset discovery utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass
class DatasetCatalog:
    base_dir: Path

    def _search(self, relative: str, patterns: Iterable[str]) -> Optional[Path]:
        root = self.base_dir / relative
        if not root.exists():
            return None
        for pattern in patterns:
            matches = sorted(root.rglob(pattern))
            if matches:
                return matches[0]
        return None

    def corine(self, country: Optional[str] = None) -> Path:
        """Get CORINE Land Cover dataset, optionally country-specific.
        
        Args:
            country: Country code (e.g., 'ITA', 'GRC'). If None, returns full dataset.
        """
        if country:
            # Try country-specific file first - prefer GeoJSON (pre-converted, faster)
            country_upper = country.upper()
            country_path = self._search("corine", [f"corine_{country_upper}.geojson", f"corine_{country_upper}.shp", f"corine_{country_upper}.gpkg"])
            if country_path:
                return country_path
        # Fall back to full dataset - prefer GeoJSON if available
        path = self._search("corine", ["*.geojson", "*.shp", "*.gpkg"])
        if not path:
            raise FileNotFoundError("No CORINE dataset found under data source directory.")
        return path

    def natura2000(self, country: Optional[str] = None) -> Optional[Path]:
        """Get Natura 2000 dataset, optionally country-specific.
        
        Args:
            country: Country code (e.g., 'ITA', 'GRC'). If None, returns full dataset.
        """
        if country:
            # Try country-specific file first
            country_upper = country.upper()
            country_path = self._search(f"protected_areas/natura2000", [f"natura2000_{country_upper}.shp", f"natura2000_{country_upper}.gpkg"])
            if country_path:
                return country_path
        # Fall back to full dataset
        return self._search("protected_areas/natura2000", ["Natura2000*.shp", "Natura2000*.gpkg", "*.gpkg", "*.shp"])

    def gadm(self, level: int = 2) -> Optional[Path]:
        pattern = f"*_{level}.shp"
        return self._search("gadm", [pattern])

    def eurostat_nuts(self) -> Optional[Path]:
        return self._search("eurostat", ["*.shp", "*.gpkg"])

    def natural_earth_admin(self) -> Optional[Path]:
        return self._search("natural_earth", ["ne_10m_admin_0_countries.*", "*.shp", "*.gpkg"])

    def biodiversity_training(self) -> Optional[Path]:
        return self._search("biodiversity", ["training.parquet", "training.csv", "*.parquet", "*.csv"])

