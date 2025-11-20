"""OAuth/OpenID Connect integration service."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException, status

from ..config.base_settings import settings
from ..db.client import DatabaseClient
from .auth import AuthenticationService


class OAuthService:
    """Service for OAuth/OpenID Connect authentication."""

    def __init__(self, db_client: DatabaseClient) -> None:
        """Initialize OAuth service.

        Args:
            db_client: Database client
        """
        self.db_client = db_client
        self.auth_service = AuthenticationService(db_client)

    async def get_google_user_info(self, access_token: str) -> dict[str, Any]:
        """Get user information from Google OAuth.

        Args:
            access_token: Google OAuth access token

        Returns:
            User information dictionary

        Raises:
            HTTPException: If token is invalid
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to verify Google token: {str(e)}",
            )

    async def get_microsoft_user_info(self, access_token: str) -> dict[str, Any]:
        """Get user information from Microsoft OAuth.

        Args:
            access_token: Microsoft OAuth access token

        Returns:
            User information dictionary

        Raises:
            HTTPException: If token is invalid
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "sub": data.get("id"),
                    "email": data.get("mail") or data.get("userPrincipalName"),
                    "name": data.get("displayName"),
                    "given_name": data.get("givenName"),
                    "family_name": data.get("surname"),
                }
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to verify Microsoft token: {str(e)}",
            )

    async def get_okta_user_info(self, access_token: str, okta_domain: str) -> dict[str, Any]:
        """Get user information from Okta OAuth.

        Args:
            access_token: Okta OAuth access token
            okta_domain: Okta domain (e.g., 'dev-123456.okta.com')

        Returns:
            User information dictionary

        Raises:
            HTTPException: If token is invalid
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{okta_domain}/oauth2/v1/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to verify Okta token: {str(e)}",
            )

    async def authenticate_oauth(
        self,
        provider: str,
        access_token: str,
        okta_domain: str | None = None,
    ) -> dict[str, Any]:
        """Authenticate user via OAuth provider.

        Args:
            provider: OAuth provider ('google', 'microsoft', 'okta')
            access_token: OAuth access token
            okta_domain: Okta domain (required for Okta)

        Returns:
            User dictionary

        Raises:
            HTTPException: If authentication fails
        """
        # Get user info from provider
        if provider == "google":
            user_info = await self.get_google_user_info(access_token)
            oauth_sub = user_info.get("id")
            email = user_info.get("email")
            full_name = user_info.get("name")
        elif provider == "microsoft":
            user_info = await self.get_microsoft_user_info(access_token)
            oauth_sub = user_info.get("sub")
            email = user_info.get("email")
            full_name = user_info.get("name")
        elif provider == "okta":
            if not okta_domain:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Okta domain required for Okta authentication",
                )
            user_info = await self.get_okta_user_info(access_token, okta_domain)
            oauth_sub = user_info.get("sub")
            email = user_info.get("email")
            full_name = user_info.get("name")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}",
            )

        if not oauth_sub or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OAuth token: missing user information",
            )

        # Find or create user
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Check if user exists by OAuth sub
                cur.execute(
                    """
                    SELECT id, username, email, full_name, is_active, is_superuser
                    FROM users
                    WHERE oauth_provider = %s AND oauth_sub = %s
                    """,
                    (provider, oauth_sub),
                )
                row = cur.fetchone()

                if row:
                    # Update last login
                    cur.execute(
                        "UPDATE users SET last_login = NOW() WHERE id = %s",
                        (row[0],),
                    )

                    return {
                        "id": str(row[0]),
                        "username": row[1],
                        "email": row[2],
                        "full_name": row[3],
                        "is_active": row[4],
                        "is_superuser": row[5],
                    }
                else:
                    # Create new user
                    username = email.split("@")[0]  # Use email prefix as username
                    # Ensure username is unique
                    base_username = username
                    counter = 1
                    while True:
                        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                        if not cur.fetchone():
                            break
                        username = f"{base_username}{counter}"
                        counter += 1

                    cur.execute(
                        """
                        INSERT INTO users (
                            id, username, email, password_hash, full_name,
                            oauth_provider, oauth_sub, is_active
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, TRUE
                        )
                        RETURNING id, username, email, full_name, is_active, is_superuser
                        """,
                        (uuid4(), username, email, "", full_name, provider, oauth_sub),
                    )
                    row = cur.fetchone()

                    # Assign default 'viewer' role
                    cur.execute("SELECT id FROM roles WHERE name = 'viewer'")
                    role_row = cur.fetchone()
                    if role_row:
                        cur.execute(
                            "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                            (row[0], role_row[0]),
                        )

                    return {
                        "id": str(row[0]),
                        "username": row[1],
                        "email": row[2],
                        "full_name": row[3],
                        "is_active": row[4],
                        "is_superuser": row[5],
                    }

