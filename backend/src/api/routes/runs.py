from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from ..models import RunSummary, RunDetail
from ..storage import RunManifestStore
from ...config.base_settings import settings

router = APIRouter()
run_store = RunManifestStore(settings.data_dir, settings.processed_dir_name)


@router.get("", response_model=list[RunSummary])
async def list_runs() -> list[RunSummary]:
    return run_store.list_runs()


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(run_id: str) -> RunDetail:
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    biodiversity_layers = run_store.list_biodiversity_layers(run_id)
    if biodiversity_layers:
        if "outputs" not in run.dict():
            run.outputs = {}
        run.outputs["biodiversity_layers"] = biodiversity_layers
    return run


@router.get("/{run_id}/results")
async def get_run_results(run_id: str) -> JSONResponse:
    """
    Get comprehensive results for a run.

    Returns all analysis results including:
    - Biodiversity predictions
    - Emissions calculations
    - Environmental KPIs
    - AI/ML model predictions (RESM, AHSM, CIM)
    - Receptor distances
    - Land cover summary
    """
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run_dir = settings.data_dir / run_id / settings.processed_dir_name
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run results not found")

    results: dict[str, Any] = {
        "run_id": run_id,
        "project_id": run.project_id,
        "project_type": run.project_type,
        "created_at": run.created_at.isoformat(),
    }

    # Load biodiversity prediction
    biodiversity_path = run_dir / "biodiversity" / "prediction.json"
    if biodiversity_path.exists():
        with open(biodiversity_path, encoding="utf-8") as f:
            results["biodiversity"] = json.load(f)

    # Load emissions
    emissions_path = run_dir / "emissions" / "emission_summary.json"
    if emissions_path.exists():
        with open(emissions_path, encoding="utf-8") as f:
            results["emissions"] = json.load(f)

    # Load KPIs
    kpis_path = run_dir / "kpis" / "environmental_kpis.json"
    if kpis_path.exists():
        with open(kpis_path, encoding="utf-8") as f:
            results["kpis"] = json.load(f)

    # Load RESM prediction
    resm_path = run_dir / "predictions" / "resm_prediction.json"
    if resm_path.exists():
        with open(resm_path, encoding="utf-8") as f:
            results["resm"] = json.load(f)

    # Load AHSM prediction
    ahsm_path = run_dir / "predictions" / "ahsm_prediction.json"
    if ahsm_path.exists():
        with open(ahsm_path, encoding="utf-8") as f:
            results["ahsm"] = json.load(f)

    # Load CIM prediction
    cim_path = run_dir / "predictions" / "cim_prediction.json"
    if cim_path.exists():
        with open(cim_path, encoding="utf-8") as f:
            results["cim"] = json.load(f)

    # Load receptor distances
    receptor_path = run_dir / "receptors" / "receptor_distances.json"
    if receptor_path.exists():
        with open(receptor_path, encoding="utf-8") as f:
            results["receptor_distances"] = json.load(f)

    # Load land cover summary
    land_cover_path = run_dir / "land_cover_summary.json"
    if land_cover_path.exists():
        with open(land_cover_path, encoding="utf-8") as f:
            results["land_cover"] = json.load(f)

    return JSONResponse(content=results)


@router.get("/{run_id}/legal")
async def get_run_legal(run_id: str) -> JSONResponse:
    """
    Get legal compliance results for a run.

    Returns the legal evaluation results including:
    - Overall compliance status
    - Rule-by-rule evaluation
    - Critical violations
    - Warnings
    - Informational messages
    """
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run_dir = settings.data_dir / run_id / settings.processed_dir_name
    legal_path = run_dir / "legal_evaluation.json"
    if not legal_path.exists():
        raise HTTPException(status_code=404, detail="Legal evaluation not found for this run")

    with open(legal_path, encoding="utf-8") as f:
        legal_data = json.load(f)

    return JSONResponse(content=legal_data)


@router.get("/{run_id}/export")
async def export_run(run_id: str) -> FileResponse:
    """
    Export a complete run package as a ZIP file.

    The export includes:
    - All processed geospatial data
    - Analysis results (JSON)
    - Biodiversity layers
    - Predictions
    - Legal evaluation
    - Manifest
    """
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run_dir = settings.data_dir / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run directory not found")

    # Create temporary ZIP file
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
        zip_path = Path(tmp_zip.name)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the run directory
            for file_path in run_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(run_dir.parent)
                    zipf.write(file_path, arcname)

        return FileResponse(
            path=zip_path,
            filename=f"{run_id}_export.zip",
            media_type="application/zip",
        )
    except Exception as exc:
        # Clean up on error
        if zip_path.exists():
            zip_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error creating export: {str(exc)}")

