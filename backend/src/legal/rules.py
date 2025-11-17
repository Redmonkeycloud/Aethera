"""Data structures for legal rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LegalRule:
    """Represents a single legal rule or requirement."""

    rule_id: str
    name: str
    description: str
    category: str  # e.g., "biodiversity", "emissions", "buffer_zones", "land_use"
    condition: dict[str, Any]  # JSONLogic expression
    severity: str  # "critical", "high", "medium", "low", "informational"
    message_template: str  # Template for compliance message
    references: list[str] | None = None  # Legal references, regulations, etc.


@dataclass
class RuleSet:
    """Collection of rules for a specific country/jurisdiction."""

    country_code: str
    country_name: str
    version: str
    rules: list[LegalRule]
    metadata: dict[str, Any] | None = None

