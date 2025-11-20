"""Integration tests for the full analysis pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.utils.geometry import load_aoi


@pytest.mark.integration
@pytest.mark.slow
class TestFullPipeline:
    """Test the complete analysis pipeline."""

    def test_pipeline_with_simple_aoi(self, temp_dir: Path) -> None:
        """Test pipeline execution with a simple AOI."""
        # Create a simple test AOI
        aoi_wkt = "POLYGON((10 50, 11 50, 11 51, 10 51, 10 50))"
        aoi_file = temp_dir / "test_aoi.wkt"
        aoi_file.write_text(aoi_wkt)

        # This would run the full pipeline
        # For now, just test that we can load the AOI
        gdf = load_aoi(str(aoi_file), "EPSG:4326")
        assert len(gdf) == 1
        assert gdf.crs.to_string() == "EPSG:4326"

    @pytest.mark.skip(reason="Requires full pipeline setup")
    def test_pipeline_with_project_type(self, temp_dir: Path) -> None:
        """Test pipeline with specific project type."""
        # This would test the full pipeline with a project type
        # Requires database, datasets, etc.
        pass

