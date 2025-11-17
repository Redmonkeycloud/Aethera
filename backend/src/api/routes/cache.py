"""API routes for dataset cache management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...config.base_settings import settings
from ...datasets.catalog import DatasetCatalog

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats() -> dict[str, Any]:
    """Get dataset cache statistics."""
    catalog = DatasetCatalog(settings.data_sources_dir)
    stats = catalog.get_cache_stats()
    if stats is None:
        return {"enabled": False, "message": "Dataset cache is not enabled"}
    return {"enabled": True, **stats}


@router.post("/clear")
async def clear_cache(memory_only: bool = False) -> dict[str, str]:
    """Clear the dataset cache."""
    catalog = DatasetCatalog(settings.data_sources_dir)
    catalog.clear_cache(memory_only=memory_only)
    return {
        "status": "success",
        "message": f"Cache cleared ({'memory only' if memory_only else 'memory and disk'})",
    }

