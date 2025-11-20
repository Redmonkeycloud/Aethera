"""Celery tasks for async processing."""

from __future__ import annotations

import json
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

        # Write config to temp file if provided
        config_path = None
        if config:
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, delete_on_close=False) as f:
                json.dump(config, f)
                config_path = f.name
                cmd.extend(["--config", config_path])

        # Update task state
        self.update_state(state="PROCESSING", meta={"message": "Executing analysis pipeline"})

        # Run the analysis
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
        )

        # Clean up temp files
        if config_path:
            Path(config_path).unlink(missing_ok=True)
        if aoi_geojson and aoi_path:
            Path(aoi_path).unlink(missing_ok=True)

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            logger.error("Analysis pipeline failed: %s", error_msg)
            self.update_state(state="FAILURE", meta={"error": error_msg})
            return {"status": "failed", "error": error_msg}

        # Extract run_id from output (assuming it's printed)
        # In practice, we'd parse the manifest or output directory
        run_id = "unknown"
        if "run_" in result.stdout:
            # Try to extract run_id from output
            for line in result.stdout.split("\n"):
                if "run_" in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith("run_"):
                            run_id = part
                            break

        logger.info("Analysis pipeline completed successfully for run %s", run_id)
        return {
            "status": "completed",
            "run_id": run_id,
            "project_id": project_id,
        }

    except Exception as exc:
        logger.exception("Error in analysis task: %s", exc)
        self.update_state(state="FAILURE", meta={"error": str(exc)})
        return {"status": "failed", "error": str(exc)}

