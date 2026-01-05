"""Helper functions for building enhanced reports with visualizations and explanations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from ..config.base_settings import settings
from ..logging_utils import get_logger
from .text_generator import TextGenerator
from .visualizations import VisualizationGenerator

logger = get_logger(__name__)


def build_enhanced_report_context(
    run_id: str,
    run_dict: Dict[str, Any],
    text_generator: TextGenerator,
    viz_generator: VisualizationGenerator,
) -> Dict[str, Any]:
    """
    Build enhanced report context with visualizations and explanatory text.
    
    Args:
        run_id: Run identifier
        run_dict: Run metadata dictionary
        text_generator: TextGenerator instance
        viz_generator: VisualizationGenerator instance
    
    Returns:
        Enhanced context dictionary for report template
    """
    run_dir = settings.data_dir / run_id / settings.processed_dir_name
    results: Dict[str, Any] = {}
    
    # Load all result files
    try:
        biodiversity_path = run_dir / "biodiversity" / "prediction.json"
        if biodiversity_path.exists():
            with open(biodiversity_path, encoding="utf-8") as f:
                biodiversity_data = json.load(f)
                results["biodiversity"] = biodiversity_data[0] if isinstance(biodiversity_data, list) else biodiversity_data
        
        emissions_path = run_dir / "emissions" / "emission_summary.json"
        if emissions_path.exists():
            with open(emissions_path, encoding="utf-8") as f:
                emissions_data = json.load(f)
                results["emissions"] = emissions_data[0] if isinstance(emissions_data, list) else emissions_data
        
        resm_path = run_dir / "predictions" / "resm_prediction.json"
        if resm_path.exists():
            with open(resm_path, encoding="utf-8") as f:
                resm_data = json.load(f)
                results["resm"] = resm_data[0] if isinstance(resm_data, list) else resm_data
        
        ahsm_path = run_dir / "predictions" / "ahsm_prediction.json"
        if ahsm_path.exists():
            with open(ahsm_path, encoding="utf-8") as f:
                ahsm_data = json.load(f)
                results["ahsm"] = ahsm_data[0] if isinstance(ahsm_data, list) else ahsm_data
        
        cim_path = run_dir / "predictions" / "cim_prediction.json"
        if cim_path.exists():
            with open(cim_path, encoding="utf-8") as f:
                cim_data = json.load(f)
                results["cim"] = cim_data[0] if isinstance(cim_data, list) else cim_data
        
        kpis_path = run_dir / "kpis" / "environmental_kpis.json"
        if kpis_path.exists():
            with open(kpis_path, encoding="utf-8") as f:
                kpis_data = json.load(f)
                results["kpis"] = kpis_data[0] if isinstance(kpis_data, list) else kpis_data
        
        land_cover_path = run_dir / "land_cover_summary.json"
        if land_cover_path.exists():
            with open(land_cover_path, encoding="utf-8") as f:
                land_cover_data = json.load(f)
                results["land_cover"] = land_cover_data if isinstance(land_cover_data, list) else [land_cover_data]
        
        legal_path = run_dir / "legal_evaluation.json"
        if legal_path.exists():
            try:
                with open(legal_path, encoding="utf-8") as f:
                    legal_data = json.load(f)
                    results["legal"] = legal_data[0] if isinstance(legal_data, list) else legal_data
            except Exception:
                pass  # Legal data may be corrupted, skip it
    except Exception as e:
        logger.warning("Error loading some result files: %s", e)

    # Generate visualizations
    charts_dir = settings.data_dir / "reports" / "charts" / run_id
    charts_dir.mkdir(parents=True, exist_ok=True)
    chart_paths: Dict[str, str] = {}
    
    # Biodiversity chart
    if results.get("biodiversity") and results["biodiversity"].get("score") is not None:
        biodiversity_score = results["biodiversity"]["score"]
        chart_path = charts_dir / "biodiversity_scale.png"
        viz_generator.generate_score_scale_image(biodiversity_score, "Biodiversity Sensitivity", chart_path)
        chart_paths["biodiversity"] = f"charts/{run_id}/biodiversity_scale.png"
    
    # Emissions chart
    if results.get("emissions"):
        emissions_dict = {
            "Baseline": results["emissions"].get("baseline_tco2e", 0),
            "Construction": results["emissions"].get("project_construction_tco2e", 0),
            "Operation (annual)": results["emissions"].get("project_operation_tco2e_per_year", 0),
        }
        chart_path = charts_dir / "emissions_comparison.png"
        viz_generator.emissions_comparison_chart(emissions_dict, "Carbon Emissions Comparison", chart_path)
        chart_paths["emissions"] = f"charts/{run_id}/emissions_comparison.png"
    
    # AI models chart
    ai_scores: Dict[str, float] = {}
    if results.get("resm") and results["resm"].get("score") is not None:
        ai_scores["RESM"] = results["resm"]["score"]
    if results.get("ahsm") and results["ahsm"].get("score") is not None:
        ai_scores["AHSM"] = results["ahsm"]["score"]
    if results.get("cim") and results["cim"].get("score") is not None:
        ai_scores["CIM"] = results["cim"]["score"]
    
    if ai_scores:
        chart_path = charts_dir / "ai_scores.png"
        viz_generator.score_bar_chart(ai_scores, "AI Model Assessment Scores", chart_path)
        chart_paths["ai_models"] = f"charts/{run_id}/ai_scores.png"
    
    # Generate explanatory text
    project_context = {
        "project_type": run_dict.get("project_type", "unknown"),
        "country": run_dict.get("country"),
    }
    
    # Add explanations to results
    if results.get("biodiversity") and results["biodiversity"].get("score") is not None:
        results["biodiversity"]["explanation"] = text_generator.generate_explanation(
            "biodiversity_score", results["biodiversity"]["score"], project_context, "biodiversity"
        )
    
    if results.get("emissions"):
        results["emissions"]["explanation"] = text_generator.generate_section_summary(
            "emissions", results["emissions"], project_context
        )
    
    if results.get("resm") and results["resm"].get("score") is not None:
        results["resm"]["explanation"] = text_generator.generate_explanation(
            "resm_score", results["resm"]["score"], project_context, "ai_model"
        )
    
    if results.get("ahsm") and results["ahsm"].get("score") is not None:
        results["ahsm"]["explanation"] = text_generator.generate_explanation(
            "ahsm_score", results["ahsm"]["score"], project_context, "ai_model"
        )
    
    if results.get("cim") and results["cim"].get("score") is not None:
        results["cim"]["explanation"] = text_generator.generate_explanation(
            "cim_score", results["cim"]["score"], project_context, "ai_model"
        )
    
    # Generate executive summary
    summary_parts = []
    if results.get("biodiversity", {}).get("score") is not None:
        summary_parts.append(f"Biodiversity sensitivity score: {results['biodiversity']['score']:.1f}/100")
    if results.get("cim", {}).get("score") is not None:
        summary_parts.append(f"Cumulative impact score: {results['cim']['score']:.1f}/100")
    if results.get("legal", {}).get("overall_compliant") is not None:
        compliance_status = "compliant" if results["legal"]["overall_compliant"] else "non-compliant"
        summary_parts.append(f"Legal compliance: {compliance_status}")
    
    executive_summary = text_generator.generate_section_summary(
        "executive_summary",
        {"summary_parts": summary_parts, "project": {"type": run_dict.get("project_type", "unknown")}},
        project_context
    ) if summary_parts else "This report presents a comprehensive environmental impact assessment for the proposed project."
    
    # Build context
    context = {
        "run_id": run_id,
        "project": {
            "name": run_dict.get("project_name") or run_dict.get("name", "Unknown Project"),
            "type": run_dict.get("project_type", "unknown"),
            "country": run_dict.get("country"),
            "capacity_mw": run_dict.get("capacity_mw", 0),
        },
        "indicators": run_dict.get("indicators", {}),
        "emissions": results.get("emissions", {}),
        "biodiversity": results.get("biodiversity", {}),
        "ai_models": {
            "resm": results.get("resm", {}),
            "ahsm": results.get("ahsm", {}),
            "cim": results.get("cim", {}),
        },
        "kpis": results.get("kpis", {}),
        "legal": results.get("legal", {}),
        "legal_summary": results.get("legal", {}).get("summary", "No legal assessment available.") if results.get("legal") else "No legal assessment available.",
        "land_cover": results.get("land_cover", []),
        "assessment_date": run_dict.get("created_at", ""),
        "report_date": datetime.utcnow().isoformat(),
        "executive_summary": executive_summary,
        "biodiversity_chart": chart_paths.get("biodiversity", ""),
        "emissions_chart": chart_paths.get("emissions", ""),
        "ai_models_chart": chart_paths.get("ai_models", ""),
    }
    
    return context

