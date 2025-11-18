"""Parser for YAML/JSON legal rules configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ..logging_utils import get_logger
from .rules import LegalRule, RuleSet

logger = get_logger(__name__)


class RuleParser:
    """Parses YAML/JSON files into RuleSet objects."""

    @staticmethod
    def load_from_file(file_path: Path) -> RuleSet:
        """Load a RuleSet from a YAML or JSON file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Rules file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            if file_path.suffix in {".yaml", ".yml"}:
                data = yaml.safe_load(f)
            elif file_path.suffix == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

        return RuleParser._parse_dict(data)

    @staticmethod
    def load_from_dict(data: dict[str, Any]) -> RuleSet:
        """Load a RuleSet from a dictionary."""
        return RuleParser._parse_dict(data)

    @staticmethod
    def _parse_dict(data: dict[str, Any]) -> RuleSet:
        """Parse a dictionary into a RuleSet."""
        country_code = data.get("country_code", "").upper()
        country_name = data.get("country_name", "")
        version = data.get("version", "1.0.0")
        metadata = data.get("metadata", {})

        rules: list[LegalRule] = []
        rules_data = data.get("rules", [])

        for rule_data in rules_data:
            rule = LegalRule(
                rule_id=rule_data.get("id", ""),
                name=rule_data.get("name", ""),
                description=rule_data.get("description", ""),
                category=rule_data.get("category", "general"),
                condition=rule_data.get("condition", {}),
                severity=rule_data.get("severity", "medium"),
                message_template=rule_data.get("message_template", ""),
                references=rule_data.get("references"),
            )
            rules.append(rule)

        logger.info("Parsed %d rules for country %s", len(rules), country_code)
        return RuleSet(
            country_code=country_code,
            country_name=country_name,
            version=version,
            rules=rules,
            metadata=metadata,
        )

