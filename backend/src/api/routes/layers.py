"""Base layer endpoints for serving Natura2000, CORINE, and other data sources."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import geopandas as gpd
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ...config.base_settings import settings
from ...datasets.catalog import DatasetCatalog

router = APIRouter(prefix="/layers", tags=["layers"])


def get_catalog() -> DatasetCatalog:
    """Get or create the dataset catalog (lazy initialization)."""
    return DatasetCatalog(settings.data_sources_dir)


def _get_country_boundary(country_code: str) -> Optional[gpd.GeoDataFrame]:
    """Get country boundary from GADM data.
    
    Args:
        country_code: ISO 3166-1 alpha-3 code (e.g., 'GRC') or alpha-2 code (e.g., 'GR')
    """
    import logging
    logger = logging.getLogger(__name__)
    
    catalog = get_catalog()
    try:
        # GADM level 0 is country level
        gadm_path = catalog.gadm(level=0)
        if not gadm_path or not gadm_path.exists():
            logger.warning("GADM level 0 not found for country filtering")
            return None
        
        # Load GADM and filter by country code
        gadm_gdf = gpd.read_file(gadm_path)
        logger.info(f"Loaded GADM data with {len(gadm_gdf)} features. Columns: {list(gadm_gdf.columns)}")
        
        # Normalize country code
        country_code_upper = country_code.upper()
        
        # ISO3 to ISO2 mapping for common countries
        iso3_to_iso2 = {
            'GRC': 'GR', 'DEU': 'DE', 'FRA': 'FR', 'ITA': 'IT', 'ESP': 'ES',
            'GBR': 'GB', 'POL': 'PL', 'ROU': 'RO', 'NLD': 'NL', 'BEL': 'BE',
            'CZE': 'CZ', 'PRT': 'PT', 'HUN': 'HU', 'SWE': 'SE', 'AUT': 'AT',
            'BGR': 'BG', 'DNK': 'DK', 'FIN': 'FI', 'SVK': 'SK', 'IRL': 'IE',
            'HRV': 'HR', 'LTU': 'LT', 'SVN': 'SI', 'LVA': 'LV', 'EST': 'EE',
            'CYP': 'CY', 'LUX': 'LU', 'MLT': 'MT'
        }
        
        # Try to convert ISO3 to ISO2 if needed
        iso2_code = iso3_to_iso2.get(country_code_upper, country_code_upper if len(country_code_upper) == 2 else None)
        
        # Log sample values from key columns for debugging
        sample_cols = ['GID_0', 'ISO', 'ISO3', 'NAME_0', 'COUNTRY']
        available_cols = [col for col in sample_cols if col in gadm_gdf.columns]
        if available_cols:
            logger.info(f"Sample values from GADM columns: {', '.join(available_cols)}")
            for col in available_cols[:3]:  # Log first 3 countries
                sample_values = gadm_gdf[col].unique()[:5]
                logger.info(f"  {col}: {list(sample_values)}")
        
        # Try matching in order of preference: ISO3, ISO, GID_0, NAME_0
        country_gdf = None
        match_column = None
        
        # Try ISO3 column first (if country_code is 3 chars)
        if len(country_code_upper) == 3 and 'ISO3' in gadm_gdf.columns:
            country_gdf = gadm_gdf[gadm_gdf['ISO3'].str.upper() == country_code_upper]
            if not country_gdf.empty:
                match_column = 'ISO3'
                logger.info(f"Matched {country_code_upper} using ISO3 column")
        
        # Try ISO column (alpha-2)
        if (country_gdf is None or country_gdf.empty) and 'ISO' in gadm_gdf.columns:
            test_code = iso2_code if iso2_code and len(iso2_code) == 2 else country_code_upper
            country_gdf = gadm_gdf[gadm_gdf['ISO'].str.upper() == test_code.upper()]
            if not country_gdf.empty:
                match_column = 'ISO'
                logger.info(f"Matched {country_code_upper} (as {test_code}) using ISO column")
        
        # Try GID_0 column (GADM identifier, usually same as ISO3)
        if (country_gdf is None or country_gdf.empty) and 'GID_0' in gadm_gdf.columns:
            country_gdf = gadm_gdf[gadm_gdf['GID_0'].str.upper() == country_code_upper]
            if not country_gdf.empty:
                match_column = 'GID_0'
                logger.info(f"Matched {country_code_upper} using GID_0 column")
        
        # Try NAME_0 as last resort (case-insensitive partial match)
        if (country_gdf is None or country_gdf.empty) and 'NAME_0' in gadm_gdf.columns:
            # Country name mapping for common cases
            country_names = {
                'GRC': 'Greece', 'DEU': 'Germany', 'FRA': 'France', 'ITA': 'Italy',
                'ESP': 'Spain', 'GBR': 'United Kingdom', 'POL': 'Poland', 'ROU': 'Romania'
            }
            search_name = country_names.get(country_code_upper, country_code_upper)
            country_gdf = gadm_gdf[gadm_gdf['NAME_0'].str.upper().str.contains(search_name.upper(), na=False)]
            if not country_gdf.empty:
                match_column = 'NAME_0'
                logger.info(f"Matched {country_code_upper} (as {search_name}) using NAME_0 column")
        
        if country_gdf is None or country_gdf.empty:
            logger.warning(f"Country {country_code_upper} not found in GADM data using any column")
            logger.info(f"Available country codes in GADM (first 20):")
            if 'ISO3' in gadm_gdf.columns:
                logger.info(f"  ISO3: {sorted(gadm_gdf['ISO3'].dropna().unique())[:20]}")
            elif 'ISO' in gadm_gdf.columns:
                logger.info(f"  ISO: {sorted(gadm_gdf['ISO'].dropna().unique())[:20]}")
            elif 'GID_0' in gadm_gdf.columns:
                logger.info(f"  GID_0: {sorted(gadm_gdf['GID_0'].dropna().unique())[:20]}")
            return None
        
        # Dissolve if multiple features
        if len(country_gdf) > 1:
            country_gdf = country_gdf.dissolve().reset_index()
        
        logger.info(f"Found country boundary for {country_code_upper} (matched via {match_column}), {len(country_gdf)} feature(s)")
        return country_gdf
    except Exception as e:
        logger.error(f"Error loading country boundary: {e}", exc_info=True)
        return None


def _load_and_convert_to_geojson(path: Path, clip_to: Optional[gpd.GeoDataFrame] = None) -> bytes:
    """Load a vector file (GPKG, Shapefile, etc.) and convert to GeoJSON."""
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        gdf = gpd.read_file(path)
        logger.info(f"Loaded {len(gdf)} features from {path.name}")
        
        if gdf.empty:
            logger.warning(f"Empty dataset: {path.name}")
            return b'{"type":"FeatureCollection","features":[]}'
        
        # Log original CRS and sample coordinates for debugging
        original_crs = gdf.crs
        logger.info(f"Original CRS: {original_crs}")
        
        # Sample first feature coordinates for debugging
        if len(gdf) > 0:
            first_geom = gdf.iloc[0].geometry
            if first_geom and hasattr(first_geom, 'centroid'):
                centroid = first_geom.centroid
                logger.info(f"Sample coordinates (before reprojection): x={centroid.x:.2f}, y={centroid.y:.2f}")
        
        # Handle CRS: if None, try to detect or assume EPSG:3035 (common for CORINE/Natura)
        if gdf.crs is None:
            logger.warning(f"No CRS defined for {path.name}, attempting to detect or assume EPSG:3035")
            # Try to detect from coordinates (if x > 1e6, likely projected)
            if len(gdf) > 0:
                first_geom = gdf.iloc[0].geometry
                if first_geom and hasattr(first_geom, 'centroid'):
                    centroid = first_geom.centroid
                    if abs(centroid.x) > 1e6 or abs(centroid.y) > 1e6:
                        logger.info("Large coordinate values detected, assuming EPSG:3035")
                        gdf = gdf.set_crs("EPSG:3035")
                    else:
                        logger.info("Small coordinate values, assuming EPSG:4326")
                        gdf = gdf.set_crs("EPSG:4326")
            else:
                # Default assumption for European datasets
                gdf = gdf.set_crs("EPSG:3035")
        
        # Clip to country boundary if provided
        if clip_to is not None and not clip_to.empty:
            logger.info(f"Clipping dataset to country boundary")
            # Ensure same CRS
            if gdf.crs != clip_to.crs:
                clip_to = clip_to.to_crs(gdf.crs)
            # Use bbox first for faster filtering
            bbox = clip_to.total_bounds
            gdf = gdf.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            if not gdf.empty:
                gdf = gpd.clip(gdf, clip_to)
            logger.info(f"After clipping: {len(gdf)} features")
        
        # Convert to WGS84 for web display
        if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
            logger.info(f"Reprojecting from {gdf.crs.to_string()} to EPSG:4326")
            gdf = gdf.to_crs("EPSG:4326")
            
            # Log sample coordinates after reprojection
            if len(gdf) > 0:
                first_geom = gdf.iloc[0].geometry
                if first_geom and hasattr(first_geom, 'centroid'):
                    centroid = first_geom.centroid
                    logger.info(f"Sample coordinates (after reprojection): lon={centroid.x:.6f}, lat={centroid.y:.6f}")
        elif gdf.crs is None or gdf.crs.to_string() != "EPSG:4326":
            # Ensure WGS84
            if gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4326", allow_override=True)
            else:
                gdf = gdf.to_crs("EPSG:4326")
        
        # Verify coordinates are in valid WGS84 range
        if len(gdf) > 0:
            bounds = gdf.total_bounds
            if bounds[0] < -180 or bounds[0] > 180 or bounds[2] < -180 or bounds[2] > 180:
                logger.error(f"Invalid longitude range: {bounds[0]} to {bounds[2]}")
            if bounds[1] < -90 or bounds[1] > 90 or bounds[3] < -90 or bounds[3] > 90:
                logger.error(f"Invalid latitude range: {bounds[1]} to {bounds[3]}")
            logger.info(f"Bounds: lon=[{bounds[0]:.6f}, {bounds[2]:.6f}], lat=[{bounds[1]:.6f}, {bounds[3]:.6f}]")
        
        # Convert to GeoJSON
        geojson_str = gdf.to_json()
        geojson_bytes = geojson_str.encode("utf-8")
        logger.info(f"Converted to GeoJSON: {len(geojson_bytes)} bytes")
        return geojson_bytes
        
    except Exception as e:
        logger.error(f"Error loading {path}: {e}", exc_info=True)
        raise


@router.get("/natura2000")
async def get_natura2000_layer(country: Optional[str] = None) -> Response:
    """Get Natura 2000 protected areas layer, optionally clipped to a country."""
    import logging
    logger = logging.getLogger(__name__)
    
    catalog = get_catalog()
    try:
        logger.info(f"Fetching Natura 2000 layer{'' if not country else f' for country {country}'}...")
        # Try to get country-specific file if available
        natura_path = catalog.natura2000(country=country)
        if not natura_path or not natura_path.exists():
            logger.warning(f"Natura 2000 path not found: {natura_path}")
            raise HTTPException(
                status_code=404,
                detail="Natura 2000 dataset not found. Please ensure the dataset is available in the data sources directory.",
            )
        
        # Check file size first - if small, likely already clipped, skip GADM lookup
        file_size_mb = natura_path.stat().st_size / (1024 * 1024)
        logger.info(f"Natura 2000 file size: {file_size_mb:.2f} MB")
        
        # Get country boundary if country code provided and file is large
        country_boundary = None
        if country and file_size_mb >= 50:  # Only do GADM lookup for large files
            country_boundary = _get_country_boundary(country)
            if country_boundary is None:
                logger.warning(f"Could not load country boundary for {country}, loading full dataset")
        elif country and file_size_mb < 50:
            logger.info(f"File is small ({file_size_mb:.2f} MB), likely already clipped - skipping GADM lookup")
        
        logger.info(f"Loading Natura 2000 from: {natura_path}")
        geojson_bytes = _load_and_convert_to_geojson(natura_path, clip_to=country_boundary)
        logger.info(f"Returning Natura 2000 layer: {len(geojson_bytes)} bytes")
        return Response(content=geojson_bytes, media_type="application/geo+json")
    except FileNotFoundError as e:
        logger.error(f"Natura 2000 file not found: {e}")
        raise HTTPException(
            status_code=404,
            detail="Natura 2000 dataset not found. Please ensure the dataset is available in the data sources directory.",
        )
    except Exception as e:
        logger.error(f"Error serving Natura 2000 layer: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error loading Natura 2000 layer: {str(e)}",
        )


@router.get("/corine")
async def get_corine_layer(country: Optional[str] = None) -> Response:
    """Get CORINE Land Cover layer, optionally clipped to a country."""
    import logging
    logger = logging.getLogger(__name__)
    
    catalog = get_catalog()
    try:
        logger.info(f"Fetching CORINE layer{'' if not country else f' for country {country}'}...")
        corine_path = catalog.corine(country=country)  # Pass country to catalog
        if not corine_path or not corine_path.exists():
            logger.warning(f"CORINE path not found: {corine_path}")
            raise HTTPException(
                status_code=404,
                detail="CORINE Land Cover dataset not found. Please ensure the dataset is available in the data sources directory.",
            )
        
        # Check file size first - if small, likely already clipped, skip GADM lookup
        file_size_mb = corine_path.stat().st_size / (1024 * 1024)
        logger.info(f"CORINE file size: {file_size_mb:.2f} MB")
        
        # Get country boundary if country code provided and file is large
        country_boundary = None
        if country and file_size_mb >= 50:  # Only do GADM lookup for large files
            country_boundary = _get_country_boundary(country)
            if country_boundary is None:
                logger.warning(f"Could not load country boundary for {country}, loading full dataset")
        elif country and file_size_mb < 50:
            logger.info(f"File is small ({file_size_mb:.2f} MB), likely already clipped - skipping GADM lookup")
        
        logger.info(f"Loading CORINE from: {corine_path}")
        geojson_bytes = _load_and_convert_to_geojson(corine_path, clip_to=country_boundary)
        logger.info(f"Returning CORINE layer: {len(geojson_bytes)} bytes")
        return Response(content=geojson_bytes, media_type="application/geo+json")
    except FileNotFoundError as e:
        logger.error(f"CORINE file not found: {e}")
        raise HTTPException(
            status_code=404,
            detail="CORINE Land Cover dataset not found. Please ensure the dataset is available in the data sources directory.",
        )
    except Exception as e:
        error_msg = str(e)
        # Check for database corruption errors
        if "malformed" in error_msg.lower() or "database disk image" in error_msg.lower() or "corrupt" in error_msg.lower():
            logger.error(f"CORINE database file appears to be corrupted: {corine_path}")
            raise HTTPException(
                status_code=500,
                detail="CORINE database file is corrupted. Please check the file integrity in your data directory or replace it with a valid copy."
            )
        logger.error(f"Error serving CORINE layer: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error loading CORINE layer: {str(e)}",
        )


@router.get("/available")
async def list_available_layers() -> dict[str, bool]:
    """List which base layers are available."""
    catalog = get_catalog()
    natura_available = False
    corine_available = False
    
    try:
        natura_path = catalog.natura2000()
        natura_available = natura_path is not None and natura_path.exists()
    except (FileNotFoundError, AttributeError, Exception):
        natura_available = False
    
    try:
        corine_path = catalog.corine()
        corine_available = corine_path.exists() if corine_path else False
    except (FileNotFoundError, AttributeError, Exception):
        corine_available = False
    
    return {
        "natura2000": natura_available,
        "corine": corine_available,
    }

