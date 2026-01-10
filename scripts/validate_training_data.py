"""
Validate training data quality for ML models.

Checks for:
- Missing values
- Outliers
- Data distributions
- Feature correlations
- Label distribution
- Data consistency
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def validate_training_data(
    data_path: Path,
    model_name: str,
    label_column: str | None = None,
    min_samples: int = 100,
) -> dict[str, Any]:
    """
    Validate training data quality.
    
    Args:
        data_path: Path to training data file (CSV or Parquet)
        model_name: Name of the model (resm, ahsm, cim, biodiversity)
        label_column: Name of label column (if None, auto-detect)
        min_samples: Minimum number of samples required
        
    Returns:
        Dictionary with validation results
    """
    # Load data
    if data_path.suffix == ".parquet":
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)
    
    validation_results: dict[str, Any] = {
        "model_name": model_name,
        "file_path": str(data_path),
        "n_samples": len(df),
        "n_features": len(df.columns),
        "issues": [],
        "warnings": [],
        "stats": {},
    }
    
    # Check minimum samples
    if len(df) < min_samples:
        validation_results["issues"].append(
            f"Too few samples: {len(df)} < {min_samples} (minimum required)"
        )
    
    # Auto-detect label column if not provided
    if label_column is None:
        label_candidates = {
            "resm": ["suitability_score", "label", "target", "score"],
            "ahsm": ["hazard_risk", "risk_level", "label", "target"],
            "cim": ["cumulative_impact_class", "impact_level", "label", "target"],
            "biodiversity": ["label", "sensitivity", "target"],
        }
        candidates = label_candidates.get(model_name, ["label", "target", "score"])
        label_column = next((col for col in candidates if col in df.columns), None)
    
    if label_column and label_column in df.columns:
        validation_results["label_column"] = label_column
        
        # For regression models (RESM), compute statistics instead of distribution
        if model_name == "resm":
            label_min = df[label_column].min()
            label_max = df[label_column].max()
            label_mean = df[label_column].mean()
            label_std = df[label_column].std()
            label_median = df[label_column].median()
            label_q25 = df[label_column].quantile(0.25)
            label_q75 = df[label_column].quantile(0.75)
            label_nunique = df[label_column].nunique()
            
            validation_results["stats"]["label_stats"] = {
                "min": float(label_min),
                "max": float(label_max),
                "mean": float(label_mean),
                "std": float(label_std),
                "median": float(label_median),
                "q25": float(label_q25),
                "q75": float(label_q75),
                "nunique": int(label_nunique),
            }
            
            if label_min < 0 or label_max > 100:
                validation_results["warnings"].append(
                    f"Label values outside expected range [0, 100]: [{label_min:.2f}, {label_max:.2f}]"
                )
        else:
            # For classification models, compute distribution
            label_counts = df[label_column].value_counts()
            validation_results["stats"]["label_distribution"] = label_counts.to_dict()
            
            # Check for class imbalance (for classification models)
            if model_name in ("ahsm", "cim", "biodiversity"):
                if len(label_counts) < 2:
                    validation_results["issues"].append(
                        f"Only {len(label_counts)} unique label(s) found. Need at least 2 classes."
                    )
                else:
                    min_class_count = label_counts.min()
                    max_class_count = label_counts.max()
                    imbalance_ratio = max_class_count / min_class_count if min_class_count > 0 else float('inf')
                    if imbalance_ratio > 10:
                        validation_results["warnings"].append(
                            f"Class imbalance detected: ratio {imbalance_ratio:.2f} (max/min class counts)"
                        )
    else:
        validation_results["issues"].append("Label column not found in data")
    
    # Check for missing values
    missing_counts = df.isnull().sum()
    missing_cols = missing_counts[missing_counts > 0]
    if len(missing_cols) > 0:
        validation_results["stats"]["missing_values"] = missing_cols.to_dict()
        missing_pct = (missing_cols / len(df) * 100).max()
        if missing_pct > 50:
            validation_results["issues"].append(
                f"Some columns have >50% missing values (max: {missing_pct:.1f}%)"
            )
        elif missing_pct > 10:
            validation_results["warnings"].append(
                f"Some columns have >10% missing values (max: {missing_pct:.1f}%)"
            )
    
    # Check for outliers (using IQR method)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if label_column:
        numeric_cols = numeric_cols.drop(label_column, errors='ignore')
    
    outlier_counts = {}
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            lower_bound = Q1 - 3 * IQR  # Using 3*IQR for extreme outliers
            upper_bound = Q3 + 3 * IQR
            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            if outliers > 0:
                outlier_counts[col] = outliers
    
    if outlier_counts:
        validation_results["stats"]["outliers"] = outlier_counts
        max_outlier_pct = max(outlier_counts.values()) / len(df) * 100
        if max_outlier_pct > 5:
            validation_results["warnings"].append(
                f"Some columns have >5% outliers (max: {max_outlier_pct:.1f}%)"
            )
    
    # Check feature ranges
    feature_ranges = {}
    for col in numeric_cols:
        if col != label_column:
            col_min = df[col].min()
            col_max = df[col].max()
            feature_ranges[col] = {"min": float(col_min), "max": float(col_max)}
    
    validation_results["stats"]["feature_ranges"] = feature_ranges
    
    # Check for constant features
    constant_features = []
    for col in numeric_cols:
        if col != label_column and df[col].nunique() <= 1:
            constant_features.append(col)
    
    if constant_features:
        validation_results["issues"].append(
            f"Constant features found (no variance): {', '.join(constant_features)}"
        )
    
    # Calculate summary statistics
    validation_results["stats"]["summary"] = df[numeric_cols].describe().to_dict()
    
    # Overall validation status
    validation_results["is_valid"] = len(validation_results["issues"]) == 0
    validation_results["has_warnings"] = len(validation_results["warnings"]) > 0
    
    return validation_results


def print_validation_report(results: dict[str, Any]) -> None:
    """Print validation results in a readable format."""
    print(f"\n{'='*60}")
    print(f"Training Data Validation Report: {results['model_name'].upper()}")
    print(f"{'='*60}")
    print(f"File: {results['file_path']}")
    print(f"Samples: {results['n_samples']}")
    print(f"Features: {results['n_features']}")
    
    if results.get("label_column"):
        print(f"Label Column: {results['label_column']}")
    
    # Status
    if results["is_valid"]:
        print("\n[OK] Status: VALID")
    else:
        print("\n[ERROR] Status: INVALID")
    
    # Issues
    if results["issues"]:
        print(f"\n[ERROR] Issues ({len(results['issues'])}):")
        for issue in results["issues"]:
            print(f"  - {issue}")
    
    # Warnings
    if results["warnings"]:
        print(f"\n[WARN] Warnings ({len(results['warnings'])}):")
        for warning in results["warnings"]:
            print(f"  - {warning}")
    
    # Statistics
    model_name = results["model_name"]
    
    # For regression models (RESM), show summary statistics instead of listing all values
    if model_name == "resm" and results["stats"].get("label_stats"):
        stats = results["stats"]["label_stats"]
        print("\n[INFO] Label Statistics (Regression):")
        print(f"  Range: [{stats['min']:.2f}, {stats['max']:.2f}]")
        print(f"  Mean: {stats['mean']:.2f}")
        print(f"  Std: {stats['std']:.2f}")
        print(f"  Median: {stats['median']:.2f}")
        print(f"  25th percentile: {stats['q25']:.2f}")
        print(f"  75th percentile: {stats['q75']:.2f}")
        print(f"  Unique values: {stats['nunique']}")
    elif results["stats"].get("label_distribution"):
        # For classification models, show class distribution
        label_dist = results["stats"]["label_distribution"]
        print("\n[INFO] Label Distribution:")
        for label, count in sorted(label_dist.items()):
            print(f"  {label}: {count} ({count/results['n_samples']*100:.1f}%)")
    
    if results["stats"].get("missing_values"):
        print("\n[INFO] Missing Values:")
        for col, count in list(results["stats"]["missing_values"].items())[:10]:
            print(f"  {col}: {count} ({count/results['n_samples']*100:.1f}%)")
    
    print(f"\n{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate training data quality")
    parser.add_argument(
        "data_path",
        type=Path,
        help="Path to training data file (CSV or Parquet)",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        choices=["resm", "ahsm", "cim", "biodiversity"],
        help="Model name",
    )
    parser.add_argument(
        "--label-column",
        type=str,
        default=None,
        help="Label column name (auto-detect if not provided)",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=100,
        help="Minimum number of samples required (default: 100)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    
    args = parser.parse_args()
    
    if not args.data_path.exists():
        print(f"Error: File not found: {args.data_path}")
        sys.exit(1)
    
    results = validate_training_data(
        data_path=args.data_path,
        model_name=args.model,
        label_column=args.label_column,
        min_samples=args.min_samples,
    )
    
    if args.json:
        import json
        print(json.dumps(results, indent=2, default=str))
    else:
        print_validation_report(results)
    
    # Exit with error code if validation failed
    if not results["is_valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

