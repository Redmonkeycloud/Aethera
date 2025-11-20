"""Celery instrumentation for observability."""

from __future__ import annotations

from ..config.base_settings import settings
from ..logging_utils import get_logger
from .tracing import setup_tracing

logger = get_logger(__name__)


def instrument_celery() -> None:
    """Set up observability for Celery workers."""
    if settings.enable_tracing:
        try:
            setup_tracing()
            logger.info("Celery worker observability enabled")
        except Exception as e:
            logger.warning("Failed to setup Celery observability: %s", e)

