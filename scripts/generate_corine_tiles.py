#!/usr/bin/env python3
"""Generate Mapbox Vector Tiles (MVT) from CORINE dataset."""

import sys
from pathlib import Path
import argparse
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = project_root / "data2"
CORINE_DIR = DATA_DIR / "corine"
TILES_DIR = DATA_DIR / "corine" / "tiles"


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import mapbox_vector_tile
        import geopandas as gpd
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Please install: pip install mapbox-vector-tile geopandas")
        return False


def generate_tiles_with_tippecanoe(input_file: Path, output_dir: Path, country: str = None):
    """Generate tiles using tippecanoe (recommended for large datasets).
    
    This is the preferred method as tippecanoe is optimized for large datasets.
    """
    import subprocess
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Tippecanoe command for CORINE
    # -z14: max zoom level 14
    # -Z0: min zoom level 0
    # --force: overwrite existing tiles
    # --layer=corine: layer name
    # --drop-densest-as-needed: drop features when needed
    cmd = [
        "tippecanoe",
        "-z14",  # Max zoom
        "-Z0",   # Min zoom
        "--force",
        "--layer=corine",
        "--drop-densest-as-needed",
        "-o", str(output_dir / f"corine_{country or 'all'}.mbtiles"),
        str(input_file)
    ]
    
    logger.info(f"Running tippecanoe: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Tippecanoe output:")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Tippecanoe failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.warning("Tippecanoe not found. Please install tippecanoe:")
        logger.info("  Windows: Download from https://github.com/felt/tippecanoe/releases")
        logger.info("  Or use: pip install tippecanoe-tool")
        return False


def generate_tiles_python(input_file: Path, output_dir: Path, country: str = None):
    """Generate MBTiles using Python libraries (slower but no external dependencies).
    
    This is a fallback if tippecanoe is not available.
    For large datasets, this will be very slow.
    """
    try:
        import mapbox_vector_tile
        import geopandas as gpd
        from shapely.geometry import box, mapping
        import morecantile
        import sqlite3
        import json
        import gzip
    except ImportError as e:
        logger.error(f"Required libraries not installed: {e}")
        logger.info("Please install: pip install mapbox-vector-tile geopandas shapely morecantile")
        return False
    
    logger.info(f"Loading GeoDataFrame from {input_file}...")
    gdf = gpd.read_file(input_file)
    
    # Ensure WGS84
    if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
        logger.info(f"Reprojecting from {gdf.crs.to_string()} to EPSG:4326...")
        gdf = gdf.to_crs("EPSG:4326")
    
    logger.warning("Python-based tile generation is very slow for large datasets.")
    logger.warning("Consider using tippecanoe for better performance.")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    mbtiles_path = output_dir / f"corine_{country.upper() if country else 'all'}.mbtiles"
    
    # Remove existing file if it exists
    if mbtiles_path.exists():
        logger.info(f"Removing existing MBTiles file: {mbtiles_path}")
        mbtiles_path.unlink()
    
    # Create MBTiles database
    logger.info(f"Creating MBTiles database: {mbtiles_path}")
    conn = sqlite3.connect(str(mbtiles_path))
    cursor = conn.cursor()
    
    # Create MBTiles schema
    cursor.execute("""
        CREATE TABLE tiles (
            zoom_level INTEGER,
            tile_column INTEGER,
            tile_row INTEGER,
            tile_data BLOB
        )
    """)
    cursor.execute("CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)")
    
    cursor.execute("""
        CREATE TABLE metadata (
            name TEXT,
            value TEXT
        )
    """)
    
    # Get bounds
    bounds = gdf.total_bounds  # minx, miny, maxx, maxy
    bounds_str = ",".join(str(b) for b in bounds)
    
    # Add metadata
    metadata = [
        ("name", f"CORINE Land Cover {country or 'All'}"),
        ("format", "pbf"),
        ("bounds", bounds_str),
        ("center", f"{(bounds[0] + bounds[2]) / 2},{(bounds[1] + bounds[3]) / 2},6"),
        ("minzoom", "0"),
        ("maxzoom", "14"),
        ("type", "overlay"),
        ("description", f"CORINE Land Cover dataset {'for ' + country if country else ''}")
    ]
    
    cursor.executemany("INSERT INTO metadata (name, value) VALUES (?, ?)", metadata)
    
    # Use Web Mercator (EPSG:3857) for tiles
    tms = morecantile.tms.get("WebMercatorQuad")
    
    # Define zoom levels (0-14)
    min_zoom = 0
    max_zoom = 14
    
    logger.info(f"Generating tiles for zoom levels {min_zoom}-{max_zoom}...")
    logger.info("This may take a long time for large datasets...")
    
    total_tiles = 0
    tiles_with_data = 0
    
    # Generate tiles for each zoom level
    for zoom in range(min_zoom, max_zoom + 1):
        logger.info(f"Processing zoom level {zoom}...")
        
        # Get min/max tiles that cover the bounding box
        min_tile = tms.tile(bounds[0], bounds[1], zoom)
        max_tile = tms.tile(bounds[2], bounds[3], zoom)
        
        # Handle reversed Y coordinates (Y increases from top to bottom in tile coordinates)
        min_x, max_x = min(min_tile.x, max_tile.x), max(min_tile.x, max_tile.x)
        min_y, max_y = min(min_tile.y, max_tile.y), max(min_tile.y, max_tile.y)
        
        zoom_tiles = 0
        zoom_tiles_with_data = 0
        
        # Process tiles in this zoom level
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                total_tiles += 1
                zoom_tiles += 1
                
                if zoom_tiles % 100 == 0:
                    logger.info(f"  Zoom {zoom}: Processed {zoom_tiles} tiles ({zoom_tiles_with_data} with data)")
                
                # Get tile bounding box in WGS84 (morecantile returns bbox in WGS84)
                tile = morecantile.Tile(x, y, zoom)
                tile_bbox_wgs84 = box(*tms.bounds(tile))
                
                # Clip features to tile
                tile_gdf = gdf[gdf.intersects(tile_bbox_wgs84)].copy()
                
                if tile_gdf.empty:
                    continue
                
                # Clip geometries to tile bounds
                tile_gdf['geometry'] = tile_gdf.intersection(tile_bbox_wgs84)
                tile_gdf = tile_gdf[~tile_gdf.is_empty]
                
                if tile_gdf.empty:
                    continue
                
                # Convert to Web Mercator for encoding
                tile_gdf_mercator = tile_gdf.to_crs("EPSG:3857")
                
                # Prepare features for MVT encoding
                features = []
                for idx, row in tile_gdf_mercator.iterrows():
                    geom = row.geometry
                    if geom is None or geom.is_empty:
                        continue
                    
                    # Convert to GeoJSON-like format
                    geom_dict = mapping(geom)
                    
                    # Extract properties (exclude geometry)
                    props = {k: v for k, v in row.items() if k != 'geometry'}
                    # Convert non-serializable types
                    props = {k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v) 
                            for k, v in props.items()}
                    
                    features.append({
                        "geometry": geom_dict,
                        "properties": props
                    })
                
                if not features:
                    continue
                
                # Encode as MVT
                try:
                    mvt_data = mapbox_vector_tile.encode([{
                        "name": "corine",
                        "features": features
                    }])
                    
                    # Compress with gzip
                    compressed = gzip.compress(mvt_data)
                    
                    # Store in database (MBTiles uses TMS Y coordinate)
                    tms_y = (2 ** zoom) - 1 - y
                    cursor.execute(
                        "INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                        (zoom, x, tms_y, compressed)
                    )
                    
                    tiles_with_data += 1
                    zoom_tiles_with_data += 1
                    
                except Exception as e:
                    logger.warning(f"Error encoding tile {zoom}/{x}/{y}: {e}")
                    continue
        
        logger.info(f"Zoom {zoom} complete: {zoom_tiles_with_data} tiles with data out of {zoom_tiles} total")
        conn.commit()  # Commit after each zoom level
    
    conn.commit()
    conn.close()
    
    logger.info(f"MBTiles generation complete!")
    logger.info(f"Total tiles processed: {total_tiles}")
    logger.info(f"Tiles with data: {tiles_with_data}")
    logger.info(f"Output file: {mbtiles_path}")
    logger.info(f"File size: {mbtiles_path.stat().st_size / (1024 * 1024):.2f} MB")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate vector tiles from CORINE dataset")
    parser.add_argument("--country", type=str, help="Country code (e.g., ITA, GRC)")
    parser.add_argument("--method", choices=["tippecanoe", "python"], default="tippecanoe",
                       help="Tile generation method (default: tippecanoe)")
    parser.add_argument("--output-dir", type=str, help="Output directory for tiles")
    args = parser.parse_args()
    
    from backend.src.datasets.catalog import DatasetCatalog
    from backend.src.config.base_settings import settings
    
    catalog = DatasetCatalog(settings.data_sources_dir)
    
    try:
        # Get CORINE file (prefer GeoJSON if available)
        if args.country:
            corine_path = catalog.corine(country=args.country)
        else:
            corine_path = catalog.corine()
        
        if not corine_path or not corine_path.exists():
            logger.error(f"CORINE file not found: {corine_path}")
            return 1
        
        logger.info(f"Input file: {corine_path}")
        file_size_mb = corine_path.stat().st_size / (1024 * 1024)
        logger.info(f"File size: {file_size_mb:.2f} MB")
        
        # Determine output directory
        output_dir = Path(args.output_dir) if args.output_dir else TILES_DIR
        if args.country:
            output_dir = output_dir / args.country.upper()
        
        if args.method == "tippecanoe":
            success = generate_tiles_with_tippecanoe(corine_path, output_dir, args.country)
        else:
            success = generate_tiles_python(corine_path, output_dir, args.country)
        
        if success:
            logger.info(f"Tiles generated successfully in: {output_dir}")
            return 0
        else:
            return 1
            
    except Exception as e:
        logger.error(f"Error generating tiles: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

