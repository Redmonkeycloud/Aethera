"""Model Registry: Centralized model versioning and lifecycle management."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from ..db.client import DatabaseClient


class ModelStage(str, Enum):
    """Model lifecycle stages."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


@dataclass
class ModelRegistryEntry:
    """Represents a model in the registry."""

    model_name: str
    version: str
    stage: ModelStage = ModelStage.DEVELOPMENT
    description: str | None = None
    model_path: str | None = None
    training_data_hash: str | None = None
    hyperparameters: dict[str, Any] | None = None
    training_metadata: dict[str, Any] | None = None
    created_by: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: UUID | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id) if self.id else None,
            "model_name": self.model_name,
            "version": self.version,
            "stage": self.stage.value,
            "description": self.description,
            "model_path": self.model_path,
            "training_data_hash": self.training_data_hash,
            "hyperparameters": self.hyperparameters,
            "training_metadata": self.training_metadata,
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ModelRegistry:
    """Manages model versions and lifecycle in the registry."""

    def __init__(self, db_client: DatabaseClient) -> None:
        """Initialize model registry.

        Args:
            db_client: Database client for persistence
        """
        self.db_client = db_client

    def register_model(
        self,
        model_name: str,
        version: str,
        stage: ModelStage | str = ModelStage.DEVELOPMENT,
        description: str | None = None,
        model_path: str | None = None,
        training_data_path: str | None = None,
        hyperparameters: dict[str, Any] | None = None,
        training_metadata: dict[str, Any] | None = None,
        created_by: str | None = None,
    ) -> ModelRegistryEntry:
        """Register a new model version.

        Args:
            model_name: Name of the model (e.g., 'biodiversity_ensemble')
            version: Version string (e.g., '0.1.0', '1.2.3')
            stage: Lifecycle stage
            description: Optional description
            model_path: Path to serialized model file
            training_data_path: Path to training data (for hash calculation)
            hyperparameters: Model hyperparameters
            training_metadata: Additional training metadata
            created_by: User who created this version

        Returns:
            Registered model entry
        """
        # Calculate training data hash if path provided
        training_data_hash = None
        if training_data_path:
            training_data_hash = self._calculate_file_hash(training_data_path)

        # Normalize stage
        if isinstance(stage, str):
            stage = ModelStage(stage)

        entry = ModelRegistryEntry(
            model_name=model_name,
            version=version,
            stage=stage,
            description=description,
            model_path=model_path,
            training_data_hash=training_data_hash,
            hyperparameters=hyperparameters,
            training_metadata=training_metadata,
            created_by=created_by,
        )

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO model_registry (
                        id, model_name, version, stage, description, model_path,
                        training_data_hash, hyperparameters, training_metadata,
                        created_by, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id, created_at, updated_at
                    """,
                    (
                        uuid4(),
                        entry.model_name,
                        entry.version,
                        entry.stage.value,
                        entry.description,
                        entry.model_path,
                        entry.training_data_hash,
                        Jsonb(entry.hyperparameters) if entry.hyperparameters else None,
                        Jsonb(entry.training_metadata) if entry.training_metadata else None,
                        entry.created_by,
                        entry.created_at,
                        entry.updated_at,
                    ),
                )
                row = cur.fetchone()
                entry.id = row[0]
                entry.created_at = row[1]
                entry.updated_at = row[2]

        return entry

    def get_model(self, model_name: str, version: str) -> ModelRegistryEntry | None:
        """Get a specific model version.

        Args:
            model_name: Model name
            version: Model version

        Returns:
            Model entry or None if not found
        """
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, model_name, version, stage, description, model_path,
                           training_data_hash, hyperparameters, training_metadata,
                           created_by, approved_by, approved_at, created_at, updated_at
                    FROM model_registry
                    WHERE model_name = %s AND version = %s
                    """,
                    (model_name, version),
                )
                row = cur.fetchone()
                if not row:
                    return None

                return self._row_to_entry(row)

    def list_models(
        self,
        model_name: str | None = None,
        stage: ModelStage | str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelRegistryEntry]:
        """List models in the registry.

        Args:
            model_name: Filter by model name
            stage: Filter by stage
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of model entries
        """
        conditions = []
        params: list[Any] = []

        if model_name:
            conditions.append("model_name = %s")
            params.append(model_name)

        if stage:
            stage_value = stage.value if isinstance(stage, ModelStage) else stage
            conditions.append("stage = %s")
            params.append(stage_value)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        params.extend([limit, offset])

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, model_name, version, stage, description, model_path,
                           training_data_hash, hyperparameters, training_metadata,
                           created_by, approved_by, approved_at, created_at, updated_at
                    FROM model_registry
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    tuple(params),
                )
                rows = cur.fetchall()
                return [self._row_to_entry(row) for row in rows]

    def get_latest_version(self, model_name: str, stage: ModelStage | str | None = None) -> ModelRegistryEntry | None:
        """Get the latest version of a model.

        Args:
            model_name: Model name
            stage: Optional stage filter

        Returns:
            Latest model entry or None
        """
        conditions = ["model_name = %s"]
        params: list[Any] = [model_name]

        if stage:
            stage_value = stage.value if isinstance(stage, ModelStage) else stage
            conditions.append("stage = %s")
            params.append(stage_value)

        where_clause = "WHERE " + " AND ".join(conditions)

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, model_name, version, stage, description, model_path,
                           training_data_hash, hyperparameters, training_metadata,
                           created_by, approved_by, approved_at, created_at, updated_at
                    FROM model_registry
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    tuple(params),
                )
                row = cur.fetchone()
                if not row:
                    return None

                return self._row_to_entry(row)

    def promote_model(
        self,
        model_name: str,
        version: str,
        target_stage: ModelStage | str,
        approved_by: str,
    ) -> ModelRegistryEntry:
        """Promote a model to a new stage (e.g., development -> production).

        Args:
            model_name: Model name
            version: Model version
            target_stage: Target stage
            approved_by: User approving the promotion

        Returns:
            Updated model entry
        """
        if isinstance(target_stage, str):
            target_stage = ModelStage(target_stage)

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE model_registry
                    SET stage = %s, approved_by = %s, approved_at = %s, updated_at = %s
                    WHERE model_name = %s AND version = %s
                    RETURNING id, model_name, version, stage, description, model_path,
                              training_data_hash, hyperparameters, training_metadata,
                              created_by, approved_by, approved_at, created_at, updated_at
                    """,
                    (
                        target_stage.value,
                        approved_by,
                        datetime.now(timezone.utc),
                        datetime.now(timezone.utc),
                        model_name,
                        version,
                    ),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Model {model_name} version {version} not found")

                return self._row_to_entry(row)

    def _row_to_entry(self, row: tuple) -> ModelRegistryEntry:
        """Convert database row to ModelRegistryEntry."""
        return ModelRegistryEntry(
            id=row[0],
            model_name=row[1],
            version=row[2],
            stage=ModelStage(row[3]),
            description=row[4],
            model_path=row[5],
            training_data_hash=row[6],
            hyperparameters=dict(row[7]) if row[7] else None,
            training_metadata=dict(row[8]) if row[8] else None,
            created_by=row[9],
            approved_by=row[10],
            approved_at=row[11],
            created_at=row[12],
            updated_at=row[13],
        )

    @staticmethod
    def _calculate_file_hash(file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

