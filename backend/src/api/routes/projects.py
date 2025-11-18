from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import Project, ProjectCreate, RunCreate, RunCreateResponse
from ..storage import ProjectStore
from ...config.base_settings import settings
from ...workers.tasks import run_analysis_task

router = APIRouter()
store = ProjectStore(settings.projects_store)


@router.get("", response_model=list[Project])
async def list_projects() -> list[Project]:
    return store.list_projects()


@router.post("", response_model=Project, status_code=201)
async def create_project(payload: ProjectCreate) -> Project:
    return store.add_project(payload)


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/runs", response_model=RunCreateResponse, status_code=202)
async def create_run(project_id: str, payload: RunCreate) -> RunCreateResponse:
    """
    Trigger a new analysis run for a project.

    This endpoint queues an async task to run the AETHERA analysis pipeline.
    """
    # Verify project exists
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate that either aoi_path or aoi_geojson is provided
    if not payload.aoi_path and not payload.aoi_geojson:
        raise HTTPException(
            status_code=400, detail="Either 'aoi_path' or 'aoi_geojson' must be provided"
        )

    # Queue the analysis task
    task = run_analysis_task.delay(
        project_id=project_id,
        aoi_path=payload.aoi_path,
        aoi_geojson=payload.aoi_geojson,
        project_type=payload.project_type,
        country=payload.country,
        config=payload.config,
    )

    return RunCreateResponse(
        task_id=task.id,
        status="pending",
        message="Analysis task queued successfully",
    )

