"""API routes for Model Governance."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...config.base_settings import settings
from ...db.client import DatabaseClient
from ...governance import ABTestManager, DriftDetector, ModelRegistry, ValidationMetricsTracker

router = APIRouter(prefix="/governance", tags=["governance"])


def get_db_client() -> DatabaseClient:
    """Get database client."""
    return DatabaseClient(settings.postgres_dsn)


def get_model_registry(db: DatabaseClient = Depends(get_db_client)) -> ModelRegistry:
    """Get model registry."""
    return ModelRegistry(db)


def get_drift_detector(db: DatabaseClient = Depends(get_db_client)) -> DriftDetector:
    """Get drift detector."""
    return DriftDetector(db)


def get_validation_tracker(db: DatabaseClient = Depends(get_db_client)) -> ValidationMetricsTracker:
    """Get validation metrics tracker."""
    return ValidationMetricsTracker(db)


def get_ab_test_manager(db: DatabaseClient = Depends(get_db_client)) -> ABTestManager:
    """Get A/B test manager."""
    return ABTestManager(db)


# Model Registry Endpoints

class ModelRegisterRequest(BaseModel):
    """Request to register a model."""

    model_name: str = Field(..., description="Model name (e.g., 'biodiversity_ensemble')")
    version: str = Field(..., description="Model version (e.g., '0.1.0')")
    stage: str = Field(default="development", description="Lifecycle stage")
    description: str | None = None
    model_path: str | None = None
    training_data_path: str | None = None
    hyperparameters: dict[str, Any] | None = None
    training_metadata: dict[str, Any] | None = None
    created_by: str | None = None


@router.post("/models/register")
async def register_model(
    request: ModelRegisterRequest,
    registry: ModelRegistry = Depends(get_model_registry),
) -> dict[str, Any]:
    """Register a new model version."""
    try:
        entry = registry.register_model(
            model_name=request.model_name,
            version=request.version,
            stage=request.stage,
            description=request.description,
            model_path=request.model_path,
            training_data_path=request.training_data_path,
            hyperparameters=request.hyperparameters,
            training_metadata=request.training_metadata,
            created_by=request.created_by,
        )
        return entry.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models")
async def list_models(
    model_name: str | None = Query(None, description="Filter by model name"),
    stage: str | None = Query(None, description="Filter by stage"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    registry: ModelRegistry = Depends(get_model_registry),
) -> dict[str, Any]:
    """List models in the registry."""
    models = registry.list_models(model_name=model_name, stage=stage, limit=limit, offset=offset)
    return {
        "models": [m.to_dict() for m in models],
        "count": len(models),
    }


@router.get("/models/{model_name}/{version}")
async def get_model(
    model_name: str,
    version: str,
    registry: ModelRegistry = Depends(get_model_registry),
) -> dict[str, Any]:
    """Get a specific model version."""
    model = registry.get_model(model_name, version)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_name} version {version} not found")
    return model.to_dict()


@router.get("/models/{model_name}/latest")
async def get_latest_model(
    model_name: str,
    stage: str | None = Query(None, description="Filter by stage"),
    registry: ModelRegistry = Depends(get_model_registry),
) -> dict[str, Any]:
    """Get the latest version of a model."""
    model = registry.get_latest_version(model_name, stage=stage)
    if not model:
        raise HTTPException(status_code=404, detail=f"No model found for {model_name}")
    return model.to_dict()


class ModelPromoteRequest(BaseModel):
    """Request to promote a model."""

    target_stage: str = Field(..., description="Target stage")
    approved_by: str = Field(..., description="User approving the promotion")


@router.post("/models/{model_name}/{version}/promote")
async def promote_model(
    model_name: str,
    version: str,
    request: ModelPromoteRequest,
    registry: ModelRegistry = Depends(get_model_registry),
) -> dict[str, Any]:
    """Promote a model to a new stage."""
    try:
        model = registry.promote_model(
            model_name=model_name,
            version=version,
            target_stage=request.target_stage,
            approved_by=request.approved_by,
        )
        return model.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Validation Metrics Endpoints

class LogMetricRequest(BaseModel):
    """Request to log a validation metric."""

    metric_name: str
    metric_value: float
    metric_type: str
    dataset_split: str | None = None
    metadata: dict[str, Any] | None = None


@router.post("/models/{model_name}/{version}/metrics")
async def log_metric(
    model_name: str,
    version: str,
    request: LogMetricRequest,
    tracker: ValidationMetricsTracker = Depends(get_validation_tracker),
) -> dict[str, Any]:
    """Log a validation metric."""
    metric = tracker.log_metric(
        model_name=model_name,
        model_version=version,
        metric_name=request.metric_name,
        metric_value=request.metric_value,
        metric_type=request.metric_type,
        dataset_split=request.dataset_split,
        metadata=request.metadata,
    )
    return {
        "id": str(metric.id),
        "model_name": metric.model_name,
        "model_version": metric.model_version,
        "metric_name": metric.metric_name,
        "metric_value": metric.metric_value,
        "metric_type": metric.metric_type.value,
        "dataset_split": metric.dataset_split,
        "evaluated_at": metric.evaluated_at.isoformat() if metric.evaluated_at else None,
    }


@router.get("/models/{model_name}/{version}/metrics")
async def get_metrics(
    model_name: str,
    version: str | None = Query(None),
    metric_name: str | None = Query(None),
    dataset_split: str | None = Query(None),
    tracker: ValidationMetricsTracker = Depends(get_validation_tracker),
) -> dict[str, Any]:
    """Get validation metrics for a model."""
    metrics = tracker.get_metrics(
        model_name=model_name,
        model_version=version,
        metric_name=metric_name,
        dataset_split=dataset_split,
    )
    return {
        "metrics": [
            {
                "id": str(m.id),
                "metric_name": m.metric_name,
                "metric_value": m.metric_value,
                "metric_type": m.metric_type.value,
                "dataset_split": m.dataset_split,
                "evaluated_at": m.evaluated_at.isoformat() if m.evaluated_at else None,
            }
            for m in metrics
        ],
        "count": len(metrics),
    }


# Drift Detection Endpoints

@router.get("/drift/alerts")
async def get_drift_alerts(
    model_name: str | None = Query(None),
    model_version: str | None = Query(None),
    drift_type: str | None = Query(None),
    is_alert: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    detector: DriftDetector = Depends(get_drift_detector),
) -> dict[str, Any]:
    """Get drift alerts."""
    alerts = detector.get_drift_alerts(
        model_name=model_name,
        model_version=model_version,
        drift_type=drift_type,
        is_alert=is_alert,
        limit=limit,
    )
    return {
        "alerts": [
            {
                "id": str(a.id),
                "model_name": a.model_name,
                "model_version": a.model_version,
                "drift_type": a.drift_type.value,
                "feature_name": a.feature_name,
                "drift_score": a.drift_score,
                "threshold": a.threshold,
                "is_alert": a.is_alert,
                "detection_method": a.detection_method,
                "detected_at": a.detected_at.isoformat(),
                "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            }
            for a in alerts
        ],
        "count": len(alerts),
    }


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge a drift alert."""

    acknowledged_by: str


@router.post("/drift/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    request: AcknowledgeAlertRequest,
    detector: DriftDetector = Depends(get_drift_detector),
) -> dict[str, Any]:
    """Acknowledge a drift alert."""
    detector.acknowledge_alert(alert_id, request.acknowledged_by)
    return {"status": "acknowledged", "alert_id": str(alert_id)}


# A/B Testing Endpoints

class CreateABTestRequest(BaseModel):
    """Request to create an A/B test."""

    test_name: str
    model_a_name: str
    model_a_version: str
    model_b_name: str
    model_b_version: str
    success_metric: str
    traffic_split: float = Field(default=0.5, ge=0.0, le=1.0)
    min_samples: int = Field(default=100, ge=1)
    success_threshold: float | None = None
    statistical_test: str = Field(default="t_test")
    significance_level: float = Field(default=0.05, ge=0.0, le=1.0)
    description: str | None = None
    created_by: str | None = None


@router.post("/ab-tests")
async def create_ab_test(
    request: CreateABTestRequest,
    manager: ABTestManager = Depends(get_ab_test_manager),
) -> dict[str, Any]:
    """Create a new A/B test."""
    try:
        test = manager.create_test(
            test_name=request.test_name,
            model_a_name=request.model_a_name,
            model_a_version=request.model_a_version,
            model_b_name=request.model_b_name,
            model_b_version=request.model_b_version,
            success_metric=request.success_metric,
            traffic_split=request.traffic_split,
            min_samples=request.min_samples,
            success_threshold=request.success_threshold,
            statistical_test=request.statistical_test,
            significance_level=request.significance_level,
            description=request.description,
            created_by=request.created_by,
        )
        return {
            "id": str(test.id),
            "test_name": test.test_name,
            "model_a": f"{test.model_a_name}:{test.model_a_version}",
            "model_b": f"{test.model_b_name}:{test.model_b_version}",
            "status": test.status.value,
            "created_at": test.created_at.isoformat() if test.created_at else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ab-tests/{test_id}/start")
async def start_ab_test(
    test_id: UUID,
    manager: ABTestManager = Depends(get_ab_test_manager),
) -> dict[str, Any]:
    """Start an A/B test."""
    try:
        test = manager.start_test(test_id)
        return {
            "id": str(test.id),
            "status": test.status.value,
            "start_date": test.start_date.isoformat() if test.start_date else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/ab-tests")
async def list_ab_tests(
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    manager: ABTestManager = Depends(get_ab_test_manager),
) -> dict[str, Any]:
    """List A/B tests."""
    tests = manager.list_tests(status=status, limit=limit)
    return {
        "tests": [
            {
                "id": str(t.id),
                "test_name": t.test_name,
                "model_a": f"{t.model_a_name}:{t.model_a_version}",
                "model_b": f"{t.model_b_name}:{t.model_b_version}",
                "status": t.status.value,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tests
        ],
        "count": len(tests),
    }


@router.get("/ab-tests/{test_id}")
async def get_ab_test(
    test_id: UUID,
    manager: ABTestManager = Depends(get_ab_test_manager),
) -> dict[str, Any]:
    """Get an A/B test."""
    test = manager.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail=f"A/B test {test_id} not found")
    return {
        "id": str(test.id),
        "test_name": test.test_name,
        "model_a": f"{test.model_a_name}:{test.model_a_version}",
        "model_b": f"{test.model_b_name}:{test.model_b_version}",
        "status": test.status.value,
        "success_metric": test.success_metric,
        "traffic_split": test.traffic_split,
        "created_at": test.created_at.isoformat() if test.created_at else None,
    }


@router.get("/ab-tests/{test_id}/results")
async def get_ab_test_results(
    test_id: UUID,
    manager: ABTestManager = Depends(get_ab_test_manager),
) -> dict[str, Any]:
    """Get results for an A/B test."""
    results = manager.get_test_results(test_id)
    return {
        "results": [
            {
                "id": str(r.id),
                "metric_name": r.metric_name,
                "model_a_value": r.model_a_value,
                "model_b_value": r.model_b_value,
                "difference": r.difference,
                "relative_improvement": r.relative_improvement,
                "p_value": r.p_value,
                "is_significant": r.is_significant,
                "evaluated_at": r.evaluated_at.isoformat(),
            }
            for r in results
        ],
        "count": len(results),
    }

