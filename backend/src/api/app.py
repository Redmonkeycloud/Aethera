from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..observability.metrics import record_http_request, setup_metrics
from ..observability.tracing import setup_tracing
from ..config.base_settings import settings
from .routes import biodiversity, governance, layers, observability, projects, reports, runs, tasks


app = FastAPI(title="AETHERA API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Metrics middleware
class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""

    async def dispatch(self, request: Request, call_next):
        import time
        start_time = time.time()
        method = request.method
        path = request.url.path

        # Skip metrics endpoint
        if path == "/metrics":
            return await call_next(request)

        response = await call_next(request)
        duration = time.time() - start_time
        status_code = response.status_code

        # Get request size if available
        content_length = request.headers.get("content-length")
        size = int(content_length) if content_length else 0

        record_http_request(method, path, status_code, duration, size)
        return response


app.add_middleware(MetricsMiddleware)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "AETHERA API",
        "version": "0.1.0",
        "docs": "/docs",
    }


app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(biodiversity.router)
app.include_router(layers.router)
app.include_router(reports.router)
app.include_router(observability.router)
app.include_router(governance.router)


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    from ..observability.metrics import get_metrics
    return Response(content=get_metrics(), media_type="text/plain; version=0.0.4")


# Initialize observability
@app.on_event("startup")
async def startup_event():
    """Initialize observability on startup."""
    try:
        setup_tracing(app)
        setup_metrics()
        from ..observability.metrics import service_info
        service_info.info(
            {
                "version": settings.service_version,
                "environment": settings.environment,
            }
        )
    except Exception as e:
        # Don't fail startup if observability setup fails
        import logging
        logging.getLogger(__name__).warning("Failed to initialize observability: %s", e)

