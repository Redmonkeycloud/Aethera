"""Utilities for loading pretrained ensembles saved by scripts/pretrain_all_models.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import joblib


@dataclass
class PretrainedBundle:
    model_name: str
    model_path: Path
    models: Any
    vector_fields: Optional[list[str]] = None
    dataset_source: Optional[str] = None


def project_root_from_here(file: str) -> Path:
    # ai/models/*.py -> parents[2] is repo root
    return Path(file).resolve().parents[2]


def load_pretrained_bundle(model_name: str, *, here_file: str) -> PretrainedBundle | None:
    """
    Load pretrained model artifacts if present.

    Expected layout:
      <repo>/models/pretrained/<model_name>/ensemble.pkl
      <repo>/models/pretrained/<model_name>/metadata.json
    """
    repo_root = project_root_from_here(here_file)
    model_dir = repo_root / "models" / "pretrained" / model_name
    model_path = model_dir / "ensemble.pkl"
    if not model_path.exists():
        return None

    try:
        models = joblib.load(model_path)
    except Exception:
        return None

    vector_fields: list[str] | None = None
    dataset_source: str | None = None
    meta_path = model_dir / "metadata.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            vf = meta.get("vector_fields")
            if isinstance(vf, list) and all(isinstance(x, str) for x in vf):
                vector_fields = list(vf)
            ds = meta.get("dataset_source")
            if isinstance(ds, str) and ds:
                dataset_source = ds
        except Exception:
            pass

    return PretrainedBundle(
        model_name=model_name,
        model_path=model_path,
        models=models,
        vector_fields=vector_fields,
        dataset_source=dataset_source,
    )


