from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .models import Project, ProjectCreate, RunSummary, RunDetail


class ProjectStore:
    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> list[dict]:
        if not self.store_path.exists():
            return []
        with open(self.store_path, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: list[dict]) -> None:
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def list_projects(self) -> list[Project]:
        return [Project(**item) for item in self._read()]

    def get_project(self, project_id: str) -> Project | None:
        for item in self._read():
            if item["id"] == project_id:
                return Project(**item)
        return None

    def add_project(self, payload: ProjectCreate) -> Project:
        projects = self._read()
        project = Project(
            id=str(uuid4()),
            name=payload.name,
            country=payload.country,
            sector=payload.sector,
            created_at=datetime.utcnow(),
        )
        projects.append(project.dict())
        self._write(projects)
        return project


class RunManifestStore:
    def __init__(self, data_dir: Path, processed_dir_name: str) -> None:
        self.data_dir = Path(data_dir)
        self.processed_dir_name = processed_dir_name

    def _manifest_path(self, run_dir: Path) -> Path:
        return run_dir / "manifest.json"

    def _load_manifest(self, manifest_path: Path) -> dict | None:
        if manifest_path.exists():
            with open(manifest_path, encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_runs(self) -> list[RunSummary]:
        runs: list[RunSummary] = []
        for run_dir in sorted(self.data_dir.glob("run_*")):
            manifest = self._load_manifest(self._manifest_path(run_dir))
            if manifest:
                runs.append(RunSummary(**manifest))
        return runs

    def get_run(self, run_id: str) -> RunDetail | None:
        run_dir = self.data_dir / run_id
        manifest = self._load_manifest(self._manifest_path(run_dir))
        if manifest:
            return RunDetail(**manifest)
        return None

    def list_biodiversity_layers(self, run_id: str) -> dict[str, str]:
        run_dir = self.data_dir / run_id / self.processed_dir_name / "biodiversity"
        layers = {}
        if run_dir.exists():
            for key in ["sensitivity", "natura", "overlap"]:
                candidate = run_dir / f"{key}.geojson"
                if candidate.exists():
                    layers[key] = f"/runs/{run_id}/biodiversity/{key}"
        return layers

