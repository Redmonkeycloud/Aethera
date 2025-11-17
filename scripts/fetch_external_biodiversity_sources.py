"""Download vetted biodiversity datasets into data2/biodiversity/external."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Callable

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data2" / "biodiversity" / "external"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_file(url: str, destination: Path) -> None:
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    destination.write_bytes(response.content)
    print(f"Downloaded {destination.name}")  # noqa: T201


def fetch_owid_dataset() -> Path:
    url = (
        "https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/"
        "Biodiversity%20habitat%20loss%20(Williams%20et%20al.%202021)/"
        "Biodiversity%20habitat%20loss%20(Williams%20et%20al.%202021).csv"
    )
    dest = DATA_DIR / "owid_biodiversity_habitat_loss.csv"
    download_file(url, dest)
    return dest


def fetch_gbif_occurrences() -> Path:
    params = {
        "country": "IT",
        "taxon_key": 212,  # Raptors (Accipitriformes)
        "limit": 300,
        "hasCoordinate": "true",
    }
    url = "https://api.gbif.org/v1/occurrence/search"
    response = requests.get(url, params=params, timeout=120)
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])
    if not results:
        raise RuntimeError("GBIF response returned no results.")

    records = []
    for row in results:
        records.append(
            {
                "scientificName": row.get("scientificName"),
                "eventDate": row.get("eventDate"),
                "decimallatitude": row.get("decimalLatitude"),
                "decimallongitude": row.get("decimalLongitude"),
                "basisOfRecord": row.get("basisOfRecord"),
                "datasetKey": row.get("datasetKey"),
                "license": row.get("license"),
            }
        )
    dest = DATA_DIR / "gbif_occurrences_italy_raptors.csv"
    pd.DataFrame.from_records(records).to_csv(dest, index=False)
    print(f"Saved GBIF sample to {dest}")  # noqa: T201
    return dest


DATASETS: dict[str, Callable[[], Path]] = {
    "owid_biodiversity_habitat_loss": fetch_owid_dataset,
    "gbif_occurrences_italy_raptors": fetch_gbif_occurrences,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Download vetted biodiversity datasets.")
    parser.add_argument(
        "--dataset",
        choices=list(DATASETS.keys()) + ["all"],
        default="all",
        help="Which dataset to download.",
    )
    args = parser.parse_args()

    targets = DATASETS.keys() if args.dataset == "all" else [args.dataset]
    for key in targets:
        DATASETS[key]()


if __name__ == "__main__":
    main()

