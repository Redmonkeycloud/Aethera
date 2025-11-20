"""Unit tests for report memory store."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.reporting.embeddings import EmbeddingService
from src.reporting.report_memory import ReportEntry, ReportMemoryStore


@pytest.mark.unit
class TestReportMemoryStore:
    """Test in-memory report store."""

    def test_store_initialization(self) -> None:
        """Test store initialization."""
        store = ReportMemoryStore()
        assert store is not None

    def test_add_entry(self) -> None:
        """Test adding entries to store."""
        store = ReportMemoryStore()
        entry = ReportEntry(
            report_id="test-1",
            project_id="proj-1",
            run_id="run-1",
            version=1,
            status="draft",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            summary="Test summary",
        )
        store.add_entry(entry)
        entries = store.list_entries()
        assert len(entries) == 1
        assert entries[0].report_id == "test-1"


@pytest.mark.unit
class TestEmbeddingService:
    """Test embedding generation service."""

    def test_service_initialization(self) -> None:
        """Test embedding service initialization."""
        service = EmbeddingService()
        assert service is not None

    def test_generate_embedding(self) -> None:
        """Test embedding generation."""
        service = EmbeddingService()
        # Use sentence-transformers by default
        embedding = service.generate_embedding("test text")
        assert len(embedding) > 0
        assert isinstance(embedding, list)
        assert all(isinstance(x, (int, float)) for x in embedding)

    def test_batch_embeddings(self) -> None:
        """Test batch embedding generation."""
        service = EmbeddingService()
        texts = ["text 1", "text 2", "text 3"]
        embeddings = service.generate_embeddings_batch(texts)
        assert len(embeddings) == len(texts)
        assert all(len(emb) > 0 for emb in embeddings)

