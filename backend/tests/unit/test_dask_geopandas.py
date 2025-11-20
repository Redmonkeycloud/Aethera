"""Unit tests for Dask-Geopandas integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import geopandas as gpd
import pytest
from shapely.geometry import box

from src.utils.dask_geopandas import DaskGeoPandasWrapper, DASK_AVAILABLE


@pytest.fixture
def sample_aoi():
    """Create a sample AOI for testing."""
    return gpd.GeoDataFrame(
        geometry=[box(0, 0, 10000, 10000)],
        crs="EPSG:3035",
    )


def test_dask_wrapper_initialization():
    """Test Dask wrapper initialization."""
    wrapper = DaskGeoPandasWrapper(n_workers=2)
    assert wrapper.n_workers == 2
    assert wrapper.client is None
    assert wrapper._cluster is None


def test_dask_wrapper_context_manager(monkeypatch):
    """Test Dask wrapper as context manager."""
    if not DASK_AVAILABLE:
        pytest.skip("Dask-Geopandas not available")
    
    monkeypatch.setenv("ENABLE_DASK", "true")
    from src.config.base_settings import settings
    settings.enable_dask = True
    
    wrapper = DaskGeoPandasWrapper()
    with wrapper:
        if wrapper.is_available():
            assert wrapper.client is not None
        else:
            # Dask might not be available, that's okay
            assert wrapper.client is None


def test_is_available(monkeypatch):
    """Test is_available method."""
    monkeypatch.setenv("ENABLE_DASK", "false")
    from src.config.base_settings import settings
    settings.enable_dask = False
    
    wrapper = DaskGeoPandasWrapper()
    assert not wrapper.is_available()


def test_to_dask_geodataframe(sample_aoi, monkeypatch):
    """Test conversion to Dask-GeoDataFrame."""
    if not DASK_AVAILABLE:
        pytest.skip("Dask-Geopandas not available")
    
    monkeypatch.setenv("ENABLE_DASK", "true")
    from src.config.base_settings import settings
    settings.enable_dask = True
    
    wrapper = DaskGeoPandasWrapper()
    with wrapper:
        if wrapper.is_available():
            dgdf = wrapper.to_dask_geodataframe(sample_aoi, npartitions=2)
            # Should return either Dask-GeoDataFrame or original GeoDataFrame
            assert dgdf is not None
        else:
            # If Dask not available, should return original
            dgdf = wrapper.to_dask_geodataframe(sample_aoi)
            assert isinstance(dgdf, gpd.GeoDataFrame)


def test_apply_parallel(sample_aoi, monkeypatch):
    """Test parallel apply."""
    if not DASK_AVAILABLE:
        pytest.skip("Dask-Geopandas not available")
    
    monkeypatch.setenv("ENABLE_DASK", "true")
    from src.config.base_settings import settings
    settings.enable_dask = True
    
    def process_func(gdf):
        gdf["processed"] = True
        return gdf
    
    wrapper = DaskGeoPandasWrapper()
    with wrapper:
        result = wrapper.apply_parallel(sample_aoi, process_func)
        assert isinstance(result, gpd.GeoDataFrame)
        assert "processed" in result.columns or len(result) == 0

