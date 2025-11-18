"""Base layer endpoints for serving Natura2000, CORINE, and other data sources."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...config.base_settings import settings
from ...datasets.catalog import DatasetCatalog

router = APIRouter(prefix="/layers", tags=["layers"])


def get_catalog() -> DatasetCatalog:
    """Get or create the dataset catalog (lazy initialization)."""
    return DatasetCatalog(settings.data_sources_dir)


def _load_and_convert_to_geojson(path: Path) -> bytes:
    """Load a vector file (GPKG, Shapefile, etc.) and convert to GeoJSON."""
    gdf = gpd.read_file(path)
    if gdf.empty:
        # Return empty GeoJSON FeatureCollection
        return b'{"type":"FeatureCollection","features":[]}'
    # Convert to WGS84 for web display
    if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    # Convert to GeoJSON
    geojson_str = gdf.to_json()
    return geojson_str.encode("utf-8")


@router.get("/natura2000")
async def get_natura2000_layer() -> Response:
    """Get Natura 2000 protected areas layer."""
    catalog = get_catalog()
    try:
        natura_path = catalog.natura2000()
        if not natura_path or not natura_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Natura 2000 dataset not found. Please ensure the dataset is available in the data sources directory.",
            )
        geojson_bytes = _load_and_convert_to_geojson(natura_path)
        return Response(content=geojson_bytes, media_type="application/geo+json")
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Natura 2000 dataset not found. Please ensure the dataset is available in the data sources directory.",
        )


@router.get("/corine")
async def get_corine_layer() -> Response:
    """Get CORINE Land Cover layer."""
    catalog = get_catalog()
    try:
        corine_path = catalog.corine()
        if not corine_path or not corine_path.exists():
            raise HTTPException(
                status_code=404,
                detail="CORINE Land Cover dataset not found. Please ensure the dataset is available in the data sources directory.",
            )
        geojson_bytes = _load_and_convert_to_geojson(corine_path)
        return Response(content=geojson_bytes, media_type="application/geo+json")
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="CORINE Land Cover dataset not found. Please ensure the dataset is available in the data sources directory.",
        )


@router.get("/available")
async def list_available_layers() -> dict[str, bool]:
    """List which base layers are available."""
    catalog = get_catalog()
    try:
        natura_path = catalog.natura2000()
        natura_available = natura_path is not None and natura_path.exists()
    except Exception:
        natura_available = False
    
    try:
        corine_path = catalog.corine()
        corine_available = corine_path.exists()
    except Exception:
        corine_available = False
    
    return {
        "natura2000": natura_available,
        "corine": corine_available,
    }

