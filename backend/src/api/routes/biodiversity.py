from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...config.base_settings import settings


router = APIRouter(prefix="/runs", tags=["biodiversity"])


LAYER_FILES = {
    "sensitivity": "biodiversity/sensitivity.geojson",
    "natura": "biodiversity/natura_clipped.geojson",
    "overlap": "biodiversity/overlap.geojson",
}


def _resolve_layer_path(run_id: str, layer_key: str) -> Path:
    base = Path(settings.data_dir) / run_id / settings.processed_dir_name
    return base / LAYER_FILES[layer_key]


@router.get("/{run_id}/biodiversity/{layer_name}")
async def get_biodiversity_layer(run_id: str, layer_name: Literal["sensitivity", "natura", "overlap"]) -> FileResponse:
    if layer_name not in LAYER_FILES:
        raise HTTPException(status_code=404, detail="Unknown biodiversity layer")

    path = _resolve_layer_path(run_id, layer_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Layer {layer_name} not found for run {run_id}")

    return FileResponse(path, media_type="application/geo+json")

