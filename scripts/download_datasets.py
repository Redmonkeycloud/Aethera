#!/usr/bin/env python3
"""
Script to download and organize geospatial datasets for Italy and Greece.

This script downloads datasets from authoritative sources and organizes them
with clear naming conventions for easy identification.
"""

import os
import sys
from pathlib import Path
import json
from typing import Dict, List, Optional
import requests
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Data sources directory
DATA_DIR = project_root / "data2"


class DatasetDownloader:
    """Download and organize geospatial datasets."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.data_dir / "datasets_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load existing metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    def download_file(self, url: str, output_path: Path, description: str) -> bool:
        """Download a file from URL."""
        print(f"\n[DOWNLOAD] {description}...")
        print(f"   URL: {url}")
        print(f"   Output: {output_path}")
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # For large files, use streaming
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   Progress: {percent:.1f}%", end='', flush=True)
            
            print(f"\n   [OK] Downloaded successfully!")
            return True
            
        except Exception as e:
            print(f"\n   [ERROR] {e}")
            return False
    
    def tag_dataset(self, dataset_path: Path, country: str, category: str, 
                    source: str, description: str, url: Optional[str] = None):
        """Tag and document a dataset."""
        # Create metadata entry
        key = f"{country}_{category}"
        self.metadata[key] = {
            "path": str(dataset_path.relative_to(self.data_dir)),
            "country": country,
            "category": category,
            "source": source,
            "description": description,
            "url": url,
            "added_date": datetime.now().isoformat(),
            "file_size_mb": dataset_path.stat().st_size / (1024 * 1024) if dataset_path.exists() else 0
        }
        self._save_metadata()
        print(f"   [TAGGED] {country} - {category}")


def organize_existing_data(downloader: DatasetDownloader):
    """Organize and tag existing datasets."""
    print("\n[INFO] Organizing existing datasets...")
    
    data_dir = downloader.data_dir
    
    # CORINE - Italy
    corine_ita = data_dir / "corine" / "corine_ITA.shp"
    if corine_ita.exists():
        downloader.tag_dataset(
            corine_ita,
            country="ITA",
            category="corine_land_cover",
            source="Copernicus (pre-clipped)",
            description="CORINE Land Cover 2018 for Italy",
            url="https://land.copernicus.eu/pan-european/corine-land-cover"
        )
    
    # Natura 2000 - Europe (needs clipping)
    natura2000 = data_dir / "protected_areas" / "natura2000" / "Natura2000_end2021_rev1_epsg3035.shp"
    if natura2000.exists():
        downloader.tag_dataset(
            natura2000,
            country="EUR",  # Europe-wide
            category="natura2000",
            source="EEA",
            description="Natura 2000 Protected Areas (Europe-wide, needs country clipping)",
            url="https://www.eea.europa.eu/data-and-maps/data/natura-11"
        )
    
    # Rivers - Europe
    rivers_eu = data_dir / "rivers" / "HydroRIVERS_v10_eu_shp" / "HydroRIVERS_v10_eu.shp"
    if rivers_eu.exists():
        downloader.tag_dataset(
            rivers_eu,
            country="EUR",
            category="rivers",
            source="HydroRIVERS",
            description="River network for Europe",
            url="https://www.hydrosheds.org/products/hydrorivers"
        )
    
    # GADM - Administrative boundaries
    gadm_ita = data_dir / "gadm" / "gadm41_ITA_shp" / "gadm41_ITA_0.shp"
    if gadm_ita.exists():
        downloader.tag_dataset(
            gadm_ita,
            country="ITA",
            category="admin_boundaries",
            source="GADM",
            description="Administrative boundaries for Italy (Level 0 = Country)",
            url="https://gadm.org/"
        )
    
    gadm_grc = data_dir / "gadm" / "gadm41_GRC_shp" / "gadm41_GRC_0.shp"
    if gadm_grc.exists():
        downloader.tag_dataset(
            gadm_grc,
            country="GRC",
            category="admin_boundaries",
            source="GADM",
            description="Administrative boundaries for Greece (Level 0 = Country)",
            url="https://gadm.org/"
        )
    
    # Natura 2000 - Country-specific
    natura_ita = data_dir / "protected_areas" / "natura2000" / "natura2000_ITA.shp"
    if natura_ita.exists():
        downloader.tag_dataset(
            natura_ita,
            country="ITA",
            category="natura2000",
            source="EEA (clipped)",
            description="Natura 2000 Protected Areas for Italy (clipped from Europe-wide dataset)",
            url="https://www.eea.europa.eu/data-and-maps/data/natura-11"
        )
    
    # Agricultural Lands
    agri_ita = data_dir / "agricultural" / "agricultural_lands_ITA.shp"
    if agri_ita.exists():
        downloader.tag_dataset(
            agri_ita,
            country="ITA",
            category="agricultural_lands",
            source="Extracted from CORINE",
            description="Agricultural lands extracted from CORINE (codes 2xx)",
            url="https://land.copernicus.eu/pan-european/corine-land-cover"
        )
    
    # Forests
    forests_ita = data_dir / "forests" / "forests_ITA.shp"
    if forests_ita.exists():
        downloader.tag_dataset(
            forests_ita,
            country="ITA",
            category="forests",
            source="Extracted from CORINE",
            description="Forest areas extracted from CORINE (codes 3xx)",
            url="https://land.copernicus.eu/pan-european/corine-land-cover"
        )
    
    # GBIF Biodiversity (samples)
    gbif_ita_sample = data_dir / "biodiversity" / "external" / "gbif_occurrences_ITA_sample.csv"
    if gbif_ita_sample.exists():
        downloader.tag_dataset(
            gbif_ita_sample,
            country="ITA",
            category="biodiversity",
            source="GBIF (sample)",
            description="GBIF species occurrence records for Italy (sample: 5000 records)",
            url="https://www.gbif.org/"
        )
    
    gbif_grc_sample = data_dir / "biodiversity" / "external" / "gbif_occurrences_GRC_sample.csv"
    if gbif_grc_sample.exists():
        downloader.tag_dataset(
            gbif_grc_sample,
            country="GRC",
            category="biodiversity",
            source="GBIF (sample)",
            description="GBIF species occurrence records for Greece (sample: 5000 records)",
            url="https://www.gbif.org/"
        )
    
    # GBIF Biodiversity (full datasets)
    gbif_ita_full = data_dir / "biodiversity" / "gbif_occurrences_ITA.csv"
    if gbif_ita_full.exists():
        downloader.tag_dataset(
            gbif_ita_full,
            country="ITA",
            category="biodiversity",
            source="GBIF (full)",
            description="GBIF species occurrence records for Italy (full dataset with coordinates)",
            url="https://www.gbif.org/"
        )
    
    # Urban Atlas
    ua_ita = data_dir / "cities" / "urban_atlas" / "UA_2018_ITA.gpkg"
    if ua_ita.exists():
        downloader.tag_dataset(
            ua_ita,
            country="ITA",
            category="cities",
            source="Copernicus Urban Atlas",
            description="Urban Atlas 2018 for Italy (merged from individual city files)",
            url="https://land.copernicus.eu/local/urban-atlas"
        )
    
    ua_grc = data_dir / "cities" / "urban_atlas" / "UA_2018_GRC.gpkg"
    if ua_grc.exists():
        downloader.tag_dataset(
            ua_grc,
            country="GRC",
            category="cities",
            source="Copernicus Urban Atlas",
            description="Urban Atlas 2018 for Greece (merged from individual city files)",
            url="https://land.copernicus.eu/local/urban-atlas"
        )


def main():
    """Main function."""
    print("=" * 60)
    print("Geospatial Dataset Organizer")
    print("Italy & Greece")
    print("=" * 60)
    
    downloader = DatasetDownloader(DATA_DIR)
    
    # Organize existing data
    organize_existing_data(downloader)
    
    print("\n" + "=" * 60)
    print("[OK] Data organization complete!")
    print(f"[INFO] Metadata saved to: {downloader.metadata_file}")
    print("\nNext steps:")
    print("1. Review datasets_metadata.json")
    print("2. Download missing datasets using download scripts")
    print("3. Update DatasetCatalog to recognize new datasets")
    print("=" * 60)


if __name__ == "__main__":
    main()

