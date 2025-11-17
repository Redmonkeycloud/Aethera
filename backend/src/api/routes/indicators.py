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

