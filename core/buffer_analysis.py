# buffer_analysis.py

import os
import geopandas as gpd
from shapely.geometry import Point

def load_vector_data(path):
    """Load shapefile or GeoJSON as GeoDataFrame."""
    return gpd.read_file(path)

def calculate_min_distance(aoi_gdf, features_gdf, features_label):
    """Compute minimum distance from AOI to features."""
    # Ensure both layers have projected CRS (meters)
    if aoi_gdf.crs.is_geographic:
        aoi_gdf = aoi_gdf.to_crs(epsg=3857)
    if features_gdf.crs.is_geographic:
        features_gdf = features_gdf.to_crs(epsg=3857)
    # Calculate minimum distance for each AOI polygon
    min_distances = []
    for idx, aoi_geom in aoi_gdf.geometry.iteritems():
        min_dist = features_gdf.distance(aoi_geom).min()
        min_distances.append(min_dist)
    aoi_gdf[f"min_dist_to_{features_label}"] = min_distances
    return aoi_gdf

def buffer_features(features_gdf, buffer_m=500):
    """Create buffer polygons around each feature."""
    if features_gdf.crs.is_geographic:
        features_gdf = features_gdf.to_crs(epsg=3857)
    features_gdf['geometry'] = features_gdf.geometry.buffer(buffer_m)
    return features_gdf

def summary_stats(aoi_gdf, features_label):
    """Summary statistics on minimum distances."""
    col = f"min_dist_to_{features_label}"
    return {
        "mean_m": aoi_gdf[col].mean(),
        "min_m": aoi_gdf[col].min(),
        "max_m": aoi_gdf[col].max()
    }
