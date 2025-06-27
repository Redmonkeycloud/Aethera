import pandas as pd

# Example: IPCC Tier 1 emission factors for land use change (tonnes CO2e/ha/year)
# You can easily expand/replace with more detailed or country-specific data!
IPCC_FACTORS = {
    "forest": -5.8,     # forests typically sequester CO2
    "cropland": 3.2,
    "grassland": 1.2,
    "wetlands": -2.4,
    "urban": 0.0,
    "other": 0.0
}

def estimate_emissions(land_cover_stats, country=None):
    """
    Estimate annual emissions for an AOI using land cover statistics and default factors.
    land_cover_stats: dict with land cover class as key, area (in hectares) as value
    country: not used in this basic version, but ready for country-specific factors later
    Returns: DataFrame with class, area, factor, emissions
    """
    results = []
    for lc_class, area_ha in land_cover_stats.items():
        factor = IPCC_FACTORS.get(lc_class, IPCC_FACTORS["other"])
        emissions = area_ha * factor
        results.append({
            "land_cover": lc_class,
            "area_ha": area_ha,
            "factor_tCO2e_per_ha": factor,
            "annual_emissions_tCO2e": emissions
        })
    return pd.DataFrame(results)

# Example: utility to summarize land cover from a GeoDataFrame
def summarize_land_cover(gdf, land_cover_column="landcover"):
    """
    Quickly aggregate area by land cover class from a GeoDataFrame.
    Assumes CRS is in meters, geometry column exists.
    """
    if gdf.crs is None or gdf.crs.is_geographic:
        # Recommend to reproject to something like EPSG:3857 (meters)
        gdf = gdf.to_crs(epsg=3857)
    gdf["area_ha"] = gdf.geometry.area / 10000  # m² to hectares
    stats = gdf.groupby(land_cover_column)["area_ha"].sum().to_dict()
    return stats

# Example usage/test
if __name__ == "__main__":
    # Let's pretend you have this AOI land cover result:
    land_cover_stats = {
        "forest": 15.0,
        "cropland": 10.0,
        "urban": 2.0,
        "grassland": 1.0
    }
    summary = estimate_emissions(land_cover_stats)
    print(summary)
