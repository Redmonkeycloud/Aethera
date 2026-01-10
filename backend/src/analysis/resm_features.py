"""Feature engineering for RESM (Renewable/Resilience Suitability Model)."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from .kpis import EnvironmentalKPIs
from .weather_features import extract_weather_features


def build_resm_features(
    aoi: gpd.GeoDataFrame,
    land_cover_summary: list[dict],
    environmental_kpis: EnvironmentalKPIs,
    receptor_distances: dict,
    project_type: str,
    solar_raster_path: Path | None = None,
    wind_raster_path: Path | None = None,
    weather_summary_path: Path | None = None,
) -> dict[str, float]:
    """
    Build features for Renewable/Resilience Suitability Model.

    Args:
        aoi: Area of Interest
        land_cover_summary: Land cover summary statistics
        environmental_kpis: Calculated environmental KPIs
        receptor_distances: Distance to receptors analysis
        project_type: Type of renewable project (e.g., 'solar_farm', 'wind_farm')

    Returns:
        Dictionary of feature values
    """
    aoi_area_ha = aoi.geometry.area.sum() / 10_000

    # Land use features
    impervious_classes = {"111", "112", "121", "122", "131", "133"}
    impervious_area = sum(
        float(row.get("total_area_ha", 0))
        for row in land_cover_summary
        if str(row.get("class_code")) in impervious_classes
    )
    impervious_ratio = impervious_area / aoi_area_ha if aoi_area_ha > 0 else 0.0

    # Natural habitat features
    natural_classes = {"311", "312", "313", "321", "322", "324", "411", "412", "421"}
    natural_area = sum(
        float(row.get("total_area_ha", 0))
        for row in land_cover_summary
        if str(row.get("class_code")) in natural_classes
    )
    natural_ratio = natural_area / aoi_area_ha if aoi_area_ha > 0 else 0.0

    # Agricultural land (often suitable for renewables)
    agri_classes = {"211", "212", "213", "221", "222", "223", "231", "241", "242", "243"}
    agri_area = sum(
        float(row.get("total_area_ha", 0))
        for row in land_cover_summary
        if str(row.get("class_code")) in agri_classes
    )
    agri_ratio = agri_area / aoi_area_ha if aoi_area_ha > 0 else 0.0

    # Distance to protected areas (constraint)
    nearest_protected = receptor_distances.get("nearest_protected_area")
    distance_to_protected_km = (
        nearest_protected.get("distance_km")
        if nearest_protected and isinstance(nearest_protected, dict)
        else 999.0
    )

    # Distance to settlements (infrastructure proximity)
    nearest_settlement = receptor_distances.get("nearest_settlement")
    distance_to_settlement_km = (
        nearest_settlement.get("distance_km")
        if nearest_settlement and isinstance(nearest_settlement, dict)
        else 999.0
    )

    features = {
        # Area features
        "aoi_area_ha": aoi_area_ha,
        "natural_habitat_ratio": natural_ratio,
        "impervious_surface_ratio": impervious_ratio,
        "agricultural_ratio": agri_ratio,
        # Environmental constraints
        "distance_to_protected_km": distance_to_protected_km,
        "protected_area_overlap_pct": (
            environmental_kpis.natural_habitat_ratio * 100
            if nearest_protected and nearest_protected.get("distance_km", 999) < 1.0
            else 0.0
        ),
        # Environmental quality indicators
        "habitat_fragmentation_index": environmental_kpis.habitat_fragmentation_index,
        "connectivity_index": environmental_kpis.connectivity_index,
        "ecosystem_service_value": environmental_kpis.ecosystem_service_value_index,
        "soil_erosion_risk": environmental_kpis.soil_erosion_risk,
        # Infrastructure proximity
        "distance_to_settlement_km": distance_to_settlement_km,
        # Resource efficiency
        "resource_efficiency_index": environmental_kpis.resource_efficiency_index,
        # Project type indicator (encoded)
        "project_type_solar": 1.0 if project_type == "solar_farm" else 0.0,
        "project_type_wind": 1.0 if project_type == "wind_farm" else 0.0,
        "project_type_other": (
            1.0 if project_type not in ("solar_farm", "wind_farm") else 0.0
        ),
    }
    
    # Add weather features if available
    weather_features = extract_weather_features(
        aoi=aoi,
        solar_raster_path=solar_raster_path,
        wind_raster_path=wind_raster_path,
        weather_summary_path=weather_summary_path,
    )
    features.update(weather_features)

    return features

