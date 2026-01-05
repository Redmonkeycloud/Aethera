"""Task status and polling endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import TaskStatus
from ...workers.task_tracker import TaskTracker

router = APIRouter()
tracker = TaskTracker()


@router.get("/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str) -> TaskStatus:
    """
    Get the current status of a task.

    Use this endpoint to poll for task completion.
    """
    import traceback
    from ...logging_utils import get_logger
    
    logger = get_logger(__name__)
    
    try:
        task_info = tracker.get_task_status(task_id)
        return TaskStatus(
            task_id=task_info.task_id,
            status=task_info.status.value,
            project_id=task_info.project_id,
            run_id=task_info.run_id,
            progress=task_info.progress,
            error=task_info.error,
        )
    except Exception as exc:
        error_msg = f"Error getting task status: {str(exc)}"
        logger.error("%s\n%s", error_msg, traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)


@router.delete("/{task_id}")
async def cancel_task(task_id: str) -> dict[str, str]:
    """
    Cancel a running task.
    """
    try:
        success = tracker.cancel_task(task_id)
        if success:
            return {"status": "cancelled", "message": f"Task {task_id} has been cancelled"}
        else:
            raise HTTPException(status_code=400, detail="Task could not be cancelled")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error cancelling task: {str(exc)}")

