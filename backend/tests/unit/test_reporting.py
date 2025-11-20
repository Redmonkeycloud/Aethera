"""Unit tests for reporting components."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from src.reporting.engine import ReportEngine
from src.reporting.exports import ReportExporter
from src.reporting.report_memory import ReportMemoryStore


@pytest.mark.unit
class TestReportEngine:
    """Test report generation engine."""

    def test_engine_initialization(self, temp_dir: Path) -> None:
        """Test report engine initialization."""
        templates_dir = temp_dir / "templates"
        templates_dir.mkdir()
        engine = ReportEngine(templates_dir=templates_dir)
        assert engine is not None

    def test_template_rendering(self, temp_dir: Path) -> None:
        """Test template rendering."""
        templates_dir = temp_dir / "templates"
        templates_dir.mkdir()
        
        # Create a simple template
        template_file = templates_dir / "test.md.jinja"
        template_file.write_text("Hello {{ name }}!")
        
        engine = ReportEngine(templates_dir=templates_dir)
        result = engine.render("test.md.jinja", {"name": "World"})
        assert "Hello World!" in result

    def test_rag_disabled(self, temp_dir: Path) -> None:
        """Test RAG can be disabled."""
        templates_dir = temp_dir / "templates"
        templates_dir.mkdir()
        
        template_file = templates_dir / "test.md.jinja"
        template_file.write_text("Test content")
        
        engine = ReportEngine(templates_dir=templates_dir, use_rag=False)
        result = engine.render("test.md.jinja", {}, enable_rag=False)
        assert "Test content" in result


@pytest.mark.unit
class TestReportExporter:
    """Test report export functionality."""

    def test_csv_export(self, temp_dir: Path) -> None:
        """Test CSV export."""
        data = [
            {"name": "Test", "value": 123},
            {"name": "Another", "value": 456},
        ]
        output_path = temp_dir / "test.csv"
        ReportExporter.to_csv(data, output_path)
        assert output_path.exists()
        content = output_path.read_text()
        assert "Test" in content
        assert "123" in content

    @pytest.mark.hypothesis
    @given(
        num_rows=st.integers(min_value=1, max_value=100),
        num_cols=st.integers(min_value=1, max_value=20),
    )
    def test_csv_export_property_based(self, num_rows: int, num_cols: int, temp_dir: Path) -> None:
        """Property-based test for CSV export."""
        data = [
            {f"col_{i}": f"value_{i}_{j}" for i in range(num_cols)}
            for j in range(num_rows)
        ]
        output_path = temp_dir / "test_prop.csv"
        ReportExporter.to_csv(data, output_path)
        assert output_path.exists()
        lines = output_path.read_text().splitlines()
        assert len(lines) == num_rows + 1  # +1 for header

