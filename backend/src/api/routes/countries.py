"""API routes for country selection and country-specific data."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import List

from ...config.base_settings import settings
from ...datasets.catalog import DatasetCatalog


router = APIRouter(prefix="/countries", tags=["countries"])


@router.get("", response_model=List[str])
async def list_countries() -> List[str]:
    """List available countries based on GADM data."""
    catalog = DatasetCatalog(settings.data_sources_dir)
    countries = []
    
    # Check GADM directory for available countries
    gadm_dir = settings.data_sources_dir / "gadm"
    if gadm_dir.exists():
        for country_dir in gadm_dir.iterdir():
            if country_dir.is_dir() and country_dir.name.startswith("gadm41_"):
                # Extract country code from directory name (e.g., gadm41_ITA_shp -> ITA)
                parts = country_dir.name.split("_")
                if len(parts) >= 2:
                    country_code = parts[1]
                    # Map common country codes to names
                    country_names = {
                        "ITA": "Italy",
                        "GRC": "Greece",
                        "FRA": "France",
                        "DEU": "Germany",
                        "ESP": "Spain",
                        "GBR": "United Kingdom",
                        "POL": "Poland",
                        "ROU": "Romania",
                        "BGR": "Bulgaria",
                        "HRV": "Croatia",
                        "CZE": "Czech Republic",
                        "HUN": "Hungary",
                        "PRT": "Portugal",
                        "NLD": "Netherlands",
                        "BEL": "Belgium",
                        "AUT": "Austria",
                        "SWE": "Sweden",
                        "DNK": "Denmark",
                        "FIN": "Finland",
                    }
                    country_name = country_names.get(country_code, country_code)
                    countries.append(f"{country_name} ({country_code})")
    
    return sorted(countries)


@router.get("/{country_code}/bounds")
async def get_country_bounds(country_code: str) -> dict:
    """Get bounding box for a country."""
    import geopandas as gpd
    
    catalog = DatasetCatalog(settings.data_sources_dir)
    gadm_path = catalog.gadm(level=0)
    
    if not gadm_path:
        raise HTTPException(status_code=404, detail="GADM data not found")
    
    try:
        # Find the GADM file for this country
        gadm_dir = settings.data_sources_dir / "gadm"
        country_gadm_path = None
        
        for country_dir in gadm_dir.iterdir():
            if country_dir.is_dir() and country_dir.name.startswith("gadm41_"):
                parts = country_dir.name.split("_")
                if len(parts) >= 2 and parts[1] == country_code.upper():
                    # Look for level 0 file
                    level0_file = country_dir / f"gadm41_{country_code.upper()}_0.shp"
                    if level0_file.exists():
                        country_gadm_path = level0_file
                        break
        
        if not country_gadm_path:
            raise HTTPException(status_code=404, detail=f"GADM data not found for country {country_code}")
        
        gdf = gpd.read_file(country_gadm_path)
        country_data = gdf
        
        if country_data.empty:
            raise HTTPException(status_code=404, detail=f"Country {country_code} not found")
        
        bounds = country_data.total_bounds
        return {
            "minx": float(bounds[0]),
            "miny": float(bounds[1]),
            "maxx": float(bounds[2]),
            "maxy": float(bounds[3]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading country bounds: {str(e)}")

