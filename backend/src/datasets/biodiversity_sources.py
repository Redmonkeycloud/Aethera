from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VettedDataset:
    name: str
    url: str
    description: str
    license: str


VETTED_DATASETS: list[VettedDataset] = [
    VettedDataset(
        name="Natura 2000 (EEA)",
        url="https://sdi.eea.europa.eu/catalogue/srv/api/records/f5b78e1b-4a50-4f59-8956-321cce0ed0e5/download",
        description="Official EU network of protected areas used for biodiversity assessments.",
        license="Creative Commons Attribution (EEA)",
    ),
    VettedDataset(
        name="CORINE Land Cover 2018 (Copernicus)",
        url="https://land.copernicus.eu/pan-european/corine-land-cover/clc2018",
        description="Pan-European land cover dataset for environmental monitoring.",
        license="Copernicus open data license",
    ),
    VettedDataset(
        name="Biodiversity habitat loss (Williams et al. 2021)",
        url=(
            "https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/"
            "Biodiversity%20habitat%20loss%20(Williams%20et%20al.%202021)/"
            "Biodiversity%20habitat%20loss%20(Williams%20et%20al.%202021).csv"
        ),
        description="Our World in Data compilation quantifying habitat loss across species groups.",
        license="CC BY 4.0",
    ),
    VettedDataset(
        name="GBIF Occurrence API",
        url="https://api.gbif.org/v1/occurrence/search",
        description="Global Biodiversity Information Facility API for species occurrence records.",
        license="CC BY 4.0 (per dataset)",
    ),
]

