# core/osm_utils.py

from __future__ import annotations
import os
from typing import Optional, Any
import geopandas as gpd

def _get_base_dir() -> str:
    """Project base directory (two levels up from here)."""
    return os.path.dirname(os.path.dirname(__file__))


def _get_data_dir() -> str:
    """Project data directory."""
    return os.path.join(_get_base_dir(), "data")


def load_roads_layer(roads_gpkg: str, layer: str = "roads", logger: Optional[Any] = None) -> gpd.GeoDataFrame:
    """Load a roads layer from a GPKG."""
    if not os.path.exists(roads_gpkg):
        raise FileNotFoundError(f"Roads file not found: {roads_gpkg}")
    try:
        gdf = gpd.read_file(roads_gpkg, layer=layer)
        if logger:
            logger.info(f"[OSM] Loaded roads layer from {roads_gpkg} ({len(gdf)} features)")
        return gdf
    except Exception as e:
        raise RuntimeError(f"Failed to read layer='{layer}' from {roads_gpkg}: {e}")


def build_roads_osmnx(aoi_gdf: gpd.GeoDataFrame, out_gpkg: str, logger: Optional[Any] = None,
                      layer: str = "roads", buffer_m: int = 5000) -> str:
    """
    Build a roads layer using OSMnx by querying the drivable network for the AOI polygon (buffered).
    Saves a GPKG with layer=<layer> in EPSG:3035.
    """
    try:
        import osmnx as ox
    except ImportError as e:
        raise ImportError(
            "OSMnx is required to build roads from Overpass API. Install with: pip install osmnx"
        ) from e

    if aoi_gdf.empty:
        raise ValueError("AOI GeoDataFrame is empty; cannot build roads.")

    if logger:
        logger.info("[OSM] Building roads with OSMnx (network_type='drive')")

    # 1) Buffer AOI in meters to ensure network continuity, then transform to WGS84 for OSMnx
    if aoi_gdf.crs is None:
        raise ValueError("AOI has no CRS; please set CRS before using OSMnx.")
    aoi_proj = aoi_gdf.to_crs("EPSG:3035")
    buffered = aoi_proj.buffer(buffer_m)
    buffered_union = gpd.GeoSeries(buffered.unary_union, crs="EPSG:3035").to_crs("EPSG:4326")
    poly_for_osmnx = buffered_union.iloc[0]

    # 2) Fetch drivable network graph
    G = ox.graph_from_polygon(
        poly_for_osmnx,
        network_type="drive",
        simplify=True,
        retain_all=True
    )

    # 3) Convert to GeoDataFrame (edges only)
    edges = ox.graph_to_gdfs(G, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)

    if edges is None or edges.empty:
        raise ValueError("OSMnx returned no drivable roads for this AOI/buffer.")

    # Keep a small subset of useful columns if present
    keep_cols = ["highway", "name", "oneway", "maxspeed", "geometry"]
    cols = [c for c in keep_cols if c in edges.columns]
    edges = edges[cols].copy() if cols else edges[["geometry"]].copy()

    # OSMnx columns (like 'highway', 'name') can be lists; normalize by taking first item if list
    for col in ["highway", "name", "maxspeed"]:
        if col in edges.columns:
            edges[col] = edges[col].apply(lambda v: v[0] if isinstance(v, list) and len(v) > 0 else v)

    # 4) Project to EPSG:3035 (meters for distances)
    edges = edges.set_crs("EPSG:4326", allow_override=True).to_crs("EPSG:3035")

    # 5) Save to GPKG
    os.makedirs(os.path.dirname(out_gpkg), exist_ok=True)
    edges.to_file(out_gpkg, driver="GPKG", layer=layer)

    if logger:
        logger.info(f"[OSM] Saved roads to {out_gpkg} (layer='{layer}'), features={len(edges)}")
    return out_gpkg


def build_roads_pyrosm_from_pbf(pbf_path: str, out_gpkg: str, logger: Optional[Any] = None,
                                layer: str = "roads") -> str:
    """
    Convert an OSM .pbf to a roads GPKG using pyrosm.
    Filters to the 'driving' network (primary/secondary/tertiary/etc.).
    """
    try:
        from pyrosm import OSM
    except ImportError as e:
        raise ImportError(
            "pyrosm is required to build roads from .pbf. Install with: pip install pyrosm"
        ) from e

    if not os.path.exists(pbf_path):
        raise FileNotFoundError(f"PBF file not found: {pbf_path}")

    if logger:
        logger.info(f"[OSM] Reading PBF: {pbf_path}")
    osm = OSM(pbf_path)

    roads = osm.get_network(network_type="driving")  # lines only
    if roads is None or roads.empty:
        raise ValueError("No drivable roads found in PBF. Try different network_type or check the PBF file.")

    # Keep only geometry + a handful of useful attrs
    keep_cols = [c for c in ["highway", "name", "oneway", "maxspeed", "geometry"] if c in roads.columns]
    roads = roads[keep_cols]

    # Project and save to GPKG
    roads = roads.set_crs("EPSG:4326", allow_override=True).to_crs("EPSG:3035")
    os.makedirs(os.path.dirname(out_gpkg), exist_ok=True)
    roads.to_file(out_gpkg, driver="GPKG", layer=layer)

    if logger:
        logger.info(f"[OSM] Wrote roads to {out_gpkg} (layer='{layer}'), features={len(roads)}")
    return out_gpkg


def ensure_roads_gpkg(country_code: str,
                      aoi_gdf: gpd.GeoDataFrame,
                      logger: Optional[Any] = None,
                      preferred: str = "osmnx",
                      cache_dir: Optional[str] = None,
                      force: bool = False,
                      pbf_path: Optional[str] = None,
                      layer: str = "roads",
                      buffer_m: int = 5000) -> str:
    """
    Ensure a country-specific roads layer exists in GPKG form; builds it if missing.
    - If preferred='osmnx', use Overpass API to fetch drivable network (recommended)
    - If preferred='pyrosm', require pbf_path and build from PBF
    - Caches output under data/roads/roads_{ISO3}.gpkg
    """
    if cache_dir is None:
        cache_dir = os.path.join(_get_data_dir(), "roads")
    os.makedirs(cache_dir, exist_ok=True)

    out_gpkg = os.path.join(cache_dir, f"roads_{country_code}.gpkg")

    # Reuse cached output unless force=True
    if os.path.exists(out_gpkg) and not force:
        try:
            # Also ensure the layer is present and non-empty
            gdf = gpd.read_file(out_gpkg, layer=layer)
            if len(gdf) > 0:
                if logger:
                    logger.info(f"[OSM] Using cached roads: {out_gpkg} (features={len(gdf)})")
                return out_gpkg
            else:
                if logger:
                    logger.warning(f"[OSM] Cached roads file is empty: {out_gpkg} — rebuilding.")
        except Exception as e:
            if logger:
                logger.warning(f"[OSM] Cached roads not readable ({e}) — rebuilding.")

    # Build roads
    if preferred.lower() == "osmnx":
        if logger:
            logger.info("[OSM] Building roads with OSMnx (cached)...")
        return build_roads_osmnx(aoi_gdf, out_gpkg, logger=logger, layer=layer, buffer_m=buffer_m)

    elif preferred.lower() == "pyrosm":
        if not pbf_path:
            raise ValueError("pbf_path is required when preferred='pyrosm'")
        if logger:
            logger.info("[OSM] Building roads with pyrosm from PBF (cached)...")
        return build_roads_pyrosm_from_pbf(pbf_path, out_gpkg, logger=logger, layer=layer)

    else:
        raise ValueError(f"Unknown preferred method: {preferred} (use 'osmnx' or 'pyrosm')")
