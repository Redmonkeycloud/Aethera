"""Legal Rules Engine for country-specific EIA compliance evaluation."""

from __future__ import annotations

from .evaluator import LegalEvaluator, LegalEvaluationResult
from .parser import RuleParser
from .rules import LegalRule, RuleSet

__all__ = [
    "LegalEvaluator",
    "LegalEvaluationResult",
    "LegalRule",
    "RuleParser",
    "RuleSet",
]

