"""Integration tests for Celery workers."""

from __future__ import annotations

import pytest

from src.workers.celery_app import celery_app


@pytest.mark.integration
@pytest.mark.celery
class TestCeleryWorkers:
    """Test Celery worker functionality."""

    def test_celery_app_initialization(self) -> None:
        """Test Celery app is properly initialized."""
        assert celery_app is not None
        assert celery_app.conf.broker_url is not None

    @pytest.mark.skip(reason="Requires Redis to be running")
    def test_task_registration(self) -> None:
        """Test that tasks are properly registered."""
        # Check that tasks are registered
        registered_tasks = celery_app.tasks.keys()
        assert len(registered_tasks) > 0

