#!/usr/bin/env python3
"""Convert CORINE shapefile to GeoJSON for faster web delivery."""

import sys
from pathlib import Path
import geopandas as gpd
import argparse
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = project_root / "data2"
CORINE_DIR = DATA_DIR / "corine"


def convert_corine_to_geojson(country: str = None, force: bool = False):
    """Convert CORINE shapefile to GeoJSON.
    
    Args:
        country: Country code (e.g., 'ITA', 'GRC'). If None, converts the default file.
        force: If True, overwrite existing GeoJSON file.
    """
    from backend.src.datasets.catalog import DatasetCatalog
    from backend.src.config.base_settings import settings
    
    catalog = DatasetCatalog(settings.data_sources_dir)
    
    try:
        # Get CORINE file path
        if country:
            corine_path = catalog.corine(country=country)
        else:
            corine_path = catalog.corine()
        
        if not corine_path or not corine_path.exists():
            logger.error(f"CORINE file not found: {corine_path}")
            return False
        
        logger.info(f"Converting CORINE file: {corine_path}")
        logger.info(f"File size: {corine_path.stat().st_size / (1024*1024):.2f} MB")
        
        # Determine output path
        output_path = corine_path.with_suffix('.geojson')
        if output_path.exists() and not force:
            logger.warning(f"GeoJSON file already exists: {output_path}")
            logger.info("Use --force to overwrite")
            return False
        
        # Load shapefile
        logger.info("Loading shapefile...")
        gdf = gpd.read_file(corine_path)
        logger.info(f"Loaded {len(gdf)} features")
        
        # Handle CRS
        if gdf.crs is None:
            logger.warning("No CRS defined, assuming EPSG:3035")
            gdf = gdf.set_crs("EPSG:3035")
        
        # Convert to WGS84 for web display
        if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
            logger.info(f"Reprojecting from {gdf.crs.to_string()} to EPSG:4326...")
            gdf = gdf.to_crs("EPSG:4326")
        
        # Simplify geometries slightly to reduce file size (optional)
        # Using a very small tolerance (1 meter) to preserve detail
        logger.info("Simplifying geometries (tolerance: 0.00001 degrees ~1m)...")
        gdf['geometry'] = gdf.geometry.simplify(tolerance=0.00001, preserve_topology=True)
        
        # Save as GeoJSON
        logger.info(f"Saving GeoJSON to {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(output_path, driver='GeoJSON')
        
        output_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Conversion complete!")
        logger.info(f"Output file: {output_path}")
        logger.info(f"Output size: {output_size_mb:.2f} MB")
        logger.info(f"Features: {len(gdf)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error converting CORINE: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert CORINE shapefile to GeoJSON")
    parser.add_argument("--country", type=str, help="Country code (e.g., ITA, GRC)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing GeoJSON file")
    args = parser.parse_args()
    
    success = convert_corine_to_geojson(country=args.country, force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

