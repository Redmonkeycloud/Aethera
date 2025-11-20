"""Report learning memory scaffolding.

This module wires up the infrastructure needed to ingest past reports once they
become available. It does not require existing data; it simply prepares the
schema and interfaces so future ingestion is straightforward.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ReportEntry:
    report_id: str
    project_id: str | None
    run_id: str | None
    version: int
    status: str
    created_at: datetime
    updated_at: datetime
    summary: str | None = None
    file_path: Path | None = None


class ReportMemoryStore:
    """
    In-memory placeholder for report memory store.
    
    .. deprecated:: 0.1.0
        This class is deprecated. Use :class:`DatabaseReportMemoryStore` instead
        for production use. This class is kept for backward compatibility and testing.
    """

    def __init__(self) -> None:
        self._entries: list[ReportEntry] = []

    def add_entry(self, entry: ReportEntry) -> None:
        """Register a new report version (placeholder - use DatabaseReportMemoryStore for production)."""
        self._entries.append(entry)

    def list_entries(self) -> list[ReportEntry]:
        """Return known reports (in-memory only - use DatabaseReportMemoryStore for persistence)."""
        return list(self._entries)

    def find_similar(self, summary: str) -> list[ReportEntry]:
        """
        Stub for similarity search.
        
        .. deprecated:: 0.1.0
            Use :class:`DatabaseReportMemoryStore.find_similar()` for actual semantic search.
        """
        return []


SQL_SCHEMA = """
-- Projects table (simplified)
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT,
    sector TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Report history stores raw files plus metadata
CREATE TABLE IF NOT EXISTS reports_history (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    run_id UUID,
    version INTEGER NOT NULL,
    status TEXT NOT NULL, -- draft, reviewed, approved, rejected
    summary TEXT,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Embeddings table for retrieval-augmented generation
CREATE TABLE IF NOT EXISTS report_embeddings (
    report_id UUID REFERENCES reports_history(id),
    section TEXT,
    embedding VECTOR(1536), -- pgvector extension
    metadata JSONB,
    PRIMARY KEY (report_id, section)
);
"""

