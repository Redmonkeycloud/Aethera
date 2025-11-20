"""OpenTelemetry tracing setup and configuration."""

from __future__ import annotations

import logging
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from ..config.base_settings import settings
from ..logging_utils import get_logger

logger = get_logger(__name__)


def setup_tracing(app: Any | None = None) -> None:
    """
    Set up OpenTelemetry tracing.

    Args:
        app: Optional FastAPI app instance to instrument
    """
    if not settings.enable_tracing:
        logger.info("Tracing is disabled")
        return

    try:
        # Create resource with service information
        resource = Resource.create(
            {
                "service.name": settings.service_name,
                "service.version": settings.service_version,
                "service.namespace": "aethera",
            }
        )

        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)

        # Add span processors
        if settings.otlp_endpoint:
            # Export to OTLP collector
            otlp_exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
            tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("Tracing configured with OTLP exporter: %s", settings.otlp_endpoint)
        else:
            # Export to console (for development)
            console_exporter = ConsoleSpanExporter()
            tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("Tracing configured with console exporter")

        # Instrument libraries
        try:
            FastAPIInstrumentor().instrument()
            logger.debug("FastAPI instrumentation enabled")
        except Exception as e:
            logger.warning("Failed to instrument FastAPI: %s", e)

        try:
            HTTPXClientInstrumentor().instrument()
            logger.debug("HTTPX instrumentation enabled")
        except Exception as e:
            logger.warning("Failed to instrument HTTPX: %s", e)

        try:
            PsycopgInstrumentor().instrument()
            logger.debug("Psycopg instrumentation enabled")
        except Exception as e:
            logger.warning("Failed to instrument Psycopg: %s", e)

        try:
            RedisInstrumentor().instrument()
            logger.debug("Redis instrumentation enabled")
        except Exception as e:
            logger.warning("Failed to instrument Redis: %s", e)

        # Instrument FastAPI app if provided
        if app is not None:
            try:
                FastAPIInstrumentor.instrument_app(app)
                logger.info("FastAPI app instrumented for tracing")
            except Exception as e:
                logger.warning("Failed to instrument FastAPI app: %s", e)

        logger.info("OpenTelemetry tracing setup complete")

    except ImportError as e:
        logger.warning("OpenTelemetry not available: %s. Tracing disabled.", e)
    except Exception as e:
        logger.error("Failed to setup tracing: %s", e, exc_info=True)


def get_tracer(name: str) -> trace.Tracer:
    """
    Get a tracer instance.

    Args:
        name: Tracer name (usually module name)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def trace_function(name: str | None = None):
    """
    Decorator to trace a function.

    Args:
        name: Optional span name (defaults to function name)

    Returns:
        Decorator function
    """
    def decorator(func):
        from functools import wraps
        import asyncio

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            span_name = name or f"{func.__module__}.{func.__name__}"
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            span_name = name or f"{func.__module__}.{func.__name__}"
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator

