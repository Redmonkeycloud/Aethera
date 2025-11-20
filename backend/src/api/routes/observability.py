"""Observability endpoints for health checks and diagnostics."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ...observability.metrics import get_metrics_registry
from ...observability.performance import PerformanceMonitor
from ...config.base_settings import settings

router = APIRouter(prefix="/observability", tags=["observability"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str
    tracing_enabled: bool
    metrics_enabled: bool


class DiagnosticsResponse(BaseModel):
    """Diagnostics response."""

    service_name: str
    service_version: str
    environment: str
    tracing_enabled: bool
    metrics_enabled: bool
    metrics_port: int


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.service_version,
        tracing_enabled=settings.enable_tracing,
        metrics_enabled=settings.enable_metrics,
    )


@router.get("/diagnostics", response_model=DiagnosticsResponse)
async def diagnostics() -> DiagnosticsResponse:
    """Get service diagnostics."""
    return DiagnosticsResponse(
        service_name=settings.service_name,
        service_version=settings.service_version,
        environment=settings.environment,
        tracing_enabled=settings.enable_tracing,
        metrics_enabled=settings.enable_metrics,
        metrics_port=settings.metrics_port,
    )


@router.get("/metrics/registry")
async def metrics_registry_info() -> dict:
    """Get information about the metrics registry."""
    registry = get_metrics_registry()
    collectors = list(registry._collector_to_names.keys())
    return {
        "collectors_count": len(collectors),
        "collectors": [str(c) for c in collectors[:10]],  # Limit to first 10
    }

