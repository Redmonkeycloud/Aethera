# osm_utils.py
from __future__ import annotations
import os
from typing import Optional, Any
import geopandas as gpd

def pbf_to_roads_gpkg(pbf_path: str, out_gpkg: str, logger: Optional[Any] = None) -> str:
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

    if logger: logger.info(f"[OSM] Reading PBF: {pbf_path}")
    osm = OSM(pbf_path)

    # 'driving' returns a lines GeoDataFrame of the drivable network
    roads = osm.get_network(network_type="driving")  # lines only
    if roads is None or roads.empty:
        raise ValueError("No drivable roads found in PBF. Try different network_type or check the PBF file.")

    # Keep only geometry + a handful of useful attrs
    keep_cols = [c for c in ["highway", "name", "oneway", "maxspeed", "geometry"] if c in roads.columns]
    roads = roads[keep_cols]

    # Use a metric CRS (LAEA Europe). Save as GPKG.
    roads = roads.set_crs("EPSG:4326", allow_override=True).to_crs("EPSG:3035")
    os.makedirs(os.path.dirname(out_gpkg), exist_ok=True)
    roads.to_file(out_gpkg, driver="GPKG", layer="roads")

    if logger: logger.info(f"[OSM] Wrote roads to {out_gpkg} (layer='roads'), features={len(roads)}")
    return out_gpkg
