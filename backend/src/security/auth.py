"""Authentication service for JWT tokens and password management."""

from __future__ import annotations

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from psycopg.types.json import Jsonb

from ..config.base_settings import settings
from ..db.client import DatabaseClient


# JWT Configuration
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()


class AuthenticationService:
    """Service for user authentication and token management."""

    def __init__(self, db_client: DatabaseClient, secret_key: str | None = None) -> None:
        """Initialize authentication service.

        Args:
            db_client: Database client
            secret_key: JWT secret key (defaults to settings)
        """
        self.db_client = db_client
        self.secret_key = secret_key or getattr(settings, "jwt_secret_key", "change-me-in-production")

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash.

        Args:
            password: Plain text password
            password_hash: Hashed password

        Returns:
            True if password matches
        """
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str | None = None,
        is_superuser: bool = False,
    ) -> dict[str, Any]:
        """Create a new user.

        Args:
            username: Username
            email: Email address
            password: Plain text password
            full_name: Full name
            is_superuser: Whether user is superuser

        Returns:
            User dictionary
        """
        password_hash = self.hash_password(password)

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (id, username, email, password_hash, full_name, is_superuser)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, username, email, full_name, is_active, is_superuser, created_at
                    """,
                    (uuid4(), username, email, password_hash, full_name, is_superuser),
                )
                row = cur.fetchone()

                # Assign default 'viewer' role
                cur.execute(
                    "SELECT id FROM roles WHERE name = 'viewer'",
                )
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
                    "created_at": row[6].isoformat(),
                }

    def authenticate_user(self, username: str, password: str) -> dict[str, Any] | None:
        """Authenticate a user with username and password.

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            User dictionary if authenticated, None otherwise
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, username, email, password_hash, full_name, is_active, is_superuser
                    FROM users
                    WHERE (username = %s OR email = %s) AND is_active = TRUE
                    """,
                    (username, username),
                )
                row = cur.fetchone()
                if not row:
                    return None

                user_id, db_username, email, password_hash, full_name, is_active, is_superuser = row

                if not self.verify_password(password, password_hash):
                    return None

                # Update last login
                cur.execute(
                    "UPDATE users SET last_login = %s WHERE id = %s",
                    (datetime.now(timezone.utc), user_id),
                )

                return {
                    "id": str(user_id),
                    "username": db_username,
                    "email": email,
                    "full_name": full_name,
                    "is_active": is_active,
                    "is_superuser": is_superuser,
                }

    def get_user_by_id(self, user_id: UUID | str) -> dict[str, Any] | None:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User dictionary or None
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, username, email, full_name, is_active, is_superuser, created_at
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None

                return {
                    "id": str(row[0]),
                    "username": row[1],
                    "email": row[2],
                    "full_name": row[3],
                    "is_active": row[4],
                    "is_superuser": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                }

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User dictionary or None
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, username, email, full_name, is_active, is_superuser, created_at
                    FROM users
                    WHERE username = %s
                    """,
                    (username,),
                )
                row = cur.fetchone()
                if not row:
                    return None

                return {
                    "id": str(row[0]),
                    "username": row[1],
                    "email": row[2],
                    "full_name": row[3],
                    "is_active": row[4],
                    "is_superuser": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                }

    def store_refresh_token(
        self,
        user_id: UUID | str,
        token: str,
        expires_at: datetime,
        ip_address: str | None = None,
        device_info: str | None = None,
    ) -> None:
        """Store a refresh token.

        Args:
            user_id: User ID
            token: Refresh token
            expires_at: Expiration time
            ip_address: IP address
            device_info: Device information
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO refresh_tokens (id, user_id, token, expires_at, ip_address, device_info)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (uuid4(), user_id, token, expires_at, ip_address, device_info),
                )

    def get_refresh_token(self, token: str) -> dict[str, Any] | None:
        """Get refresh token information.

        Args:
            token: Refresh token

        Returns:
            Token information or None
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, token, expires_at, revoked_at, created_at
                    FROM refresh_tokens
                    WHERE token = %s AND revoked_at IS NULL AND expires_at > NOW()
                    """,
                    (token,),
                )
                row = cur.fetchone()
                if not row:
                    return None

                return {
                    "id": str(row[0]),
                    "user_id": str(row[1]),
                    "token": row[2],
                    "expires_at": row[3].isoformat() if row[3] else None,
                    "revoked_at": row[4].isoformat() if row[4] else None,
                    "created_at": row[5].isoformat() if row[5] else None,
                }

    def revoke_refresh_token(self, token: str) -> None:
        """Revoke a refresh token.

        Args:
            token: Refresh token
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE refresh_tokens SET revoked_at = %s WHERE token = %s",
                    (datetime.now(timezone.utc), token),
                )


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Expiration time delta

    Returns:
        Encoded JWT token
    """
    secret_key = getattr(settings, "jwt_secret_key", "change-me-in-production")
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token.

    Args:
        data: Data to encode in token

    Returns:
        Encoded JWT refresh token
    """
    secret_key = getattr(settings, "jwt_secret_key", "change-me-in-production")
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> dict[str, Any]:
    """Verify and decode a JWT token.

    Args:
        token: JWT token
        token_type: Expected token type ('access' or 'refresh')

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    secret_key = getattr(settings, "jwt_secret_key", "change-me-in-production")

    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DatabaseClient = Depends(lambda: DatabaseClient(settings.postgres_dsn)),
) -> dict[str, Any]:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database client

    Returns:
        Current user dictionary

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    auth_service = AuthenticationService(db)
    user = auth_service.get_user_by_id(user_id)

    if user is None or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user

