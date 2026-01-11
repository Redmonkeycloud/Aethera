"""
Integration test fixtures and utilities.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def create_sample_aoi_geojson() -> dict:
    """Create a sample AOI GeoJSON for testing."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [10.0, 45.0],
                        [10.1, 45.0],
                        [10.1, 45.1],
                        [10.0, 45.1],
                        [10.0, 45.0]
                    ]]
                }
            }
        ]
    }


def get_test_project_data() -> dict:
    """Get test project data."""
    return {
        "name": "Test E2E Project",
        "country": "ITA",
        "sector": "renewable",
    }


def get_test_run_data() -> dict:
    """Get test run data."""
    return {
        "project_type": "solar",
        "country": "ITA",
        "aoi_geojson": create_sample_aoi_geojson(),
    }
