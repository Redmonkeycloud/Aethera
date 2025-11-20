"""Audit logging service for tracking security-relevant actions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import Request
from psycopg.types.json import Jsonb

from ..config.base_settings import settings
from ..db.client import DatabaseClient


class AuditLogger:
    """Service for logging audit events."""

    def __init__(self, db_client: DatabaseClient) -> None:
        """Initialize audit logger.

        Args:
            db_client: Database client
        """
        self.db_client = db_client

    def log(
        self,
        action: str,
        user_id: UUID | str | None = None,
        username: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_method: str | None = None,
        request_path: str | None = None,
        request_body: dict[str, Any] | None = None,
        response_status: int | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log an audit event.

        Args:
            action: Action name (e.g., 'LOGIN', 'CREATE_PROJECT')
            user_id: User ID (if authenticated)
            username: Username (denormalized for historical records)
            resource_type: Type of resource affected (e.g., 'project', 'run')
            resource_id: ID of resource affected
            ip_address: Client IP address
            user_agent: User agent string
            request_method: HTTP method
            request_path: API endpoint path
            request_body: Request payload (will be sanitized)
            response_status: HTTP status code
            error_message: Error message if action failed
            metadata: Additional context
        """
        # Sanitize request body (remove sensitive fields)
        sanitized_body = self._sanitize_request_body(request_body) if request_body else None

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_logs (
                        id, user_id, username, action, resource_type, resource_id,
                        ip_address, user_agent, request_method, request_path,
                        request_body, response_status, error_message, metadata, created_at
                    ) VALUES (
                        uuid_generate_v4(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        user_id,
                        username,
                        action,
                        resource_type,
                        resource_id,
                        ip_address,
                        user_agent,
                        request_method,
                        request_path,
                        Jsonb(sanitized_body) if sanitized_body else None,
                        response_status,
                        error_message,
                        Jsonb(metadata) if metadata else None,
                        datetime.now(timezone.utc),
                    ),
                )

    def log_request(
        self,
        request: Request,
        user_id: UUID | str | None = None,
        username: str | None = None,
        response_status: int | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log an HTTP request.

        Args:
            request: FastAPI request object
            user_id: User ID (if authenticated)
            username: Username
            response_status: HTTP response status
            error_message: Error message if request failed
            metadata: Additional context
        """
        # Extract resource info from path
        path_parts = request.url.path.strip("/").split("/")
        resource_type = path_parts[0] if path_parts else None
        resource_id = path_parts[1] if len(path_parts) > 1 and path_parts[1] not in [
            "new",
            "create",
            "list",
            "search",
        ] else None

        # Determine action from method and path
        action = self._determine_action(request.method, request.url.path)

        # Get request body if available
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Note: This requires the request body to be read, which may not always be available
                # In production, you might want to capture this differently
                pass
            except Exception:
                pass

        self.log(
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_method=request.method,
            request_path=request.url.path,
            request_body=request_body,
            response_status=response_status,
            error_message=error_message,
            metadata=metadata,
        )

    def get_logs(
        self,
        user_id: UUID | str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get audit logs.

        Args:
            user_id: Filter by user ID
            action: Filter by action
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of audit log entries
        """
        conditions = []
        params: list[Any] = []

        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)

        if action:
            conditions.append("action = %s")
            params.append(action)

        if resource_type:
            conditions.append("resource_type = %s")
            params.append(resource_type)

        if resource_id:
            conditions.append("resource_id = %s")
            params.append(resource_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        params.extend([limit, offset])

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, user_id, username, action, resource_type, resource_id,
                           ip_address, user_agent, request_method, request_path,
                           request_body, response_status, error_message, metadata, created_at
                    FROM audit_logs
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    tuple(params),
                )
                rows = cur.fetchall()
                return [
                    {
                        "id": str(row[0]),
                        "user_id": str(row[1]) if row[1] else None,
                        "username": row[2],
                        "action": row[3],
                        "resource_type": row[4],
                        "resource_id": row[5],
                        "ip_address": row[6],
                        "user_agent": row[7],
                        "request_method": row[8],
                        "request_path": row[9],
                        "request_body": dict(row[10]) if row[10] else None,
                        "response_status": row[11],
                        "error_message": row[12],
                        "metadata": dict(row[13]) if row[13] else None,
                        "created_at": row[14].isoformat() if row[14] else None,
                    }
                    for row in rows
                ]

    @staticmethod
    def _sanitize_request_body(body: dict[str, Any]) -> dict[str, Any]:
        """Sanitize request body by removing sensitive fields.

        Args:
            body: Request body dictionary

        Returns:
            Sanitized body
        """
        sensitive_fields = {"password", "password_hash", "token", "secret", "api_key", "access_token"}
        sanitized = body.copy()

        for key in sensitive_fields:
            if key in sanitized:
                sanitized[key] = "***REDACTED***"

        return sanitized

    @staticmethod
    def _determine_action(method: str, path: str) -> str:
        """Determine action name from HTTP method and path.

        Args:
            method: HTTP method
            path: Request path

        Returns:
            Action name
        """
        path_lower = path.lower()

        # Login/logout
        if "login" in path_lower:
            return "LOGIN"
        if "logout" in path_lower:
            return "LOGOUT"

        # Resource actions
        resource = path.split("/")[1] if len(path.split("/")) > 1 else "unknown"
        resource_upper = resource.upper().replace("-", "_")

        if method == "GET":
            return f"READ_{resource_upper}"
        elif method == "POST":
            return f"CREATE_{resource_upper}"
        elif method == "PUT" or method == "PATCH":
            return f"UPDATE_{resource_upper}"
        elif method == "DELETE":
            return f"DELETE_{resource_upper}"

        return f"{method}_{resource_upper}"


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance.

    Returns:
        Audit logger
    """
    global _audit_logger
    if _audit_logger is None:
        from ..db.client import DatabaseClient
        _audit_logger = AuditLogger(DatabaseClient(settings.postgres_dsn))
    return _audit_logger


def audit_log(
    action: str,
    user_id: UUID | str | None = None,
    username: str | None = None,
    **kwargs: Any,
) -> None:
    """Convenience function to log an audit event.

    Args:
        action: Action name
        user_id: User ID
        username: Username
        **kwargs: Additional audit log fields
    """
    logger = get_audit_logger()
    logger.log(action=action, user_id=user_id, username=username, **kwargs)

