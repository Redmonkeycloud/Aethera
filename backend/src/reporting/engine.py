"""Report generation engine with RAG support."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .report_memory import ReportMemoryStore
from .report_memory_db import DatabaseReportMemoryStore
from .langchain_llm import LangChainLLMService
from ..logging_utils import get_logger

logger = get_logger(__name__)


class ReportEngine:
    """Report generation engine with retrieval-augmented generation (RAG)."""

    def __init__(
        self,
        templates_dir: Path,
        memory_store: ReportMemoryStore | DatabaseReportMemoryStore | None = None,
        use_rag: bool = True,
        use_llm: bool = True,
    ) -> None:
        self.templates_dir = templates_dir
        self.memory_store = memory_store
        self.use_rag = use_rag
        self.use_llm = use_llm
        self.llm_service = LangChainLLMService() if use_llm else None
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
        use_llm: bool | None = None,
    ) -> str:
        """
        Generate a complete report and optionally save it.

        Args:
            template_name: Name of the template file
            context: Template context variables
            output_path: Optional path to save the report
            use_llm: Override instance-level use_llm setting

        Returns:
            Generated report content as string
        """
        # Generate LLM-enhanced sections if enabled
        if (use_llm if use_llm is not None else self.use_llm) and self.llm_service:
            context = self._enhance_context_with_llm(context)

        content = self.render(template_name, context)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            logger.info("Report saved to %s", output_path)

        return content

    def _enhance_context_with_llm(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance context with LLM-generated content."""
        if not self.llm_service or not self.llm_service.enabled:
            return context

        try:
            project_context = context.get("project", {})
            analysis_results = {
                "biodiversity": context.get("biodiversity", {}),
                "resm": context.get("ai", {}).get("resm", {}),
                "ahsm": context.get("ai", {}).get("ahsm", {}),
                "cim": context.get("ai", {}).get("cim", {}),
                "emissions": context.get("emissions", {}),
                "legal_summary": context.get("legal_summary", ""),
                "indicators": context.get("indicators", {}),
            }

            # Get similar reports for RAG
            similar_reports = []
            if self.use_rag and self.memory_store and isinstance(self.memory_store, DatabaseReportMemoryStore):
                try:
                    query_text = project_context.get("description", "") or project_context.get("name", "")
                    if query_text:
                        similar = self.memory_store.find_similar(query_text, limit=3, min_similarity=0.7)
                        similar_reports = [
                            {"summary": entry.summary or "", "report_id": entry.report_id}
                            for entry, _, _ in similar
                        ]
                except Exception as e:
                    logger.debug("Failed to retrieve similar reports for LLM: %s", e)

            # Generate executive summary
            if not context.get("executive_summary") or context.get("executive_summary") == "Executive summary not available.":
                try:
                    context["executive_summary"] = self.llm_service.generate_executive_summary(
                        analysis_results=analysis_results,
                        project_context=project_context,
                        similar_reports=similar_reports,
                    )
                except Exception as e:
                    logger.warning("Failed to generate executive summary with LLM: %s", e)

            # Generate biodiversity narrative
            biodiversity = context.get("biodiversity", {})
            if biodiversity and isinstance(biodiversity, dict):
                try:
                    context["biodiversity_narrative"] = self.llm_service.generate_biodiversity_narrative(
                        biodiversity_data=biodiversity,
                        project_context=project_context,
                    )
                except Exception as e:
                    logger.warning("Failed to generate biodiversity narrative with LLM: %s", e)

            # Generate ML model explanations
            ai_models = context.get("ai", {})
            if not context.get("ai_explanations"):
                context["ai_explanations"] = {}

            for model_name in ["resm", "ahsm", "cim", "biodiversity"]:
                model_data = ai_models.get(model_name) or (biodiversity if model_name == "biodiversity" else {})
                if model_data and isinstance(model_data, dict):
                    try:
                        context["ai_explanations"][model_name.upper()] = self.llm_service.explain_ml_prediction(
                            model_name=model_name.upper(),
                            prediction=model_data,
                        )
                    except Exception as e:
                        logger.warning("Failed to generate %s explanation with LLM: %s", model_name, e)

            # Generate legal recommendations
            legal_summary = context.get("legal_summary", "")
            legal_compliance = context.get("legal_compliance", {})
            if legal_summary or legal_compliance:
                try:
                    context["legal_recommendations"] = self.llm_service.generate_legal_recommendations(
                        legal_findings={"summary": legal_summary},
                        compliance_status=legal_compliance,
                        project_context=project_context,
                    )
                except Exception as e:
                    logger.warning("Failed to generate legal recommendations with LLM: %s", e)

        except Exception as e:
            logger.warning("Error enhancing context with LLM: %s", e)

        return context
