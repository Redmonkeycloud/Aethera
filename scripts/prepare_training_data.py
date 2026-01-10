"""
Prepare training data for ML models from available geospatial datasets.

This script aggregates data from various sources in data2/ to create training datasets
for Biodiversity, RESM, AHSM, and CIM models.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.strtree import STRtree

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.config.base_settings import settings
from backend.src.datasets.catalog import DatasetCatalog

# NOTE:
# This script is designed to be able to run even when optional heavy GIS deps (e.g., rasterio)
# are missing in the active Python environment. For training data generation we prefer:
# - Fast, variable, and reproducible synthetic feature generation
# - Optional enrichment from available datasets (CORINE, Natura, Cities) loaded once


CORINE_CLASS_FIELDS = [
    "class_code",
    "code_18",
    "Code_18",
    "CODE_18",
    "clc_code",
    "CLC_CODE",
    "CLC18",
    "CLC2018",
    "legend",
    "LABEL3",
]


def _pick_corine_class_field(gdf: gpd.GeoDataFrame) -> str | None:
    return next((c for c in CORINE_CLASS_FIELDS if c in gdf.columns), None)


def _safe_to_crs(gdf: gpd.GeoDataFrame, target_crs: str) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    if gdf.crs is None:
        # Assume it's already in target CRS if unspecified (best-effort)
        gdf = gdf.set_crs(target_crs, allow_override=True)
        return gdf
    if str(gdf.crs) != target_crs:
        return gdf.to_crs(target_crs)
    return gdf


def _build_strtree(geoms: list[Any]) -> STRtree | None:
    if not geoms:
        return None
    return STRtree(geoms)


def _dirichlet_ratios(rng: np.random.Generator, alpha: tuple[float, float, float]) -> tuple[float, float, float]:
    vals = rng.dirichlet(np.array(alpha, dtype=float))
    return float(vals[0]), float(vals[1]), float(vals[2])  # natural, agricultural, impervious


def _corine_category(code: str | None) -> str:
    """
    Coarse CORINE category by leading digit.
    - 1xx: artificial (impervious)
    - 2xx: agricultural
    - 3xx/4xx/5xx: natural/wetlands/water (treated as natural for RESM/AHSM)
    """
    if not code:
        return "unknown"
    code = str(code).strip()
    if not code:
        return "unknown"
    lead = code[0]
    if lead == "1":
        return "impervious"
    if lead == "2":
        return "agricultural"
    if lead in {"3", "4", "5"}:
        return "natural"
    return "unknown"


def _sample_land_use_ratios(
    rng: np.random.Generator, corine_code: str | None
) -> tuple[float, float, float]:
    cat = _corine_category(corine_code)
    # natural, agricultural, impervious
    if cat == "natural":
        return _dirichlet_ratios(rng, (12.0, 3.0, 1.5))
    if cat == "agricultural":
        return _dirichlet_ratios(rng, (3.0, 12.0, 2.0))
    if cat == "impervious":
        return _dirichlet_ratios(rng, (1.5, 2.5, 12.0))
    # unknown -> mixed landscape
    return _dirichlet_ratios(rng, (5.0, 5.0, 2.5))


def _clip01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def _sample_weather(
    rng: np.random.Generator,
    allow_defaults: bool = True,
) -> tuple[float, float, float]:
    """
    Fast stochastic weather sampling used for training data so that labels/features are not constant
    even if rasterio is missing.
    Returns: (solar_ghi_kwh_m2_day, wind_speed_100m_ms, temperature_2m_c)
    """
    solar = float(np.clip(rng.normal(4.6, 0.9), 2.0, 7.5))
    wind = float(np.clip(rng.normal(6.8, 1.8), 2.0, 13.0))
    temp = float(np.clip(rng.normal(15.0, 7.0), -10.0, 35.0))
    if allow_defaults:
        # Small probability of returning "moderate" values to mimic coarse regional products
        if rng.random() < 0.05:
            return 4.0, 6.0, 15.0
    return solar, wind, temp


def sample_points_from_area(
    gdf: gpd.GeoDataFrame, n_points: int = 1000, seed: int = 42
) -> gpd.GeoDataFrame:
    """Generate sample points within a geographic area."""
    bounds = gdf.total_bounds
    np.random.seed(seed)
    
    points = []
    for _ in range(n_points * 10):  # Generate more than needed, then filter
        x = np.random.uniform(bounds[0], bounds[2])
        y = np.random.uniform(bounds[1], bounds[3])
        point = Point(x, y)
        
        # Check if point is within any geometry
        if gdf.contains(point).any():
            points.append(point)
            if len(points) >= n_points:
                break
    
    if not points:
        # Fallback: use centroids of geometries
        points = [geom.centroid for geom in gdf.geometry]
    
    return gpd.GeoDataFrame(geometry=points[:n_points], crs=gdf.crs)


def extract_features_for_point(
    point: Point,
    catalog: DatasetCatalog,
    buffer_m: float = 5000.0,
    *,
    rng: np.random.Generator | None = None,
    corine_geoms: list[Any] | None = None,
    corine_codes: list[str] | None = None,
    corine_tree: STRtree | None = None,
    natura_geoms: list[Any] | None = None,
    natura_tree: STRtree | None = None,
    cities_geoms: list[Any] | None = None,
    cities_tree: STRtree | None = None,
    project_type: str | None = None,
) -> dict[str, Any]:
    """
    Extract features for a single point.

    IMPORTANT: This function is optimized for training-data generation speed:
    - reference layers are expected to be preloaded (CORINE/Natura/Cities) and passed in
    - avoids per-point file reads and expensive clip/overlay operations
    """
    features: dict[str, Any] = {}
    rng = rng or np.random.default_rng(42)
    
    # Randomize buffer to introduce realistic AOI size variance
    # (kept deterministic via rng)
    if buffer_m <= 0:
        buffer_m = 5000.0
    buffer_m = float(np.clip(rng.normal(buffer_m, buffer_m * 0.35), 500.0, 12000.0))
    buffer_area_ha = (np.pi * (buffer_m**2)) / 10000.0  # hectares
    
    features["aoi_area_ha"] = buffer_area_ha

    # --- Land cover ratios (fast synthetic using CORINE code-at-point if available) ---
    corine_code: str | None = None
    if corine_tree is not None and corine_codes is not None:
        try:
            hits = corine_tree.query(point, predicate="within")
            if len(hits) > 0:
                corine_code = str(corine_codes[int(hits[0])])
        except Exception:
            corine_code = None

    natural_ratio, agri_ratio, impervious_ratio = _sample_land_use_ratios(rng, corine_code)
    features["natural_habitat_ratio"] = natural_ratio
    features["agricultural_ratio"] = agri_ratio
    features["impervious_surface_ratio"] = impervious_ratio

    # --- Protected areas (Natura) ---
    protected_overlap_pct = 0.0
    distance_to_protected_km = 999.0
    if natura_tree is not None and natura_geoms is not None and len(natura_geoms) > 0:
        try:
            within_hits = natura_tree.query(point, predicate="within")
            if len(within_hits) > 0:
                protected_overlap_pct = float(np.clip(rng.normal(35.0, 20.0), 5.0, 100.0))
                distance_to_protected_km = 0.0
            else:
                nearest_idx = int(natura_tree.nearest(point))
                dist_m = float(point.distance(natura_geoms[nearest_idx]))
                distance_to_protected_km = dist_m / 1000.0
                protected_overlap_pct = 0.0
        except Exception:
            protected_overlap_pct = 0.0
            distance_to_protected_km = 999.0
    features["protected_area_overlap_pct"] = protected_overlap_pct
    features["distance_to_protected_km"] = distance_to_protected_km

    # --- Distance to settlements (cities) ---
    if cities_tree is not None and cities_geoms is not None and len(cities_geoms) > 0:
        try:
            nearest_idx = int(cities_tree.nearest(point))
            dist_m = float(point.distance(cities_geoms[nearest_idx]))
            features["distance_to_settlement_km"] = dist_m / 1000.0
        except Exception:
            features["distance_to_settlement_km"] = float(np.clip(rng.normal(12.0, 6.0), 0.5, 60.0))
    else:
        features["distance_to_settlement_km"] = float(np.clip(rng.normal(12.0, 6.0), 0.5, 60.0))

    # --- Environmental proxies (fast, variable) ---
    # These are synthetic indices derived from land-use + distances, meant for training stability.
    frag = _clip01(0.15 + impervious_ratio * 0.75 + agri_ratio * 0.25 + rng.normal(0.0, 0.08))
    conn = _clip01(natural_ratio * 0.85 + rng.normal(0.0, 0.08))
    eco = _clip01(natural_ratio * 0.95 - impervious_ratio * 0.35 + rng.normal(0.0, 0.10))
    erosion = _clip01(agri_ratio * 0.55 + (1.0 - natural_ratio) * 0.25 + rng.normal(0.0, 0.10))
    water_reg = _clip01(natural_ratio * 0.75 + rng.normal(0.0, 0.10))
    land_eff = _clip01(agri_ratio * 0.55 + impervious_ratio * 0.15 + rng.normal(0.0, 0.12))

    features["habitat_fragmentation_index"] = frag
    features["connectivity_index"] = conn
    features["ecosystem_service_value"] = eco
    features["soil_erosion_risk"] = erosion
    features["water_regulation_capacity"] = water_reg
    features["land_use_efficiency"] = land_eff

    # --- Resource efficiency index ---
    features["resource_efficiency_index"] = float(rng.uniform(0.0, 1.0))

    # --- Project type indicators (RESM) ---
    if project_type is None:
        project_type = "solar" if rng.random() < 0.6 else "wind"
    features["project_type_solar"] = 1.0 if project_type == "solar" else 0.0
    features["project_type_wind"] = 1.0 if project_type == "wind" else 0.0

    # --- Weather features (fast stochastic fallback) ---
    solar, wind, temp = _sample_weather(rng, allow_defaults=True)
    features["solar_ghi_kwh_m2_day"] = solar
    features["wind_speed_100m_ms"] = wind
    features["temperature_2m_c"] = temp
    
    return features


def generate_training_data_resm(
    catalog: DatasetCatalog,
    output_path: Path,
    n_samples: int = 2000,
    *,
    seed: int = 42,
) -> None:
    """Generate training data for RESM model."""
    print(f"Generating RESM training data ({n_samples} samples)...")
    rng = np.random.default_rng(seed)
    
    # Get a reference area (use CORINE bounds)
    corine_geoms: list[Any] | None = None
    corine_codes: list[str] | None = None
    corine_tree: STRtree | None = None
    natura_geoms: list[Any] | None = None
    natura_tree: STRtree | None = None
    cities_geoms: list[Any] | None = None
    cities_tree: STRtree | None = None

    try:
        corine_path = catalog.corine()
        corine = gpd.read_file(corine_path, rows=3000)  # sample for speed + variety
        corine = _safe_to_crs(corine, "EPSG:3035")
        class_field = _pick_corine_class_field(corine)
        if class_field:
            corine_geoms = list(corine.geometry.values)
            corine_codes = [str(v) for v in corine[class_field].astype(str).values]
            corine_tree = _build_strtree(corine_geoms)
        sample_points = sample_points_from_area(corine, n_samples, seed=seed)
    except Exception as e:
        print(f"Warning: Could not sample from CORINE, using synthetic points: {e}")
        # Generate synthetic points in Europe (EPSG:3035 bounds)
        bounds = [2500000, 1500000, 6500000, 5500000]  # Approximate Europe bounds
        points = [
            Point(rng.uniform(bounds[0], bounds[2]), rng.uniform(bounds[1], bounds[3]))
            for _ in range(n_samples)
        ]
        sample_points = gpd.GeoDataFrame(geometry=points, crs="EPSG:3035")

    # Load Natura and Cities once (optional)
    try:
        natura_path = catalog.natura2000()
        if natura_path:
            natura = gpd.read_file(natura_path)
            natura = _safe_to_crs(natura, "EPSG:3035")
            natura_geoms = list(natura.geometry.values)
            natura_tree = _build_strtree(natura_geoms)
    except Exception:
        natura_geoms, natura_tree = None, None
    try:
        cities_path = catalog._search("cities", ["*.shp", "*.gpkg"])
        if cities_path:
            cities = gpd.read_file(cities_path)
            cities = _safe_to_crs(cities, "EPSG:3035")
            cities_geoms = list(cities.geometry.values)
            cities_tree = _build_strtree(cities_geoms)
    except Exception:
        cities_geoms, cities_tree = None, None
    
    # Extract features
    features_list = []
    for idx, point in enumerate(sample_points.geometry):
        if (idx + 1) % 100 == 0:
            print(f"  Processing point {idx + 1}/{n_samples}...")
        try:
            project_type = "solar" if rng.random() < 0.6 else "wind"
            features = extract_features_for_point(
                point,
                catalog,
                rng=rng,
                corine_geoms=corine_geoms,
                corine_codes=corine_codes,
                corine_tree=corine_tree,
                natura_geoms=natura_geoms,
                natura_tree=natura_tree,
                cities_geoms=cities_geoms,
                cities_tree=cities_tree,
                project_type=project_type,
            )
            features_list.append(features)
        except Exception as e:
            print(f"  Warning: Failed to extract features for point {idx + 1}: {e}")
            continue
    
    df = pd.DataFrame(features_list)
    
    # Generate labels (suitability_score 0-100) based on domain expertise
    # Refined rules based on renewable energy suitability factors:
    # 1. Land use: Agricultural land is most suitable (weight: 25%)
    # 2. Environmental constraints: Protected areas reduce suitability (weight: 20%)
    # 3. Weather resources: Solar/wind availability (weight: 25% if available)
    # 4. Infrastructure: Distance to settlements (weight: 10%)
    # 5. Environmental quality: Fragmentation, connectivity (weight: 20%)
    
    # Base suitability from land use (agricultural > natural > impervious)
    land_use_score = (
        df["agricultural_ratio"] * 0.5 +  # Agricultural land is highly suitable
        df["natural_habitat_ratio"] * 0.3 +  # Natural habitat is moderately suitable
        (1 - df["impervious_surface_ratio"]) * 0.2  # Less impervious = more suitable
    ) * 30
    
    # Environmental constraints (protected areas reduce suitability)
    protected_penalty = (df["protected_area_overlap_pct"] / 100.0).clip(0, 1) * 20
    distance_bonus = (1 - (df["distance_to_protected_km"] / 50.0).clip(0, 1)) * 10
    constraint_score = 30 - protected_penalty + distance_bonus
    
    # Environmental quality (connectivity, ecosystem services)
    quality_score = (
        df["connectivity_index"] * 0.4 +
        df["ecosystem_service_value"] * 0.3 +
        (1 - df["habitat_fragmentation_index"]) * 0.3
    ) * 20
    
    # Infrastructure proximity (moderate distance is ideal)
    infrastructure_score = (
        (1 - (df["distance_to_settlement_km"] / 30.0).clip(0, 1)) * 0.5 +  # Not too far
        ((df["distance_to_settlement_km"] / 30.0).clip(0, 1)) * 0.5  # Not too close
    ) * 10
    
    # Weather resources weighted by project type
    solar_norm = ((df["solar_ghi_kwh_m2_day"] - 2.5) / 5.0).clip(0, 1)  # ~2.5-7.5
    wind_norm = ((df["wind_speed_100m_ms"] - 2.0) / 11.0).clip(0, 1)  # ~2-13
    weather_score = (
        df["project_type_solar"] * solar_norm +
        df["project_type_wind"] * wind_norm
    ) * 10
    
    suitability = (
        land_use_score +
        constraint_score +
        quality_score +
        infrastructure_score +
        weather_score
    )
    # Add small noise to avoid degenerate distributions
    suitability = (suitability + rng.normal(0.0, 3.5, size=len(df))).clip(0, 100)
    df["suitability_score"] = suitability
    
    # Ensure all required columns are present (including weather features)
    required_columns = [
        "aoi_area_ha",
        "natural_habitat_ratio",
        "impervious_surface_ratio",
        "agricultural_ratio",
        "distance_to_protected_km",
        "protected_area_overlap_pct",
        "habitat_fragmentation_index",
        "connectivity_index",
        "ecosystem_service_value",
        "soil_erosion_risk",
        "distance_to_settlement_km",
        "resource_efficiency_index",
        "project_type_solar",
        "project_type_wind",
        "solar_ghi_kwh_m2_day",
        "wind_speed_100m_ms",
        "temperature_2m_c",
        "suitability_score",
    ]
    
    for col in required_columns:
        if col not in df.columns:
            df[col] = 0.0
    
    df = df[required_columns]
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == ".parquet":
        df.to_parquet(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    
    print(f"[OK] Saved RESM training data to {output_path} ({len(df)} samples)")


def generate_training_data_ahsm(
    catalog: DatasetCatalog,
    output_path: Path,
    n_samples: int = 2000,
    *,
    seed: int = 42,
) -> None:
    """Generate training data for AHSM model."""
    print(f"Generating AHSM training data ({n_samples} samples)...")
    rng = np.random.default_rng(seed + 7)
    
    # Similar to RESM but with different labels
    corine_geoms: list[Any] | None = None
    corine_codes: list[str] | None = None
    corine_tree: STRtree | None = None
    natura_geoms: list[Any] | None = None
    natura_tree: STRtree | None = None
    cities_geoms: list[Any] | None = None
    cities_tree: STRtree | None = None

    try:
        corine_path = catalog.corine()
        corine = gpd.read_file(corine_path, rows=3000)
        corine = _safe_to_crs(corine, "EPSG:3035")
        class_field = _pick_corine_class_field(corine)
        if class_field:
            corine_geoms = list(corine.geometry.values)
            corine_codes = [str(v) for v in corine[class_field].astype(str).values]
            corine_tree = _build_strtree(corine_geoms)
        sample_points = sample_points_from_area(corine, n_samples, seed=seed + 7)
    except Exception:
        bounds = [2500000, 1500000, 6500000, 5500000]
        points = [
            Point(rng.uniform(bounds[0], bounds[2]), rng.uniform(bounds[1], bounds[3]))
            for _ in range(n_samples)
        ]
        sample_points = gpd.GeoDataFrame(geometry=points, crs="EPSG:3035")

    # Load optional layers once
    try:
        natura_path = catalog.natura2000()
        if natura_path:
            natura = gpd.read_file(natura_path)
            natura = _safe_to_crs(natura, "EPSG:3035")
            natura_geoms = list(natura.geometry.values)
            natura_tree = _build_strtree(natura_geoms)
    except Exception:
        natura_geoms, natura_tree = None, None
    try:
        cities_path = catalog._search("cities", ["*.shp", "*.gpkg"])
        if cities_path:
            cities = gpd.read_file(cities_path)
            cities = _safe_to_crs(cities, "EPSG:3035")
            cities_geoms = list(cities.geometry.values)
            cities_tree = _build_strtree(cities_geoms)
    except Exception:
        cities_geoms, cities_tree = None, None
    
    features_list = []
    for idx, point in enumerate(sample_points.geometry):
        if (idx + 1) % 100 == 0:
            print(f"  Processing point {idx + 1}/{n_samples}...")
        try:
            features = extract_features_for_point(
                point,
                catalog,
                rng=rng,
                corine_geoms=corine_geoms,
                corine_codes=corine_codes,
                corine_tree=corine_tree,
                natura_geoms=natura_geoms,
                natura_tree=natura_tree,
                cities_geoms=cities_geoms,
                cities_tree=cities_tree,
            )
            features_list.append(features)
        except Exception as e:
            print(f"  Warning: Failed to extract features for point {idx + 1}: {e}")
            continue
    
    df = pd.DataFrame(features_list)
    
    # Generate labels (hazard_risk: 0-4 for very_low to very_high)
    # Higher risk for: high impervious, high erosion, low connectivity
    risk_score = (
        df["impervious_surface_ratio"] * 0.4 +
        df["soil_erosion_risk"] * 0.3 +
        (1 - df["connectivity_index"]) * 0.3
    ).clip(0, 1)
    # Add mild noise to avoid single-class collapse
    risk_score = (risk_score + rng.normal(0.0, 0.06, size=len(df))).clip(0, 1)
    # IMPORTANT: include_lowest=True so exact 0.0 does not become NaN
    df["hazard_risk"] = (
        pd.cut(
            risk_score,
            bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
            labels=[0, 1, 2, 3, 4],
            include_lowest=True,
        )
        .astype("float")
        .fillna(0)
        .astype(int)
    )
    
    # Required columns for AHSM (match model's expected fields)
    required_columns = [
        "aoi_area_ha",
        "forest_ratio",
        "water_ratio",
        "impervious_ratio",
        "agricultural_ratio",
        "habitat_fragmentation_index",
        "edge_density",
        "patch_density",
        "water_regulation_capacity",
        "soil_erosion_risk",
        "distance_to_water_km",
        "ecosystem_service_value",
        "connectivity_index",
        "hazard_risk",
    ]
    
    # Map feature names if needed
    if "impervious_surface_ratio" in df.columns and "impervious_ratio" not in df.columns:
        df["impervious_ratio"] = df["impervious_surface_ratio"]
    
    # Calculate missing AHSM-specific features if possible
    # Derive AHSM-specific features deterministically from RESM base features
    df["forest_ratio"] = (df.get("natural_habitat_ratio", 0.0) * 0.65 + rng.normal(0.0, 0.05, size=len(df))).clip(0, 1)
    df["water_ratio"] = (rng.beta(2.0, 14.0, size=len(df)) * 0.25).clip(0, 1)
    df["impervious_ratio"] = df.get("impervious_surface_ratio", 0.0)
    df["edge_density"] = (df.get("habitat_fragmentation_index", 0.5) * 120.0 + rng.normal(0.0, 10.0, size=len(df))).clip(0, None)
    df["patch_density"] = (df.get("habitat_fragmentation_index", 0.5) * 18.0 + rng.normal(0.0, 2.0, size=len(df))).clip(0, None)
    df["distance_to_water_km"] = (np.maximum(0.1, (1.0 - df["water_ratio"]) * rng.uniform(0.5, 25.0, size=len(df)))).astype(float)
    
    if "water_ratio" not in df.columns:
        df["water_ratio"] = 0.0  # Default
    
    if "edge_density" not in df.columns:
        df["edge_density"] = df.get("habitat_fragmentation_index", 0.5) * 100.0  # Approximate
    
    if "patch_density" not in df.columns:
        df["patch_density"] = df.get("habitat_fragmentation_index", 0.5) * 10.0  # Approximate
    
    if "distance_to_water_km" not in df.columns:
        df["distance_to_water_km"] = 10.0  # Default
    
    for col in required_columns:
        if col not in df.columns:
            df[col] = 0.0 if col != "hazard_risk" else 0
    
    df = df[required_columns]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == ".parquet":
        df.to_parquet(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    
    print(f"[OK] Saved AHSM training data to {output_path} ({len(df)} samples)")


def generate_training_data_cim(
    catalog: DatasetCatalog,
    output_path: Path,
    n_samples: int = 2500,
    *,
    seed: int = 42,
) -> None:
    """Generate training data for CIM model."""
    print(f"Generating CIM training data ({n_samples} samples)...")
    rng = np.random.default_rng(seed + 13)
    
    # CIM uses aggregated scores from other models
    corine_geoms: list[Any] | None = None
    corine_codes: list[str] | None = None
    corine_tree: STRtree | None = None
    natura_geoms: list[Any] | None = None
    natura_tree: STRtree | None = None
    cities_geoms: list[Any] | None = None
    cities_tree: STRtree | None = None

    try:
        corine_path = catalog.corine()
        corine = gpd.read_file(corine_path, rows=3000)
        corine = _safe_to_crs(corine, "EPSG:3035")
        class_field = _pick_corine_class_field(corine)
        if class_field:
            corine_geoms = list(corine.geometry.values)
            corine_codes = [str(v) for v in corine[class_field].astype(str).values]
            corine_tree = _build_strtree(corine_geoms)
        sample_points = sample_points_from_area(corine, n_samples, seed=seed + 13)
    except Exception:
        bounds = [2500000, 1500000, 6500000, 5500000]
        points = [
            Point(rng.uniform(bounds[0], bounds[2]), rng.uniform(bounds[1], bounds[3]))
            for _ in range(n_samples)
        ]
        sample_points = gpd.GeoDataFrame(geometry=points, crs="EPSG:3035")

    # Load optional layers once
    try:
        natura_path = catalog.natura2000()
        if natura_path:
            natura = gpd.read_file(natura_path)
            natura = _safe_to_crs(natura, "EPSG:3035")
            natura_geoms = list(natura.geometry.values)
            natura_tree = _build_strtree(natura_geoms)
    except Exception:
        natura_geoms, natura_tree = None, None
    try:
        cities_path = catalog._search("cities", ["*.shp", "*.gpkg"])
        if cities_path:
            cities = gpd.read_file(cities_path)
            cities = _safe_to_crs(cities, "EPSG:3035")
            cities_geoms = list(cities.geometry.values)
            cities_tree = _build_strtree(cities_geoms)
    except Exception:
        cities_geoms, cities_tree = None, None
    
    features_list = []
    for idx, point in enumerate(sample_points.geometry):
        if (idx + 1) % 100 == 0:
            print(f"  Processing point {idx + 1}/{n_samples}...")
        try:
            features = extract_features_for_point(
                point,
                catalog,
                rng=rng,
                corine_geoms=corine_geoms,
                corine_codes=corine_codes,
                corine_tree=corine_tree,
                natura_geoms=natura_geoms,
                natura_tree=natura_tree,
                cities_geoms=cities_geoms,
                cities_tree=cities_tree,
            )
            features_list.append(features)
        except Exception as e:
            print(f"  Warning: Failed to extract features for point {idx + 1}: {e}")
            continue
    
    df = pd.DataFrame(features_list)
    
    # Generate model scores (synthetic for now, in real scenario these would come from model predictions)
    df["resm_score"] = (
        df["natural_habitat_ratio"] * 30 +
        (1 - df["impervious_surface_ratio"]) * 20 +
        df["connectivity_index"] * 20 +
        (1 - df["distance_to_protected_km"] / 100.0).clip(0, 1) * 15 +
        df["ecosystem_service_value"] * 15
    ).clip(0, 100)
    
    df["ahsm_score"] = (
        df["impervious_surface_ratio"] * 40 +
        df["soil_erosion_risk"] * 30 +
        (1 - df["connectivity_index"]) * 30
    ).clip(0, 100)
    
    df["biodiversity_score"] = (
        df["natural_habitat_ratio"] * 40 +
        (1 - df["distance_to_protected_km"] / 50.0).clip(0, 1) * 30 +
        df["protected_area_overlap_pct"] / 100.0 * 30
    ).clip(0, 100)

    # Emissions proxies (avoid constant features)
    # ghg_emissions_intensity: higher when impervious + low natural (proxy for disturbed/industrial context)
    df["ghg_emissions_intensity"] = (
        0.25
        + df["impervious_surface_ratio"] * 1.4
        + (1 - df["natural_habitat_ratio"]) * 0.6
        + rng.normal(0.0, 0.18, size=len(df))
    ).clip(0.05, 4.0)

    # net_carbon_balance: negative is better (more sequestration potential) when natural is high
    df["net_carbon_balance"] = (
        (df["impervious_surface_ratio"] - df["natural_habitat_ratio"]) * 80.0
        + rng.normal(0.0, 12.0, size=len(df))
    ).astype(float)
    
    # Cumulative impact label (0-4: negligible to very_high) based on domain expertise
    # Refined rules: Biodiversity has highest weight (45%), followed by RESM (30%) and AHSM (25%)
    # This reflects that cumulative impact assessment prioritizes biodiversity protection
    
    # Normalize scores to 0-1 range
    resm_norm = (df["resm_score"] / 100.0).clip(0, 1)
    ahsm_norm = (df["ahsm_score"] / 100.0).clip(0, 1)
    biodiversity_norm = (df["biodiversity_score"] / 100.0).clip(0, 1)
    
    # Weighted combination (biodiversity has highest weight) + emissions signal + noise to avoid class collapse
    emissions_norm = (df["ghg_emissions_intensity"] / 4.0).clip(0, 1)
    carbon_norm = ((df["net_carbon_balance"] + 80.0) / 160.0).clip(0, 1)  # rough scaling
    impact_score = (
        resm_norm * 0.28 +  # Renewable energy suitability
        ahsm_norm * 0.22 +  # Hazard risk
        biodiversity_norm * 0.40 +  # Biodiversity (highest weight)
        emissions_norm * 0.06 +
        carbon_norm * 0.04
    )
    # Add noise to prevent narrow distributions collapsing into 1-2 classes
    impact_score = (impact_score + rng.normal(0.0, 0.12, size=len(df))).clip(0, 1)

    # Prefer quantile-based binning for synthetic labels (reduces severe imbalance)
    try:
        df["cumulative_impact_class"] = pd.qcut(
            impact_score,
            q=5,
            labels=[0, 1, 2, 3, 4],
            duplicates="drop",
        ).astype(int)
    except Exception:
        df["cumulative_impact_class"] = pd.cut(
            impact_score,
            bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
            labels=[0, 1, 2, 3, 4],
        ).astype(int)
    
    # Required columns for CIM
    required_columns = [
        "resm_score",
        "ahsm_score",
        "biodiversity_score",
        "distance_to_protected_km",
        "protected_overlap_pct",
        "habitat_fragmentation_index",
        "connectivity_index",
        "ecosystem_service_value",
        "ghg_emissions_intensity",
        "net_carbon_balance",
        "land_use_efficiency",
        "natural_habitat_ratio",
        "soil_erosion_risk",
        "water_regulation_capacity",
        "cumulative_impact_class",
    ]
    
    # Add missing columns with defaults (should not happen in normal flow)
    if "protected_overlap_pct" not in df.columns:
        df["protected_overlap_pct"] = df.get("protected_area_overlap_pct", 0.0)
    if "ghg_emissions_intensity" not in df.columns:
        df["ghg_emissions_intensity"] = rng.uniform(0.2, 2.0, size=len(df))
    if "net_carbon_balance" not in df.columns:
        df["net_carbon_balance"] = rng.normal(0.0, 25.0, size=len(df))
    
    for col in required_columns:
        if col not in df.columns:
            df[col] = 0.0 if col != "cumulative_impact_class" else 0
    
    df = df[required_columns]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == ".parquet":
        df.to_parquet(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    
    print(f"[OK] Saved CIM training data to {output_path} ({len(df)} samples)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare training data for ML models")
    parser.add_argument(
        "--data-sources-dir",
        type=Path,
        default=settings.data_sources_dir,
        help="Directory containing source datasets (default: data2)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=settings.data_sources_dir,
        help="Directory to save training data (default: data_sources_dir)",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=["resm", "ahsm", "cim", "all"],
        default=["all"],
        help="Models to generate training data for",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=2000,
        help="Number of training samples to generate (default: 2000)",
    )
    parser.add_argument(
        "--format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Output format (default: parquet)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated training data quality",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible generation (default: 42)",
    )
    parser.add_argument(
        "--continue-on-invalid",
        action="store_true",
        help="Continue generating other models even if validation fails for one model",
    )
    
    args = parser.parse_args()
    
    catalog = DatasetCatalog(args.data_sources_dir)
    
    models_to_generate = ["resm", "ahsm", "cim"] if "all" in args.models else args.models
    any_invalid = False
    
    for model in models_to_generate:
        output_path = args.output_dir / model / f"training.{args.format}"
        
        if model == "resm":
            generate_training_data_resm(catalog, output_path, args.n_samples, seed=args.seed)
        elif model == "ahsm":
            generate_training_data_ahsm(catalog, output_path, args.n_samples, seed=args.seed)
        elif model == "cim":
            generate_training_data_cim(catalog, output_path, args.n_samples, seed=args.seed)
        
        # Validate generated data if requested
        if args.validate:
            print(f"\nValidating {model} training data...")
            try:
                sys.path.insert(0, str(Path(__file__).parent))
                from validate_training_data import validate_training_data, print_validation_report
                validation_results = validate_training_data(output_path, model)
                print_validation_report(validation_results)
                if not validation_results.get("is_valid", False):
                    any_invalid = True
                    if not args.continue_on_invalid:
                        print("[ERROR] Validation failed. Stopping (use --continue-on-invalid to proceed).")
                        sys.exit(1)
            except Exception as e:
                print(f"[WARN] Validation failed: {e}")
                any_invalid = True
                if not args.continue_on_invalid:
                    sys.exit(1)
    
    print("\n[OK] Training data generation complete!")
    if any_invalid:
        # Signal failure to callers that want strict validation.
        sys.exit(1)


if __name__ == "__main__":
    main()

