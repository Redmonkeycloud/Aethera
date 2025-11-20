"""Authentication API routes."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from ...config.base_settings import settings
from ...db.client import DatabaseClient
from ...security.auth import (
    AuthenticationService,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from ...security.audit import AuditLogger
from ...security.oauth import OAuthService

router = APIRouter(prefix="/auth", tags=["authentication"])

security = HTTPBearer()


def get_db_client() -> DatabaseClient:
    """Get database client."""
    return DatabaseClient(settings.postgres_dsn)


def get_auth_service(db: DatabaseClient = Depends(get_db_client)) -> AuthenticationService:
    """Get authentication service."""
    return AuthenticationService(db)


def get_audit_logger(db: DatabaseClient = Depends(get_db_client)) -> AuditLogger:
    """Get audit logger."""
    return AuditLogger(db)


# Request/Response Models

class UserRegister(BaseModel):
    """User registration request."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    """User login request."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class OAuthLoginRequest(BaseModel):
    """OAuth login request."""

    provider: str = Field(..., description="OAuth provider: 'google', 'microsoft', 'okta'")
    access_token: str
    okta_domain: str | None = None


# Endpoints

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> dict[str, Any]:
    """Register a new user."""
    try:
        user = auth_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
        )

        # Log registration
        audit_logger.log(
            action="USER_REGISTER",
            username=user["username"],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_method="POST",
            request_path=request.url.path,
            response_status=201,
        )

        return {"message": "User registered successfully", "user": user}
    except Exception as e:
        # Log failed registration
        audit_logger.log(
            action="USER_REGISTER_FAILED",
            username=user_data.username,
            ip_address=request.client.host if request.client else None,
            request_method="POST",
            request_path=request.url.path,
            response_status=400,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    user = auth_service.authenticate_user(credentials.username, credentials.password)

    if not user:
        # Log failed login
        audit_logger.log(
            action="LOGIN_FAILED",
            username=credentials.username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_method="POST",
            request_path=request.url.path,
            response_status=401,
            error_message="Invalid credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token(data={"sub": user["id"], "username": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["id"]})

    # Store refresh token
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    auth_service.store_refresh_token(
        user_id=user["id"],
        token=refresh_token,
        expires_at=expires_at,
        ip_address=request.client.host if request.client else None,
        device_info=request.headers.get("user-agent"),
    )

    # Log successful login
    audit_logger.log(
        action="LOGIN",
        user_id=user["id"],
        username=user["username"],
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_method="POST",
        request_path=request.url.path,
        response_status=200,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/oauth/login", response_model=TokenResponse)
async def oauth_login(
    oauth_data: OAuthLoginRequest,
    request: Request,
    db: DatabaseClient = Depends(get_db_client),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> TokenResponse:
    """Authenticate user via OAuth/OpenID Connect."""
    oauth_service = OAuthService(db)

    try:
        user = await oauth_service.authenticate_oauth(
            provider=oauth_data.provider,
            access_token=oauth_data.access_token,
            okta_domain=oauth_data.okta_domain,
        )

        # Create tokens
        access_token = create_access_token(data={"sub": user["id"], "username": user["username"]})
        refresh_token = create_refresh_token(data={"sub": user["id"]})

        # Store refresh token
        auth_service = AuthenticationService(db)
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        auth_service.store_refresh_token(
            user_id=user["id"],
            token=refresh_token,
            expires_at=expires_at,
            ip_address=request.client.host if request.client else None,
            device_info=request.headers.get("user-agent"),
        )

        # Log successful OAuth login
        audit_logger.log(
            action="OAUTH_LOGIN",
            user_id=user["id"],
            username=user["username"],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_method="POST",
            request_path=request.url.path,
            response_status=200,
            metadata={"provider": oauth_data.provider},
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except HTTPException:
        raise
    except Exception as e:
        # Log failed OAuth login
        audit_logger.log(
            action="OAUTH_LOGIN_FAILED",
            ip_address=request.client.host if request.client else None,
            request_method="POST",
            request_path=request.url.path,
            response_status=401,
            error_message=str(e),
            metadata={"provider": oauth_data.provider},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth authentication failed: {str(e)}",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> TokenResponse:
    """Refresh access token using refresh token."""
    # Verify refresh token
    try:
        payload = verify_token(token_data.refresh_token, token_type="refresh")
    except HTTPException:
        audit_logger.log(
            action="TOKEN_REFRESH_FAILED",
            ip_address=request.client.host if request.client else None,
            request_method="POST",
            request_path=request.url.path,
            response_status=401,
            error_message="Invalid refresh token",
        )
        raise

    # Check if token exists in database and is not revoked
    token_info = auth_service.get_refresh_token(token_data.refresh_token)
    if not token_info:
        audit_logger.log(
            action="TOKEN_REFRESH_FAILED",
            ip_address=request.client.host if request.client else None,
            request_method="POST",
            request_path=request.url.path,
            response_status=401,
            error_message="Refresh token not found or revoked",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked",
        )

    user_id = payload.get("sub")
    user = auth_service.get_user_by_id(user_id)

    if not user or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new access token
    access_token = create_access_token(data={"sub": user["id"], "username": user["username"]})

    # Log token refresh
    audit_logger.log(
        action="TOKEN_REFRESH",
        user_id=user["id"],
        username=user["username"],
        ip_address=request.client.host if request.client else None,
        request_method="POST",
        request_path=request.url.path,
        response_status=200,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=token_data.refresh_token,  # Return same refresh token
    )


@router.post("/logout")
async def logout(
    token_data: RefreshTokenRequest,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> dict[str, Any]:
    """Logout user by revoking refresh token."""
    # Revoke refresh token
    auth_service.revoke_refresh_token(token_data.refresh_token)

    # Log logout
    audit_logger.log(
        action="LOGOUT",
        ip_address=request.client.host if request.client else None,
        request_method="POST",
        request_path=request.url.path,
        response_status=200,
    )

    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(
    request: Request,
) -> dict[str, Any]:
    """Get current user information."""
    # User is attached to request state by authentication middleware
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return request.state.user

