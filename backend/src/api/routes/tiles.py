"""Vector tile endpoints for serving CORINE and other datasets as MVT tiles."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...config.base_settings import settings

router = APIRouter(prefix="/tiles", tags=["tiles"])

# Tile directory
TILES_DIR = settings.data_sources_dir / "corine" / "tiles"


def get_mbtiles_path(country: Optional[str] = None) -> Optional[Path]:
    """Get path to MBTiles file for a country."""
    if country:
        country_dir = TILES_DIR / country.upper()
        mbtiles_path = country_dir / f"corine_{country.upper()}.mbtiles"
    else:
        mbtiles_path = TILES_DIR / "corine_all.mbtiles"
    
    return mbtiles_path if mbtiles_path.exists() else None


@router.get("/corine/{z}/{x}/{y}.mvt")
async def get_corine_tile(z: int, x: int, y: int, country: Optional[str] = None) -> Response:
    """
    Get a vector tile for CORINE dataset.
    
    Parameters:
    - z: Zoom level (0-14)
    - x: Tile X coordinate
    - y: Tile Y coordinate  
    - country: Optional country code (e.g., ITA, GRC)
    
    Returns:
    - MVT (Mapbox Vector Tile) binary data
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate zoom level
    if z < 0 or z > 14:
        raise HTTPException(status_code=400, detail="Zoom level must be between 0 and 14")
    
    # Get MBTiles file path
    mbtiles_path = get_mbtiles_path(country)
    
    if not mbtiles_path:
        raise HTTPException(
            status_code=404,
            detail=f"CORINE tiles not found for country {country or 'all'}. Please generate tiles first using scripts/generate_corine_tiles.py"
        )
    
    try:
        # Extract tile from MBTiles using sqlite3
        # MBTiles is a SQLite database with tiles stored as blobs
        import sqlite3
        
        conn = sqlite3.connect(str(mbtiles_path))
        cursor = conn.cursor()
        
        # MBTiles schema: tiles table with zoom_level, tile_column, tile_row, tile_data
        # Note: MBTiles uses TMS Y coordinate (inverted), but we serve in XYZ format
        # So we need to convert: tms_y = (2^z - 1) - y
        tms_y = (2 ** z) - 1 - y
        
        cursor.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
            (z, x, tms_y)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            # Return empty 204 No Content for missing tiles (valid in tile services)
            return Response(status_code=204)
        
        tile_data = result[0]
        
        return Response(
            content=tile_data,
            media_type="application/x-protobuf",
            headers={
                "Content-Encoding": "gzip",  # MBTiles tiles are usually gzipped
                "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
            }
        )
        
    except sqlite3.Error as e:
        logger.error(f"Error reading MBTiles: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading tile: {str(e)}")
    except Exception as e:
        logger.error(f"Error serving tile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error serving tile: {str(e)}")


@router.get("/corine/metadata")
async def get_corine_tiles_metadata(country: Optional[str] = None) -> dict:
    """Get metadata about CORINE tiles."""
    mbtiles_path = get_mbtiles_path(country)
    
    if not mbtiles_path:
        raise HTTPException(
            status_code=404,
            detail=f"CORINE tiles not found for country {country or 'all'}"
        )
    
    try:
        import sqlite3
        import json
        
        conn = sqlite3.connect(str(mbtiles_path))
        cursor = conn.cursor()
        
        # Get metadata
        cursor.execute("SELECT name, value FROM metadata")
        metadata = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get bounds from metadata if available
        bounds = None
        if "bounds" in metadata:
            bounds = [float(x) for x in metadata["bounds"].split(",")]
        
        conn.close()
        
        return {
            "country": country,
            "mbtiles_path": str(mbtiles_path),
            "bounds": bounds,
            "metadata": metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading metadata: {str(e)}")

