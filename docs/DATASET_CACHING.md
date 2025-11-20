# Dataset Caching Mechanism

AETHERA includes a comprehensive dataset caching system to improve performance by avoiding redundant dataset loads.

## Overview

The dataset cache provides:
- **In-memory caching**: Fast access to recently used datasets
- **Optional disk caching**: Persistent cache across application restarts
- **Automatic invalidation**: Cache entries expire based on file modification time and TTL
- **Memory management**: LRU eviction when memory limits are reached

## Configuration

Cache settings are configured in `backend/src/config/base_settings.py` and can be overridden via environment variables:

```bash
# Enable/disable caching (default: true)
DATASET_CACHE_ENABLED=true

# Cache directory (default: ../data/cache)
DATASET_CACHE_DIR=../data/cache

# Maximum memory cache size in MB (default: 500)
DATASET_CACHE_MAX_MB=500

# Cache TTL in hours (default: 24)
DATASET_CACHE_TTL_HOURS=24
```

## How It Works

### Cache Key Generation

Cache keys are generated from:
- File path (absolute, resolved)
- Optional parameters (e.g., bounding box, layer name)

This ensures that different queries for the same file with different parameters get separate cache entries.

### Cache Validation

Cache entries are considered valid if:
1. The source file still exists
2. The file modification time matches the cached entry
3. The entry hasn't exceeded its TTL (time-to-live)

### Memory Management

When the memory cache exceeds the configured limit:
- Least Recently Used (LRU) entries are evicted
- Eviction continues until the cache is under the limit
- Disk cache entries are not affected by memory eviction

## Usage

### Automatic Caching

The cache is automatically used when loading datasets through `DatasetCatalog`:

```python
from backend.src.datasets.catalog import DatasetCatalog
from backend.src.config.base_settings import settings

catalog = DatasetCatalog(settings.data_sources_dir)

# This will use cache if available
corine_path = catalog.corine()

# Load with caching and optional bbox filtering
gdf = catalog.load_dataset("corine", bbox=(minx, miny, maxx, maxy))
```

### Manual Cache Control

```python
# Get cache statistics
stats = catalog.get_cache_stats()
print(f"Memory cache: {stats['memory_entries']} entries, {stats['memory_size_mb']} MB")

# Clear cache
catalog.clear_cache(memory_only=False)  # Clear both memory and disk
catalog.clear_cache(memory_only=True)   # Clear only memory
```

### API Endpoints

The cache can be managed via REST API:

```bash
# Get cache statistics
curl http://localhost:8000/cache/stats

# Clear cache
curl -X POST http://localhost:8000/cache/clear?memory_only=false
```

## Cache Storage

### Memory Cache

- Stored in application memory
- Fastest access
- Lost on application restart
- Subject to memory limits and LRU eviction

### Disk Cache

- Stored in `DATASET_CACHE_DIR`
- Persists across restarts
- Slower than memory but faster than re-reading files
- Files are stored as pickle format (`.pkl`)
- Metadata stored as JSON (`.meta.json`)

## Performance Benefits

Caching provides significant performance improvements for:
- Large datasets (CORINE, Natura 2000)
- Repeated analyses on the same datasets
- Bounding box queries that are frequently repeated
- Multi-run analyses using the same source data

## Best Practices

1. **Enable caching in production**: Set `DATASET_CACHE_ENABLED=true`
2. **Adjust memory limit**: Based on available RAM and dataset sizes
3. **Set appropriate TTL**: Balance freshness vs. performance
4. **Monitor cache stats**: Use API endpoints to track cache effectiveness
5. **Clear cache when datasets update**: After updating source data files

## Troubleshooting

### Cache Not Working

- Check `DATASET_CACHE_ENABLED` is set to `true`
- Verify cache directory is writable
- Check logs for cache-related warnings

### High Memory Usage

- Reduce `DATASET_CACHE_MAX_MB`
- Clear cache periodically
- Use `memory_only=True` when clearing to keep disk cache

### Stale Data

- Reduce `DATASET_CACHE_TTL_HOURS`
- Clear cache after updating datasets
- Cache automatically invalidates on file modification

