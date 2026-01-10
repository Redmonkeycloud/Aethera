"""Generate a curated biodiversity training dataset from Natura 2000 and CORINE."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import List

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_SOURCES = BASE_DIR / "data2"
OUTPUT_DIR = DATA_SOURCES / "biodiversity"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CRS = "EPSG:3035"

# Find Natura 2000 file
_natura_files = list((DATA_SOURCES / "protected_areas" / "natura2000").glob("*.shp"))
if not _natura_files:
    raise FileNotFoundError(
        f"No Natura 2000 shapefiles found in {DATA_SOURCES / 'protected_areas' / 'natura2000'}. "
        "Please download the Natura 2000 dataset."
    )
NATURA_PATH = _natura_files[0]

CORINE_PATH = DATA_SOURCES / "corine" / "U2018_CLC2018_V2020_20u1.gpkg"
CORINE_LAYER = "U2018_CLC2018_V2020_20u1"

import sys

sys.path.append(str(BASE_DIR))
from backend.src.datasets.catalog import DatasetCatalog  # noqa: E402
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
    """
    Clip CORINE to AOI.
    Uses DatasetCatalog discovery first; falls back to the legacy hardcoded path.
    Returns empty GeoDataFrame if the dataset is missing or corrupted.
    """
    minx, miny, maxx, maxy = aoi.total_bounds
    catalog = DatasetCatalog(DATA_SOURCES)
    corine_path = None
    try:
        corine_path = catalog.corine()
    except Exception:
        corine_path = CORINE_PATH

    try:
        # Prefer bbox reads for speed. For some formats (or unknown gpkg layers),
        # geopandas can read without specifying layer.
        if corine_path.suffix.lower() == ".gpkg":
            try:
                corine = gpd.read_file(corine_path, layer=CORINE_LAYER, bbox=(minx, miny, maxx, maxy))
            except Exception:
                corine = gpd.read_file(corine_path, bbox=(minx, miny, maxx, maxy))
        else:
            corine = gpd.read_file(corine_path, bbox=(minx, miny, maxx, maxy))
    except Exception:
        return gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS)

    if corine.empty:
        return corine.to_crs(TARGET_CRS) if corine.crs else gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS)

    corine = corine.to_crs(TARGET_CRS)
    return gpd.clip(corine, aoi)


def synthetic_land_cover_summary(aoi_area_ha: float, rng: np.random.Generator) -> list[dict]:
    """
    Build a minimal CORINE-like land_cover_summary so forest_ratio() works even if CORINE is unavailable.
    """
    # forest / agriculture / artificial
    fr = float(np.clip(rng.beta(2.5, 3.5), 0, 1))
    ar = float(np.clip(rng.beta(2.8, 3.0), 0, 1))
    ir = float(np.clip(rng.beta(1.8, 6.0), 0, 1))
    total = fr + ar + ir
    if total <= 0:
        fr, ar, ir = 0.3, 0.5, 0.2
        total = 1.0
    fr, ar, ir = fr / total, ar / total, ir / total

    forest_ha = aoi_area_ha * fr
    agri_ha = aoi_area_ha * ar
    imperv_ha = aoi_area_ha * ir

    return [
        {"class_code": "311", "total_area_ha": forest_ha},
        {"class_code": "211", "total_area_ha": agri_ha},
        {"class_code": "111", "total_area_ha": imperv_ha},
    ]


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
    rng = np.random.default_rng(seed)
    
    print(f"[INFO] Loading Natura 2000 dataset...")  # noqa: T201
    natura = load_datasets()
    sindex = natura.sindex
    collected: List[dict] = []
    
    # Check if CORINE is available (only once, not in loop)
    print(f"[INFO] Checking CORINE dataset availability...")  # noqa: T201
    catalog = DatasetCatalog(DATA_SOURCES)
    corine_available = False
    try:
        corine_path = catalog.corine()
        # Try a test read
        test_bbox = (2500000, 1500000, 2600000, 1600000)  # Small test bbox
        try:
            test_read = gpd.read_file(corine_path, bbox=test_bbox)
            corine_available = not test_read.empty
        except Exception:
            corine_available = False
    except Exception:
        corine_available = False
    
    if not corine_available:
        print(f"[INFO] CORINE dataset unavailable or corrupted. Using synthetic land cover data.")  # noqa: T201
    else:
        print(f"[INFO] CORINE dataset available. Using real land cover data.")  # noqa: T201

    # Mix of samples:
    # - "near protected" samples centered around Natura sites (likely higher sensitivity)
    # - "background" samples across CORINE bbox (likely lower sensitivity)
    # This avoids collapsing into a single label.
    max_iterations = sample_count * 6
    print(f"[INFO] Generating {sample_count} samples (max {max_iterations} attempts)...")  # noqa: T201
    
    for i in range(max_iterations):
        if random.random() < 0.55:
            # near Natura
            row = natura.sample(1).iloc[0]
            centroid = row.geometry.representative_point()
            offset_x = random.uniform(-15000, 15000)
            offset_y = random.uniform(-15000, 15000)
            point = Point(centroid.x + offset_x, centroid.y + offset_y)
            sitecode = row.SITECODE
            sitename = row.SITENAME
            sitetype = row.SITETYPE
        else:
            # background (Europe-ish in EPSG:3035)
            # (keep within typical bounds; these are coarse but good for diversity)
            point = Point(
                rng.uniform(2500000, 6500000),
                rng.uniform(1500000, 5500000),
            )
            sitecode = ""
            sitename = ""
            sitetype = ""

        radius_km = random.uniform(1.5, 25)
        aoi_geom = point.buffer(radius_km * 1000)
        aoi = gpd.GeoDataFrame({"id": [sitecode or "background"]}, geometry=[aoi_geom], crs=TARGET_CRS)

        hits = list(sindex.query(aoi_geom, predicate="intersects"))
        subset = natura.iloc[hits] if hits else natura.iloc[0:0]

        # Progress output every 50 samples
        if (i + 1) % 50 == 0:
            print(f"[INFO] Progress: {len(collected)}/{sample_count} samples collected ({i+1}/{max_iterations} iterations)")  # noqa: T201
        
        # Skip expensive CORINE clipping if not available
        aoi_area_ha = float(aoi.geometry.area.sum() / 10_000)
        if not corine_available:
            # CORINE unavailable -> use synthetic land cover (fast)
            land_cover_summary = synthetic_land_cover_summary(aoi_area_ha, rng)
        else:
            # CORINE available -> try to clip (slow, but only if available)
            try:
                corine_clip = clip_corine(aoi)
                if corine_clip.empty:
                    land_cover_summary = synthetic_land_cover_summary(aoi_area_ha, rng)
                else:
                    land_cover_summary = summarize_land_cover(corine_clip)
            except Exception:
                # If clipping fails, use synthetic
                land_cover_summary = synthetic_land_cover_summary(aoi_area_ha, rng)
        overlap_metrics, _ = compute_overlap_metrics(aoi, subset)
        features = build_biodiversity_features(aoi, land_cover_summary, overlap_metrics)
        features["sitecode"] = sitecode
        features["sitename"] = sitename
        features["sitetype"] = sitetype

        # Severity score (continuous) for robust class binning.
        # Add small noise so ties don't collapse qcut.
        severity = (
            features.get("protected_overlap_pct", 0.0) * 1.25
            + features.get("fragmentation_index", 0.0) * 45.0
            + features.get("forest_ratio", 0.0) * 25.0
            + float(features.get("protected_site_count", 0)) * 1.5
            + (features.get("protected_overlap_ha", 0.0) / max(features.get("aoi_area_ha", 1.0), 1.0)) * 120.0
        )
        severity += float(rng.normal(0.0, 3.0))
        features["severity"] = severity
        collected.append(features)

        if len(collected) >= sample_count:
            break

    if not collected:
        raise RuntimeError("Unable to collect training samples. Check data paths.")

    df = pd.DataFrame(collected)

    # Balanced label creation via quantiles (4 classes).
    labels = ["low", "moderate", "high", "very_high"]
    try:
        # Ensure we have variation in severity scores
        if df["severity"].nunique() < 4:
            # Add small random noise if all scores are too similar
            rng_noise = np.random.default_rng(seed + 999)
            df["severity"] = df["severity"] + rng_noise.normal(0, df["severity"].std() * 0.1, len(df))
        df["label"] = pd.qcut(df["severity"], q=4, labels=labels, duplicates="drop").astype(str)
        # Check if we got a balanced distribution
        label_counts = df["label"].value_counts()
        if label_counts.nunique() == 1 and len(label_counts) == 1:
            # All same label - fall back to thresholding with adjusted thresholds
            print(f"[WARN] All samples got same label from qcut. Falling back to thresholding.")  # noqa: T201
            df["label"] = df.apply(lambda r: classify_label(r.to_dict()), axis=1)
    except Exception as e:
        print(f"[WARN] qcut failed: {e}. Falling back to thresholding.")  # noqa: T201
        # Fallback to thresholding
        df["label"] = df.apply(lambda r: classify_label(r.to_dict()), axis=1)

    return df.drop(columns=["severity"], errors="ignore")


def main() -> None:
    import time
    parser = argparse.ArgumentParser(description="Build biodiversity training dataset.")
    parser.add_argument("--samples", type=int, default=150, help="Number of AOI samples to generate.")
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    print("=" * 60)  # noqa: T201
    print(f"Building Biodiversity Training Dataset")  # noqa: T201
    print(f"Samples: {args.samples}")  # noqa: T201
    print(f"Seed: {args.seed}")  # noqa: T201
    print("=" * 60)  # noqa: T201
    
    start_time = time.time()
    df = build_training_dataframe(args.samples, args.seed)
    elapsed = time.time() - start_time
    
    print(f"\n[INFO] Dataset generation completed in {elapsed:.1f} seconds")  # noqa: T201
    print(f"[INFO] Saving dataset...")  # noqa: T201
    
    csv_path = OUTPUT_DIR / "training.csv"
    parquet_path = OUTPUT_DIR / "training.parquet"

    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(parquet_path, index=False)
        print(f"[OK] Saved both CSV and Parquet formats")  # noqa: T201
    except Exception as exc:  # pragma: no cover
        print(f"[WARN] Unable to write parquet file: {exc}")  # noqa: T201
        print(f"[OK] Saved CSV format only")  # noqa: T201
    
    print(f"\n[OK] Wrote {len(df)} samples to {csv_path}")  # noqa: T201
    print(f"[INFO] Label distribution:")  # noqa: T201
    label_counts = df["label"].value_counts().sort_index()
    for label, count in label_counts.items():
        print(f"  {label}: {count} ({count/len(df)*100:.1f}%)")  # noqa: T201


if __name__ == "__main__":
    main()

