"""Emissions calculation logic."""

from __future__ import annotations

from dataclasses import dataclass

from .factors import EmissionFactorStore


@dataclass
class EmissionResult:
    baseline_tco2e: float
    project_construction_tco2e: float
    project_operation_tco2e_per_year: float
    net_difference_tco2e: float

    def as_dict(self) -> dict[str, float]:
        return {
            "baseline_tco2e": self.baseline_tco2e,
            "project_construction_tco2e": self.project_construction_tco2e,
            "project_operation_tco2e_per_year": self.project_operation_tco2e_per_year,
            "net_difference_tco2e": self.net_difference_tco2e,
        }


class EmissionCalculator:
    def __init__(self, factor_store: EmissionFactorStore) -> None:
        self.factors = factor_store

    def _baseline_emissions(self, land_cover_summary: list[dict]) -> float:
        factors = self.factors.baseline
        total = 0.0
        for record in land_cover_summary:
            code = str(record.get("class_code"))
            area = float(record.get("total_area_ha", 0))
            factor = float(factors.get(code, 0))
            total += factor * area
        return total

    def _project_construction(
        self, land_cover_summary: list[dict], project_capacity_mw: float
    ) -> float:
        area_total = sum(float(record.get("total_area_ha", 0)) for record in land_cover_summary)
        land_clearing = (
            self.factors.project.get("land_clearing_tco2e_per_ha", 0.0) * area_total
        )
        construction = (
            self.factors.project.get("construction_tco2e_per_mw", 0.0) * project_capacity_mw
        )
        return land_clearing + construction

    def _project_operation(self, project_capacity_mw: float) -> float:
        return self.factors.project.get("operation_tco2e_per_mw_year", 0.0) * project_capacity_mw

    def compute(self, land_cover_summary: list[dict], project_config: dict) -> EmissionResult:
        capacity = float(
            project_config.get("capacity_mw")
            or self.factors.defaults.get("project_capacity_mw", 0)
        )
        baseline = self._baseline_emissions(land_cover_summary)
        construction = self._project_construction(land_cover_summary, capacity)
        operation = self._project_operation(capacity)
        net = construction + operation - baseline

        return EmissionResult(
            baseline_tco2e=baseline,
            project_construction_tco2e=construction,
            project_operation_tco2e_per_year=operation,
            net_difference_tco2e=net,
        )

