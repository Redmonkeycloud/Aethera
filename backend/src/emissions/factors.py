"""Emission factor loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..logging_utils import get_logger


logger = get_logger(__name__)


class EmissionFactorStore:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self._data: dict[str, Any] = {}

    def load(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Emission factor config not found: {self.config_path}")
        with open(self.config_path, encoding="utf-8") as f:
            self._data = yaml.safe_load(f)
        logger.info("Loaded emission factors from %s", self.config_path)

    @property
    def baseline(self) -> dict[str, float]:
        return self._data.get("baseline", {}).get("corine_ha_tco2e", {})

    @property
    def project(self) -> dict[str, float]:
        return self._data.get("project", {})

    @property
    def defaults(self) -> dict[str, float]:
        return self._data.get("defaults", {})

