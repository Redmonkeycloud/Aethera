from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...config.base_settings import settings
from ..models import Project, ProjectCreate
from ..storage import ProjectStore


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

