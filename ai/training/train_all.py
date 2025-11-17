"""Train all AETHERA models in sequence."""

from __future__ import annotations

import argparse
import logging

from .train_ahsm import train_ahsm
from .train_biodiversity import train_biodiversity
from .train_cim import train_cim
from .train_resm import train_resm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_all(
    training_data_dir: str | None = None,
    output_dir: str | None = None,
    use_mlflow: bool = True,
    use_wandb: bool = False,
    mlflow_tracking_uri: str | None = None,
) -> None:
    """Train all AETHERA models."""
    logger.info("Starting training for all models...")

    base_output = output_dir or "models"

    # Train Biodiversity (mandatory)
    logger.info("=" * 60)
    logger.info("Training Biodiversity AI Model")
    logger.info("=" * 60)
    train_biodiversity(
        training_data_path=f"{training_data_dir}/biodiversity/training.csv" if training_data_dir else None,
        output_dir=f"{base_output}/biodiversity",
        use_mlflow=use_mlflow,
        use_wandb=use_wandb,
        mlflow_tracking_uri=mlflow_tracking_uri,
    )

    # Train RESM
    logger.info("=" * 60)
    logger.info("Training RESM Model")
    logger.info("=" * 60)
    train_resm(
        training_data_path=f"{training_data_dir}/resm/training.csv" if training_data_dir else None,
        output_dir=f"{base_output}/resm",
        use_mlflow=use_mlflow,
        use_wandb=use_wandb,
        mlflow_tracking_uri=mlflow_tracking_uri,
    )

    # Train AHSM
    logger.info("=" * 60)
    logger.info("Training AHSM Model")
    logger.info("=" * 60)
    train_ahsm(
        training_data_path=f"{training_data_dir}/ahsm/training.csv" if training_data_dir else None,
        output_dir=f"{base_output}/ahsm",
        use_mlflow=use_mlflow,
        use_wandb=use_wandb,
        mlflow_tracking_uri=mlflow_tracking_uri,
    )

    # Train CIM
    logger.info("=" * 60)
    logger.info("Training CIM Model")
    logger.info("=" * 60)
    train_cim(
        training_data_path=f"{training_data_dir}/cim/training.csv" if training_data_dir else None,
        output_dir=f"{base_output}/cim",
        use_mlflow=use_mlflow,
        use_wandb=use_wandb,
        mlflow_tracking_uri=mlflow_tracking_uri,
    )

    logger.info("=" * 60)
    logger.info("All models trained successfully!")
    logger.info("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train all AETHERA models")
    parser.add_argument("--training-data-dir", type=str, help="Directory containing training data")
    parser.add_argument("--output-dir", type=str, help="Output directory for models")
    parser.add_argument("--no-mlflow", action="store_true", help="Disable MLflow tracking")
    parser.add_argument("--wandb", action="store_true", help="Enable W&B tracking")
    parser.add_argument("--mlflow-uri", type=str, help="MLflow tracking URI")
    args = parser.parse_args()

    train_all(
        training_data_dir=args.training_data_dir,
        output_dir=args.output_dir,
        use_mlflow=not args.no_mlflow,
        use_wandb=args.wandb,
        mlflow_tracking_uri=args.mlflow_uri,
    )


if __name__ == "__main__":
    main()

