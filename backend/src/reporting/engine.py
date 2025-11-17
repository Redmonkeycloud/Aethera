"""Report generation engine scaffolding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..logging_utils import get_logger
from .report_memory import ReportMemoryStore


logger = get_logger(__name__)


class ReportEngine:
    def __init__(self, templates_dir: Path, memory_store: ReportMemoryStore | None = None) -> None:
        self.templates_dir = templates_dir
        self.memory_store = memory_store or ReportMemoryStore()
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(enabled_extensions=("md", "jinja")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        template = self.env.get_template(template_name)

        # Placeholder hook: future versions will retrieve similar report sections
        # and augment context.
        logger.debug("Rendering report using template %s", template_name)
        return template.render(**context)

