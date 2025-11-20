from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str
    country: Optional[str] = None
    sector: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: str
    created_at: datetime


class RunSummary(BaseModel):
    run_id: str
    project_id: Optional[str]
    project_type: str
    created_at: datetime
    status: str = "completed"


class RunDetail(RunSummary):
    outputs: Dict[str, Dict[str, str]] = Field(default_factory=dict)


class RunCreate(BaseModel):
    """Request model for creating a new run."""

    aoi_geojson: Optional[Dict] = None
    aoi_path: Optional[str] = None
    project_type: str = "solar"
    country: Optional[str] = None
    config: Optional[Dict] = None


class RunCreateResponse(BaseModel):
    """Response model for run creation."""

    task_id: str
    run_id: Optional[str] = None
    status: str
    message: str


class TaskStatus(BaseModel):
    """Task status model."""

    task_id: str
    status: str
    project_id: Optional[str] = None
    run_id: Optional[str] = None
    progress: Optional[Dict] = None
    error: Optional[str] = None

