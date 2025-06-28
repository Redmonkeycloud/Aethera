import geopandas as gpd

gdf = gpd.read_file("data/corine/corine_ITA.shp")  # adjust path if needed
print(gdf.columns)
