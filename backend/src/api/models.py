from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str
    country: str | None = None
    sector: str | None = None


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: str
    created_at: datetime


class RunSummary(BaseModel):
    run_id: str
    project_id: str | None
    project_type: str
    created_at: datetime
    status: str = "completed"


class RunDetail(RunSummary):
    outputs: dict[str, dict[str, str]] = Field(default_factory=dict)

