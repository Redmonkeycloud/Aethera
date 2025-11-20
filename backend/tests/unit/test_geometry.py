"""Unit tests for geometry utilities."""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st
from shapely.geometry import Point, Polygon

from src.utils.geometry import load_aoi


@pytest.mark.unit
@pytest.mark.geospatial
class TestGeometryUtils:
    """Test geometry utility functions."""

    def test_load_aoi_from_wkt_point(self, temp_dir: Path) -> None:
        """Test loading AOI from WKT point."""
        wkt = "POINT(10 50)"
        gdf = load_aoi(wkt, "EPSG:4326")
        assert len(gdf) == 1
        assert gdf.crs.to_string() == "EPSG:4326"

    def test_load_aoi_from_wkt_polygon(self, temp_dir: Path) -> None:
        """Test loading AOI from WKT polygon."""
        wkt = "POLYGON((10 50, 11 50, 11 51, 10 51, 10 50))"
        gdf = load_aoi(wkt, "EPSG:4326")
        assert len(gdf) == 1
        assert gdf.crs.to_string() == "EPSG:4326"

    @pytest.mark.hypothesis
    @given(
        lon=st.floats(min_value=-180, max_value=180),
        lat=st.floats(min_value=-90, max_value=90),
    )
    def test_load_aoi_point_property_based(self, lon: float, lat: float) -> None:
        """Property-based test for point loading."""
        wkt = f"POINT({lon} {lat})"
        gdf = load_aoi(wkt, "EPSG:4326")
        assert len(gdf) == 1
        point = gdf.geometry.iloc[0]
        assert isinstance(point, Point)
        assert abs(point.x - lon) < 0.0001
        assert abs(point.y - lat) < 0.0001

    def test_load_aoi_crs_transformation(self, temp_dir: Path) -> None:
        """Test CRS transformation."""
        wkt = "POLYGON((10 50, 11 50, 11 51, 10 51, 10 50))"
        gdf = load_aoi(wkt, "EPSG:3035")  # ETRS89 / LAEA Europe
        assert gdf.crs.to_string() == "EPSG:3035"

