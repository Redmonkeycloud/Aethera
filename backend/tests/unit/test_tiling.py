"""Unit tests for tiling utilities."""

from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import box

from src.utils.tiling import create_tiles, process_tiles, should_tile


@pytest.fixture
def small_aoi():
    """Create a small AOI for testing."""
    return gpd.GeoDataFrame(
        geometry=[box(0, 0, 10000, 10000)],  # 10km x 10km
        crs="EPSG:3035",
    )


@pytest.fixture
def large_aoi():
    """Create a large AOI for testing."""
    return gpd.GeoDataFrame(
        geometry=[box(0, 0, 200000, 200000)],  # 200km x 200km = 40,000 km²
        crs="EPSG:3035",
    )


def test_create_tiles(small_aoi):
    """Test tile creation."""
    tiles = list(create_tiles(small_aoi, tile_size_km=5.0))
    assert len(tiles) > 0
    for tile in tiles:
        assert not tile.empty
        assert "tile_id" in tile.columns
        assert "tile_x" in tile.columns
        assert "tile_y" in tile.columns


def test_create_tiles_with_overlap(small_aoi):
    """Test tile creation with overlap."""
    tiles = list(create_tiles(small_aoi, tile_size_km=5.0, overlap_km=1.0))
    assert len(tiles) > 0


def test_should_tile(small_aoi, large_aoi, monkeypatch):
    """Test should_tile function."""
    # Test with small AOI (should not tile)
    monkeypatch.setenv("ENABLE_TILING", "true")
    monkeypatch.setenv("AOI_SIZE_THRESHOLD_KM2", "1000.0")
    from src.config.base_settings import settings
    settings.enable_tiling = True
    settings.aoi_size_threshold_km2 = 1000.0
    
    assert not should_tile(small_aoi)
    
    # Test with large AOI (should tile)
    assert should_tile(large_aoi)


def test_process_tiles(small_aoi):
    """Test process_tiles function."""
    def process_func(tile_gdf):
        # Simple processing: just return the tile
        return tile_gdf

    results = process_tiles(
        small_aoi,
        process_func,
        tile_size_km=5.0,
        merge_results=True,
    )
    
    assert isinstance(results, gpd.GeoDataFrame)
    assert not results.empty


def test_process_tiles_no_merge(small_aoi):
    """Test process_tiles without merging."""
    def process_func(tile_gdf):
        return tile_gdf

    results = process_tiles(
        small_aoi,
        process_func,
        tile_size_km=5.0,
        merge_results=False,
    )
    
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(r, gpd.GeoDataFrame) for r in results)

