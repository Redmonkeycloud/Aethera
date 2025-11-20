"""Database-backed report memory store with pgvector support."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import psycopg
from psycopg.types.json import Jsonb

from ..db.client import DatabaseClient
from ..config.base_settings import settings
from ..logging_utils import get_logger
from .embeddings import EmbeddingService
from .report_memory import ReportEntry

logger = get_logger(__name__)


@dataclass
class ReportSection:
    """A section of a report with its embedding."""

    report_id: str
    section: str
    content: str
    embedding: List[float]
    metadata: dict


class DatabaseReportMemoryStore:
    """Database-backed report memory store with semantic search."""

    def __init__(self, db_client: DatabaseClient | None = None, embedding_service: EmbeddingService | None = None) -> None:
        self.db_client = db_client or DatabaseClient(settings.postgres_dsn)
        self.embedding_service = embedding_service or EmbeddingService()
        self.embedding_dim = self.embedding_service.get_embedding_dimension()

    def add_entry(
        self,
        entry: ReportEntry,
        content: str,
        sections: dict[str, str] | None = None,
    ) -> str:
        """
        Register a new report version in the database.

        Args:
            entry: Report entry metadata
            content: Full report content
            sections: Optional dict mapping section names to section content

        Returns:
            The report ID (UUID as string)
        """
        report_id = str(uuid.uuid4())

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Insert into reports_history
                cur.execute(
                    """
                    INSERT INTO reports_history (
                        id, project_id, run_id, version, status, summary, storage_path, metadata, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        report_id,
                        entry.project_id,
                        entry.run_id,
                        entry.version,
                        entry.status,
                        entry.summary,
                        str(entry.file_path) if entry.file_path else "",
                        Jsonb({}),
                        entry.created_at,
                        entry.updated_at,
                    ),
                )

                # Generate embeddings for sections
                if sections:
                    section_embeddings = []
                    for section_name, section_content in sections.items():
                        embedding = self.embedding_service.generate_embedding(section_content)
                        section_embeddings.append((report_id, section_name, embedding, {"content_length": len(section_content)}))

                    # Insert embeddings
                    if section_embeddings:
                        # Convert embeddings to PostgreSQL vector format
                        for report_id_val, section, embedding, metadata in section_embeddings:
                            # Format as PostgreSQL vector: [0.1,0.2,0.3]
                            vector_str = "[" + ",".join(str(x) for x in embedding) + "]"
                            cur.execute(
                                """
                                INSERT INTO report_embeddings (report_id, section, embedding, metadata)
                                VALUES (%s, %s, %s::vector, %s)
                                """,
                                (report_id_val, section, vector_str, Jsonb(metadata)),
                            )

                # Also generate embedding for summary if available
                if entry.summary:
                    summary_embedding = self.embedding_service.generate_embedding(entry.summary)
                    vector_str = "[" + ",".join(str(x) for x in summary_embedding) + "]"
                    cur.execute(
                        """
                        INSERT INTO report_embeddings (report_id, section, embedding, metadata)
                        VALUES (%s, %s, %s::vector, %s)
                        ON CONFLICT (report_id, section) DO UPDATE
                        SET embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata
                        """,
                        (report_id, "summary", vector_str, Jsonb({"type": "summary"})),
                    )

        logger.info("Added report entry: %s (version %d)", report_id, entry.version)
        return report_id

    def list_entries(
        self,
        project_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> List[ReportEntry]:
        """Return known reports from database."""
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                query = "SELECT id, project_id, run_id, version, status, summary, storage_path, created_at, updated_at FROM reports_history WHERE 1=1"
                params: list = []

                if project_id:
                    query += " AND project_id = %s"
                    params.append(project_id)
                if status:
                    query += " AND status = %s"
                    params.append(status)

                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)

                cur.execute(query, params)
                rows = cur.fetchall()

                entries = []
                for row in rows:
                    entries.append(
                        ReportEntry(
                            report_id=row[0],
                            project_id=row[1],
                            run_id=row[2],
                            version=row[3],
                            status=row[4],
                            summary=row[5],
                            file_path=Path(row[6]) if row[6] else None,
                            created_at=row[7],
                            updated_at=row[8],
                        )
                    )

        return entries

    def find_similar(
        self,
        query_text: str,
        limit: int = 5,
        min_similarity: float = 0.7,
        section_filter: str | None = None,
    ) -> List[tuple[ReportEntry, str, float]]:
        """
        Find similar report sections using semantic search.

        Args:
            query_text: Text to search for
            limit: Maximum number of results
            min_similarity: Minimum cosine similarity threshold
            section_filter: Optional section name filter

        Returns:
            List of tuples: (ReportEntry, section_name, similarity_score)
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query_text)
        query_vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Use pgvector cosine similarity (<=> operator)
                query = """
                    SELECT
                        rh.id, rh.project_id, rh.run_id, rh.version, rh.status,
                        rh.summary, rh.storage_path, rh.created_at, rh.updated_at,
                        re.section,
                        1 - (re.embedding <=> %s::vector) as similarity
                    FROM report_embeddings re
                    JOIN reports_history rh ON re.report_id = rh.id
                    WHERE 1 - (re.embedding <=> %s::vector) >= %s
                """
                params: list = [query_vector_str, query_vector_str, min_similarity]

                if section_filter:
                    query += " AND re.section = %s"
                    params.append(section_filter)

                query += " ORDER BY similarity DESC LIMIT %s"
                params.append(limit)

                cur.execute(query, params)
                rows = cur.fetchall()

                results = []
                for row in rows:
                    entry = ReportEntry(
                        report_id=row[0],
                        project_id=row[1],
                        run_id=row[2],
                        version=row[3],
                        status=row[4],
                        summary=row[5],
                        file_path=Path(row[6]) if row[6] else None,
                        created_at=row[7],
                        updated_at=row[8],
                    )
                    section = row[9]
                    similarity = float(row[10])
                    results.append((entry, section, similarity))

        return results

    def get_report_content(self, report_id: str) -> str | None:
        """Retrieve the full content of a report from storage."""
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT storage_path FROM reports_history WHERE id = %s", (report_id,))
                row = cur.fetchone()
                if row and row[0]:
                    storage_path = Path(row[0])
                    if storage_path.exists():
                        return storage_path.read_text(encoding="utf-8")
        return None

    def update_status(self, report_id: str, status: str) -> None:
        """Update the status of a report."""
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE reports_history SET status = %s, updated_at = NOW() WHERE id = %s",
                    (status, report_id),
                )
        logger.info("Updated report %s status to %s", report_id, status)

    def add_feedback(
        self,
        report_id: str,
        feedback_text: str,
        reviewer: str | None = None,
        rating: int | None = None,
    ) -> None:
        """Add reviewer feedback to a report (stored in metadata)."""
        with self.db_client.connection() as conn:
            with conn.cursor() as cur:
                # Get existing metadata or create new
                cur.execute("SELECT metadata FROM reports_history WHERE id = %s", (report_id,))
                row = cur.fetchone()
                if row and row[0]:
                    metadata = row[0] if isinstance(row[0], dict) else json.loads(row[0])
                else:
                    metadata = {}

                # Add feedback
                if "feedback" not in metadata:
                    metadata["feedback"] = []
                metadata["feedback"].append(
                    {
                        "text": feedback_text,
                        "reviewer": reviewer,
                        "rating": rating,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                cur.execute(
                    "UPDATE reports_history SET metadata = %s, updated_at = NOW() WHERE id = %s",
                    (Jsonb(metadata), report_id),
                )
        logger.info("Added feedback to report %s", report_id)

