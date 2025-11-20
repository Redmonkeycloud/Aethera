"""Report generation engine with RAG support."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .report_memory import ReportMemoryStore
from .report_memory_db import DatabaseReportMemoryStore
from ..logging_utils import get_logger

logger = get_logger(__name__)


class ReportEngine:
    """Report generation engine with retrieval-augmented generation (RAG)."""

    def __init__(
        self,
        templates_dir: Path,
        memory_store: ReportMemoryStore | DatabaseReportMemoryStore | None = None,
        use_rag: bool = True,
    ) -> None:
        self.templates_dir = templates_dir
        self.memory_store = memory_store
        self.use_rag = use_rag
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(enabled_extensions=("md", "jinja")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _augment_context_with_rag(self, context: Dict[str, Any], section: str | None = None) -> Dict[str, Any]:
        """Retrieve similar report sections and augment context."""
        if not self.use_rag or not self.memory_store:
            return context

        if not isinstance(self.memory_store, DatabaseReportMemoryStore):
            logger.debug("Memory store does not support RAG, skipping augmentation")
            return context

        # Extract query text from context
        query_text = ""
        if section:
            # Query for specific section
            query_text = context.get(section, "")
        else:
            # Use project summary or description
            project = context.get("project", {})
            query_text = project.get("description", "") or project.get("name", "")

        if not query_text:
            logger.debug("No query text available for RAG")
            return context

        # Find similar sections
        try:
            similar = self.memory_store.find_similar(query_text, limit=3, min_similarity=0.7, section_filter=section)
            if similar:
                context["_rag_context"] = {
                    "similar_sections": [
                        {
                            "report_id": entry.report_id,
                            "section": section_name,
                            "similarity": sim_score,
                            "summary": entry.summary,
                        }
                        for entry, section_name, sim_score in similar
                    ]
                }
                logger.info("Retrieved %d similar sections for RAG", len(similar))
            else:
                context["_rag_context"] = {"similar_sections": []}
        except Exception as e:
            logger.warning("Failed to retrieve similar sections: %s", e)
            context["_rag_context"] = {"similar_sections": []}

        return context

    def render(
        self,
        template_name: str,
        context: Dict[str, Any],
        section: str | None = None,
        enable_rag: bool | None = None,
    ) -> str:
        """
        Render a report template with optional RAG augmentation.

        Args:
            template_name: Name of the template file
            context: Template context variables
            section: Optional section name for targeted RAG retrieval
            enable_rag: Override instance-level use_rag setting

        Returns:
            Rendered report as string
        """
        template = self.env.get_template(template_name)

        # Augment context with RAG if enabled
        use_rag = enable_rag if enable_rag is not None else self.use_rag
        if use_rag:
            context = self._augment_context_with_rag(context, section)

        logger.debug("Rendering report using template %s (RAG: %s)", template_name, use_rag)
        return template.render(**context)

    def generate_report(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: Path | None = None,
    ) -> str:
        """
        Generate a complete report and optionally save it.

        Args:
            template_name: Name of the template file
            context: Template context variables
            output_path: Optional path to save the report

        Returns:
            Generated report content as string
        """
        content = self.render(template_name, context)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            logger.info("Report saved to %s", output_path)

        return content
