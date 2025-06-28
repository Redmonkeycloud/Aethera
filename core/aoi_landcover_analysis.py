# core/aoi_landcover_analysis.py

import os
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# Import emissions calculator
from core.emissions_api import estimate_emissions

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# CORINE code-to-label mapping
CORINE_CODES = {
    111: "Continuous Urban Fabric",
    112: "Discontinuous Urban Fabric",
    121: "Industrial or Commercial Units",
    131: "Mineral Extraction Sites",
    211: "Non-Irrigated Arable Land",
    231: "Pastures",
    311: "Broad-leaved Forest",
    312: "Coniferous Forest",
    313: "Mixed Forest",
    321: "Natural Grasslands",
    411: "Inland Marshes",
    511: "Water Courses",
    512: "Water Bodies",
    # Expand this table as needed
}

def intersect_aoi_with_corine(aoi_gdf, corine_shapefile_path):
    """Intersect AOI with CORINE shapefile and summarize land cover areas."""
    # Load country-specific CORINE shapefile
    corine = gpd.read_file(corine_shapefile_path)

    # Reproject AOI to match CORINE CRS if needed
    if corine.crs != aoi_gdf.crs:
        aoi_gdf = aoi_gdf.to_crs(corine.crs)

    # Clip CORINE polygons to AOI
    clipped = gpd.overlay(corine, aoi_gdf, how="intersection")

    # Calculate area in hectares
    if clipped.crs.is_geographic:
        clipped = clipped.to_crs(epsg=3857)  # Project to meters
    clipped["area_ha"] = clipped.geometry.area / 10000  # m² to hectares

    # Normalize column names to lowercase for robustness
    clipped.columns = [col.lower() for col in clipped.columns]

    # Map CORINE land cover codes to labels
    if "code_18" not in clipped.columns:
        raise KeyError("Expected 'Code_18' or 'CODE_18' column not found in CORINE data.")

    clipped["land_cover_label"] = clipped["code_18"].map(CORINE_CODES).fillna("Unknown")

    # Summarize area by land cover label
    summary = clipped.groupby(["code_18", "land_cover_label"])["area_ha"].sum().reset_index()
    summary.columns = ["corine_code", "land_cover", "area_hectares"]

    return clipped, summary

def plot_landcover(clipped_gdf, country_code):
    """Plot land cover classes colored by label."""
    fig, ax = plt.subplots(figsize=(12, 10))
    clipped_gdf.plot(ax=ax, column="land_cover_label", cmap="tab20", legend=True, edgecolor='black')
    plt.title(f"Land Cover Classes - {country_code}")
    plt.axis('off')
    plt.tight_layout()

    plot_path = os.path.join(OUTPUT_DIR, f"land_cover_map_{country_code}.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"[PLOT] Saved land cover map to {plot_path}")

def run_full_analysis(aoi_gdf, country_code, corine_shapefile_path):
    """Run full AOI analysis: clip CORINE, summarize, estimate emissions."""
    clipped_gdf, landcover_summary = intersect_aoi_with_corine(aoi_gdf, corine_shapefile_path)

    # Prepare land cover stats dict for emissions API
    land_cover_stats = {
        row["land_cover"]: row["area_hectares"] for _, row in landcover_summary.iterrows()
    }

    # Estimate emissions
    emissions_summary = estimate_emissions(land_cover_stats)

    # Save clipped land cover to GeoJSON
    clipped_path = os.path.join(OUTPUT_DIR, f"clipped_landcover_{country_code}.geojson")
    clipped_gdf.to_file(clipped_path, driver="GeoJSON")
    print(f"[OUTPUT] Saved clipped land cover GeoJSON to {clipped_path}")

    # Plot land cover map
    plot_landcover(clipped_gdf, country_code)

    return landcover_summary, emissions_summary

if __name__ == "__main__":
    print("[ERROR] Please run this module via 'main_controller.py'.")
