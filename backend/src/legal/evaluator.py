"""Evaluator for legal rules compliance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import jsonlogic
except ImportError:
    jsonlogic = None  # type: ignore

from ..logging_utils import get_logger
from .rules import LegalRule, RuleSet

logger = get_logger(__name__)


@dataclass
class ComplianceStatus:
    """Status of a single rule evaluation."""

    rule_id: str
    rule_name: str
    passed: bool
    message: str
    severity: str
    category: str
    details: dict[str, Any] | None = None


@dataclass
class LegalEvaluationResult:
    """Result of evaluating a RuleSet against project metrics."""

    country_code: str
    overall_compliant: bool
    statuses: list[ComplianceStatus]
    summary: dict[str, Any]
    critical_violations: list[ComplianceStatus]
    warnings: list[ComplianceStatus]
    informational: list[ComplianceStatus]


class LegalEvaluator:
    """Evaluates project metrics against legal rules."""

    def __init__(self, rule_set: RuleSet) -> None:
        self.rule_set = rule_set
        if jsonlogic is None:
            logger.warning(
                "jsonlogic not installed. Install with: pip install jsonlogic-python"
            )
            logger.warning("Falling back to simple condition evaluation.")

    def evaluate(self, project_metrics: dict[str, Any]) -> LegalEvaluationResult:
        """
        Evaluate all rules in the RuleSet against project metrics.

        Args:
            project_metrics: Dictionary containing project analysis results
                (e.g., biodiversity scores, emissions, receptor distances, KPIs)

        Returns:
            LegalEvaluationResult with compliance status for each rule
        """
        statuses: list[ComplianceStatus] = []
        critical_violations: list[ComplianceStatus] = []
        warnings: list[ComplianceStatus] = []
        informational: list[ComplianceStatus] = []

        for rule in self.rule_set.rules:
            status = self._evaluate_rule(rule, project_metrics)
            statuses.append(status)

            if not status.passed:
                if status.severity == "critical":
                    critical_violations.append(status)
                elif status.severity in {"high", "medium"}:
                    warnings.append(status)
                elif status.severity in {"low", "informational"}:
                    informational.append(status)

        overall_compliant = len(critical_violations) == 0

        summary = {
            "total_rules": len(self.rule_set.rules),
            "passed": sum(1 for s in statuses if s.passed),
            "failed": sum(1 for s in statuses if not s.passed),
            "critical_violations": len(critical_violations),
            "warnings": len(warnings),
            "informational": len(informational),
        }

        return LegalEvaluationResult(
            country_code=self.rule_set.country_code,
            overall_compliant=overall_compliant,
            statuses=statuses,
            summary=summary,
            critical_violations=critical_violations,
            warnings=warnings,
            informational=informational,
        )

    def _evaluate_rule(
        self, rule: LegalRule, project_metrics: dict[str, Any]
    ) -> ComplianceStatus:
        """Evaluate a single rule against project metrics."""
        try:
            if jsonlogic:
                # Use jsonlogic for complex condition evaluation
                passed = bool(jsonlogic.apply(rule.condition, project_metrics))
            else:
                # Fallback to simple evaluation
                passed = self._simple_evaluate(rule.condition, project_metrics)

            # Generate message
            message = self._format_message(rule.message_template, project_metrics, passed)

            return ComplianceStatus(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                passed=passed,
                message=message,
                severity=rule.severity,
                category=rule.category,
                details={"condition": rule.condition},
            )
        except Exception as exc:
            logger.error("Error evaluating rule %s: %s", rule.rule_id, exc)
            return ComplianceStatus(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                passed=False,
                message=f"Error evaluating rule: {exc}",
                severity=rule.severity,
                category=rule.category,
                details={"error": str(exc)},
            )

    def _simple_evaluate(
        self, condition: dict[str, Any], project_metrics: dict[str, Any]
    ) -> bool:
        """
        Simple condition evaluator (fallback when jsonlogic is not available).

        Supports basic comparisons: {"field": "value"}, {"field": {"<": threshold}}, etc.
        """
        if not condition:
            return True

        # Handle simple field comparison
        if len(condition) == 1:
            field, value = next(iter(condition.items()))
            if isinstance(value, dict):
                # Handle operators: {"<": 10}, {">": 5}, {"<=": 100}, etc.
                if len(value) == 1:
                    op, threshold = next(iter(value.items()))
                    metric_value = project_metrics.get(field, 0)
                    if op == "<":
                        return metric_value < threshold
                    elif op == ">":
                        return metric_value > threshold
                    elif op == "<=":
                        return metric_value <= threshold
                    elif op == ">=":
                        return metric_value >= threshold
                    elif op == "==":
                        return metric_value == threshold
                    elif op == "!=":
                        return metric_value != threshold
            else:
                # Direct comparison
                return project_metrics.get(field) == value

        # Handle AND/OR logic
        if "and" in condition:
            return all(
                self._simple_evaluate(sub_cond, project_metrics)
                for sub_cond in condition["and"]
            )
        if "or" in condition:
            return any(
                self._simple_evaluate(sub_cond, project_metrics)
                for sub_cond in condition["or"]
            )

        # Default: check if all conditions are met
        return all(
            project_metrics.get(field) == value
            for field, value in condition.items()
            if not isinstance(value, dict)
        )

    def _format_message(
        self, template: str, project_metrics: dict[str, Any], passed: bool
    ) -> str:
        """Format message template with project metrics."""
        if not template:
            return "Rule evaluation completed" if passed else "Rule violation detected"

        try:
            # Simple template substitution
            message = template
            for key, value in project_metrics.items():
                placeholder = f"{{{key}}}"
                if placeholder in message:
                    message = message.replace(placeholder, str(value))
            return message
        except Exception as exc:
            logger.warning("Error formatting message template: %s", exc)
            return template

