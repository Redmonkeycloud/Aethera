"""Distance-to-receptor calculations for environmental impact assessment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

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
    protected_areas_global: gpd.GeoDataFrame | None = None,
    settlements: gpd.GeoDataFrame | None = None,
    water_bodies: gpd.GeoDataFrame | None = None,
    max_distance_km: float = 50.0,
) -> ReceptorAnalysis:
    """
    Calculate distances from AOI to sensitive receptors.

    Args:
        aoi: Area of Interest GeoDataFrame
        protected_areas: Protected areas (Natura 2000, regional protected areas)
        protected_areas_global: Global protected areas (WDPA, etc.) - used as fallback
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

    # Combine protected areas: prefer regional (Natura 2000), fallback to global (WDPA)
    combined_protected = None
    if protected_areas is not None and not protected_areas.empty:
        combined_protected = protected_areas.copy()
        if protected_areas_global is not None and not protected_areas_global.empty:
            # Ensure same CRS
            if combined_protected.crs != protected_areas_global.crs:
                protected_areas_global = protected_areas_global.to_crs(combined_protected.crs)
            # Combine datasets
            combined_protected = gpd.GeoDataFrame(
                pd.concat([combined_protected, protected_areas_global], ignore_index=True),
                crs=combined_protected.crs
            )
    elif protected_areas_global is not None and not protected_areas_global.empty:
        combined_protected = protected_areas_global.copy()

    # Calculate distance to protected areas (combined regional + global)
    if combined_protected is not None and not combined_protected.empty:
        # Try Natura 2000 field names first, then WDPA field names
        name_field = "SITENAME" if "SITENAME" in combined_protected.columns else (
            "NAME" if "NAME" in combined_protected.columns else "name"
        )
        id_field = "SITECODE" if "SITECODE" in combined_protected.columns else (
            "WDPAID" if "WDPAID" in combined_protected.columns else "id"
        )
        
        nearest_protected = _find_nearest_receptor(
            aoi_centroid,
            combined_protected,
            "protected_area",
            max_distance_km,
            name_field=name_field,
            id_field=id_field,
        )
        if nearest_protected:
            analysis.nearest_protected_area = nearest_protected
            all_distances.append(nearest_protected)

            # Find all protected areas within max distance
            all_protected = _find_all_receptors(
                aoi_centroid,
                combined_protected,
                "protected_area",
                max_distance_km,
                name_field=name_field,
                id_field=id_field,
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
    # Ensure same CRS
    if receptors.crs != "EPSG:4326":
        receptors = receptors.to_crs("EPSG:4326")

    # Calculate distances
    distances = receptors.geometry.distance(point)
    min_idx = distances.idxmin()
    min_distance_m = distances.loc[min_idx]

    if min_distance_m > max_distance_km * 1000:
        return None

    receptor = receptors.loc[min_idx]
    nearest_point = receptor.geometry.interpolate(
        receptor.geometry.project(point)
    )

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
    if receptors.crs != "EPSG:4326":
        receptors = receptors.to_crs("EPSG:4326")

    max_distance_m = max_distance_km * 1000
    distances = receptors.geometry.distance(point)
    within_range = receptors[distances <= max_distance_m]

    results = []
    for idx, receptor in within_range.iterrows():
        distance_m = distances.loc[idx]
        nearest_point = receptor.geometry.interpolate(
            receptor.geometry.project(point)
        )

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

