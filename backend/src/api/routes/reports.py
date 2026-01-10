"""Report generation and management endpoints."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from ...config.base_settings import settings
from ...db.client import DatabaseClient
from ...reporting.engine import ReportEngine
from ...reporting.exports import ReportExporter
from ...reporting.report_memory import ReportEntry
from ...reporting.report_memory_db import DatabaseReportMemoryStore
from ...reporting.text_generator import TextGenerator
from ...reporting.visualizations import VisualizationGenerator
from ...api.storage import RunManifestStore
from ...logging_utils import get_logger

router = APIRouter(prefix="/reports", tags=["reports"])
logger = get_logger(__name__)

# Initialize services with error handling
try:
    db_client = DatabaseClient(settings.postgres_dsn)
    memory_store = DatabaseReportMemoryStore(db_client)
except Exception as e:
    logger.warning(f"Failed to initialize database-backed memory store: {e}, using in-memory store")
    from ...reporting.report_memory import ReportMemoryStore
    memory_store = ReportMemoryStore()

templates_dir = Path(__file__).parent.parent.parent / "reporting" / "templates"
report_engine = ReportEngine(
    templates_dir=templates_dir,
    memory_store=memory_store,
    use_rag=True,
    use_llm=True,
)
exporter = ReportExporter()
text_generator = TextGenerator()
viz_generator = VisualizationGenerator()


def _build_basic_context(run_dict: dict) -> dict:
    """Build basic context for report templates."""
    # Extract project info
    project_data = run_dict.get("project", {})
    if isinstance(project_data, dict):
        project_name = project_data.get("name") or run_dict.get("project_name") or run_dict.get("name", "Unknown Project")
        project_type = project_data.get("type") or run_dict.get("project_type", "unknown")
        project_country = project_data.get("country") or run_dict.get("country", "Unknown")
        capacity_mw = project_data.get("capacity_mw") or run_dict.get("capacity_mw", 0)
    else:
        project_name = run_dict.get("project_name") or run_dict.get("name", "Unknown Project")
        project_type = run_dict.get("project_type", "unknown")
        project_country = run_dict.get("country", "Unknown")
        capacity_mw = run_dict.get("capacity_mw", 0)
    
    # Extract AI model results
    ai_models = run_dict.get("ai_models", {})
    if not ai_models:
        ai_models = {
            "resm": run_dict.get("resm", {}),
            "ahsm": run_dict.get("ahsm", {}),
            "cim": run_dict.get("cim", {}),
        }
    
    # Extract indicators for AOI area
    indicators = run_dict.get("indicators", {})
    aoi_area_km2 = indicators.get("aoi_area_km2") if isinstance(indicators, dict) else 0
    
    return {
        "project": {
            "name": project_name,
            "type": project_type,
            "country": project_country,
            "capacity_mw": capacity_mw,
            "aoi_area_km2": aoi_area_km2,
        },
        "indicators": indicators,
        "emissions": run_dict.get("emissions", {}),
        "biodiversity": run_dict.get("biodiversity", {}),
        "ai": ai_models,
        "legal_summary": run_dict.get("legal_summary", "No legal assessment available."),
        "legal_compliance": run_dict.get("legal_compliance", {}),
        "executive_summary": run_dict.get("executive_summary", "Executive summary not available."),
        "land_cover": run_dict.get("land_cover", []),
    }


class ReportGenerateRequest(BaseModel):
    """Request to generate a report."""

    run_id: str
    template_name: str = Field(default="base_report.md.jinja")
    enable_rag: bool = Field(default=True)
    format: Literal["markdown", "docx", "pdf"] = Field(default="markdown")


class ReportFeedbackRequest(BaseModel):
    """Request to add feedback to a report."""

    feedback_text: str
    reviewer: str | None = None
    rating: int | None = Field(None, ge=1, le=5)


class ReportListResponse(BaseModel):
    """Response for listing reports."""

    reports: list[dict]
    total: int


class ScenarioComparisonRequest(BaseModel):
    """Request to compare multiple scenarios."""

    run_ids: list[str] = Field(..., min_items=2, max_items=10)
    comparison_type: Literal["indicators", "emissions", "legal", "full"] = Field(default="full")


@router.post("/generate")
async def generate_report(request: ReportGenerateRequest) -> dict:
    """
    Generate a report for a given run.

    This endpoint generates a report using the specified template and optionally
    uses RAG to augment the context with similar past reports.
    """
    # Load run data
    run_store = RunManifestStore(settings.data_dir, settings.processed_dir_name)
    try:
        run_data = run_store.get_run(request.run_id)
        # Convert RunDetail to dict if needed
        if hasattr(run_data, "dict"):
            run_dict = run_data.dict()
        elif hasattr(run_data, "model_dump"):
            run_dict = run_data.model_dump()
        else:
            run_dict = run_data if isinstance(run_data, dict) else {}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Run not found: {request.run_id}")

    # Build context for report template
    # Try to use enhanced context if template supports it, otherwise use basic context
    try:
        if request.template_name == "enhanced_report.md.jinja":
            try:
                from ...reporting.report_builder import build_enhanced_report_context
                context = build_enhanced_report_context(request.run_id, run_dict, text_generator, viz_generator)
            except ImportError:
                logger.warning("build_enhanced_report_context not available, using basic context")
                context = _build_basic_context(run_dict)
        else:
            context = _build_basic_context(run_dict)
    except Exception as e:
        logger.warning(f"Error building enhanced context: {e}, using basic context")
        context = _build_basic_context(run_dict)

    # Generate report with LLM enhancement
    try:
        content = report_engine.generate_report(
            template_name=request.template_name,
            context=context,
            use_llm=True,  # Enable LLM generation by default
        )

        # Save to storage
        report_id = str(uuid.uuid4())
        reports_dir = settings.data_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"{report_id}.{request.format if request.format != 'markdown' else 'md'}"
        report_path.write_text(content, encoding="utf-8")

        # Create report entry
        entry = ReportEntry(
            report_id=report_id,
            project_id=run_dict.get("project_id"),
            run_id=request.run_id,
            version=1,
            status="draft",
            summary=context.get("executive_summary", "")[:500] if context.get("executive_summary") else None,
            file_path=Path(report_path),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Extract sections for embedding
        sections = {
            "executive_summary": context.get("executive_summary", ""),
            "biodiversity": str(context.get("biodiversity", {})),
            "emissions": str(context.get("emissions", {})),
        }

        # Add to memory store
        memory_store.add_entry(entry, content, sections)

        return {
            "report_id": report_id,
            "run_id": request.run_id,
            "format": request.format,
            "status": "generated",
            "storage_path": report_path,
        }

    except Exception as e:
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"Failed to generate report: {error_detail}\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {error_detail}")


@router.get("")
async def list_reports(
    project_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> ReportListResponse:
    """List all reports with optional filtering."""
    entries = memory_store.list_entries(project_id=project_id, status=status, limit=limit)

    reports = [
        {
            "report_id": entry.report_id,
            "project_id": entry.project_id,
            "run_id": entry.run_id,
            "version": entry.version,
            "status": entry.status,
            "summary": entry.summary,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
        }
        for entry in entries
    ]

    return ReportListResponse(reports=reports, total=len(reports))


@router.get("/{report_id}")
async def get_report(report_id: str) -> dict:
    """Get report details and content."""
    entries = memory_store.list_entries()
    entry = next((e for e in entries if e.report_id == report_id), None)

    if not entry:
        raise HTTPException(status_code=404, detail="Report not found")

    content = memory_store.get_report_content(report_id)

    return {
        "report_id": entry.report_id,
        "project_id": entry.project_id,
        "run_id": entry.run_id,
        "version": entry.version,
        "status": entry.status,
        "summary": entry.summary,
        "content": content,
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
    }


@router.get("/{report_id}/export")
async def export_report(
    report_id: str,
    format: Literal["docx", "pdf", "excel", "csv"] = Query("pdf"),
) -> FileResponse:
    """Export report in various formats."""
    entries = memory_store.list_entries()
    entry = next((e for e in entries if e.report_id == report_id), None)

    if not entry:
        raise HTTPException(status_code=404, detail="Report not found")

    content = memory_store.get_report_content(report_id)
    if not content:
        raise HTTPException(status_code=404, detail="Report content not found")

    try:
        # Create temporary output path
        output_dir = Path(settings.data_dir) / "exports" / report_id
        output_dir.mkdir(parents=True, exist_ok=True)

        if format == "docx":
            output_path = output_dir / f"report_{report_id}.docx"
            exporter.to_docx(content, output_path, metadata={"title": entry.summary or "AETHERA Report"})
        elif format == "pdf":
            output_path = output_dir / f"report_{report_id}.pdf"
            exporter.to_pdf(content, output_path)
        elif format == "excel":
            # Convert content to structured data (simplified)
            # In production, extract structured data from run
            data = {"Report Summary": [{"Field": "Summary", "Value": entry.summary or "N/A"}]}
            output_path = output_dir / f"report_{report_id}.xlsx"
            exporter.to_excel(data, output_path)
        elif format == "csv":
            data = [{"Field": "Summary", "Value": entry.summary or "N/A"}]
            output_path = output_dir / f"report_{report_id}.csv"
            exporter.to_csv(data, output_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        media_types = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pdf": "application/pdf",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv",
        }
        
        return FileResponse(
            path=str(output_path),
            filename=output_path.name,
            media_type=media_types.get(format, "application/octet-stream"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")


@router.post("/{report_id}/feedback")
async def add_feedback(report_id: str, request: ReportFeedbackRequest) -> dict:
    """Add reviewer feedback to a report."""
    entries = memory_store.list_entries()
    entry = next((e for e in entries if e.report_id == report_id), None)

    if not entry:
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        memory_store.add_feedback(report_id, request.feedback_text, request.reviewer, request.rating)
        return {"status": "success", "message": "Feedback added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add feedback: {str(e)}")


@router.post("/compare")
async def compare_scenarios(request: ScenarioComparisonRequest) -> dict:
    """Compare multiple scenarios/runs side by side."""
    run_store = RunManifestStore(settings.data_dir, settings.processed_dir_name)
    comparisons = []

    for run_id in request.run_ids:
        try:
            run_data = run_store.get_run(run_id)
            # Convert RunDetail to dict if needed
            if hasattr(run_data, "dict"):
                run_dict = run_data.dict()
            elif hasattr(run_data, "model_dump"):
                run_dict = run_data.model_dump()
            else:
                run_dict = run_data if isinstance(run_data, dict) else {}
            
            comparisons.append(
                {
                    "run_id": run_id,
                    "project_name": run_dict.get("project_name") or run_dict.get("name", "Unknown"),
                    "indicators": run_dict.get("indicators", {}),
                    "emissions": run_dict.get("emissions", {}),
                    "legal": run_dict.get("legal_summary", {}),
                }
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    return {
        "comparison_type": request.comparison_type,
        "runs": comparisons,
        "summary": _generate_comparison_summary(comparisons, request.comparison_type),
    }


def _generate_comparison_summary(comparisons: list[dict], comparison_type: str) -> str:
    """Generate a text summary of the comparison."""
    if comparison_type == "indicators":
        return "Indicator comparison summary (to be implemented)"
    elif comparison_type == "emissions":
        return "Emissions comparison summary (to be implemented)"
    elif comparison_type == "legal":
        return "Legal compliance comparison summary (to be implemented)"
    else:
        return "Full comparison summary (to be implemented)"


@router.get("/{report_id}/similar")
async def find_similar_reports(
    report_id: str,
    limit: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0),
) -> dict:
    """Find similar reports using semantic search."""
    entries = memory_store.list_entries()
    entry = next((e for e in entries if e.report_id == report_id), None)

    if not entry:
        raise HTTPException(status_code=404, detail="Report not found")

    query_text = entry.summary or ""

    try:
        similar = memory_store.find_similar(query_text, limit=limit, min_similarity=min_similarity)
        return {
            "report_id": report_id,
            "similar_reports": [
                {
                    "report_id": e.report_id,
                    "section": section,
                    "similarity": float(sim),
                    "summary": e.summary,
                }
                for e, section, sim in similar
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar reports: {str(e)}")


@router.post("/llm/generate")
async def generate_llm_content(
    run_id: str,
    content_type: Literal["executive_summary", "biodiversity_narrative", "ml_explanation", "legal_recommendations"] = Query(...),
    model_name: str | None = Query(None),
) -> dict:
    """
    Generate LLM content for specific sections.
    
    This endpoint allows on-demand generation of LLM-enhanced content for:
    - Executive summaries
    - Biodiversity narratives
    - ML model explanations
    - Legal compliance recommendations
    """
    from ...reporting.langchain_llm import LangChainLLMService
    
    # Load run data
    run_store = RunManifestStore(settings.data_dir, settings.processed_dir_name)
    try:
        run_data = run_store.get_run(run_id)
        if hasattr(run_data, "dict"):
            run_dict = run_data.dict()
        elif hasattr(run_data, "model_dump"):
            run_dict = run_data.model_dump()
        else:
            run_dict = run_data if isinstance(run_data, dict) else {}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    # Build context
    context = _build_basic_context(run_dict)
    project_context = context.get("project", {})
    analysis_results = {
        "biodiversity": context.get("biodiversity", {}),
        "resm": context.get("ai", {}).get("resm", {}),
        "ahsm": context.get("ai", {}).get("ahsm", {}),
        "cim": context.get("ai", {}).get("cim", {}),
        "emissions": context.get("emissions", {}),
        "legal_summary": context.get("legal_summary", ""),
        "indicators": context.get("indicators", {}),
    }

    # Initialize LLM service
    llm_service = LangChainLLMService()
    
    if not llm_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="LLM service is not enabled. Please configure GROQ_API_KEY or set USE_LLM=true."
        )

    try:
        generated_content = ""
        
        if content_type == "executive_summary":
            # Get similar reports for RAG
            from ...reporting.report_memory_db import DatabaseReportMemoryStore
            similar_reports = []
            if isinstance(memory_store, DatabaseReportMemoryStore):
                try:
                    query_text = project_context.get("description", "") or project_context.get("name", "")
                    if query_text:
                        similar = memory_store.find_similar(query_text, limit=3, min_similarity=0.7)
                        similar_reports = [
                            {"summary": entry.summary or "", "report_id": entry.report_id}
                            for entry, _, _ in similar
                        ]
                except Exception:
                    pass
            
            generated_content = llm_service.generate_executive_summary(
                analysis_results=analysis_results,
                project_context=project_context,
                similar_reports=similar_reports,
            )
            
        elif content_type == "biodiversity_narrative":
            biodiversity = context.get("biodiversity", {})
            if not biodiversity:
                raise HTTPException(status_code=400, detail="No biodiversity data available for this run")
            
            generated_content = llm_service.generate_biodiversity_narrative(
                biodiversity_data=biodiversity,
                project_context=project_context,
            )
            
        elif content_type == "ml_explanation":
            if not model_name:
                raise HTTPException(status_code=400, detail="model_name is required for ml_explanation")
            
            model_data = analysis_results.get(model_name.lower(), {})
            if not model_data:
                raise HTTPException(status_code=400, detail=f"No data available for model: {model_name}")
            
            generated_content = llm_service.explain_ml_prediction(
                model_name=model_name.upper(),
                prediction=model_data,
            )
            
        elif content_type == "legal_recommendations":
            legal_findings = {"summary": context.get("legal_summary", "")}
            compliance_status = context.get("legal_compliance", {})
            
            generated_content = llm_service.generate_legal_recommendations(
                legal_findings=legal_findings,
                compliance_status=compliance_status,
                project_context=project_context,
            )
        
        return {
            "run_id": run_id,
            "content_type": content_type,
            "model_name": model_name,
            "content": generated_content,
            "provider": llm_service.provider,
        }
        
    except Exception as e:
        logger.error(f"Failed to generate LLM content: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate LLM content: {str(e)}")

