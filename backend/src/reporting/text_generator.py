"""Text generation service for creating explanatory text using OpenAI/ChatGPT."""

from __future__ import annotations

from typing import Any, Dict, Optional
from ..config.base_settings import settings
from ..logging_utils import get_logger

logger = get_logger(__name__)


class TextGenerator:
    """Service for generating explanatory text using OpenAI/ChatGPT."""

    def __init__(self) -> None:
        self._client = None
        self.api_key = settings.openai_api_key
        self.enabled = bool(self.api_key)

    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is not None:
            return self._client

        if not self.api_key:
            logger.warning("OpenAI API key not set. Text generation will be disabled.")
            return None

        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized for text generation")
            return self._client
        except ImportError:
            logger.warning("OpenAI not installed. Install with: pip install openai")
            return None

    def generate_explanation(
        self,
        metric_name: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
        metric_type: str = "general",
    ) -> str:
        """
        Generate explanatory text for a metric/value.

        Args:
            metric_name: Name of the metric (e.g., "biodiversity_score", "cim_score")
            value: The metric value
            context: Additional context (e.g., project type, country, other metrics)
            metric_type: Type of metric ("biodiversity", "emissions", "ai_model", "kpi", etc.)

        Returns:
            Explanatory text string
        """
        if not self.enabled:
            return self._fallback_explanation(metric_name, value, metric_type)

        client = self._get_client()
        if not client:
            return self._fallback_explanation(metric_name, value, metric_type)

        try:
            prompt = self._build_prompt(metric_name, value, context, metric_type)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use cost-effective model
                messages=[
                    {
                        "role": "system",
                        "content": "You are an environmental impact assessment expert. Provide clear, concise explanations of environmental metrics for non-technical stakeholders. Use plain language and include context about what the metric means and why it matters."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=300,
                temperature=0.7,
            )

            explanation = response.choices[0].message.content.strip()
            logger.debug("Generated explanation for %s: %s", metric_name, explanation[:100])
            return explanation

        except Exception as e:
            logger.warning("Failed to generate text with OpenAI: %s. Using fallback.", e)
            return self._fallback_explanation(metric_name, value, metric_type)

    def _build_prompt(
        self,
        metric_name: str,
        value: Any,
        context: Optional[Dict[str, Any]],
        metric_type: str,
    ) -> str:
        """Build prompt for text generation."""
        prompt = f"Explain the following {metric_type} metric in plain language:\n\n"
        prompt += f"Metric: {metric_name}\n"
        prompt += f"Value: {value}\n\n"

        if context:
            prompt += "Context:\n"
            if context.get("project_type"):
                prompt += f"- Project type: {context['project_type']}\n"
            if context.get("country"):
                prompt += f"- Country: {context['country']}\n"
            if context.get("aoi_area"):
                prompt += f"- Area of Interest: {context['aoi_area']} km²\n"

        prompt += "\nProvide a brief explanation (2-3 sentences) that:\n"
        prompt += "1. Describes what this metric measures\n"
        prompt += "2. Explains what the value means in practical terms\n"
        prompt += "3. Mentions any implications or significance"

        return prompt

    def _fallback_explanation(self, metric_name: str, value: Any, metric_type: str) -> str:
        """Generate fallback explanation when AI is not available."""
        explanations = {
            "biodiversity_score": f"The biodiversity sensitivity score is {value:.2f} (scale 0-100). Higher values indicate greater biodiversity sensitivity and potential impact on protected species and habitats.",
            "cim_score": f"The cumulative impact score is {value:.2f} (scale 0-100). This integrates multiple environmental factors including biodiversity, suitability, and hazard risks to provide an overall impact assessment.",
            "resm_score": f"The renewable/resilience suitability score is {value:.2f} (scale 0-100). Higher scores indicate better suitability for the proposed renewable energy project based on environmental and technical factors.",
            "ahsm_score": f"The asset hazard susceptibility score is {value:.2f} (scale 0-100). This indicates the level of risk from natural hazards such as floods, wildfires, and extreme weather events.",
        }

        if metric_name in explanations:
            return explanations[metric_name]

        # Generic fallback
        return f"The {metric_name} has a value of {value}. This metric reflects various environmental factors relevant to the project assessment."

    def generate_section_summary(
        self,
        section_name: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a summary paragraph for a report section.

        Args:
            section_name: Name of the section (e.g., "biodiversity", "emissions")
            data: Section data dictionary
            context: Additional context

        Returns:
            Summary text
        """
        if not self.enabled:
            return self._fallback_section_summary(section_name, data)

        client = self._get_client()
        if not client:
            return self._fallback_section_summary(section_name, data)

        try:
            prompt = f"Generate a 3-4 sentence summary for the '{section_name}' section of an environmental impact assessment report.\n\n"
            prompt += f"Data: {str(data)[:500]}\n\n"
            prompt += "Write a professional, clear summary that highlights key findings and their significance."

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an environmental consultant writing report summaries. Be concise, professional, and highlight key insights."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.warning("Failed to generate section summary: %s. Using fallback.", e)
            return self._fallback_section_summary(section_name, data)

    def _fallback_section_summary(self, section_name: str, data: Dict[str, Any]) -> str:
        """Generate fallback section summary."""
        if section_name == "biodiversity":
            score = data.get("score", data.get("biodiversity_score", "N/A"))
            return f"This section presents the biodiversity assessment for the project area. The analysis evaluates species sensitivity, protected area overlap, and habitat quality. The biodiversity sensitivity score of {score} indicates the level of potential impact on local ecosystems and protected species."

        elif section_name == "emissions":
            baseline = data.get("baseline_tco2e", "N/A")
            project = data.get("project_construction_tco2e", "N/A")
            return f"Emissions analysis compares baseline carbon emissions ({baseline} tCO₂e) with projected project emissions ({project} tCO₂e). This assessment helps quantify the carbon footprint and climate impact of the proposed development."

        elif section_name == "ai_models":
            return "This section presents AI/ML model predictions for project suitability, hazard risks, and cumulative environmental impact. These models integrate multiple data sources to provide comprehensive risk assessment and impact evaluation."

        return f"The {section_name} section contains detailed analysis and findings relevant to the environmental impact assessment."

