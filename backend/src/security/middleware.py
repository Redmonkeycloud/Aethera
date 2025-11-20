"""Authentication and audit middleware for FastAPI."""

from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..config.base_settings import settings
from ..db.client import DatabaseClient
from .audit import AuditLogger
from .auth import verify_token


# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = {
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/auth/login",
    "/auth/register",
    "/auth/oauth/login",
    "/auth/refresh",
    "/metrics",
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to authenticate requests and attach user to request state."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize authentication middleware.

        Args:
            app: FastAPI application
        """
        super().__init__(app)
        self.db_client = DatabaseClient(settings.postgres_dsn)

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Process request and authenticate if needed.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response
        """
        # Skip authentication for public endpoints
        if request.url.path in PUBLIC_ENDPOINTS or request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
            return await call_next(request)

        # Get authorization header
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract token
        token = authorization.split(" ")[1]

        try:
            # Verify token
            payload = verify_token(token, token_type="access")
            user_id = payload.get("sub")

            if not user_id:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token"},
                )

            # Get user from database
            from .auth import AuthenticationService
            auth_service = AuthenticationService(self.db_client)
            user = auth_service.get_user_by_id(user_id)

            if not user or not user.get("is_active"):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found or inactive"},
                )

            # Attach user to request state
            request.state.user = user
            request.state.user_id = user["id"]

        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Could not validate credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests for audit purposes."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize audit middleware.

        Args:
            app: FastAPI application
        """
        super().__init__(app)
        self.db_client = DatabaseClient(settings.postgres_dsn)
        self.audit_logger = AuditLogger(self.db_client)

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Process request and log for audit.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response
        """
        # Get user from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "user", {}).get("username") if hasattr(request.state, "user") else None

        # Process request
        response = await call_next(request)

        # Log request
        try:
            self.audit_logger.log_request(
                request=request,
                user_id=user_id,
                username=username,
                response_status=response.status_code,
                error_message=None if response.status_code < 400 else "Request failed",
            )
        except Exception:
            # Don't fail request if audit logging fails
            pass

        return response

