"""Celery application configuration."""

from __future__ import annotations

import sys

from celery import Celery

from ..config.base_settings import settings

celery_app = Celery(
    "aethera",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Windows-specific configuration
# IMPORTANT: Windows does not support prefork pool (multiprocessing)
# Must use 'solo' pool on Windows, which runs tasks in the main process
worker_pool = "solo" if sys.platform == "win32" else "prefork"

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 30 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    worker_pool=worker_pool,  # Use solo pool on Windows, prefork on Unix
    # Force solo pool on Windows - this prevents any prefork attempts
    worker_disable_rate_limits=False,
)

# Additional Windows-specific settings
if sys.platform == "win32":
    # Disable prefork-related settings on Windows
    celery_app.conf.worker_pool = "solo"
    celery_app.conf.worker_max_tasks_per_child = None  # Not applicable for solo pool

