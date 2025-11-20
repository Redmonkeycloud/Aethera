"""Prometheus metrics setup and collection."""

from __future__ import annotations

import asyncio
import time
from functools import wraps
from typing import Any, Callable

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    REGISTRY,
    generate_latest,
    start_http_server,
)
from prometheus_client.core import CollectorRegistry

from ..config.base_settings import settings
from ..logging_utils import get_logger

logger = get_logger(__name__)

# Global metrics registry
_metrics_registry: CollectorRegistry | None = None


def setup_metrics() -> None:
    """Set up Prometheus metrics and start metrics server."""
    global _metrics_registry

    if not settings.enable_metrics:
        logger.info("Metrics are disabled")
        return

    try:
        # Use default registry
        _metrics_registry = REGISTRY

        # Start metrics HTTP server
        try:
            start_http_server(settings.metrics_port)
            logger.info("Prometheus metrics server started on port %d", settings.metrics_port)
        except OSError as e:
            logger.warning("Failed to start metrics server on port %d: %s", settings.metrics_port, e)

        logger.info("Prometheus metrics setup complete")

    except ImportError:
        logger.warning("Prometheus client not available. Metrics disabled.")
    except Exception as e:
        logger.error("Failed to setup metrics: %s", e, exc_info=True)


def get_metrics_registry() -> CollectorRegistry:
    """Get the metrics registry."""
    if _metrics_registry is None:
        return REGISTRY
    return _metrics_registry


def get_metrics() -> bytes:
    """Get metrics in Prometheus format."""
    return generate_latest(get_metrics_registry())


# Application metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000),
)

celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"],
)

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)

database_queries_total = Counter(
    "database_queries_total",
    "Total database queries",
    ["operation", "table"],
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

geospatial_operations_total = Counter(
    "geospatial_operations_total",
    "Total geospatial operations",
    ["operation_type"],
)

geospatial_operation_duration_seconds = Histogram(
    "geospatial_operation_duration_seconds",
    "Geospatial operation duration in seconds",
    ["operation_type"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0),
)

active_runs = Gauge(
    "active_runs",
    "Number of active analysis runs",
)

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

service_info = Info(
    "service_info",
    "Service information",
)


def record_http_request(method: str, endpoint: str, status_code: int, duration: float, size: int = 0) -> None:
    """Record HTTP request metrics."""
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    if size > 0:
        http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(size)


def record_celery_task(task_name: str, status: str, duration: float) -> None:
    """Record Celery task metrics."""
    celery_tasks_total.labels(task_name=task_name, status=status).inc()
    celery_task_duration_seconds.labels(task_name=task_name).observe(duration)


def record_database_query(operation: str, table: str, duration: float) -> None:
    """Record database query metrics."""
    database_queries_total.labels(operation=operation, table=table).inc()
    database_query_duration_seconds.labels(operation=operation, table=table).observe(duration)


def record_geospatial_operation(operation_type: str, duration: float) -> None:
    """Record geospatial operation metrics."""
    geospatial_operations_total.labels(operation_type=operation_type).inc()
    geospatial_operation_duration_seconds.labels(operation_type=operation_type).observe(duration)


def record_cache_hit(cache_type: str) -> None:
    """Record cache hit."""
    cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str) -> None:
    """Record cache miss."""
    cache_misses_total.labels(cache_type=cache_type).inc()


def metrics_middleware(func: Callable) -> Callable:
    """
    Decorator to automatically record metrics for a function.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            # Record metrics based on function name
            func_name = func.__name__
            if "query" in func_name.lower() or "database" in func_name.lower():
                record_database_query("query", "unknown", duration)
            elif "geospatial" in func_name.lower() or "gis" in func_name.lower():
                record_geospatial_operation(func_name, duration)
            return result
        except Exception:
            duration = time.time() - start_time
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            # Record metrics based on function name
            func_name = func.__name__
            if "query" in func_name.lower() or "database" in func_name.lower():
                record_database_query("query", "unknown", duration)
            elif "geospatial" in func_name.lower() or "gis" in func_name.lower():
                record_geospatial_operation(func_name, duration)
            return result
        except Exception:
            duration = time.time() - start_time
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

