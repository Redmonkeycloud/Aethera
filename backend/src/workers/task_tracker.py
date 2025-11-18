"""Task status tracking and polling."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from celery.result import AsyncResult
from pydantic import BaseModel

from .celery_app import celery_app


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVOKED = "REVOKED"


class TaskInfo(BaseModel):
    """Task information model."""

    task_id: str
    status: TaskStatus
    project_id: str | None = None
    run_id: str | None = None
    progress: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class TaskTracker:
    """Tracks Celery task status and provides polling interface."""

    @staticmethod
    def get_task_status(task_id: str) -> TaskInfo:
        """
        Get current status of a task.

        Args:
            task_id: Celery task ID

        Returns:
            TaskInfo with current status
        """
        result = AsyncResult(task_id, app=celery_app)

        # Map Celery states to our TaskStatus
        state_map = {
            "PENDING": TaskStatus.PENDING,
            "STARTED": TaskStatus.PROCESSING,
            "PROCESSING": TaskStatus.PROCESSING,
            "SUCCESS": TaskStatus.COMPLETED,
            "FAILURE": TaskStatus.FAILED,
            "REVOKED": TaskStatus.REVOKED,
        }

        status = state_map.get(result.state, TaskStatus.PENDING)

        # Extract metadata
        meta = result.info or {}
        if isinstance(meta, dict):
            progress = meta.get("progress") or meta
            error = meta.get("error")
            run_id = meta.get("run_id")
            project_id = meta.get("project_id")
        else:
            progress = None
            error = None
            run_id = None
            project_id = None

        # Get result if completed
        if status == TaskStatus.COMPLETED and result.ready():
            try:
                task_result = result.get(timeout=1)
                if isinstance(task_result, dict):
                    run_id = task_result.get("run_id") or run_id
                    project_id = task_result.get("project_id") or project_id
            except Exception:
                pass

        return TaskInfo(
            task_id=task_id,
            status=status,
            project_id=project_id,
            run_id=run_id,
            progress=progress,
            error=error,
            created_at=datetime.utcnow(),  # Note: Celery doesn't expose creation time easily
            updated_at=datetime.utcnow(),
        )

    @staticmethod
    def cancel_task(task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: Celery task ID

        Returns:
            True if task was cancelled, False otherwise
        """
        celery_app.control.revoke(task_id, terminate=True)
        return True

