"""Distance-to-receptor calculations for environmental impact assessment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import nearest_points

from ..logging_utils import get_logger


logger = get_logger(__name__)


@dataclass
class ReceptorDistance:
    """Distance measurement to a sensitive receptor."""

    receptor_type: str
    receptor_id: str | None
    receptor_name: str | None
    distance_m: float
    distance_km: float
    nearest_point: Point | None = None


@dataclass
class ReceptorAnalysis:
    """Complete receptor analysis results."""

    aoi_centroid: Point
    nearest_protected_area: ReceptorDistance | None = None
    nearest_settlement: ReceptorDistance | None = None
    nearest_water_body: ReceptorDistance | None = None
    all_receptors: list[ReceptorDistance] = None

    def __post_init__(self) -> None:
        """Initialize all_receptors list if None."""
        if self.all_receptors is None:
            self.all_receptors = []


def calculate_distance_to_receptors(
    aoi: gpd.GeoDataFrame,
    protected_areas: gpd.GeoDataFrame | None = None,
    settlements: gpd.GeoDataFrame | None = None,
    water_bodies: gpd.GeoDataFrame | None = None,
    max_distance_km: float = 50.0,
) -> ReceptorAnalysis:
    """
    Calculate distances from AOI to sensitive receptors.

    Args:
        aoi: Area of Interest GeoDataFrame
        protected_areas: Protected areas (Natura 2000, national parks, etc.)
        settlements: Human settlements (cities, towns)
        water_bodies: Water bodies (rivers, lakes, wetlands)
        max_distance_km: Maximum distance to search for receptors (default: 50 km)

    Returns:
        ReceptorAnalysis with distance measurements
    """
    # Get AOI centroid
    aoi_union = aoi.geometry.unary_union
    aoi_centroid = aoi_union.centroid

    # Ensure centroid is in same CRS as AOI
    if aoi.crs:
        centroid_gdf = gpd.GeoDataFrame(geometry=[aoi_centroid], crs=aoi.crs)
        if aoi.crs != "EPSG:4326":
            centroid_gdf = centroid_gdf.to_crs("EPSG:4326")
        aoi_centroid = centroid_gdf.geometry.iloc[0]

    analysis = ReceptorAnalysis(aoi_centroid=aoi_centroid)
    all_distances: list[ReceptorDistance] = []

    # Calculate distance to protected areas
    if protected_areas is not None and not protected_areas.empty:
        nearest_protected = _find_nearest_receptor(
            aoi_centroid,
            protected_areas,
            "protected_area",
            max_distance_km,
            name_field="SITENAME",
            id_field="SITECODE",
        )
        if nearest_protected:
            analysis.nearest_protected_area = nearest_protected
            all_distances.append(nearest_protected)

            # Find all protected areas within max distance
            all_protected = _find_all_receptors(
                aoi_centroid,
                protected_areas,
                "protected_area",
                max_distance_km,
                name_field="SITENAME",
                id_field="SITECODE",
            )
            all_distances.extend(all_protected)

    # Calculate distance to settlements
    if settlements is not None and not settlements.empty:
        nearest_settlement = _find_nearest_receptor(
            aoi_centroid,
            settlements,
            "settlement",
            max_distance_km,
            name_field="NAME",
            id_field="NAME",
        )
        if nearest_settlement:
            analysis.nearest_settlement = nearest_settlement
            all_distances.append(nearest_settlement)

    # Calculate distance to water bodies
    if water_bodies is not None and not water_bodies.empty:
        nearest_water = _find_nearest_receptor(
            aoi_centroid,
            water_bodies,
            "water_body",
            max_distance_km,
            name_field="NAME",
            id_field="NAME",
        )
        if nearest_water:
            analysis.nearest_water_body = nearest_water
            all_distances.append(nearest_water)

    analysis.all_receptors = all_distances
    logger.info(
        "Calculated distances to %d receptors (max distance: %.1f km)",
        len(all_distances),
        max_distance_km,
    )

    return analysis


def _find_nearest_receptor(
    point: Point,
    receptors: gpd.GeoDataFrame,
    receptor_type: str,
    max_distance_km: float,
    name_field: str = "NAME",
    id_field: str = "ID",
) -> ReceptorDistance | None:
    """Find the nearest receptor to a point."""
    # Project to a projected CRS for accurate distance calculations
    if receptors.crs and receptors.crs.is_geographic:
        receptors_proj = receptors.to_crs("EPSG:3857")  # Web Mercator
        point_proj = Point(point.x, point.y)
        point_gdf = gpd.GeoDataFrame(geometry=[point_proj], crs="EPSG:4326")
        point_gdf_proj = point_gdf.to_crs("EPSG:3857")
        point_proj_geom = point_gdf_proj.geometry.iloc[0]
    else:
        receptors_proj = receptors
        point_proj_geom = point

    # Calculate distances in projected CRS
    distances = receptors_proj.geometry.distance(point_proj_geom)
    min_idx = distances.idxmin()
    min_distance_m = distances.loc[min_idx]

    if min_distance_m > max_distance_km * 1000:
        return None

    receptor = receptors_proj.loc[min_idx]
    
    # Find nearest point on geometry (works for any geometry type)
    try:
        # Use shapely's nearest_points to find the nearest point on the geometry
        nearest_geom = nearest_points(point_proj_geom, receptor.geometry)[1]
        # Convert back to EPSG:4326 if needed
        if receptors.crs and receptors.crs.is_geographic:
            nearest_gdf = gpd.GeoDataFrame(geometry=[nearest_geom], crs="EPSG:3857")
            nearest_point = nearest_gdf.to_crs("EPSG:4326").geometry.iloc[0]
        else:
            nearest_point = nearest_geom
    except Exception:
        # Fallback: use point itself if nearest_points fails
        nearest_point = point

    return ReceptorDistance(
        receptor_type=receptor_type,
        receptor_id=str(receptor.get(id_field, "")) if id_field in receptor else None,
        receptor_name=str(receptor.get(name_field, "")) if name_field in receptor else None,
        distance_m=min_distance_m,
        distance_km=min_distance_m / 1000.0,
        nearest_point=nearest_point,
    )


def _find_all_receptors(
    point: Point,
    receptors: gpd.GeoDataFrame,
    receptor_type: str,
    max_distance_km: float,
    name_field: str = "NAME",
    id_field: str = "ID",
) -> list[ReceptorDistance]:
    """Find all receptors within max distance."""
    # Project to a projected CRS for accurate distance calculations
    if receptors.crs and receptors.crs.is_geographic:
        receptors_proj = receptors.to_crs("EPSG:3857")  # Web Mercator
        point_proj = Point(point.x, point.y)
        point_gdf = gpd.GeoDataFrame(geometry=[point_proj], crs="EPSG:4326")
        point_gdf_proj = point_gdf.to_crs("EPSG:3857")
        point_proj_geom = point_gdf_proj.geometry.iloc[0]
    else:
        receptors_proj = receptors
        point_proj_geom = point

    max_distance_m = max_distance_km * 1000
    distances = receptors_proj.geometry.distance(point_proj_geom)
    within_range_idx = distances <= max_distance_m
    within_range = receptors_proj[within_range_idx]

    results = []
    
    for idx, receptor in within_range.iterrows():
        distance_m = distances.loc[idx]
        # Find nearest point on geometry (works for any geometry type)
        try:
            nearest_geom = nearest_points(point_proj_geom, receptor.geometry)[1]
            # Convert back to EPSG:4326 if needed
            if receptors.crs and receptors.crs.is_geographic:
                nearest_gdf = gpd.GeoDataFrame(geometry=[nearest_geom], crs="EPSG:3857")
                nearest_point = nearest_gdf.to_crs("EPSG:4326").geometry.iloc[0]
            else:
                nearest_point = nearest_geom
        except Exception:
            # Fallback: use point itself if nearest_points fails
            nearest_point = point

        results.append(
            ReceptorDistance(
                receptor_type=receptor_type,
                receptor_id=str(receptor.get(id_field, "")) if id_field in receptor else None,
                receptor_name=str(receptor.get(name_field, "")) if name_field in receptor else None,
                distance_m=distance_m,
                distance_km=distance_m / 1000.0,
                nearest_point=nearest_point,
            )
        )

    return results

