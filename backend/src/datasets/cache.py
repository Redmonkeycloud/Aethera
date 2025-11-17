"""Dataset caching mechanism for geospatial datasets."""

from __future__ import annotations

import hashlib
import json
import pickle
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import geopandas as gpd

from ..logging_utils import get_logger


logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Metadata for a cached dataset."""

    file_path: Path
    cache_key: str
    cached_at: datetime
    file_mtime: float
    size_bytes: int
    crs: str | None = None
    feature_count: int = 0


class DatasetCache:
    """In-memory and optional disk-based cache for geospatial datasets."""

    def __init__(
        self,
        max_memory_size_mb: int = 500,
        cache_dir: Path | None = None,
        ttl_hours: int = 24,
    ) -> None:
        """
        Initialize dataset cache.

        Args:
            max_memory_size_mb: Maximum memory cache size in MB
            cache_dir: Optional directory for persistent disk cache
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.max_memory_size_bytes = max_memory_size_mb * 1024 * 1024
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        self._memory_cache: dict[str, tuple[gpd.GeoDataFrame, CacheEntry]] = {}
        self._current_size_bytes = 0

        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Dataset cache initialized with disk cache at %s", self.cache_dir)

    def _generate_cache_key(self, file_path: Path, **kwargs: Any) -> str:
        """Generate a cache key from file path and optional parameters."""
        key_parts = [str(file_path.resolve())]
        if kwargs:
            key_parts.append(json.dumps(kwargs, sort_keys=True))
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the disk cache path for a given cache key."""
        if not self.cache_dir:
            raise ValueError("Disk cache not enabled")
        return self.cache_dir / f"{cache_key}.pkl"

    def _get_metadata_path(self, cache_key: str) -> Path:
        """Get the metadata path for a cache entry."""
        if not self.cache_dir:
            raise ValueError("Disk cache not enabled")
        return self.cache_dir / f"{cache_key}.meta.json"

    def _estimate_size(self, gdf: gpd.GeoDataFrame) -> int:
        """Estimate memory size of a GeoDataFrame in bytes."""
        # Rough estimation: geometry + attributes
        try:
            return gdf.memory_usage(deep=True).sum()
        except Exception:
            # Fallback: estimate based on feature count
            return len(gdf) * 10000  # ~10KB per feature estimate

    def _is_entry_valid(self, entry: CacheEntry, file_path: Path) -> bool:
        """Check if a cache entry is still valid."""
        if not file_path.exists():
            return False

        # Check if file has been modified
        current_mtime = file_path.stat().st_mtime
        if current_mtime != entry.file_mtime:
            return False

        # Check TTL
        age = datetime.now() - entry.cached_at
        if age > self.ttl:
            return False

        return True

    def _evict_lru(self) -> None:
        """Evict least recently used entries to free memory."""
        if not self._memory_cache:
            return

        # Sort by cached_at (oldest first)
        sorted_entries = sorted(
            self._memory_cache.items(),
            key=lambda x: x[1][1].cached_at,
        )

        # Remove oldest entries until we're under the limit
        for cache_key, (gdf, entry) in sorted_entries:
            if self._current_size_bytes <= self.max_memory_size_bytes:
                break

            size = self._estimate_size(gdf)
            self._current_size_bytes -= size
            del self._memory_cache[cache_key]
            logger.debug("Evicted cache entry %s (size: %d bytes)", cache_key[:8], size)

    def get(
        self,
        file_path: Path,
        loader: Callable[[Path], gpd.GeoDataFrame],
        **loader_kwargs: Any,
    ) -> gpd.GeoDataFrame:
        """
        Get a dataset from cache or load it if not cached.

        Args:
            file_path: Path to the dataset file
            loader: Function to load the dataset if not in cache
            **loader_kwargs: Additional arguments to pass to loader

        Returns:
            Loaded GeoDataFrame
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        cache_key = self._generate_cache_key(file_path, **loader_kwargs)
        file_mtime = file_path.stat().st_mtime

        # Check memory cache
        if cache_key in self._memory_cache:
            gdf, entry = self._memory_cache[cache_key]
            if self._is_entry_valid(entry, file_path):
                logger.debug("Cache hit (memory): %s", file_path.name)
                # Update access time
                entry.cached_at = datetime.now()
                return gdf
            else:
                # Invalid entry, remove it
                size = self._estimate_size(gdf)
                self._current_size_bytes -= size
                del self._memory_cache[cache_key]

        # Check disk cache
        if self.cache_dir:
            cache_path = self._get_cache_path(cache_key)
            metadata_path = self._get_metadata_path(cache_key)

            if cache_path.exists() and metadata_path.exists():
                try:
                    with open(metadata_path, encoding="utf-8") as f:
                        metadata = json.load(f)
                    entry = CacheEntry(
                        file_path=Path(metadata["file_path"]),
                        cache_key=metadata["cache_key"],
                        cached_at=datetime.fromisoformat(metadata["cached_at"]),
                        file_mtime=metadata["file_mtime"],
                        size_bytes=metadata["size_bytes"],
                        crs=metadata.get("crs"),
                        feature_count=metadata.get("feature_count", 0),
                    )

                    if self._is_entry_valid(entry, file_path):
                        logger.debug("Cache hit (disk): %s", file_path.name)
                        with open(cache_path, "rb") as f:
                            gdf = pickle.load(f)

                        # Promote to memory cache if there's space
                        size = self._estimate_size(gdf)
                        if (
                            self._current_size_bytes + size
                            <= self.max_memory_size_bytes
                        ):
                            self._memory_cache[cache_key] = (gdf, entry)
                            self._current_size_bytes += size

                        return gdf
                except Exception as exc:
                    logger.warning("Failed to load from disk cache: %s", exc)
                    # Clean up corrupted cache files
                    cache_path.unlink(missing_ok=True)
                    metadata_path.unlink(missing_ok=True)

        # Cache miss - load the dataset
        logger.debug("Cache miss: loading %s", file_path.name)
        gdf = loader(file_path, **loader_kwargs)

        # Create cache entry
        size = self._estimate_size(gdf)
        entry = CacheEntry(
            file_path=file_path,
            cache_key=cache_key,
            cached_at=datetime.now(),
            file_mtime=file_mtime,
            size_bytes=size,
            crs=str(gdf.crs) if gdf.crs else None,
            feature_count=len(gdf),
        )

        # Add to memory cache
        self._current_size_bytes += size
        if self._current_size_bytes > self.max_memory_size_bytes:
            self._evict_lru()

        if self._current_size_bytes + size <= self.max_memory_size_bytes:
            self._memory_cache[cache_key] = (gdf, entry)

        # Save to disk cache if enabled
        if self.cache_dir:
            try:
                cache_path = self._get_cache_path(cache_key)
                metadata_path = self._get_metadata_path(cache_key)

                with open(cache_path, "wb") as f:
                    pickle.dump(gdf, f)

                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "file_path": str(entry.file_path),
                            "cache_key": entry.cache_key,
                            "cached_at": entry.cached_at.isoformat(),
                            "file_mtime": entry.file_mtime,
                            "size_bytes": entry.size_bytes,
                            "crs": entry.crs,
                            "feature_count": entry.feature_count,
                        },
                        f,
                        indent=2,
                    )

                logger.debug("Saved to disk cache: %s", file_path.name)
            except Exception as exc:
                logger.warning("Failed to save to disk cache: %s", exc)

        return gdf

    def clear(self, memory_only: bool = False) -> None:
        """
        Clear the cache.

        Args:
            memory_only: If True, only clear memory cache, not disk cache
        """
        self._memory_cache.clear()
        self._current_size_bytes = 0

        if not memory_only and self.cache_dir:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink(missing_ok=True)
            for meta_file in self.cache_dir.glob("*.meta.json"):
                meta_file.unlink(missing_ok=True)
            logger.info("Cache cleared (memory and disk)")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "memory_entries": len(self._memory_cache),
            "memory_size_mb": round(self._current_size_bytes / (1024 * 1024), 2),
            "max_memory_size_mb": round(
                self.max_memory_size_bytes / (1024 * 1024), 2
            ),
            "disk_cache_enabled": self.cache_dir is not None,
            "disk_cache_dir": str(self.cache_dir) if self.cache_dir else None,
            "ttl_hours": self.ttl.total_seconds() / 3600,
        }

