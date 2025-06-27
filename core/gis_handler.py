# core/gis_handler.py

import os
import requests
import zipfile
import geopandas as gpd
import matplotlib.pyplot as plt

# Base data directory
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def ensure_directory(path):
    """Ensure a directory exists."""
    os.makedirs(path, exist_ok=True)

def download_file(url, save_path):
    """Generic download function with auto-extraction for ZIPs."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Downloaded: {save_path}")

    # Auto-extract if ZIP
    if save_path.endswith(".zip"):
        extract_path = save_path[:-4]
        with zipfile.ZipFile(save_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        print(f"Extracted to: {extract_path}")
        return extract_path
    return save_path

# -----------------------------
# DOWNLOADERS
# -----------------------------

def download_natural_earth(scale="10m", theme="cultural"):
    """Download Natural Earth admin boundaries."""
    ensure_directory(os.path.join(BASE_DATA_DIR, "natural_earth"))
    base_url = f"https://naciscdn.org/naturalearth/{scale}/{theme}/ne_{scale}_admin_0_countries.zip"
    save_path = os.path.join(BASE_DATA_DIR, "natural_earth", f"ne_{scale}_admin_0_countries.zip")
    return download_file(base_url, save_path)

def download_gadm(country_code="GRC"):
    """Download GADM administrative boundaries."""
    ensure_directory(os.path.join(BASE_DATA_DIR, "gadm"))
    base_url = f"https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_{country_code}_shp.zip"
    save_path = os.path.join(BASE_DATA_DIR, "gadm", f"gadm41_{country_code}_shp.zip")
    return download_file(base_url, save_path)

def download_eurostat():
    """Download Eurostat NUTS regions shapefile."""
    ensure_directory(os.path.join(BASE_DATA_DIR, "eurostat"))
    url = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/shp/NUTS_RG_01M_2021_4326.shp.zip"
    save_path = os.path.join(BASE_DATA_DIR, "eurostat", "NUTS_RG_01M_2021_4326.zip")
    return download_file(url, save_path)

def download_corine_vector():
    """Download CORINE 2018 land cover vector data."""
    ensure_directory(os.path.join(BASE_DATA_DIR, "corine"))
    url = "https://gisco-services.ec.europa.eu/distribution/v2/clc/clc2018/shp/CLC2018_V2020_20_SH.zip"

    save_path = os.path.join(BASE_DATA_DIR, "corine", "CLC2018_CLC2018_V2020_20_shp.zip")
    return download_file(url, save_path)

# -----------------------------
# UTILITIES
# -----------------------------

def load_geodata(filepath):
    """Load spatial data with GeoPandas."""
    gdf = gpd.read_file(filepath)
    print(f"Loaded {len(gdf)} features from {filepath}")
    return gdf

def save_geodata(gdf, save_path):
    """Save a GeoDataFrame to a GeoJSON file."""
    ensure_directory(os.path.dirname(save_path))
    gdf.to_file(save_path, driver="GeoJSON")
    print(f"Saved GeoDataFrame to {save_path}")

def plot_geodata(gdf, column=None, title="Map", cmap="tab20"):
    """Plot GeoDataFrame with optional coloring."""
    ax = gdf.plot(figsize=(12, 8), column=column, cmap=cmap, edgecolor='black', legend=True)
    plt.title(title)
    plt.axis('off')
    plt.show()

# -----------------------------
# PLACEHOLDERS (Future work)
# -----------------------------

def download_openstreetmap(query, filename):
    """TODO: Fetch data from OSM Overpass API."""
    raise NotImplementedError("OpenStreetMap download functionality coming soon.")

def download_nasa_earthdata(dataset_name, filename):
    """TODO: Connect to NASA EarthData with authentication."""
    raise NotImplementedError("NASA EarthData download functionality coming soon.")

# -----------------------------
# MAIN (for manual testing)
# -----------------------------

if __name__ == "__main__":
    print("Fetching base datasets...")
    download_natural_earth()
    download_gadm()
    download_eurostat()
    download_corine_vector()
    print("All downloads completed!")
