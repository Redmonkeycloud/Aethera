"""OpenTelemetry tracing setup and configuration."""

from __future__ import annotations

import asyncio
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode

# Conditional imports for instrumentation and exporters
try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
except ImportError:
    try:
        from opentelemetry.exporter.otlp.proto.http import OTLPSpanExporter
    except ImportError:
        OTLPSpanExporter = None  # type: ignore

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:
    FastAPIInstrumentor = None  # type: ignore

try:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
except ImportError:
    HTTPXClientInstrumentor = None  # type: ignore

try:
    from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
except ImportError:
    PsycopgInstrumentor = None  # type: ignore

try:
    from opentelemetry.instrumentation.redis import RedisInstrumentor
except ImportError:
    RedisInstrumentor = None  # type: ignore

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
            if OTLPSpanExporter is None:
                logger.warning("OTLP exporter not available. Using console exporter instead.")
                console_exporter = ConsoleSpanExporter()
                tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
                logger.info("Tracing configured with console exporter (OTLP not available)")
            else:
                try:
                    otlp_exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
                    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                    logger.info("Tracing configured with OTLP exporter: %s", settings.otlp_endpoint)
                except Exception as e:
                    logger.warning("Failed to create OTLP exporter: %s. Using console exporter.", e)
                    console_exporter = ConsoleSpanExporter()
                    tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
                    logger.info("Tracing configured with console exporter")
        else:
            # Export to console (for development)
            console_exporter = ConsoleSpanExporter()
            tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("Tracing configured with console exporter")

        # Instrument libraries
        if FastAPIInstrumentor is not None:
            try:
                FastAPIInstrumentor().instrument()
                logger.debug("FastAPI instrumentation enabled")
            except Exception as e:
                logger.warning("Failed to instrument FastAPI: %s", e)
        else:
            logger.debug("FastAPI instrumentation not available")

        if HTTPXClientInstrumentor is not None:
            try:
                HTTPXClientInstrumentor().instrument()
                logger.debug("HTTPX instrumentation enabled")
            except Exception as e:
                logger.warning("Failed to instrument HTTPX: %s", e)
        else:
            logger.debug("HTTPX instrumentation not available")

        if PsycopgInstrumentor is not None:
            try:
                PsycopgInstrumentor().instrument()
                logger.debug("Psycopg instrumentation enabled")
            except Exception as e:
                logger.warning("Failed to instrument Psycopg: %s", e)
        else:
            logger.debug("Psycopg instrumentation not available")

        if RedisInstrumentor is not None:
            try:
                RedisInstrumentor().instrument()
                logger.debug("Redis instrumentation enabled")
            except Exception as e:
                logger.warning("Failed to instrument Redis: %s", e)
        else:
            logger.debug("Redis instrumentation not available")

        try:
            from opentelemetry.instrumentation.celery import CeleryInstrumentor

            CeleryInstrumentor().instrument()
            logger.debug("Celery instrumentation enabled")
        except ImportError:
            logger.debug("Celery instrumentation not available (optional)")
        except Exception as e:
            logger.warning("Failed to instrument Celery: %s", e)

        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor

            RequestsInstrumentor().instrument()
            logger.debug("Requests instrumentation enabled")
        except ImportError:
            logger.debug("Requests instrumentation not available (optional)")
        except Exception as e:
            logger.warning("Failed to instrument Requests: %s", e)

        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

            SQLAlchemyInstrumentor().instrument()
            logger.debug("SQLAlchemy instrumentation enabled")
        except ImportError:
            logger.debug("SQLAlchemy instrumentation not available (optional)")
        except Exception as e:
            logger.warning("Failed to instrument SQLAlchemy: %s", e)

        # Instrument FastAPI app if provided
        if app is not None and FastAPIInstrumentor is not None:
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

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            span_name = name or f"{func.__module__}.{func.__name__}"
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
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
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator

