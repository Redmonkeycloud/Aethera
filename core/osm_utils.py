# core/osm_utils.py
from __future__ import annotations
import os
from typing import Optional, Any, Dict, List, Tuple
import geopandas as gpd
from shapely.ops import unary_union

try:
    import osmnx as ox
    OSMNX_AVAILABLE = True
except Exception:
    OSMNX_AVAILABLE = False


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _country_cache_path(data_dir: str, kind: str, iso: str) -> str:
    subdir = os.path.join(data_dir, kind)
    _ensure_dir(subdir)
    return os.path.join(subdir, f"{kind}_{iso}.gpkg")


def _aoi_union_geom(aoi_gdf: gpd.GeoDataFrame, to_crs: str = "EPSG:4326"):
    if aoi_gdf.crs is None:
        raise ValueError("AOI GeoDataFrame has no CRS.")
    if aoi_gdf.crs.to_string() != to_crs:
        aoi = aoi_gdf.to_crs(to_crs)
    else:
        aoi = aoi_gdf
    geom = unary_union(aoi.geometry)
    return geom


# ----------------------
# Roads (existing logic)
# ----------------------
def ensure_roads_gpkg(
    country_code: str,
    aoi_gdf: gpd.GeoDataFrame,
    logger: Optional[Any] = None,
    data_dir: str = None,
    preferred: str = "osmnx",     # or "pyrosm"
    force: bool = False,
    buffer_m: int = 5000
) -> str:
    """
    Uses OSMnx to download drivable roads per country, caches to GPKG.
    Optionally build from .pbf via pyrosm (if installed).
    """
    data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    out_path = _country_cache_path(data_dir, "roads", country_code)

    if os.path.exists(out_path) and not force:
        if logger: logger.info(f"[OSM] Using cached roads: {out_path}")
        return out_path

    if preferred == "osmnx":
        if not OSMNX_AVAILABLE:
            raise ImportError("osmnx is required for OSMnx road extraction. `pip install osmnx`.")
        if logger: logger.info(f"[OSM] Downloading roads via OSMnx for country: {country_code}")

        # Use OSMnx graph for drivable network
        place = country_code  # OSM place query works for ISO3 countries in many cases
        try:
            G = ox.graph_from_place(place, network_type="drive")
        except Exception:
            # fallback: graph by polygon from AOI
            geom = _aoi_union_geom(aoi_gdf, to_crs="EPSG:4326")
            G = ox.graph_from_polygon(geom, network_type="drive")

        edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
        # Keep essential columns
        keep = [c for c in ["highway", "name", "oneway", "maxspeed", "geometry"] if c in edges.columns]
        gdf = edges[keep].copy()
        gdf = gdf.set_crs("EPSG:4326", allow_override=True).to_crs("EPSG:3035")
        gdf.to_file(out_path, driver="GPKG", layer="roads")
        if logger: logger.info(f"[OSM] Wrote roads GPKG: {out_path} (layer='roads'), features={len(gdf)}")
        return out_path

    else:
        # pyrosm route (requires pyrosm and .pbf file)
        try:
            from pyrosm import OSM
        except ImportError as e:
            raise ImportError("pyrosm is required for pyrosm route. `pip install pyrosm`") from e

        # Find .pbf path
        pbf_path = None
        pbf_dir = os.path.join(data_dir, "roads")
        for f in os.listdir(pbf_dir):
            if f.lower().endswith(".pbf"):
                pbf_path = os.path.join(pbf_dir, f)
                break
        if pbf_path is None:
            raise FileNotFoundError(f"No .pbf found under {pbf_dir}. Place 'countryname-latest.osm.pbf' there.")

        if logger: logger.info(f"[OSM] Reading PBF via pyrosm: {pbf_path}")
        osm = OSM(pbf_path)
        roads = osm.get_network(network_type="driving")
        if roads is None or roads.empty:
            raise ValueError("No drivable roads found in PBF with pyrosm.")

        keep = [c for c in ["highway", "name", "oneway", "maxspeed", "geometry"] if c in roads.columns]
        gdf = roads[keep].copy()
        gdf = gdf.set_crs("EPSG:4326", allow_override=True).to_crs("EPSG:3035")
        gdf.to_file(out_path, driver="GPKG", layer="roads")
        if logger: logger.info(f"[OSM] Wrote roads GPKG: {out_path} (layer='roads'), features={len(gdf)}")
        return out_path


def load_roads_layer(gpkg_path: str, logger: Optional[Any] = None) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(gpkg_path, layer="roads")
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:3035", allow_override=True)
    if logger: logger.info(f"[OSM] Loaded roads: {len(gdf)} features from {gpkg_path}")
    return gdf


# -----------------------------------------
# NEW: Settlement / Port / Airport via OSMnx
# -----------------------------------------
def _ensure_osmnx():
    if not OSMNX_AVAILABLE:
        raise ImportError("osmnx is required for POI extraction. `pip install osmnx`.")


def ensure_poi_gpkg(
    poi_type: str,
    country_code: str,
    aoi_gdf: gpd.GeoDataFrame,
    logger: Optional[Any] = None,
    data_dir: str = None,
    force: bool = False
) -> str:
    """
    Download or reuse cached POIs (settlements/ports/airports) via OSMnx
    and save as GPKG. Returns path to GPKG.

    poi_type in {"settlements","ports","airports"}
    """
    _ensure_osmnx()
    data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    out_path = _country_cache_path(data_dir, f"poi_{poi_type}", country_code)

    if os.path.exists(out_path) and not force:
        if logger: logger.info(f"[POI] Using cached {poi_type}: {out_path}")
        return out_path

    if logger: logger.info(f"[POI] Downloading {poi_type} via OSMnx for {country_code}...")

    # Build AOI polygon for precise bounding
    geom = _aoi_union_geom(aoi_gdf, to_crs="EPSG:4326")

    # Define OSM tags:
    if poi_type == "settlements":
        tags = {"place": ["city", "town", "village", "hamlet", "suburb", "neighbourhood"]}
    elif poi_type == "ports":
        # Ports are tricky in OSM — we use multiple tags to approximate
        tags = {
            "harbour": True,                         # rare but present
            "seamark:type": "harbour",               # also used in marine seamarks
            "landuse": "port",
            "waterway": ["dock", "port"],
            "amenity": ["ferry_terminal"]
        }
    elif poi_type == "airports":
        tags = {"aeroway": ["aerodrome", "airport", "heliport"]}
    else:
        raise ValueError(f"Unsupported poi_type: {poi_type}")

    try:
        g = ox.geometries_from_polygon(geom, tags=tags)
    except Exception:
        # Fallback to place name if polygon query fails
        g = ox.geometries_from_place(country_code, tags=tags)

    if g is None or g.empty:
        if logger: logger.warning(f"[POI] No {poi_type} found for {country_code}")
        # Create empty GPKG anyway
        gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    else:
        # Keep only relevant columns + geometry
        keep_cols = [c for c in g.columns if c in ["name", "place", "harbour", "aeroway", "waterway", "landuse", "amenity", "geometry"]]
        gdf = g[keep_cols].copy()

    gdf = gdf.set_crs("EPSG:4326", allow_override=True).to_crs("EPSG:3035")
    _ensure_dir(os.path.dirname(out_path))
    gdf.to_file(out_path, driver="GPKG", layer=poi_type)
    if logger: logger.info(f"[POI] Wrote {poi_type} to {out_path} ({len(gdf)} features)")
    return out_path


def load_poi_layer(gpkg_path: str, layer: str, logger: Optional[Any] = None) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(gpkg_path, layer=layer)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:3035", allow_override=True)
    if logger: logger.info(f"[POI] Loaded {layer}: {len(gdf)} features from {gpkg_path}")
    return gdf
