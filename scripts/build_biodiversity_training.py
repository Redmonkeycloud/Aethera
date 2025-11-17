"""Generate a curated biodiversity training dataset from Natura 2000 and CORINE."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import List

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_SOURCES = BASE_DIR / "data2"
OUTPUT_DIR = DATA_SOURCES / "biodiversity"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CRS = "EPSG:3035"
NATURA_PATH = next((DATA_SOURCES / "protected_areas" / "natura2000").glob("*.shp"))
CORINE_PATH = DATA_SOURCES / "corine" / "U2018_CLC2018_V2020_20u1.gpkg"
CORINE_LAYER = "U2018_CLC2018_V2020_20u1"

import sys

sys.path.append(str(BASE_DIR))
from backend.src.analysis.land_cover import summarize_land_cover  # noqa: E402
from backend.src.analysis.biodiversity import (  # noqa: E402
    compute_overlap_metrics,
    build_biodiversity_features,
)


def load_datasets() -> gpd.GeoDataFrame:
    natura = gpd.read_file(NATURA_PATH)
    natura = natura.to_crs(TARGET_CRS)
    return natura[["SITECODE", "SITENAME", "SITETYPE", "geometry"]]


def clip_corine(aoi: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = aoi.total_bounds
    corine = gpd.read_file(CORINE_PATH, layer=CORINE_LAYER, bbox=(minx, miny, maxx, maxy))
    if corine.empty:
        return corine
    corine = corine.to_crs(TARGET_CRS)
    return gpd.clip(corine, aoi)


def classify_label(features: dict) -> str:
    overlap = features.get("protected_overlap_pct", 0.0)
    fragmentation = features.get("fragmentation_index", 0.0)
    forest_ratio = features.get("forest_ratio", 0.0)
    if overlap >= 30 or fragmentation >= 0.75:
        return "very_high"
    if overlap >= 15 or forest_ratio >= 0.55:
        return "high"
    if overlap >= 5 or forest_ratio >= 0.30:
        return "moderate"
    return "low"


def build_training_dataframe(sample_count: int, seed: int) -> pd.DataFrame:
    random.seed(seed)
    natura = load_datasets()
    sindex = natura.sindex
    collected: List[dict] = []
    
    # Get bounding box of natura data for sampling
    natura_bounds = natura.total_bounds

    for i in range(sample_count * 3):
        # Mix sampling strategies: 50% near Natura sites, 50% random
        if i % 2 == 0 and len(natura) > 0:
            # Sample near Natura site
            row = natura.sample(1).iloc[0]
            centroid = row.geometry.representative_point()
            offset_x = random.uniform(-10000, 10000)
            offset_y = random.uniform(-10000, 10000)
            point = Point(centroid.x + offset_x, centroid.y + offset_y)
        else:
            # Random sample within bounds
            point = Point(
                random.uniform(natura_bounds[0], natura_bounds[2]),
                random.uniform(natura_bounds[1], natura_bounds[3])
            )
        
        radius_km = random.uniform(2, 20)
        aoi_geom = point.buffer(radius_km * 1000)
        aoi = gpd.GeoDataFrame({"id": [f"sample_{i}"]}, geometry=[aoi_geom], crs=TARGET_CRS)

        hits = list(sindex.query(aoi_geom, predicate="intersects"))
        subset = natura.iloc[hits] if hits else gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS)

        corine_clip = clip_corine(aoi)
        if corine_clip.empty:
            continue

        land_cover_summary = summarize_land_cover(corine_clip)
        overlap_metrics, _ = compute_overlap_metrics(aoi, subset)
        features = build_biodiversity_features(aoi, land_cover_summary, overlap_metrics)
        features["sitecode"] = row.SITECODE if hits and len(natura) > 0 else None
        features["sitename"] = row.SITENAME if hits and len(natura) > 0 else None
        features["sitetype"] = row.SITETYPE if hits and len(natura) > 0 else None
        features["label"] = classify_label(features)
        collected.append(features)

        if len(collected) >= sample_count:
            break

    if not collected:
        raise RuntimeError("Unable to collect training samples. Check data paths.")

    return pd.DataFrame(collected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build biodiversity training dataset.")
    parser.add_argument("--samples", type=int, default=150, help="Number of AOI samples to generate.")
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    df = build_training_dataframe(args.samples, args.seed)
    csv_path = OUTPUT_DIR / "training.csv"
    parquet_path = OUTPUT_DIR / "training.parquet"

    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(parquet_path, index=False)
    except Exception as exc:  # pragma: no cover
        print(f"Unable to write parquet file: {exc}")  # noqa: T201
    print(f"Wrote {len(df)} samples to {csv_path}")  # noqa: T201


if __name__ == "__main__":
    main()

