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

