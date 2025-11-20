# Performance Optimizations Guide

This document describes the performance optimization features in AETHERA, including tiling/chunking for large AOIs and Dask-Geopandas integration.

## Overview

AETHERA includes two main performance optimization features:

1. **Tiling/Chunking**: Automatically splits large AOIs into smaller tiles for processing
2. **Dask-Geopandas**: Parallel processing for geospatial operations using distributed computing

## Configuration

Performance optimizations are configured via environment variables:

```bash
# Enable/disable Dask-Geopandas
ENABLE_DASK=false

# Enable/disable automatic tiling
ENABLE_TILING=false

# Tile size in kilometers (default: 50.0)
TILE_SIZE_KM=50.0

# AOI size threshold for auto-tiling in km² (default: 1000.0)
AOI_SIZE_THRESHOLD_KM2=1000.0

# Number of Dask workers (None = auto-detect)
DASK_WORKERS=4
```

## Tiling/Chunking for Large AOIs

### When to Use

Tiling is automatically enabled when:
- `ENABLE_TILING=true` is set
- AOI area exceeds `AOI_SIZE_THRESHOLD_KM2` (default: 1000 km²)

### How It Works

1. **Tile Generation**: The AOI is divided into square tiles of size `TILE_SIZE_KM`
2. **Overlap**: Tiles can have overlap to avoid edge effects (default: 1 km)
3. **Processing**: Each tile is processed independently
4. **Merging**: Results from all tiles are merged into a single GeoDataFrame
5. **Deduplication**: Overlapping results are deduplicated

### Example Usage

```python
from backend.src.utils.tiling import create_tiles, process_tiles
from backend.src.utils.geometry import load_aoi

# Load AOI
aoi = load_aoi("path/to/aoi.geojson", "EPSG:3035")

# Create tiles manually
for tile in create_tiles(aoi, tile_size_km=50.0, overlap_km=1.0):
    # Process each tile
    process_tile(tile)

# Or use process_tiles helper
def process_dataset(tile_gdf):
    # Your processing logic here
    return processed_gdf

results = process_tiles(
    aoi,
    process_dataset,
    tile_size_km=50.0,
    overlap_km=1.0,
    merge_results=True
)
```

### Benefits

- **Memory Efficiency**: Processes smaller chunks, reducing memory usage
- **Fault Tolerance**: If one tile fails, others can still succeed
- **Progress Tracking**: Can track progress per tile
- **Parallelization**: Tiles can be processed in parallel (with Dask)

### Limitations

- **Edge Effects**: Features crossing tile boundaries may be duplicated (handled by overlap)
- **Overhead**: Tile generation and merging add some overhead
- **Complex Geometries**: Very complex geometries may not tile efficiently

## Dask-Geopandas Integration

### Installation

Dask-Geopandas is an optional dependency. Install it with:

```bash
pip install -e ".[performance]"
```

Or manually:

```bash
pip install dask dask-geopandas distributed
```

### When to Use

Dask-Geopandas is useful for:
- Large datasets (>100k features)
- Complex geospatial operations
- Multiple parallel operations
- When you have multiple CPU cores available

### How It Works

1. **Partitioning**: GeoDataFrames are split into partitions
2. **Distributed Processing**: Each partition is processed on a separate worker
3. **Automatic Coordination**: Dask coordinates the distributed computation
4. **Result Collection**: Results are automatically collected and merged

### Example Usage

```python
from backend.src.utils.dask_geopandas import DaskGeoPandasWrapper
from pathlib import Path
import geopandas as gpd

# Create wrapper
with DaskGeoPandasWrapper(n_workers=4) as dask_wrapper:
    if dask_wrapper.is_available():
        # Load dataset
        aoi = gpd.read_file("path/to/aoi.geojson")
        
        # Parallel clip
        clipped = dask_wrapper.clip_parallel(
            Path("path/to/dataset.gpkg"),
            aoi
        )
        
        # Parallel apply
        def process_partition(gdf):
            # Your processing logic
            return gdf.buffer(1000)
        
        result = dask_wrapper.apply_parallel(
            clipped,
            process_partition,
            npartitions=8
        )
```

### Benefits

- **Parallel Processing**: Utilizes multiple CPU cores
- **Scalability**: Can scale to clusters for very large datasets
- **Memory Efficiency**: Processes data in chunks
- **Automatic Optimization**: Dask optimizes computation graphs

### Limitations

- **Overhead**: Setup overhead for small datasets
- **Memory**: Each worker needs memory for its partition
- **Complexity**: More complex than standard GeoPandas
- **Dependencies**: Requires additional packages

## Integration with GIS Handler

The `GISHandler` class automatically uses optimizations when enabled:

```python
from backend.src.gis_handler import GISHandler
from pathlib import Path
import geopandas as gpd

gis = GISHandler(Path("output"))

# This will automatically use tiling or Dask if enabled
aoi = gpd.read_file("aoi.geojson")
clipped = gis.clip_vector(
    Path("dataset.gpkg"),
    aoi,
    "output.gpkg"
)
```

The handler will:
1. Check if Dask is enabled and available → use parallel clipping
2. Check if tiling is needed → use tiled processing
3. Fall back to standard clipping if optimizations fail

## Performance Tuning

### Tiling Parameters

- **Tile Size**: Smaller tiles = more parallelism but more overhead
  - Recommended: 25-100 km depending on dataset density
- **Overlap**: More overlap = fewer edge effects but more duplicate processing
  - Recommended: 1-5 km depending on feature size
- **Threshold**: Lower threshold = more aggressive tiling
  - Recommended: 500-2000 km² depending on available memory

### Dask Parameters

- **Workers**: More workers = more parallelism but more memory usage
  - Recommended: Number of CPU cores
- **Partitions**: More partitions = better load balancing but more overhead
  - Recommended: ~10k features per partition

### Monitoring

Use observability features to monitor performance:

```python
from backend.src.observability.performance import measure_operation

with measure_operation("clip_vector") as monitor:
    result = gis.clip_vector(dataset_path, aoi, "output.gpkg")
    monitor.record_metric("features", len(result))
    monitor.record_metric("tiles_used", tiles_count)
```

## Best Practices

1. **Start with Standard Processing**: Only enable optimizations when needed
2. **Monitor Memory Usage**: Large datasets can consume significant memory
3. **Test on Sample Data**: Verify optimizations work correctly before full runs
4. **Adjust Thresholds**: Tune thresholds based on your typical AOI sizes
5. **Use Caching**: Combine with dataset caching for maximum efficiency
6. **Error Handling**: Always have fallback to standard processing

## Troubleshooting

### Tiling Issues

- **Too Many Tiles**: Increase `TILE_SIZE_KM`
- **Edge Effects**: Increase `overlap_km` parameter
- **Memory Issues**: Reduce tile size or enable Dask

### Dask Issues

- **Import Errors**: Install with `pip install dask-geopandas`
- **Worker Failures**: Check available memory and reduce workers
- **Slow Performance**: May not be beneficial for small datasets

## Examples

### Example 1: Large AOI Processing

```python
# Enable tiling for large AOI
import os
os.environ["ENABLE_TILING"] = "true"
os.environ["AOI_SIZE_THRESHOLD_KM2"] = "500.0"
os.environ["TILE_SIZE_KM"] = "50.0"

from backend.src.gis_handler import GISHandler
gis = GISHandler(Path("output"))
clipped = gis.clip_vector(dataset_path, large_aoi, "output.gpkg")
```

### Example 2: Parallel Processing

```python
# Enable Dask for parallel processing
import os
os.environ["ENABLE_DASK"] = "true"
os.environ["DASK_WORKERS"] = "8"

from backend.src.utils.dask_geopandas import DaskGeoPandasWrapper
with DaskGeoPandasWrapper() as dask:
    result = dask.clip_parallel(dataset_path, aoi)
```

### Example 3: Combined Optimizations

```python
# Use both tiling and Dask
import os
os.environ["ENABLE_TILING"] = "true"
os.environ["ENABLE_DASK"] = "true"

# Tiling will be used for large AOIs
# Dask will be used for parallel tile processing
from backend.src.gis_handler import GISHandler
gis = GISHandler(Path("output"))
clipped = gis.clip_vector(dataset_path, large_aoi, "output.gpkg")
```

