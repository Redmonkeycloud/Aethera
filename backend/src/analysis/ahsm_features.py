"""Feature engineering for AHSM (Asset Hazard Susceptibility Model)."""

from __future__ import annotations

import geopandas as gpd

from .kpis import EnvironmentalKPIs


def build_ahsm_features(
    aoi: gpd.GeoDataFrame,
    land_cover_summary: list[dict],
    environmental_kpis: EnvironmentalKPIs,
    receptor_distances: dict,
) -> dict[str, float]:
    """
    Build features for Asset Hazard Susceptibility Model.

    Args:
        aoi: Area of Interest
        land_cover_summary: Land cover summary statistics
        environmental_kpis: Calculated environmental KPIs
        receptor_distances: Distance to receptors analysis

    Returns:
        Dictionary of feature values for hazard susceptibility
    """
    aoi_area_ha = aoi.geometry.area.sum() / 10_000

    # Land cover features affecting hazard susceptibility
    forest_classes = {"311", "312", "313"}
    forest_area = sum(
        float(row.get("total_area_ha", 0))
        for row in land_cover_summary
        if str(row.get("class_code")) in forest_classes
    )
    forest_ratio = forest_area / aoi_area_ha if aoi_area_ha > 0 else 0.0

    # Wetland/water features (affect flood risk)
    water_classes = {"411", "412", "421", "511", "512"}
    water_area = sum(
        float(row.get("total_area_ha", 0))
        for row in land_cover_summary
        if str(row.get("class_code")) in water_classes
    )
    water_ratio = water_area / aoi_area_ha if aoi_area_ha > 0 else 0.0

    # Urban/impervious (affect flood runoff)
    impervious_classes = {"111", "112", "121", "122", "131", "133"}
    impervious_area = sum(
        float(row.get("total_area_ha", 0))
        for row in land_cover_summary
        if str(row.get("class_code")) in impervious_classes
    )
    impervious_ratio = impervious_area / aoi_area_ha if aoi_area_ha > 0 else 0.0

    # Agricultural land (moderate risk)
    agri_classes = {"211", "212", "213", "221", "222", "223", "231"}
    agri_area = sum(
        float(row.get("total_area_ha", 0))
        for row in land_cover_summary
        if str(row.get("class_code")) in agri_classes
    )
    agri_ratio = agri_area / aoi_area_ha if aoi_area_ha > 0 else 0.0

    # Distance to water bodies (flood risk indicator)
    nearest_water = receptor_distances.get("nearest_water_body")
    distance_to_water_km = (
        nearest_water.get("distance_km")
        if nearest_water and isinstance(nearest_water, dict)
        else 999.0
    )

    features = {
        # Area features
        "aoi_area_ha": aoi_area_ha,
        # Land cover composition
        "forest_ratio": forest_ratio,
        "water_ratio": water_ratio,
        "impervious_ratio": impervious_ratio,
        "agricultural_ratio": agri_ratio,
        # Environmental indicators
        "habitat_fragmentation_index": environmental_kpis.habitat_fragmentation_index,
        "edge_density": environmental_kpis.edge_density,
        "patch_density": environmental_kpis.patch_density,
        # Water regulation (affects flood risk)
        "water_regulation_capacity": environmental_kpis.water_regulation_capacity,
        # Soil erosion (affects landslide risk)
        "soil_erosion_risk": environmental_kpis.soil_erosion_risk,
        # Distance features
        "distance_to_water_km": distance_to_water_km,
        # Ecosystem services (resilience indicator)
        "ecosystem_service_value": environmental_kpis.ecosystem_service_value_index,
        # Connectivity (affects ecosystem resilience)
        "connectivity_index": environmental_kpis.connectivity_index,
    }

    return features

