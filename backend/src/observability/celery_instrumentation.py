"""Celery instrumentation for observability."""

from __future__ import annotations

from ..config.base_settings import settings
from ..logging_utils import get_logger

logger = get_logger(__name__)


def instrument_celery() -> None:
    """Set up observability for Celery workers."""
    if settings.enable_tracing:
        try:
            from opentelemetry.instrumentation.celery import CeleryInstrumentor

            CeleryInstrumentor().instrument()
            logger.info("Celery instrumentation enabled")
        except ImportError as e:
            logger.warning("OpenTelemetry Celery instrumentation not available: %s", e)
        except Exception as e:
            logger.warning("Failed to setup Celery instrumentation: %s", e)

