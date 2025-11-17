from __future__ import annotations

from fastapi import APIRouter, HTTPException

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

