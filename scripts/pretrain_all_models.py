"""
Pretrain all ML models and save them for faster inference.

This script trains all models (RESM, AHSM, CIM, Biodiversity) using available
training data and saves them to disk. This avoids training delays during
analysis runs and prevents server timeouts.

Usage:
    python scripts/pretrain_all_models.py --models all
    python scripts/pretrain_all_models.py --models resm ahsm cim biodiversity
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.config.base_settings import settings
from backend.src.datasets.catalog import DatasetCatalog

# Import models
from ai.models.resm import RESMEnsemble, RESMConfig, RESMModel
from ai.models.ahsm import AHSMEnsemble, AHSMConfig, AHSMModel
from ai.models.cim import CIMEnsemble, CIMConfig, CIMModel
from ai.models.biodiversity import BiodiversityEnsemble, BiodiversityConfig, BiodiversityModel


MODELS_DIR = PROJECT_ROOT / "models" / "pretrained"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def save_pretrained_model(
    model_name: str,
    ensemble: Any,
    metadata: dict[str, Any],
) -> Path:
    """
    Save a pretrained model ensemble to disk.
    
    Args:
        model_name: Name of the model (resm, ahsm, cim, biodiversity)
        ensemble: The trained ensemble object
        metadata: Metadata about the model (dataset_source, feature_count, etc.)
        
    Returns:
        Path to saved model file
    """
    model_dir = MODELS_DIR / model_name
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the ensemble models
    model_file = model_dir / "ensemble.pkl"
    joblib.dump(ensemble._models, model_file)
    
    # Save metadata
    metadata_file = model_dir / "metadata.json"
    metadata.update({
        "model_name": model_name,
        "vector_fields": ensemble.vector_fields if hasattr(ensemble, "vector_fields") else None,
        "dataset_source": ensemble.dataset_source if hasattr(ensemble, "dataset_source") else "unknown",
    })
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    
    # Save config if available
    if hasattr(ensemble, "config") and ensemble.config:
        config_file = model_dir / "config.json"
        config_dict = {
            "name": ensemble.config.name if hasattr(ensemble.config, "name") else model_name,
            "training_data_path": (
                str(ensemble.config.training_data_path) 
                if hasattr(ensemble.config, "training_data_path") and ensemble.config.training_data_path
                else None
            ),
        }
        with open(config_file, "w") as f:
            json.dump(config_dict, f, indent=2)
    
    print(f"[OK] Saved {model_name} model to {model_file}")
    print(f"   Metadata: {metadata_file}")
    
    return model_file


def pretrain_resm(catalog: DatasetCatalog, use_existing_data: bool = True) -> dict[str, Any]:
    """Pretrain RESM model."""
    print("\n" + "="*60)
    print("Pretraining RESM (Renewable Energy Suitability Model)")
    print("="*60)
    
    # Force training even if pretrained artifacts already exist
    config = RESMConfig(use_pretrained=False)
    if use_existing_data:
        training_data_path = catalog.resm_training()
        if training_data_path:
            config.training_data_path = str(training_data_path)
            print(f"Using training data: {training_data_path}")
        else:
            print("No training data found, using synthetic data")
    else:
        print("Using synthetic data")
    
    # Create and train ensemble
    ensemble = RESMEnsemble(config=config)
    
    # Get metadata
    metadata = {
        "dataset_source": ensemble.dataset_source,
        "n_features": len(ensemble.vector_fields),
        "n_models": len(ensemble._models),
    }
    
    # Save model
    save_pretrained_model("resm", ensemble, metadata)
    
    return metadata


def pretrain_ahsm(catalog: DatasetCatalog, use_existing_data: bool = True) -> dict[str, Any]:
    """Pretrain AHSM model."""
    print("\n" + "="*60)
    print("Pretraining AHSM (Asset Hazard Susceptibility Model)")
    print("="*60)
    
    # Force training even if pretrained artifacts already exist
    config = AHSMConfig(use_pretrained=False)
    if use_existing_data:
        training_data_path = catalog.ahsm_training()
        if training_data_path:
            config.training_data_path = str(training_data_path)
            print(f"Using training data: {training_data_path}")
        else:
            print("No training data found, using synthetic data")
    else:
        print("Using synthetic data")
    
    # Create and train ensemble
    ensemble = AHSMEnsemble(config=config)
    
    # Get metadata
    metadata = {
        "dataset_source": ensemble.dataset_source,
        "n_features": len(ensemble.vector_fields),
        "n_models": len(ensemble._models),
    }
    
    # Save model
    save_pretrained_model("ahsm", ensemble, metadata)
    
    return metadata


def pretrain_cim(catalog: DatasetCatalog, use_existing_data: bool = True) -> dict[str, Any]:
    """Pretrain CIM model."""
    print("\n" + "="*60)
    print("Pretraining CIM (Cumulative Impact Model)")
    print("="*60)
    
    # Force training even if pretrained artifacts already exist
    config = CIMConfig(use_pretrained=False)
    if use_existing_data:
        training_data_path = catalog.cim_training()
        if training_data_path:
            config.training_data_path = str(training_data_path)
            print(f"Using training data: {training_data_path}")
        else:
            print("No training data found, using synthetic data")
    else:
        print("Using synthetic data")
    
    # Create and train ensemble
    ensemble = CIMEnsemble(config=config)
    
    # Get metadata
    metadata = {
        "dataset_source": ensemble.dataset_source,
        "n_features": len(ensemble.vector_fields),
        "n_models": len(ensemble._models),
    }
    
    # Save model
    save_pretrained_model("cim", ensemble, metadata)
    
    return metadata


def pretrain_biodiversity(catalog: DatasetCatalog, use_existing_data: bool = True) -> dict[str, Any]:
    """Pretrain Biodiversity model."""
    print("\n" + "="*60)
    print("Pretraining Biodiversity Model")
    print("="*60)
    
    # Force training even if pretrained artifacts already exist
    config = BiodiversityConfig(use_pretrained=False)
    if use_existing_data:
        training_data_path = catalog.biodiversity_training()
        if training_data_path:
            config.training_data_path = str(training_data_path)
            print(f"Using training data: {training_data_path}")
        else:
            print("No training data found, using synthetic data")
    else:
        print("Using synthetic data")
    
    # Create and train ensemble
    ensemble = BiodiversityEnsemble(config=config)
    
    # Get metadata
    metadata = {
        "dataset_source": ensemble.dataset_source,
        "n_features": len(ensemble.vector_fields),
        "n_models": len(ensemble._models),
    }
    
    # Save model
    save_pretrained_model("biodiversity", ensemble, metadata)
    
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pretrain all ML models and save them for faster inference"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=["resm", "ahsm", "cim", "biodiversity", "all"],
        default=["all"],
        help="Models to pretrain (default: all)",
    )
    parser.add_argument(
        "--data-sources-dir",
        type=Path,
        default=settings.data_sources_dir,
        help="Directory containing training data (default: data2)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip models that are already pretrained",
    )
    parser.add_argument(
        "--force-synthetic",
        action="store_true",
        help="Force use of synthetic data instead of existing training data",
    )
    
    args = parser.parse_args()
    
    catalog = DatasetCatalog(args.data_sources_dir)
    
    models_to_train = ["resm", "ahsm", "cim", "biodiversity"] if "all" in args.models else args.models
    
    print("="*60)
    print("PRETRAINING ML MODELS")
    print("="*60)
    print(f"Models directory: {MODELS_DIR}")
    print(f"Models to train: {', '.join(models_to_train)}")
    print(f"Use existing training data: {not args.force_synthetic}")
    print("="*60)
    
    results = {}
    
    for model_name in models_to_train:
        if args.skip_existing:
            model_file = MODELS_DIR / model_name / "ensemble.pkl"
            if model_file.exists():
                print(f"\n⏭️  Skipping {model_name} (already pretrained)")
                continue
        
        try:
            if model_name == "resm":
                metadata = pretrain_resm(catalog, use_existing_data=not args.force_synthetic)
            elif model_name == "ahsm":
                metadata = pretrain_ahsm(catalog, use_existing_data=not args.force_synthetic)
            elif model_name == "cim":
                metadata = pretrain_cim(catalog, use_existing_data=not args.force_synthetic)
            elif model_name == "biodiversity":
                metadata = pretrain_biodiversity(catalog, use_existing_data=not args.force_synthetic)
            
            results[model_name] = {"status": "success", "metadata": metadata}
        except Exception as e:
            print(f"\n[ERROR] Error pretraining {model_name}: {e}")
            import traceback
            traceback.print_exc()
            results[model_name] = {"status": "error", "error": str(e)}
    
    # Summary
    print("\n" + "="*60)
    print("PRETRAINING SUMMARY")
    print("="*60)
    for model_name, result in results.items():
        status = result["status"]
        if status == "success":
            print(f"[OK] {model_name}: Success")
            if "metadata" in result:
                meta = result["metadata"]
                print(f"   Dataset: {meta.get('dataset_source', 'unknown')}")
                print(f"   Features: {meta.get('n_features', 'unknown')}")
                print(f"   Models: {meta.get('n_models', 'unknown')}")
        else:
            print(f"[ERROR] {model_name}: Failed - {result.get('error', 'unknown error')}")
    
    print(f"\n[OK] Pretrained models saved to: {MODELS_DIR}")
    print("\nNext steps:")
    print("1. Models are now available for fast inference")
    print("2. Update model initialization code to load pretrained models")
    print("3. Run analyses - models will load instantly instead of training")


if __name__ == "__main__":
    main()

