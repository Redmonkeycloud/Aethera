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
from .analysis.receptors import calculate_distance_to_receptors
from .analysis.kpis import calculate_comprehensive_kpis
from .analysis.resm_features import build_resm_features
from .analysis.ahsm_features import build_ahsm_features
from .config.base_settings import settings
from .legal import LegalEvaluator, LegalEvaluationResult
from .legal.loader import LegalRulesLoader
from .datasets.catalog import DatasetCatalog
from .db import DatabaseClient, ModelRunLogger, ModelRunRecord
from .emissions.calculator import EmissionCalculator
from .emissions.factors import EmissionFactorStore
from .gis_handler import GISHandler
from .logging_utils import configure_logging, get_logger
from .utils.dataset_checker import DatasetAvailabilityChecker
from .utils.error_handling import safe_dataset_load
from .utils.geometry import buffer_aoi, load_aoi

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai.models.biodiversity import (  # type: ignore  # noqa: E402
    BiodiversityConfig,
    BiodiversityModel,
)
from ai.models.resm import RESMConfig, RESMModel  # type: ignore  # noqa: E402
from ai.models.ahsm import AHSMConfig, AHSMModel  # type: ignore  # noqa: E402
from ai.models.cim import CIMConfig, CIMModel  # type: ignore  # noqa: E402


logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an AETHERA analysis pipeline.")
    parser.add_argument("--aoi", required=True, help="Path to AOI file (GeoJSON, Shapefile, WKT).")
    parser.add_argument("--project-type", required=True, help="Project type identifier.")
    parser.add_argument("--output-dir", help="Override default output directory.")
    parser.add_argument("--config", help="Optional JSON/YAML config for this run.")
    parser.add_argument("--country", help="ISO 3166-1 alpha-3 country code (e.g., DEU, FRA) for legal rules evaluation.")
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

    # Check dataset availability before starting analysis
    logger.info("Checking dataset availability...")
    dataset_checker = DatasetAvailabilityChecker(catalog)
    availability_report = dataset_checker.check_all()
    
    if not availability_report.all_available:
        missing = ", ".join(availability_report.missing_required)
        error_msg = f"Required datasets missing: {missing}. Cannot proceed with analysis."
        logger.error(error_msg)
        # Save availability report for debugging
        availability_path = run_dir / "dataset_availability.json"
        with open(availability_path, "w", encoding="utf-8") as f:
            import json
            json.dump(availability_report.to_dict(), f, indent=2)
        raise RuntimeError(error_msg)
    
    logger.info("All required datasets available. Optional datasets: %d/%d available",
                sum(1 for ds in availability_report.optional_datasets if ds.available),
                len(availability_report.optional_datasets))

    logger.info("Loading AOI from %s", args.aoi)
    aoi = load_aoi(args.aoi, settings.default_crs)
    buffered_aoi = buffer_aoi(aoi, settings.buffer_km)

    corine_path = safe_dataset_load(
        "CORINE",
        catalog.corine,
        required=True,
    )
    if corine_path is None:
        raise RuntimeError("CORINE dataset is required but not available")
    corine_clip = gis.clip_vector(corine_path, buffered_aoi, "corine_clipped.gpkg")
    land_cover_summary = summarize_land_cover(corine_clip)
    gis.save_summary(land_cover_summary, "land_cover_summary.json")

    biodiversity_prediction = {}
    training_data_path = catalog.biodiversity_training()

    natura_path = safe_dataset_load(
        "Natura 2000",
        catalog.natura2000,
        required=False,
    )

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

    # Distance-to-receptor calculations
    logger.info("Calculating distances to sensitive receptors...")
    
    # Load WDPA (global protected areas) as fallback/complement to Natura 2000
    wdpa_path = safe_dataset_load("WDPA", catalog.wdpa, required=False)
    wdpa_clip = None
    if wdpa_path:
        try:
            wdpa_clip = gis.clip_vector(wdpa_path, buffered_aoi, "receptors/wdpa_clipped.gpkg")
            if not wdpa_clip.empty:
                logger.info("Loaded %d WDPA protected area features", len(wdpa_clip))
        except Exception as exc:
            logger.warning("Could not clip WDPA dataset: %s", exc)
            wdpa_clip = None
    
    # Load settlements from GADM (administrative level 1 or 2 can represent cities/towns)
    settlements_clip = None
    gadm_path = safe_dataset_load("GADM Level 1", lambda: catalog.gadm(level=1), required=False)
    if gadm_path:
        try:
            settlements_clip = gis.clip_vector(gadm_path, buffered_aoi, "receptors/settlements_clipped.gpkg")
            if settlements_clip.empty:
                # Try level 0 (country) as fallback
                gadm_path = safe_dataset_load("GADM Level 0", lambda: catalog.gadm(level=0), required=False)
                if gadm_path:
                    settlements_clip = gis.clip_vector(gadm_path, buffered_aoi, "receptors/settlements_clipped.gpkg")
            if not settlements_clip.empty:
                logger.info("Loaded %d settlement features for receptor analysis", len(settlements_clip))
        except Exception as exc:
            logger.warning("Could not clip GADM dataset for settlements: %s", exc)
            settlements_clip = None
    
    # Load water bodies from rivers dataset
    rivers_path = safe_dataset_load("Rivers", catalog.rivers, required=False)
    water_bodies_clip = None
    if rivers_path:
        try:
            water_bodies_clip = gis.clip_vector(rivers_path, buffered_aoi, "receptors/rivers_clipped.gpkg")
            if not water_bodies_clip.empty:
                logger.info("Loaded %d water body features for receptor analysis", len(water_bodies_clip))
        except Exception as exc:
            logger.warning("Could not clip rivers dataset: %s", exc)
            water_bodies_clip = None
    
    # Load regional context (Eurostat NUTS) for analysis metadata
    nuts_path = safe_dataset_load("Eurostat NUTS", catalog.eurostat_nuts, required=False)
    nuts_context = None
    if nuts_path:
        try:
            nuts_clip = gis.clip_vector(nuts_path, buffered_aoi, "context/nuts_clipped.gpkg")
            if not nuts_clip.empty:
                nuts_context = {
                    "nuts_regions": len(nuts_clip),
                    "nuts_codes": nuts_clip.get("NUTS_ID", []).tolist() if "NUTS_ID" in nuts_clip.columns else [],
                }
                logger.info("Loaded NUTS regional context: %d regions", len(nuts_clip))
        except Exception as exc:
            logger.debug("Could not clip Eurostat NUTS dataset: %s", exc)
            nuts_context = None
    
    # Load country boundaries (Natural Earth) for context
    country_path = safe_dataset_load("Natural Earth", catalog.natural_earth_admin, required=False)
    country_context = None
    if country_path:
        try:
            country_clip = gis.clip_vector(country_path, buffered_aoi, "context/country_clipped.gpkg")
            if not country_clip.empty:
                country_context = {
                    "countries": country_clip.get("NAME", []).tolist() if "NAME" in country_clip.columns else [],
                    "country_count": len(country_clip),
                }
                logger.info("Loaded country boundaries context: %d countries", len(country_clip))
        except Exception as exc:
            logger.debug("Could not clip Natural Earth country dataset: %s", exc)
            country_context = None
    
    receptor_analysis = calculate_distance_to_receptors(
        aoi=aoi,
        protected_areas=natura_clip if not natura_clip.empty else None,
        protected_areas_global=wdpa_clip if wdpa_clip is not None and not wdpa_clip.empty else None,
        settlements=settlements_clip if settlements_clip is not None and not settlements_clip.empty else None,
        water_bodies=water_bodies_clip if water_bodies_clip is not None and not water_bodies_clip.empty else None,
        max_distance_km=50.0,
    )
    receptor_summary = {
        "aoi_centroid": {
            "lon": float(receptor_analysis.aoi_centroid.x),
            "lat": float(receptor_analysis.aoi_centroid.y),
        },
        "nearest_protected_area": (
            {
                "receptor_type": receptor_analysis.nearest_protected_area.receptor_type,
                "receptor_id": receptor_analysis.nearest_protected_area.receptor_id,
                "receptor_name": receptor_analysis.nearest_protected_area.receptor_name,
                "distance_km": receptor_analysis.nearest_protected_area.distance_km,
            }
            if receptor_analysis.nearest_protected_area
            else None
        ),
        "nearest_settlement": (
            {
                "receptor_type": receptor_analysis.nearest_settlement.receptor_type,
                "receptor_id": receptor_analysis.nearest_settlement.receptor_id,
                "receptor_name": receptor_analysis.nearest_settlement.receptor_name,
                "distance_km": receptor_analysis.nearest_settlement.distance_km,
            }
            if receptor_analysis.nearest_settlement
            else None
        ),
        "nearest_water_body": (
            {
                "receptor_type": receptor_analysis.nearest_water_body.receptor_type,
                "receptor_id": receptor_analysis.nearest_water_body.receptor_id,
                "receptor_name": receptor_analysis.nearest_water_body.receptor_name,
                "distance_km": receptor_analysis.nearest_water_body.distance_km,
            }
            if receptor_analysis.nearest_water_body
            else None
        ),
        "total_receptors_found": len(receptor_analysis.all_receptors),
    }
    receptor_summary_list = [receptor_summary]
    gis.save_summary(receptor_summary_list, "receptor_distances.json")

    # Advanced Environmental KPIs
    logger.info("Calculating advanced environmental KPIs...")
    environmental_kpis = calculate_comprehensive_kpis(
        aoi=aoi,
        land_cover_gdf=corine_clip,
        land_cover_summary=land_cover_summary,
        protected_areas=natura_clip if not natura_clip.empty else gpd.GeoDataFrame(geometry=[], crs=aoi.crs),
        emission_result=emission_result.as_dict(),
        project_capacity_mw=project_params.get("capacity_mw", 0) or 0.0,
    )
    gis.save_summary([environmental_kpis.as_dict()], "environmental_kpis.json")

    # RESM (Renewable/Resilience Suitability Model)
    logger.info("Running RESM (Renewable/Resilience Suitability Model)...")
    resm_features = build_resm_features(
        aoi=aoi,
        land_cover_summary=land_cover_summary,
        environmental_kpis=environmental_kpis,
        receptor_distances=receptor_summary,
        project_type=args.project_type,
    )
    resm_config = RESMConfig()
    resm_model = RESMModel(config=resm_config)
    resm_prediction = resm_model.predict(resm_features)
    gis.save_summary([resm_prediction], "resm_prediction.json")

    # AHSM (Asset Hazard Susceptibility Model)
    logger.info("Running AHSM (Asset Hazard Susceptibility Model)...")
    ahsm_features = build_ahsm_features(
        aoi=aoi,
        land_cover_summary=land_cover_summary,
        environmental_kpis=environmental_kpis,
        receptor_distances=receptor_summary,
    )
    ahsm_config = AHSMConfig()
    ahsm_model = AHSMModel(config=ahsm_config)
    ahsm_prediction = ahsm_model.predict(ahsm_features)
    gis.save_summary([ahsm_prediction], "ahsm_prediction.json")

    # CIM (Cumulative Impact Model) - integrates all models
    logger.info("Running CIM (Cumulative Impact Model)...")
    cim_features = {
        "resm_score": resm_prediction["score"],
        "ahsm_score": ahsm_prediction["score"],
        "biodiversity_score": biodiversity_prediction["score"],
        "distance_to_protected_km": (
            receptor_summary.get("nearest_protected_area", {}).get("distance_km", 999.0)
            if receptor_summary.get("nearest_protected_area")
            else 999.0
        ),
        "protected_overlap_pct": overlap_metrics.get("protected_overlap_pct", 0.0),
        "habitat_fragmentation_index": environmental_kpis.habitat_fragmentation_index,
        "connectivity_index": environmental_kpis.connectivity_index,
        "ecosystem_service_value": environmental_kpis.ecosystem_service_value_index,
        "ghg_emissions_intensity": environmental_kpis.ghg_emissions_intensity,
        "net_carbon_balance": environmental_kpis.net_carbon_balance,
        "land_use_efficiency": environmental_kpis.land_use_efficiency,
        "natural_habitat_ratio": environmental_kpis.natural_habitat_ratio,
        "soil_erosion_risk": environmental_kpis.soil_erosion_risk,
        "water_regulation_capacity": environmental_kpis.water_regulation_capacity,
    }
    cim_config = CIMConfig()
    cim_model = CIMModel(config=cim_config)
    cim_prediction = cim_model.predict(cim_features)
    gis.save_summary([cim_prediction], "cim_prediction.json")

    # Log model metadata to database
    try:
        db_client = DatabaseClient(settings.postgres_dsn)
        model_logger = ModelRunLogger(db_client)

        # Log RESM
        resm_model_details = resm_prediction.get("model_details", [])
        resm_candidates = [detail["model"] for detail in resm_model_details]
        resm_selected = (
            max(resm_model_details, key=lambda d: d.get("confidence", 0))["model"]
            if resm_model_details
            else None
        )
        resm_record = ModelRunRecord(
            run_id=run_id,
            model_name="resm_ensemble",
            model_version=resm_config.version,
            dataset_source=resm_prediction.get("dataset_source"),
            candidate_models=resm_candidates,
            selected_model=resm_selected,
            metrics={
                "score": resm_prediction.get("score"),
                "category": resm_prediction.get("category"),
                "confidence": resm_prediction.get("confidence"),
                "drivers": resm_prediction.get("drivers"),
                "model_details": resm_prediction.get("model_details"),
            },
        )
        model_logger.log(resm_record)

        # Log AHSM
        ahsm_model_details = ahsm_prediction.get("model_details", [])
        ahsm_candidates = [detail["model"] for detail in ahsm_model_details]
        ahsm_selected = (
            max(ahsm_model_details, key=lambda d: d.get("confidence", 0))["model"]
            if ahsm_model_details
            else None
        )
        ahsm_record = ModelRunRecord(
            run_id=run_id,
            model_name="ahsm_ensemble",
            model_version=ahsm_config.version,
            dataset_source=ahsm_prediction.get("dataset_source"),
            candidate_models=ahsm_candidates,
            selected_model=ahsm_selected,
            metrics={
                "score": ahsm_prediction.get("score"),
                "category": ahsm_prediction.get("category"),
                "confidence": ahsm_prediction.get("confidence"),
                "drivers": ahsm_prediction.get("drivers"),
                "hazard_types": ahsm_prediction.get("hazard_types"),
                "model_details": ahsm_prediction.get("model_details"),
            },
        )
        model_logger.log(ahsm_record)

        # Log CIM
        cim_model_details = cim_prediction.get("model_details", [])
        cim_candidates = [detail["model"] for detail in cim_model_details]
        cim_selected = (
            max(cim_model_details, key=lambda d: d.get("confidence", 0))["model"]
            if cim_model_details
            else None
        )
        cim_record = ModelRunRecord(
            run_id=run_id,
            model_name="cim_ensemble",
            model_version=cim_config.version,
            dataset_source=cim_prediction.get("dataset_source"),
            candidate_models=cim_candidates,
            selected_model=cim_selected,
            metrics={
                "score": cim_prediction.get("score"),
                "category": cim_prediction.get("category"),
                "confidence": cim_prediction.get("confidence"),
                "drivers": cim_prediction.get("drivers"),
                "model_details": cim_prediction.get("model_details"),
            },
        )
        model_logger.log(cim_record)

        logger.info("Logged RESM, AHSM, and CIM model metadata for run %s", run_id)
    except Exception as exc:
        logger.warning("Unable to log model metadata: %s", exc)

    # Legal Rules Engine Evaluation
    legal_evaluation: LegalEvaluationResult | None = None
    country_code = args.country or run_config.get("country") or run_config.get("country_code")
    if country_code:
        try:
            logger.info("Evaluating legal rules for country %s", country_code)
            loader = LegalRulesLoader()
            rule_set = loader.load_country_rules(country_code.upper())
            if rule_set:
                # Prepare project metrics for legal evaluation
                project_metrics = {
                    "protected_overlap_pct": overlap_metrics.get("protected_overlap_pct", 0.0),
                    "distance_to_protected_km": (
                        receptor_summary.get("nearest_protected_area", {}).get("distance_km", 999.0)
                        if receptor_summary.get("nearest_protected_area")
                        else 999.0
                    ),
                    "biodiversity_score": biodiversity_prediction.get("score", 0.0),
                    "project_operation_tco2e_per_year": emission_result.as_dict().get("project_operation_tco2e_per_year", 0.0),
                    "ghg_emissions_intensity": environmental_kpis.ghg_emissions_intensity,
                    "forest_ratio": environmental_kpis.natural_habitat_ratio,  # Approximate
                    "aoi_area_ha": aoi.geometry.area.sum() / 10_000,
                    "natural_habitat_ratio": environmental_kpis.natural_habitat_ratio,
                    "distance_to_water_km": (
                        receptor_summary.get("nearest_water_body", {}).get("distance_km", 999.0)
                        if receptor_summary.get("nearest_water_body")
                        else 999.0
                    ),
                    "distance_to_settlement_km": (
                        receptor_summary.get("nearest_settlement", {}).get("distance_km", 999.0)
                        if receptor_summary.get("nearest_settlement")
                        else 999.0
                    ),
                    "cim_score": cim_prediction.get("score", 0.0),
                    "ahsm_score": ahsm_prediction.get("score", 0.0),
                }
                evaluator = LegalEvaluator(rule_set)
                legal_evaluation = evaluator.evaluate(project_metrics)
                # Convert to serializable dict
                legal_dict = {
                    "country_code": legal_evaluation.country_code,
                    "overall_compliant": legal_evaluation.overall_compliant,
                    "summary": legal_evaluation.summary,
                    "statuses": [
                        {
                            "rule_id": s.rule_id,
                            "rule_name": s.rule_name,
                            "passed": s.passed,
                            "message": s.message,
                            "severity": s.severity,
                            "category": s.category,
                            "details": s.details,
                        }
                        for s in legal_evaluation.statuses
                    ],
                    "critical_violations": [
                        {
                            "rule_id": v.rule_id,
                            "rule_name": v.rule_name,
                            "message": v.message,
                            "severity": v.severity,
                            "category": v.category,
                        }
                        for v in legal_evaluation.critical_violations
                    ],
                    "warnings": [
                        {
                            "rule_id": w.rule_id,
                            "rule_name": w.rule_name,
                            "message": w.message,
                            "severity": w.severity,
                            "category": w.category,
                        }
                        for w in legal_evaluation.warnings
                    ],
                    "informational": [
                        {
                            "rule_id": i.rule_id,
                            "rule_name": i.rule_name,
                            "message": i.message,
                            "severity": i.severity,
                            "category": i.category,
                        }
                        for i in legal_evaluation.informational
                    ],
                }
                gis.save_summary([legal_dict], "legal_evaluation.json")
                logger.info(
                    "Legal evaluation complete: %s compliant, %d violations",
                    "Overall" if legal_evaluation.overall_compliant else "Not overall",
                    len(legal_evaluation.critical_violations),
                )
            else:
                logger.warning("No legal rules found for country %s", country_code)
        except Exception as exc:
            logger.warning("Unable to evaluate legal rules: %s", exc)

    manifest = {
        "run_id": run_id,
        "project_id": run_config.get("project_id"),
        "project_type": args.project_type,
        "created_at": run_timestamp.isoformat(),
        "status": "completed",
        "context": {
            "nuts_regions": nuts_context if nuts_context else None,
            "country_boundaries": country_context if country_context else None,
        },
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
                "receptor_distances": str(
                    (run_dir / settings.processed_dir_name / "receptor_distances.json")
                    .relative_to(run_dir)
                ),
                "environmental_kpis": str(
                    (run_dir / settings.processed_dir_name / "environmental_kpis.json")
                    .relative_to(run_dir)
                ),
                "resm_prediction": str(
                    (run_dir / settings.processed_dir_name / "resm_prediction.json")
                    .relative_to(run_dir)
                ),
                "ahsm_prediction": str(
                    (run_dir / settings.processed_dir_name / "ahsm_prediction.json")
                    .relative_to(run_dir)
                ),
                "cim_prediction": str(
                    (run_dir / settings.processed_dir_name / "cim_prediction.json")
                    .relative_to(run_dir)
                ),
                "legal_evaluation": (
                    str(
                        (run_dir / settings.processed_dir_name / "legal_evaluation.json")
                        .relative_to(run_dir)
                    )
                    if legal_evaluation
                    else None
                ),
            },
        },
    }
    if legal_evaluation:
        manifest["legal_compliance"] = {
            "overall_compliant": legal_evaluation.overall_compliant,
            "country_code": legal_evaluation.country_code,
            "summary": legal_evaluation.summary,
        }
    with open(run_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info("Run complete. Outputs available at %s", run_dir)


if __name__ == "__main__":
    main()
