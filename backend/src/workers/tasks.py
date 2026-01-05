"""Celery tasks for async processing."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .celery_app import celery_app
from ..config.base_settings import settings
from ..logging_utils import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="aethera.run_analysis")
def run_analysis_task(
    self,
    project_id: str,
    aoi_path: str | None = None,
    aoi_geojson: dict[str, Any] | None = None,
    project_type: str = "solar",
    country: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run an AETHERA analysis pipeline asynchronously.

    Args:
        self: Celery task instance
        project_id: Project identifier
        aoi_path: Path to AOI file (if provided)
        aoi_geojson: AOI as GeoJSON dict (if provided instead of path)
        project_type: Type of project (e.g., "solar", "wind")
        country: ISO 3166-1 alpha-3 country code for legal rules
        config: Optional run configuration dict

    Returns:
        Dictionary with run_id and status
    """
    try:
        # Update task state
        self.update_state(state="PROCESSING", meta={"message": "Starting analysis pipeline"})

        # Prepare AOI file if GeoJSON provided
        if aoi_geojson and not aoi_path:
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as f:
                json.dump(aoi_geojson, f)
                aoi_path = f.name

        if not aoi_path:
            raise ValueError("Either aoi_path or aoi_geojson must be provided")

        # Prepare command arguments
        # Find project root (3 levels up from backend/src/workers/tasks.py)
        project_root = Path(__file__).parent.parent.parent.parent
        
        cmd = [
            sys.executable,
            "-m",
            "backend.src.main_controller",
            "--aoi",
            aoi_path,
            "--project-type",
            project_type,
        ]

        if country:
            cmd.extend(["--country", country])

        # Write config to temp file (ensure project_id is included)
        import tempfile
        config_dict = config.copy() if config else {}
        config_dict["project_id"] = project_id  # Always include project_id in config
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, delete_on_close=False) as f:
            json.dump(config_dict, f)
            config_path = f.name
            cmd.extend(["--config", config_path])

        # Update task state
        self.update_state(state="PROCESSING", meta={"message": "Executing analysis pipeline"})

        # Run the analysis with PYTHONPATH set to project root
        # This ensures imports like "backend.src.config" work correctly
        env = dict(os.environ)
        # Add project root to PYTHONPATH
        pythonpath = env.get("PYTHONPATH", "")
        if pythonpath:
            env["PYTHONPATH"] = f"{project_root}{os.pathsep}{pythonpath}"
        else:
            env["PYTHONPATH"] = str(project_root)
        
        logger.info("Running analysis with PYTHONPATH=%s", env["PYTHONPATH"])

        # Run the analysis
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root,
            env=env,
        )

        # Clean up temp files
        if config_path:
            Path(config_path).unlink(missing_ok=True)
        if aoi_geojson and aoi_path:
            Path(aoi_path).unlink(missing_ok=True)

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            logger.error("Analysis pipeline failed (returncode=%d):\nSTDOUT:\n%s\nSTDERR:\n%s", 
                        result.returncode, result.stdout, result.stderr)
            # Update state with properly formatted error for Celery
            try:
                self.update_state(
                    state="FAILURE",
                    meta={
                        "error": error_msg,
                        "exc_type": "SubprocessError",
                        "returncode": result.returncode,
                    }
                )
            except Exception as update_err:
                logger.error("Failed to update task state: %s", update_err)
            return {"status": "failed", "error": error_msg}

        # Extract run_id by finding the most recent run directory
        # The analysis creates a run directory with pattern "run_YYYYMMDD_HHMMSS"
        run_dirs = sorted(settings.data_dir.glob("run_*"))
        if run_dirs:
            # Get the most recent run directory (assuming it was just created)
            run_id = run_dirs[-1].name
            # Verify it has a manifest (confirming the analysis completed)
            manifest_path = run_dirs[-1] / "manifest.json"
            if not manifest_path.exists():
                logger.warning("Most recent run directory %s does not have a manifest yet", run_id)
        else:
            run_id = "unknown"
            logger.warning("No run directories found to extract run_id")

        logger.info("Analysis pipeline completed successfully for run %s", run_id)
        return {
            "status": "completed",
            "run_id": run_id,
            "project_id": project_id,
        }

    except Exception as exc:
        import traceback
        error_msg = str(exc)
        error_traceback = traceback.format_exc()
        logger.exception("Error in analysis task: %s", exc)
        # Update state with properly formatted error
        try:
            self.update_state(
                state="FAILURE",
                meta={
                    "error": error_msg,
                    "traceback": error_traceback,
                    "exc_type": type(exc).__name__,
                }
            )
        except Exception:
            # If updating state fails, just log it
            logger.error("Failed to update task state with error: %s", error_traceback)
        return {"status": "failed", "error": error_msg}

