"""Persistence helpers for model run metadata."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from psycopg import sql
from psycopg.types.json import Jsonb

from .client import DatabaseClient


@dataclass
class ModelRunRecord:
    run_id: str
    model_name: str
    model_version: str
    dataset_source: Optional[str]
    candidate_models: Optional[list[str]]
    selected_model: Optional[str]
    metrics: Dict[str, Any]
    created_at: datetime = datetime.utcnow()
    id: str = ""

    def as_db_tuple(self) -> tuple:
        return (
            self.id or str(uuid4()),
            self.run_id,
            self.model_name,
            self.model_version,
            self.dataset_source,
            self.candidate_models,
            self.selected_model,
            self.metrics,
            self.created_at,
        )


class ModelRunLogger:
    INSERT_QUERY = """
        INSERT INTO model_runs (
            id, run_id, model_name, model_version, dataset_source,
            candidate_models, selected_model, metrics, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    def __init__(self, client: DatabaseClient) -> None:
        self.client = client

    def log(self, record: ModelRunRecord) -> None:
        with self.client.connection() as conn:
            with conn.cursor() as cur:
                # Convert metrics dict to Jsonb for proper JSONB insertion
                values = list(record.as_db_tuple())
                # Replace metrics (index 7) with Jsonb wrapper
                values[7] = Jsonb(values[7])
                cur.execute(self.INSERT_QUERY, tuple(values))

