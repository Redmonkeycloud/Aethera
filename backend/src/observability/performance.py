"""Performance monitoring utilities."""

from __future__ import annotations

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Generator

from ..logging_utils import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self, name: str) -> None:
        """
        Initialize performance monitor.

        Args:
            name: Monitor name/identifier
        """
        self.name = name
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.metrics: dict[str, Any] = {}

    def start(self) -> None:
        """Start monitoring."""
        self.start_time = time.time()
        self.metrics = {}

    def stop(self) -> float:
        """
        Stop monitoring and return duration.

        Returns:
            Duration in seconds
        """
        if self.start_time is None:
            raise ValueError("Monitor not started")
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        return duration

    def record_metric(self, key: str, value: Any) -> None:
        """
        Record a custom metric.

        Args:
            key: Metric key
            value: Metric value
        """
        self.metrics[key] = value

    def get_duration(self) -> float:
        """
        Get elapsed duration.

        Returns:
            Duration in seconds
        """
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    def log_summary(self, level: str = "info") -> None:
        """Log performance summary."""
        duration = self.get_duration()
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(
            "Performance [%s]: duration=%.3fs, metrics=%s",
            self.name,
            duration,
            self.metrics,
        )

    @contextmanager
    def measure(self) -> Generator[None, None, None]:
        """
        Context manager for measuring performance.

        Yields:
            None
        """
        self.start()
        try:
            yield
        finally:
            duration = self.stop()
            self.log_summary()


def measure_time(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.

    Args:
        func: Function to measure

    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        monitor = PerformanceMonitor(f"{func.__module__}.{func.__name__}")
        monitor.start()
        try:
            result = func(*args, **kwargs)
            duration = monitor.stop()
            logger.debug("%s took %.3f seconds", func.__name__, duration)
            return result
        except Exception as e:
            duration = monitor.stop()
            logger.warning("%s failed after %.3f seconds: %s", func.__name__, duration, e)
            raise

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        monitor = PerformanceMonitor(f"{func.__module__}.{func.__name__}")
        monitor.start()
        try:
            result = await func(*args, **kwargs)
            duration = monitor.stop()
            logger.debug("%s took %.3f seconds", func.__name__, duration)
            return result
        except Exception as e:
            duration = monitor.stop()
            logger.warning("%s failed after %.3f seconds: %s", func.__name__, duration, e)
            raise

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper


@contextmanager
def measure_operation(name: str) -> Generator[PerformanceMonitor, None, None]:
    """
    Context manager for measuring an operation.

    Args:
        name: Operation name

    Yields:
        PerformanceMonitor instance
    """
    monitor = PerformanceMonitor(name)
    monitor.start()
    try:
        yield monitor
    finally:
        monitor.stop()
        monitor.log_summary()

