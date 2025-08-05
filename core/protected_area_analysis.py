# protected_area_analysis.py

import os
import geopandas as gpd

def load_protected_areas(pa_type="natura2000"):
    """Load protected area geodata from local storage."""
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    if pa_type == "natura2000":
        shp_path = os.path.join(BASE_DIR, "data", "protected_areas", "natura2000", "Natura2000_end2023.shp")
    elif pa_type == "wdpa":
        shp_path = os.path.join(BASE_DIR, "data", "protected_areas", "wdpa", "WDPA_May2024_Public_shp", "WDPA_May2024_Public.shp")
    else:
        raise ValueError(f"Unknown protected area type: {pa_type}")
    gdf = gpd.read_file(shp_path)
    return gdf

def intersect_aoi_with_protected(aoi_gdf, protected_gdf):
    """Return intersection of AOI and protected areas, with overlap statistics."""
    # Reproject if needed
    if protected_gdf.crs != aoi_gdf.crs:
        aoi_gdf = aoi_gdf.to_crs(protected_gdf.crs)
    clipped = gpd.overlay(protected_gdf, aoi_gdf, how="intersection")
    if clipped.empty:
        return clipped, 0.0
    # Area stats
    if clipped.crs.is_geographic:
        clipped = clipped.to_crs(epsg=3857)
    clipped["overlap_ha"] = clipped.geometry.area / 10000
    total_overlap = clipped["overlap_ha"].sum()
    return clipped, total_overlap

def summarize_overlap(clipped_gdf):
    """Summarize by type/name for reporting."""
    if clipped_gdf.empty:
        return []
    # Assume columns 'NAME', 'DESIG_ENG' (designation type) in protected_gdf
    return (
        clipped_gdf.groupby(["DESIG_ENG", "NAME"])["overlap_ha"]
        .sum()
        .reset_index()
        .sort_values("overlap_ha", ascending=False)
        .to_dict(orient="records")
    )
