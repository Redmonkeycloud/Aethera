# emissions_api.py
"""
AETHERA Emissions API
- Configurable IPCC-like emission factors (tCO2e/ha/year) with country overrides
- CORINE label → emission category mapping
- Annual and multi-year totals
- Monte Carlo uncertainty
- Land-use change (before/after) transition accounting
"""

from __future__ import annotations
import math
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------
# Factor registry (tCO2e / ha / year)
# ---------------------------------------------------------------------

# Base Tier 1-ish defaults (sign indicates sink vs source)
BASE_FACTORS = {
    "forest":      -5.8,   # sequestration
    "cropland":     3.2,
    "grassland":    1.2,
    "wetlands":    -2.4,
    "urban":        0.0,
    "water":        0.0,
    "other":        0.0,
}

# Optional country-specific overrides (example placeholders; expand as you collect sources)
COUNTRY_OVERRIDES = {
    # "GRC": {"forest": -6.2, "cropland": 3.8},
    # "ITA": {"cropland": 3.4},
    # "ESP": {"grassland": 1.0},
}

# Optional uncertainty (relative ±% at 1σ). Used for Monte Carlo.
FACTOR_UNCERTAINTY = {
    "forest":   0.25,
    "cropland": 0.30,
    "grassland":0.30,
    "wetlands": 0.35,
    "urban":    0.10,
    "water":    0.10,
    "other":    0.30,
}

# ---------------------------------------------------------------------
# CORINE → category mapping
# Accepts either numeric codes (e.g., 311) or labels you've already created
# ---------------------------------------------------------------------

CORINE_TO_CATEGORY = {
    # Urban
    111: "urban", 112: "urban", 121: "urban", 122: "urban", 123: "urban",
    124: "urban", 131: "urban", 132: "urban", 133: "urban", 141: "urban", 142: "urban",

    # Cropland / agriculture
    211: "cropland", 212: "cropland", 213: "cropland",
    221: "cropland", 222: "cropland", 223: "cropland",
    231: "grassland",  # pastures

    # Forests & seminatural
    311: "forest", 312: "forest", 313: "forest",
    321: "grassland", 322: "grassland", 323: "grassland",
    324: "other",     331: "other", 332: "other", 333: "other",

    # Wetlands
    411: "wetlands", 412: "wetlands", 421: "wetlands", 422: "wetlands",

    # Water
    511: "water", 512: "water", 521: "water", 522: "water", 523: "water",
}

LABEL_TO_CATEGORY = {
    "Continuous Urban Fabric": "urban",
    "Discontinuous Urban Fabric": "urban",
    "Industrial or Commercial Units": "urban",
    "Mineral Extraction Sites": "urban",
    "Non-Irrigated Arable Land": "cropland",
    "Pastures": "grassland",
    "Broad-leaved Forest": "forest",
    "Coniferous Forest": "forest",
    "Mixed Forest": "forest",
    "Natural Grasslands": "grassland",
    "Inland Marshes": "wetlands",
    "Water Courses": "water",
    "Water Bodies": "water",
    # Add your expanded labels here as you grow CORINE_CODES
}

# ---------------------------------------------------------------------
# Factor resolution
# ---------------------------------------------------------------------

def get_factor(category: str, country: Optional[str] = None) -> float:
    """Return emission factor (tCO2e/ha/yr) for category with optional country override."""
    category = category.lower()
    if country and country in COUNTRY_OVERRIDES and category in COUNTRY_OVERRIDES[country]:
        return float(COUNTRY_OVERRIDES[country][category])
    return float(BASE_FACTORS.get(category, BASE_FACTORS["other"]))

def get_factor_sigma(category: str) -> float:
    """Return 1σ relative uncertainty for category."""
    return float(FACTOR_UNCERTAINTY.get(category.lower(), FACTOR_UNCERTAINTY["other"]))

# ---------------------------------------------------------------------
# Helpers to normalize inputs from CORINE summaries
# ---------------------------------------------------------------------

def _infer_category(key) -> str:
    """Accepts numeric CORINE code or string label and returns emission category."""
    # numeric code?
    try:
        code = int(key)
        return CORINE_TO_CATEGORY.get(code, "other")
    except (ValueError, TypeError):
        pass
    # label?
    if isinstance(key, str):
        return LABEL_TO_CATEGORY.get(key, "other")
    return "other"

def from_corine_summary(df: pd.DataFrame,
                        code_col: str = "corine_code",
                        label_col: str = "land_cover",
                        area_col: str = "area_hectares") -> Dict[str, float]:
    """
    Collapse CORINE summary to emission categories → total area (ha).
    Accepts either numeric codes or your mapped labels.
    """
    if df.empty:
        return {}

    # Prefer code column if present; fallback to label
    if code_col in df.columns and df[code_col].notna().any():
        # Some code columns may be float (e.g., 311.0); cast to int safely
        cats = df[code_col].apply(lambda v: _infer_category(int(v) if pd.notna(v) else v))
    else:
        cats = df[label_col].apply(_infer_category)

    tmp = df.assign(_cat=cats)
    out = tmp.groupby("_cat", dropna=False)[area_col].sum().to_dict()
    # ensure all known categories exist
    for k in BASE_FACTORS:
        out.setdefault(k, 0.0)
    return out

# ---------------------------------------------------------------------
# Core estimation
# ---------------------------------------------------------------------

def estimate_emissions(land_cover_stats: Dict[str, float],
                       country: Optional[str] = None,
                       years: int = 1) -> pd.DataFrame:
    """
    Estimate emissions for given areas by category (ha).
    Returns per-category rows and totals.
    """
    rows = []
    for cat, area_ha in land_cover_stats.items():
        # Accept either category names or labels; normalize
        category = _infer_category(cat)
        factor = get_factor(category, country)
        annual = factor * float(area_ha)
        total = annual * years
        rows.append({
            "category": category,
            "area_hectares": float(area_ha),
            "factor_tCO2e_per_ha_yr": factor,
            "annual_tCO2e": annual,
            "years": years,
            "total_tCO2e": total,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    totals = pd.DataFrame([{
        "category": "TOTAL",
        "area_hectares": df["area_hectares"].sum(),
        "factor_tCO2e_per_ha_yr": np.nan,
        "annual_tCO2e": df["annual_tCO2e"].sum(),
        "years": years,
        "total_tCO2e": df["total_tCO2e"].sum(),
    }])
    return pd.concat([df, totals], ignore_index=True)

# ---------------------------------------------------------------------
# Monte Carlo uncertainty
# ---------------------------------------------------------------------

def monte_carlo_emissions(land_cover_stats: Dict[str, float],
                          country: Optional[str] = None,
                          years: int = 1,
                          n_sim: int = 2000,
                          distribution: str = "lognormal",
                          random_seed: Optional[int] = 42) -> pd.DataFrame:
    """
    Monte Carlo uncertainty propagation over emission factors.
    Returns summary statistics (mean, p05, p50, p95) for total_tCO2e.
    """
    rng = np.random.default_rng(random_seed)
    totals = []

    categories = list(land_cover_stats.keys())
    areas = np.array([float(land_cover_stats[c]) for c in categories], dtype=float)
    norm_cats = [_infer_category(c) for c in categories]
    base_factors = np.array([get_factor(c, country) for c in norm_cats], dtype=float)
    sigmas = np.array([get_factor_sigma(c) for c in norm_cats], dtype=float)

    # Precompute parameters for lognormal if chosen
    if distribution == "lognormal":
        # Convert mean and relative sigma to log-space parameters
        # Assume factor > 0 for lognormal; for negative factors (sinks), use normal as fallback.
        use_logn = base_factors > 0
        mu = np.zeros_like(base_factors, dtype=float)
        sigma_ln = np.zeros_like(base_factors, dtype=float)
        with np.errstate(invalid="ignore"):
            sigma_ln[use_logn] = np.sqrt(np.log(1 + (sigmas[use_logn] ** 2)))
            mu[use_logn] = np.log(base_factors[use_logn]) - 0.5 * sigma_ln[use_logn] ** 2

    for _ in range(n_sim):
        sampled = np.zeros_like(base_factors)
        for i, f in enumerate(base_factors):
            rel = sigmas[i]
            if distribution == "lognormal" and f > 0:
                sampled[i] = rng.lognormal(mean=mu[i], sigma=sigma_ln[i])
            else:
                # Normal around f with stdev = |f|*rel
                sampled[i] = rng.normal(loc=f, scale=abs(f) * rel)

        annual = (sampled * areas).sum()
        totals.append(annual * years)

    totals = np.array(totals, dtype=float)
    return pd.DataFrame([{
        "n_sim": n_sim,
        "years": years,
        "total_mean_tCO2e": float(np.mean(totals)),
        "total_p05_tCO2e": float(np.percentile(totals, 5)),
        "total_p50_tCO2e": float(np.percentile(totals, 50)),
        "total_p95_tCO2e": float(np.percentile(totals, 95)),
    }])

# ---------------------------------------------------------------------
# Land-use change (before/after)
# ---------------------------------------------------------------------

def transition_emissions(before: Dict[str, float],
                         after: Dict[str, float],
                         country: Optional[str] = None,
                         years: int = 1) -> pd.DataFrame:
    """
    Simple net-change approach: (after_area - before_area) * factor * years per category.
    Positive total means net emissions; negative means net sequestration.
    """
    cats = sorted(set(before.keys()) | set(after.keys()))
    rows = []
    for c in cats:
        bc = _infer_category(c)
        a0 = float(before.get(c, 0.0))
        a1 = float(after.get(c, 0.0))
        dA = a1 - a0
        factor = get_factor(bc, country)
        annual = dA * factor
        total = annual * years
        rows.append({
            "category": bc,
            "delta_area_ha": dA,
            "factor_tCO2e_per_ha_yr": factor,
            "annual_delta_tCO2e": annual,
            "years": years,
            "total_delta_tCO2e": total,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    totals = pd.DataFrame([{
        "category": "TOTAL",
        "delta_area_ha": df["delta_area_ha"].sum(),
        "factor_tCO2e_per_ha_yr": np.nan,
        "annual_delta_tCO2e": df["annual_delta_tCO2e"].sum(),
        "years": years,
        "total_delta_tCO2e": df["total_delta_tCO2e"].sum(),
    }])
    return pd.concat([df, totals], ignore_index=True)

# ---------------------------------------------------------------------
# Convenience: wire directly from your CORINE summary DataFrame
# ---------------------------------------------------------------------

def estimate_from_corine_summary(corine_summary_df: pd.DataFrame,
                                 country: Optional[str] = None,
                                 years: int = 1,
                                 code_col: str = "corine_code",
                                 label_col: str = "land_cover",
                                 area_col: str = "area_hectares") -> pd.DataFrame:
    """
    Accept your CORINE landcover summary (from aoi_landcover_analysis.run_full_analysis)
    and return emission estimates (per category + totals).
    """
    stats = from_corine_summary(corine_summary_df, code_col=code_col, label_col=label_col, area_col=area_col)
    return estimate_emissions(stats, country=country, years=years)

# ---------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------

if __name__ == "__main__":
    # Example direct usage
    example_stats = {"forest": 150.0, "cropland": 90.0, "urban": 12.5}
    print(estimate_emissions(example_stats, country=None, years=1))

    # Example from CORINE-like summary
    df = pd.DataFrame({
        "corine_code": [311, 211, 112],
        "land_cover": ["Broad-leaved Forest", "Non-Irrigated Arable Land", "Discontinuous Urban Fabric"],
        "area_hectares": [120.0, 80.0, 10.0],
    })
    print(estimate_from_corine_summary(df, country="ITA", years=1))

    # Monte Carlo example
    mc = monte_carlo_emissions(example_stats, years=1, n_sim=1000)
    print(mc)
