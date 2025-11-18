"""Loader for country-specific legal rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config.base_settings import settings
from ..logging_utils import get_logger
from .parser import RuleParser
from .rules import RuleSet

logger = get_logger(__name__)


class LegalRulesLoader:
    """Loads country-specific legal rules from configuration files."""

    def __init__(self, rules_dir: Path | None = None) -> None:
        """
        Initialize the loader.

        Args:
            rules_dir: Directory containing rule files. Defaults to
                backend/src/config/legal_rules/
        """
        if rules_dir is None:
            rules_dir = Path(__file__).resolve().parent.parent / "config" / "legal_rules"
        self.rules_dir = Path(rules_dir)
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, RuleSet] = {}

    def load_country_rules(self, country_code: str) -> RuleSet | None:
        """
        Load rules for a specific country.

        Args:
            country_code: ISO 3166-1 alpha-3 country code (e.g., "DEU", "FRA")

        Returns:
            RuleSet for the country, or None if not found
        """
        country_code = country_code.upper()

        # Check cache
        if country_code in self._cache:
            return self._cache[country_code]

        # Try to find rule file
        candidates = [
            self.rules_dir / f"{country_code}.yaml",
            self.rules_dir / f"{country_code}.yml",
            self.rules_dir / f"{country_code}.json",
            self.rules_dir / f"{country_code.lower()}.yaml",
            self.rules_dir / f"{country_code.lower()}.yml",
            self.rules_dir / f"{country_code.lower()}.json",
        ]

        for candidate in candidates:
            if candidate.exists():
                try:
                    rule_set = RuleParser.load_from_file(candidate)
                    self._cache[country_code] = rule_set
                    logger.info("Loaded legal rules for country %s from %s", country_code, candidate)
                    return rule_set
                except Exception as exc:
                    logger.error("Error loading rules from %s: %s", candidate, exc)
                    continue

        logger.warning("No legal rules found for country %s", country_code)
        return None

    def list_available_countries(self) -> list[str]:
        """List all countries with available rule files."""
        countries: list[str] = []
        for ext in [".yaml", ".yml", ".json"]:
            for path in self.rules_dir.glob(f"*{ext}"):
                country_code = path.stem.upper()
                if country_code not in countries:
                    countries.append(country_code)
        return sorted(countries)

