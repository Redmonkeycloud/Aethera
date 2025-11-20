"""Audit logs API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...config.base_settings import settings
from ...db.client import DatabaseClient
from ...security.audit import AuditLogger
from ...security.rbac import require_permission

router = APIRouter(prefix="/audit", tags=["audit"])


def get_db_client() -> DatabaseClient:
    """Get database client."""
    return DatabaseClient(settings.postgres_dsn)


def get_audit_logger(db: DatabaseClient = Depends(get_db_client)) -> AuditLogger:
    """Get audit logger."""
    return AuditLogger(db)


@router.get("/logs")
async def get_audit_logs(
    user_id: UUID | None = Query(None, description="Filter by user ID"),
    action: str | None = Query(None, description="Filter by action"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    _current_user: dict[str, Any] = Depends(require_permission("audit:read")),
) -> dict[str, Any]:
    """Get audit logs (requires 'audit:read' permission)."""
    logs = audit_logger.get_logs(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
        offset=offset,
    )

    return {
        "logs": logs,
        "count": len(logs),
        "limit": limit,
        "offset": offset,
    }

