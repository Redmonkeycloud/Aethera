"""API routes for environmental indicators and KPIs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...config.base_settings import settings


router = APIRouter(prefix="/runs", tags=["indicators"])


@router.get("/{run_id}/indicators/receptor-distances")
async def get_receptor_distances(run_id: str) -> dict[str, Any]:
    """Get distance-to-receptor analysis for a run."""
    run_dir = Path(settings.data_dir) / run_id / settings.processed_dir_name
    receptor_file = run_dir / "receptor_distances.json"

    if not receptor_file.exists():
        raise HTTPException(
            status_code=404, detail=f"Receptor distances not found for run {run_id}"
        )

    import json

    with open(receptor_file, encoding="utf-8") as f:
        return json.load(f)


@router.get("/{run_id}/indicators/kpis")
async def get_environmental_kpis(run_id: str) -> dict[str, Any]:
    """Get comprehensive environmental KPIs for a run."""
    run_dir = Path(settings.data_dir) / run_id / settings.processed_dir_name
    kpi_file = run_dir / "environmental_kpis.json"

    if not kpi_file.exists():
        raise HTTPException(
            status_code=404, detail=f"Environmental KPIs not found for run {run_id}"
        )

    import json

    with open(kpi_file, encoding="utf-8") as f:
        return json.load(f)


@router.get("/{run_id}/indicators/resm")
async def get_resm_prediction(run_id: str) -> dict[str, Any]:
    """Get RESM (Renewable/Resilience Suitability) prediction for a run."""
    run_dir = Path(settings.data_dir) / run_id / settings.processed_dir_name
    resm_file = run_dir / "resm_prediction.json"

    if not resm_file.exists():
        raise HTTPException(
            status_code=404, detail=f"RESM prediction not found for run {run_id}"
        )

    import json

    with open(resm_file, encoding="utf-8") as f:
        return json.load(f)


@router.get("/{run_id}/indicators/ahsm")
async def get_ahsm_prediction(run_id: str) -> dict[str, Any]:
    """Get AHSM (Asset Hazard Susceptibility) prediction for a run."""
    run_dir = Path(settings.data_dir) / run_id / settings.processed_dir_name
    ahsm_file = run_dir / "ahsm_prediction.json"

    if not ahsm_file.exists():
        raise HTTPException(
            status_code=404, detail=f"AHSM prediction not found for run {run_id}"
        )

    import json

    with open(ahsm_file, encoding="utf-8") as f:
        return json.load(f)


@router.get("/{run_id}/indicators/cim")
async def get_cim_prediction(run_id: str) -> dict[str, Any]:
    """Get CIM (Cumulative Impact Model) prediction for a run."""
    run_dir = Path(settings.data_dir) / run_id / settings.processed_dir_name
    cim_file = run_dir / "cim_prediction.json"

    if not cim_file.exists():
        raise HTTPException(
            status_code=404, detail=f"CIM prediction not found for run {run_id}"
        )

    import json

    with open(cim_file, encoding="utf-8") as f:
        return json.load(f)

