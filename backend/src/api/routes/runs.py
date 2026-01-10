from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from ..models import RunSummary, RunDetail
from ..storage import RunManifestStore
from ...config.base_settings import settings
from ...logging_utils import get_logger

router = APIRouter()
run_store = RunManifestStore(settings.data_dir, settings.processed_dir_name)
logger = get_logger(__name__)


@router.get("", response_model=list[RunSummary])
async def list_runs() -> list[RunSummary]:
    return run_store.list_runs()


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(run_id: str) -> RunDetail:
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    biodiversity_layers = run_store.list_biodiversity_layers(run_id)
    if biodiversity_layers:
        if "outputs" not in run.dict():
            run.outputs = {}
        run.outputs["biodiversity_layers"] = biodiversity_layers
    return run


@router.get("/{run_id}/results")
async def get_run_results(run_id: str) -> JSONResponse:
    """
    Get comprehensive results for a run.

    Returns all analysis results including:
    - Biodiversity predictions
    - Emissions calculations
    - Environmental KPIs
    - AI/ML model predictions (RESM, AHSM, CIM)
    - Receptor distances
    - Land cover summary
    """
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run_dir = settings.data_dir / run_id / settings.processed_dir_name
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run results not found")

    results: dict[str, Any] = {
        "run_id": run_id,
        "project_id": run.project_id,
        "project_type": run.project_type,
        "created_at": run.created_at.isoformat(),
    }

    # Load biodiversity prediction
    biodiversity_path = run_dir / "biodiversity" / "prediction.json"
    if biodiversity_path.exists():
        with open(biodiversity_path, encoding="utf-8") as f:
            results["biodiversity"] = json.load(f)

    # Load emissions (check both new and old locations for backward compatibility)
    emissions_path = run_dir / "emissions" / "emission_summary.json"
    if not emissions_path.exists():
        # Try old location (root of run_dir) for backward compatibility
        emissions_path = run_dir / "emissions_summary.json"
    if emissions_path.exists():
        with open(emissions_path, encoding="utf-8") as f:
            data = json.load(f)
            # Handle list format from save_summary
            results["emissions"] = data[0] if isinstance(data, list) and len(data) > 0 else data

    # Load KPIs
    kpis_path = run_dir / "kpis" / "environmental_kpis.json"
    if kpis_path.exists():
        with open(kpis_path, encoding="utf-8") as f:
            results["kpis"] = json.load(f)

    # Load RESM prediction (check both new and old locations for backward compatibility)
    resm_path = run_dir / "predictions" / "resm_prediction.json"
    if not resm_path.exists():
        # Try old location (root of run_dir) for backward compatibility
        resm_path = run_dir / "resm_prediction.json"
    if resm_path.exists():
        with open(resm_path, encoding="utf-8") as f:
            data = json.load(f)
            # Handle list format from save_summary
            results["resm"] = data[0] if isinstance(data, list) and len(data) > 0 else data

    # Load AHSM prediction (check both new and old locations for backward compatibility)
    ahsm_path = run_dir / "predictions" / "ahsm_prediction.json"
    if not ahsm_path.exists():
        # Try old location (root of run_dir) for backward compatibility
        ahsm_path = run_dir / "ahsm_prediction.json"
    if ahsm_path.exists():
        with open(ahsm_path, encoding="utf-8") as f:
            data = json.load(f)
            # Handle list format from save_summary
            results["ahsm"] = data[0] if isinstance(data, list) and len(data) > 0 else data

    # Load CIM prediction (check both new and old locations for backward compatibility)
    cim_path = run_dir / "predictions" / "cim_prediction.json"
    if not cim_path.exists():
        # Try old location (root of run_dir) for backward compatibility
        cim_path = run_dir / "cim_prediction.json"
    if cim_path.exists():
        with open(cim_path, encoding="utf-8") as f:
            data = json.load(f)
            # Handle list format from save_summary
            results["cim"] = data[0] if isinstance(data, list) and len(data) > 0 else data

    # Load receptor distances
    receptor_path = run_dir / "receptors" / "receptor_distances.json"
    if receptor_path.exists():
        with open(receptor_path, encoding="utf-8") as f:
            results["receptor_distances"] = json.load(f)

    # Load land cover summary
    land_cover_path = run_dir / "land_cover_summary.json"
    if land_cover_path.exists():
        with open(land_cover_path, encoding="utf-8") as f:
            results["land_cover"] = json.load(f)

    return JSONResponse(content=results)


@router.get("/{run_id}/legal")
async def get_run_legal(run_id: str) -> JSONResponse:
    """
    Get legal compliance results for a run.

    Returns the legal evaluation results including:
    - Overall compliance status
    - Rule-by-rule evaluation
    - Critical violations
    - Warnings
    - Informational messages
    """
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run_dir = settings.data_dir / run_id / settings.processed_dir_name
    legal_path = run_dir / "legal_evaluation.json"
    if not legal_path.exists():
        raise HTTPException(status_code=404, detail="Legal evaluation not found for this run")

    try:
        with open(legal_path, encoding="utf-8") as f:
            legal_data = json.load(f)
        # save_summary saves data as a list, so extract the first element if it's a list
        if isinstance(legal_data, list) and len(legal_data) > 0:
            legal_data = legal_data[0]
    except json.JSONDecodeError as e:
        logger.error("Failed to parse legal_evaluation.json for run %s: %s", run_id, e)
        # Return a graceful error response - file is corrupted, likely from interrupted write
        return JSONResponse(
            status_code=404,
            content={
                "error": "Legal evaluation file is corrupted or incomplete",
                "detail": f"JSON parse error at {e.msg}: line {e.lineno}, column {e.colno}",
                "run_id": run_id,
                "message": "The legal evaluation file appears to be corrupted. Please re-run the analysis to regenerate it."
            }
        )
    except Exception as e:
        logger.error("Error reading legal_evaluation.json for run %s: %s", run_id, e)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Error reading legal evaluation",
                "detail": str(e),
                "run_id": run_id
            }
        )

    return JSONResponse(content=legal_data)


@router.get("/{run_id}/export")
async def export_run(run_id: str) -> FileResponse:
    """
    Export a complete run package as a ZIP file.

    The export includes:
    - All processed geospatial data
    - Analysis results (JSON)
    - Biodiversity layers
    - Predictions
    - Legal evaluation
    - Manifest
    """
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run_dir = settings.data_dir / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run directory not found")

    # Create temporary ZIP file
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
        zip_path = Path(tmp_zip.name)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the run directory
            for file_path in run_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(run_dir.parent)
                    zipf.write(file_path, arcname)

        return FileResponse(
            path=zip_path,
            filename=f"{run_id}_export.zip",
            media_type="application/zip",
        )
    except Exception as exc:
        # Clean up on error
        if zip_path.exists():
            zip_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error creating export: {str(exc)}")


@router.post("/{run_id}/explainability/{model_name}/generate")
async def generate_run_explainability(run_id: str, model_name: str) -> JSONResponse:
    """
    Generate explainability artifacts for a model (on-demand).
    
    This endpoint generates SHAP values and Yellowbrick plots for the specified model.
    Note: This may take some time as it retrains the model and generates visualizations.
    
    Args:
        run_id: Run identifier
        model_name: Model name (biodiversity, resm, ahsm, cim)
    """
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_dir = settings.data_dir / run_id / settings.processed_dir_name
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run results not found")
    
    explainability_dir = run_dir / "explainability" / model_name
    explainability_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        from ...analysis.model_explainability import (
            generate_biodiversity_explainability,
            generate_resm_explainability,
            generate_ahsm_explainability,
            generate_cim_explainability,
        )
        from ...datasets.catalog import DatasetCatalog
        
        catalog = DatasetCatalog(settings.data_sources_dir)
        
        # Get training data path from catalog
        config_path = None
        if model_name == "biodiversity":
            try:
                config_path = str(catalog.biodiversity_training())
            except FileNotFoundError:
                pass
            artifacts = generate_biodiversity_explainability(
                config_path=config_path,
                output_dir=explainability_dir,
            )
        elif model_name == "resm":
            try:
                config_path = str(catalog.resm_training()) if hasattr(catalog, "resm_training") else None
            except (FileNotFoundError, AttributeError):
                pass
            artifacts = generate_resm_explainability(
                config_path=config_path,
                output_dir=explainability_dir,
            )
        elif model_name == "ahsm":
            try:
                config_path = str(catalog.ahsm_training()) if hasattr(catalog, "ahsm_training") else None
            except (FileNotFoundError, AttributeError):
                pass
            artifacts = generate_ahsm_explainability(
                config_path=config_path,
                output_dir=explainability_dir,
            )
        elif model_name == "cim":
            try:
                config_path = str(catalog.cim_training()) if hasattr(catalog, "cim_training") else None
            except (FileNotFoundError, AttributeError):
                pass
            artifacts = generate_cim_explainability(
                config_path=config_path,
                output_dir=explainability_dir,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown model name: {model_name}")
        
        # Save artifacts
        from ...analysis.explainability import save_explainability_artifacts, _get_cache_key
        cache_key = _get_cache_key(model_name, config_path, "default")
        saved_paths = save_explainability_artifacts(
            artifacts=artifacts,
            output_dir=run_dir / "explainability",
            model_name=model_name,
            use_cache=True,
            cache_key=cache_key,
        )
        
        return JSONResponse(content={
            "status": "success",
            "model_name": model_name,
            "run_id": run_id,
            "artifacts": saved_paths,
        })
        
    except Exception as e:
        logger.error(f"Error generating explainability for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating explainability: {str(e)}")


@router.get("/{run_id}/explainability/{model_name}")
async def get_run_explainability(run_id: str, model_name: str) -> JSONResponse:
    """
    Get model explainability artifacts for a specific model.
    
    Args:
        run_id: Run identifier
        model_name: Model name (biodiversity, resm, ahsm, cim)
        
    Returns:
        Explainability artifacts including SHAP values and visualization paths
    """
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_dir = settings.data_dir / run_id / settings.processed_dir_name
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run results not found")
    
    explainability_dir = run_dir / "explainability" / model_name
    metadata_path = explainability_dir / "explainability_metadata.json"
    
    # Check if explainability artifacts exist
    if not metadata_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Explainability artifacts not found for model {model_name}. "
                   "They may not have been generated during analysis."
        )
    
    try:
        with open(metadata_path, encoding="utf-8") as f:
            metadata = json.load(f)
        
        # Load SHAP data if available
        shap_data = {}
        shap_path = explainability_dir / "shap_values.json"
        if shap_path.exists():
            with open(shap_path, encoding="utf-8") as f:
                shap_data = json.load(f)
        
        # Get plot paths (API-accessible URLs)
        plots = {}
        if "plots" in metadata.get("artifacts", {}):
            plot_artifacts = metadata["artifacts"]["plots"]
            
            # Handle nested structure (plots organized by submodel in ensemble)
            # Structure: {submodel_name: {plot_name: relative_path}}
            if isinstance(plot_artifacts, dict):
                for submodel_name, submodel_plots in plot_artifacts.items():
                    if isinstance(submodel_plots, dict):
                        # Nested: {submodel_name: {plot_name: path}}
                        for plot_name, plot_path in submodel_plots.items():
                            if isinstance(plot_path, str):
                                # Construct full path from relative path
                                plot_file = run_dir / plot_path if not Path(plot_path).is_absolute() else Path(plot_path)
                                if plot_file.exists():
                                    # Use the relative path structure for the API endpoint
                                    # e.g., "biodiversity/random_forest/confusion_matrix.png"
                                    relative_plot_path = plot_path.replace('\\', '/')  # Normalize path separators
                                    if not relative_plot_path.startswith('explainability/'):
                                        # Extract relative path from explainability directory
                                        try:
                                            rel_path = plot_file.relative_to(explainability_dir.parent)
                                            relative_plot_path = str(rel_path).replace('\\', '/')
                                        except ValueError:
                                            # Fallback: use the path from metadata
                                            relative_plot_path = plot_path.replace('\\', '/')
                                    
                                    # Store with submodel prefix for uniqueness
                                    plots[f"{submodel_name}/{plot_name}"] = f"/runs/{run_id}/explainability/{model_name}/plots/{relative_plot_path}"
                    else:
                        # Flat structure: {plot_name: path}
                        plot_name = submodel_name
                        plot_path = submodel_plots
                        if isinstance(plot_path, str):
                            plot_file = run_dir / plot_path if not Path(plot_path).is_absolute() else Path(plot_path)
                        else:
                            plot_file = explainability_dir / f"{plot_name}.png"
                        
                        if plot_file.exists():
                            # Use relative path if available, otherwise just filename
                            if isinstance(plot_path, str) and '/' in plot_path:
                                relative_plot_path = plot_path.replace('\\', '/')
                            else:
                                relative_plot_path = f"{plot_name}.png"
                            plots[plot_name] = f"/runs/{run_id}/explainability/{model_name}/plots/{relative_plot_path}"
        
        result = {
            "model_name": model_name,
            "run_id": run_id,
            "shap_values": shap_data,
            "plots": plots,
            "metadata": metadata,
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error loading explainability for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading explainability: {str(e)}")


@router.get("/{run_id}/explainability/{model_name}/plots/{plot_path:path}")
async def get_explainability_plot(run_id: str, model_name: str, plot_path: str) -> FileResponse:
    """
    Get a specific explainability plot image.
    
    Args:
        run_id: Run identifier
        model_name: Model name
        plot_path: Plot path (e.g., confusion_matrix.png or random_forest/confusion_matrix.png)
        
    Returns:
        PNG image file
    """
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_dir = settings.data_dir / run_id / settings.processed_dir_name
    explainability_dir = run_dir / "explainability" / model_name
    
    # Handle both flat and nested plot paths
    # plot_path could be "confusion_matrix.png" or "random_forest/confusion_matrix.png"
    if plot_path.endswith('.png'):
        # Remove .png extension for path construction
        plot_name = plot_path[:-4]
    else:
        plot_name = plot_path
        plot_path = f"{plot_name}.png"
    
    # Try nested path first (submodel_name/plot_name.png)
    plot_file = explainability_dir / plot_path
    if not plot_file.exists():
        # Try flat path (plot_name.png directly in model directory)
        plot_file = explainability_dir / f"{plot_name}.png"
    
    if not plot_file.exists():
        # Try to find the file by searching subdirectories
        found_file = None
        for subdir in explainability_dir.iterdir():
            if subdir.is_dir():
                candidate = subdir / plot_path
                if candidate.exists():
                    found_file = candidate
                    break
        
        if found_file:
            plot_file = found_file
        else:
            raise HTTPException(status_code=404, detail=f"Plot {plot_path} not found")
    
    return FileResponse(
        path=plot_file,
        media_type="image/png",
        filename=f"{model_name}_{Path(plot_path).name}",
    )


@router.get("/{run_id}/explainability/{model_name}/export")
async def export_explainability_report(run_id: str, model_name: str) -> FileResponse:
    """
    Export explainability report as PDF or ZIP.
    
    Args:
        run_id: Run identifier
        model_name: Model name (biodiversity, resm, ahsm, cim)
        
    Returns:
        PDF report or ZIP file with all explainability artifacts
    """
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_dir = settings.data_dir / run_id / settings.processed_dir_name
    explainability_dir = run_dir / "explainability" / model_name
    
    if not explainability_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Explainability artifacts not found for model {model_name}"
        )
    
    try:
        import tempfile
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf_path = Path(tmp_pdf.name)
        
        # Create PDF document
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
        )
        story.append(Paragraph(f"Model Explainability Report: {model_name.upper()}", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Load metadata
        metadata_path = explainability_dir / "explainability_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, encoding="utf-8") as f:
                metadata = json.load(f)
            
            story.append(Paragraph(f"<b>Run ID:</b> {run_id}", styles['Normal']))
            story.append(Paragraph(f"<b>Model:</b> {model_name}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Add plots (search recursively in subdirectories for ensemble models)
        plot_files = []
        # Direct plots
        plot_files.extend(explainability_dir.glob("*.png"))
        # Plots in subdirectories (for ensemble models)
        for subdir in explainability_dir.iterdir():
            if subdir.is_dir():
                plot_files.extend(subdir.glob("*.png"))
        
        if plot_files:
            story.append(Paragraph("<b>Visualizations</b>", styles['Heading2']))
            story.append(Spacer(1, 0.2*inch))
            
            for plot_file in sorted(plot_files):
                try:
                    # Add plot name
                    plot_name = plot_file.stem.replace("_", " ").title()
                    story.append(Paragraph(f"<b>{plot_name}</b>", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                    
                    # Add image (resize to fit page)
                    img = Image(str(plot_file), width=6*inch, height=4.5*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                    story.append(PageBreak())
                except Exception as e:
                    logger.warning(f"Failed to add plot {plot_file.name}: {e}")
        
        # Add SHAP data summary
        shap_path = explainability_dir / "shap_values.json"
        if shap_path.exists():
            story.append(Paragraph("<b>SHAP Feature Importance Summary</b>", styles['Heading2']))
            story.append(Spacer(1, 0.2*inch))
            
            with open(shap_path, encoding="utf-8") as f:
                shap_data = json.load(f)
            
            # Create table of top features
            for model_name_key, model_shap in shap_data.items():
                if "feature_importance" in model_shap:
                    story.append(Paragraph(f"<b>{model_name_key}</b>", styles['Heading3']))
                    story.append(Spacer(1, 0.1*inch))
                    
                    # Sort features by importance
                    features = sorted(
                        model_shap["feature_importance"].items(),
                        key=lambda x: abs(x[1]),
                        reverse=True
                    )[:10]  # Top 10
                    
                    for feature, importance in features:
                        story.append(
                            Paragraph(
                                f"• {feature}: {importance:.4f}",
                                styles['Normal']
                            )
                        )
                    story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{model_name}_explainability_report_{run_id}.pdf",
        )
        
    except (ImportError, NameError):
        # Fallback to ZIP if reportlab not available
        import zipfile
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
            zip_path = Path(tmp_zip.name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from explainability directory
            for file_path in explainability_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(run_dir)
                    zipf.write(file_path, arcname)
        
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=f"{model_name}_explainability_{run_id}.zip",
        )
        
    except Exception as e:
        logger.error(f"Error exporting explainability report: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting report: {str(e)}")

