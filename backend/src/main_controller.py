"""Entry point for orchestrating geospatial and analysis workflows."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import geopandas as gpd

from .analysis.biodiversity import build_biodiversity_features, compute_overlap_metrics
from .analysis.land_cover import summarize_land_cover
from .config.base_settings import settings
from .datasets.catalog import DatasetCatalog
from .db import DatabaseClient, ModelRunLogger, ModelRunRecord
from .emissions.calculator import EmissionCalculator
from .emissions.factors import EmissionFactorStore
from .gis_handler import GISHandler
from .logging_utils import configure_logging, get_logger
from .utils.geometry import buffer_aoi, load_aoi

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai.models.biodiversity import (  # type: ignore  # noqa: E402
    BiodiversityConfig,
    BiodiversityModel,
)


logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an AETHERA analysis pipeline.")
    parser.add_argument("--aoi", required=True, help="Path to AOI file (GeoJSON, Shapefile, WKT).")
    parser.add_argument("--project-type", required=True, help="Project type identifier.")
    parser.add_argument("--output-dir", help="Override default output directory.")
    parser.add_argument("--config", help="Optional JSON/YAML config for this run.")
    return parser.parse_args()


def ensure_run_dirs(base_dir: Path) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / f"run_{timestamp}"
    (run_dir / settings.raw_dir_name).mkdir(parents=True, exist_ok=True)
    (run_dir / settings.processed_dir_name).mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    return run_dir


def load_run_config(config_path: str | None) -> dict:
    if not config_path:
        return {}
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    args = parse_args()

    base_dir = Path(args.output_dir) if args.output_dir else settings.data_dir
    run_dir = ensure_run_dirs(base_dir)
    run_id = run_dir.name
    run_timestamp = datetime.utcnow()

    configure_logging(run_dir / "logs")
    logger.info("Starting run in %s", run_dir)

    run_config = load_run_config(args.config)
    logger.debug("Run config: %s", run_config)

    catalog = DatasetCatalog(settings.data_sources_dir)
    gis = GISHandler(run_dir / settings.processed_dir_name)

    logger.info("Loading AOI from %s", args.aoi)
    aoi = load_aoi(args.aoi, settings.default_crs)
    buffered_aoi = buffer_aoi(aoi, settings.buffer_km)

    corine_path = catalog.corine()
    corine_clip = gis.clip_vector(corine_path, buffered_aoi, "corine_clipped.gpkg")
    land_cover_summary = summarize_land_cover(corine_clip)
    gis.save_summary(land_cover_summary, "land_cover_summary.json")

    biodiversity_prediction = {}
    training_data_path = catalog.biodiversity_training()

    try:
        natura_path = catalog.natura2000()
    except FileNotFoundError:
        logger.warning("No Natura 2000 dataset found; biodiversity analysis limited.")
        natura_path = None

    biodiversity_layers = {}
    if natura_path:
        natura_clip = gis.clip_vector(natura_path, aoi, "biodiversity/natura_clipped.gpkg")
        if not natura_clip.empty:
            natura_geojson = natura_clip.to_crs("EPSG:4326")
            path = gis.save_vector(
                natura_geojson, "biodiversity/natura_clipped.geojson", driver="GeoJSON"
            )
            if path:
                biodiversity_layers["natura"] = f"/runs/{run_id}/biodiversity/natura"
    else:
        natura_clip = gpd.GeoDataFrame(geometry=[], crs=aoi.crs)

    overlap_metrics, overlap_gdf = compute_overlap_metrics(aoi, natura_clip)
    gis.save_summary([overlap_metrics], "biodiversity/overlap_metrics.json")

    if not overlap_gdf.empty:
        overlap_geojson = overlap_gdf.to_crs("EPSG:4326")
        path = gis.save_vector(overlap_geojson, "biodiversity/overlap.geojson", driver="GeoJSON")
        if path:
            biodiversity_layers["overlap"] = f"/runs/{run_id}/biodiversity/overlap"

    features = build_biodiversity_features(aoi, land_cover_summary, overlap_metrics)
    biodiversity_config = BiodiversityConfig(
        training_data_path=str(training_data_path) if training_data_path else None
    )
    biodiversity_model = BiodiversityModel(config=biodiversity_config)
    biodiversity_prediction = biodiversity_model.predict(features)
    gis.save_summary([biodiversity_prediction], "biodiversity/prediction.json")

    sensitivity_layer = aoi.copy()
    sensitivity_layer["biodiversity_score"] = biodiversity_prediction["score"]
    sensitivity_layer["biodiversity_sensitivity"] = biodiversity_prediction[
        "sensitivity"
    ]
    sensitivity_layer = sensitivity_layer.to_crs("EPSG:4326")
    sensitivity_path = gis.save_vector(
        sensitivity_layer, "biodiversity/sensitivity.geojson", driver="GeoJSON"
    )
    if sensitivity_path:
        biodiversity_layers["sensitivity"] = f"/runs/{run_id}/biodiversity/sensitivity"

    try:
        model_details = biodiversity_prediction.get("model_details", [])
        candidate_models = [detail["model"] for detail in model_details]
        selected_model = (
            max(model_details, key=lambda d: d.get("confidence", 0))["model"]
            if model_details
            else None
        )

        db_client = DatabaseClient(settings.postgres_dsn)
        model_logger = ModelRunLogger(db_client)
        record = ModelRunRecord(
            run_id=run_id,
            model_name="biodiversity_ensemble",
            model_version=biodiversity_config.version,
            dataset_source=biodiversity_prediction.get("dataset_source"),
            candidate_models=candidate_models,
            selected_model=selected_model,
            metrics={
                "score": biodiversity_prediction.get("score"),
                "confidence": biodiversity_prediction.get("confidence"),
                "drivers": biodiversity_prediction.get("drivers"),
                "model_details": biodiversity_prediction.get("model_details"),
            },
        )
        model_logger.log(record)
        logger.info("Logged biodiversity model metadata for run %s", run_id)
    except Exception as exc:
        logger.warning("Unable to log biodiversity model metadata: %s", exc)

    factors_path = Path(__file__).resolve().parent / "config" / "emission_factors.yaml"
    factor_store = EmissionFactorStore(factors_path)
    factor_store.load()
    emission_calculator = EmissionCalculator(factor_store)

    project_params = {
        "type": args.project_type,
        "capacity_mw": (
            run_config.get("capacity_mw")
            or run_config.get("project", {}).get("capacity_mw")
        ),
    }
    emission_result = emission_calculator.compute(land_cover_summary, project_params)
    gis.save_summary([emission_result.as_dict()], "emissions_summary.json")

    manifest = {
        "run_id": run_id,
        "project_id": run_config.get("project_id"),
        "project_type": args.project_type,
        "created_at": run_timestamp.isoformat(),
        "status": "completed",
        "outputs": {
            "biodiversity_layers": biodiversity_layers,
            "summaries": {
                "land_cover": str(
                    (run_dir / settings.processed_dir_name / "land_cover_summary.json")
                    .relative_to(run_dir)
                ),
                "emissions": str(
                    (run_dir / settings.processed_dir_name / "emissions_summary.json")
                    .relative_to(run_dir)
                ),
            },
        },
    }
    with open(run_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info("Run complete. Outputs available at %s", run_dir)


if __name__ == "__main__":
    main()

