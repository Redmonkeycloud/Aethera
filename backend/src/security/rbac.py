"""Role-Based Access Control (RBAC) service."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from starlette.requests import Request

from ..config.base_settings import settings
from ..db.client import DatabaseClient
from .auth import get_current_user


class RBACService:
    """Service for role-based access control."""

    def __init__(self, db_client: DatabaseClient) -> None:
        """Initialize RBAC service.

        Args:
            db_client: Database client
        """
        self.db_client = db_client

    def get_user_roles(self, user_id: UUID | str) -> list[str]:
        """Get roles for a user.

        Args:
            user_id: User ID

        Returns:
            List of role names
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT r.name
                    FROM roles r
                    JOIN user_roles ur ON r.id = ur.role_id
                    WHERE ur.user_id = %s
                    """,
                    (user_id,),
                )
                rows = cur.fetchall()
                return [row[0] for row in rows]

    def get_user_permissions(self, user_id: UUID | str) -> set[str]:
        """Get all permissions for a user (via roles).

        Args:
            user_id: User ID

        Returns:
            Set of permission names
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Check if user is superuser (has all permissions)
                cur.execute(
                    "SELECT is_superuser FROM users WHERE id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
                if row and row[0]:
                    # Superuser has all permissions
                    cur.execute("SELECT name FROM permissions")
                    return {row[0] for row in cur.fetchall()}

                # Get permissions via roles
                cur.execute(
                    """
                    SELECT DISTINCT p.name
                    FROM permissions p
                    JOIN role_permissions rp ON p.id = rp.permission_id
                    JOIN user_roles ur ON rp.role_id = ur.role_id
                    WHERE ur.user_id = %s
                    """,
                    (user_id,),
                )
                rows = cur.fetchall()
                return {row[0] for row in rows}

    def has_permission(self, user_id: UUID | str, permission: str) -> bool:
        """Check if user has a specific permission.

        Args:
            user_id: User ID
            permission: Permission name (e.g., 'projects:create')

        Returns:
            True if user has permission
        """
        permissions = self.get_user_permissions(user_id)
        return permission in permissions

    def has_role(self, user_id: UUID | str, role: str) -> bool:
        """Check if user has a specific role.

        Args:
            user_id: User ID
            role: Role name

        Returns:
            True if user has role
        """
        roles = self.get_user_roles(user_id)
        return role in roles

    def assign_role(self, user_id: UUID | str, role_name: str, assigned_by: UUID | str | None = None) -> None:
        """Assign a role to a user.

        Args:
            user_id: User ID
            role_name: Role name
            assigned_by: User ID who assigned the role
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Get role ID
                cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
                role_row = cur.fetchone()
                if not role_row:
                    raise ValueError(f"Role '{role_name}' not found")

                role_id = role_row[0]

                # Assign role
                cur.execute(
                    """
                    INSERT INTO user_roles (user_id, role_id, assigned_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, role_id) DO NOTHING
                    """,
                    (user_id, role_id, assigned_by),
                )

    def revoke_role(self, user_id: UUID | str, role_name: str) -> None:
        """Revoke a role from a user.

        Args:
            user_id: User ID
            role_name: Role name
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Get role ID
                cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
                role_row = cur.fetchone()
                if not role_row:
                    raise ValueError(f"Role '{role_name}' not found")

                role_id = role_row[0]

                # Revoke role
                cur.execute(
                    "DELETE FROM user_roles WHERE user_id = %s AND role_id = %s",
                    (user_id, role_id),
                )

    def create_role(self, name: str, description: str | None = None) -> dict[str, Any]:
        """Create a new role.

        Args:
            name: Role name
            description: Role description

        Returns:
            Role dictionary
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO roles (id, name, description)
                    VALUES (uuid_generate_v4(), %s, %s)
                    RETURNING id, name, description, created_at
                    """,
                    (name, description),
                )
                row = cur.fetchone()
                return {
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "created_at": row[3].isoformat() if row[3] else None,
                }

    def grant_permission(self, role_name: str, permission_name: str) -> None:
        """Grant a permission to a role.

        Args:
            role_name: Role name
            permission_name: Permission name
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Get role and permission IDs
                cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
                role_row = cur.fetchone()
                if not role_row:
                    raise ValueError(f"Role '{role_name}' not found")

                cur.execute("SELECT id FROM permissions WHERE name = %s", (permission_name,))
                perm_row = cur.fetchone()
                if not perm_row:
                    raise ValueError(f"Permission '{permission_name}' not found")

                # Grant permission
                cur.execute(
                    """
                    INSERT INTO role_permissions (role_id, permission_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (role_row[0], perm_row[0]),
                )

    def revoke_permission(self, role_name: str, permission_name: str) -> None:
        """Revoke a permission from a role.

        Args:
            role_name: Role name
            permission_name: Permission name
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Get role and permission IDs
                cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
                role_row = cur.fetchone()
                if not role_row:
                    raise ValueError(f"Role '{role_name}' not found")

                cur.execute("SELECT id FROM permissions WHERE name = %s", (permission_name,))
                perm_row = cur.fetchone()
                if not perm_row:
                    raise ValueError(f"Permission '{permission_name}' not found")

                # Revoke permission
                cur.execute(
                    "DELETE FROM role_permissions WHERE role_id = %s AND permission_id = %s",
                    (role_row[0], perm_row[0]),
                )


def get_user_permissions(
    user: dict[str, Any] = Depends(get_current_user),
    db: DatabaseClient = Depends(lambda: DatabaseClient(settings.postgres_dsn)),
) -> set[str]:
    """Dependency to get current user's permissions.

    Args:
        user: Current user
        db: Database client

    Returns:
        Set of permission names
    """
    rbac = RBACService(db)
    return rbac.get_user_permissions(user["id"])


def require_permission(permission: str):
    """Decorator/dependency to require a specific permission.

    Args:
        permission: Required permission name

    Returns:
        Dependency function
    """
    def dependency(
        user: dict[str, Any] = Depends(get_current_user),
        db: DatabaseClient = Depends(lambda: DatabaseClient(settings.postgres_dsn)),
    ) -> dict[str, Any]:
        """Check if user has required permission."""
        rbac = RBACService(db)
        if not rbac.has_permission(user["id"], permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return user

    return dependency


def require_role(role: str):
    """Decorator/dependency to require a specific role.

    Args:
        role: Required role name

    Returns:
        Dependency function
    """
    def dependency(
        user: dict[str, Any] = Depends(get_current_user),
        db: DatabaseClient = Depends(lambda: DatabaseClient(settings.postgres_dsn)),
    ) -> dict[str, Any]:
        """Check if user has required role."""
        rbac = RBACService(db)
        if not rbac.has_role(user["id"], role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return user

    return dependency

