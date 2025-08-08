import geopandas as gpd
import pandas as pd

def load_protected_areas(pa_source, pa_path, csv_lat_col=None, csv_lon_col=None, crs="EPSG:4326"):
    """
    Loads PA layer from .shp, .gdb, or .csv.
    - For .csv, provide columns for lat/lon.
    """
    if pa_path.lower().endswith(".shp") or pa_path.lower().endswith(".gdb"):
        gdf = gpd.read_file(pa_path)
        # Project if needed
        if gdf.crs is None:
            gdf.set_crs(crs, inplace=True)
        return gdf

    elif pa_path.lower().endswith(".csv"):
        df = pd.read_csv(pa_path)
        if csv_lat_col is None or csv_lon_col is None:
            raise ValueError("CSV input requires latitude and longitude columns specified.")
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df[csv_lon_col], df[csv_lat_col]),
            crs=crs
        )
        return gdf

    else:
        raise ValueError(f"Unsupported PA data format: {pa_path}")

def intersect_aoi_with_protected(aoi_gdf, pa_gdf):
    """
    Clips AOI with protected area layer.
    Returns: (clipped_gdf, area_overlap_ha)
    """
    if pa_gdf.crs != aoi_gdf.crs:
        pa_gdf = pa_gdf.to_crs(aoi_gdf.crs)
    intersection = gpd.overlay(pa_gdf, aoi_gdf, how="intersection")
    intersection["area_ha"] = intersection.geometry.area / 10000
    total_overlap = intersection["area_ha"].sum()
    return intersection, total_overlap

def summarize_overlap(clipped_gdf, pa_name):
    return {
        "layer": pa_name,
        "feature_count": len(clipped_gdf),
        "total_overlap_ha": float(clipped_gdf["area_ha"].sum())
    }
