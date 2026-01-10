"""LangChain-based LLM service for report generation using Groq."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from ..config.base_settings import settings
from ..logging_utils import get_logger

logger = get_logger(__name__)


class LangChainLLMService:
    """Service for using LangChain with Groq for LLM-based report generation."""

    def __init__(self) -> None:
        """Initialize the LLM service with Groq or fallback providers."""
        self.provider = settings.llm_provider
        self.llm = None
        self.enabled = settings.use_llm
        
        if not self.enabled:
            logger.info("LLM generation is disabled via settings")
            return
        
        try:
            if self.provider == "groq":
                from langchain_groq import ChatGroq
                
                api_key = settings.groq_api_key
                if not api_key:
                    logger.warning("GROQ_API_KEY not set. LLM generation will be disabled.")
                    self.enabled = False
                    return
                
                model_name = settings.groq_model
                temperature = settings.llm_temperature
                
                self.llm = ChatGroq(
                    groq_api_key=api_key,
                    model_name=model_name,
                    temperature=temperature,
                )
                logger.info(f"Initialized Groq LLM with model: {model_name}")
                
            elif self.provider == "openai":
                from langchain_openai import ChatOpenAI
                
                api_key = settings.openai_api_key
                if not api_key:
                    logger.warning("OPENAI_API_KEY not set. LLM generation will be disabled.")
                    self.enabled = False
                    return
                
                self.llm = ChatOpenAI(
                    api_key=api_key,
                    model_name="gpt-4o-mini",
                    temperature=settings.llm_temperature,
                )
                logger.info("Initialized OpenAI LLM")
                
            elif self.provider == "ollama":
                from langchain_community.llms import Ollama
                
                self.llm = Ollama(model="mistral", temperature=settings.llm_temperature)
                logger.info("Initialized Ollama LLM")
                
            else:
                logger.warning(f"Unknown LLM provider: {self.provider}. LLM generation will be disabled.")
                self.enabled = False
                
        except ImportError as e:
            logger.warning(f"Failed to import LLM library: {e}. LLM generation will be disabled.")
            self.enabled = False

    def generate_executive_summary(
        self,
        analysis_results: Dict[str, Any],
        project_context: Dict[str, Any],
        similar_reports: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate executive summary from analysis results.
        
        Args:
            analysis_results: Dictionary containing all analysis results
            project_context: Project metadata (name, type, country, etc.)
            similar_reports: Optional list of similar historical reports
            
        Returns:
            Generated executive summary text
        """
        if not self.enabled or not self.llm:
            return self._fallback_executive_summary(analysis_results, project_context)
        
        try:
            # Build prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert Environmental Impact Assessment (EIA) consultant. 
Your task is to write professional, clear executive summaries for EIA reports that:
- Highlight key findings and risks
- Use plain language accessible to non-technical stakeholders
- Be factual and based on the analysis results provided
- Follow standard EIA report structure
- Be concise (approximately 200-300 words)"""),
                ("human", """Generate an executive summary for an EIA report based on the following analysis results:

**Project Information:**
- Project Name: {project_name}
- Project Type: {project_type}
- Country: {country}
- Capacity: {capacity_mw} MW
- AOI Area: {aoi_area} km²

**Analysis Results:**
- Biodiversity Sensitivity Score: {biodiversity_score}/100
  {biodiversity_details}
  
- RESM Suitability Score: {resm_score}/100
  {resm_details}
  
- AHSM Hazard Susceptibility Score: {ahsm_score}/100
  {ahsm_details}
  
- CIM Cumulative Impact Score: {cim_score}/100
  {cim_details}

**Emissions:**
- Baseline: {baseline_emissions} tCO₂e
- Project Construction: {construction_emissions} tCO₂e
- Project Operation (annual): {operation_emissions} tCO₂e/year
- Net Difference: {net_emissions} tCO₂e

**Legal Compliance:**
{legal_summary}

{following_similar_reports}

Generate a professional executive summary (200-300 words) that:
1. Provides an overview of the project
2. Summarizes key environmental findings
3. Highlights critical risks and opportunities
4. Provides recommendations for decision-makers""")
            ])
            
            # Prepare context
            biodiversity = analysis_results.get("biodiversity", {})
            resm = analysis_results.get("resm", {})
            ahsm = analysis_results.get("ahsm", {})
            cim = analysis_results.get("cim", {})
            emissions = analysis_results.get("emissions", {})
            
            biodiversity_score = biodiversity.get("score", 0) if isinstance(biodiversity, dict) else 0
            resm_score = resm.get("score", 0) if isinstance(resm, dict) else 0
            ahsm_score = ahsm.get("score", 0) if isinstance(ahsm, dict) else 0
            cim_score = cim.get("score", 0) if isinstance(cim, dict) else 0
            
            similar_text = ""
            if similar_reports:
                similar_text = "\n**Similar Historical Reports:**\n"
                for i, report in enumerate(similar_reports[:3], 1):
                    similar_text += f"{i}. {report.get('summary', 'N/A')[:200]}...\n"
            
            # Execute chain
            chain = prompt | self.llm
            response = chain.invoke({
                "project_name": project_context.get("name", "Unknown Project"),
                "project_type": project_context.get("type", "Unknown"),
                "country": project_context.get("country", "Unknown"),
                "capacity_mw": project_context.get("capacity_mw", 0),
                "aoi_area": analysis_results.get("indicators", {}).get("aoi_area_km2", 0),
                "biodiversity_score": biodiversity_score,
                "biodiversity_details": biodiversity.get("explanation", biodiversity.get("category", "")) if isinstance(biodiversity, dict) else "",
                "resm_score": resm_score,
                "resm_details": resm.get("explanation", resm.get("category", "")) if isinstance(resm, dict) else "",
                "ahsm_score": ahsm_score,
                "ahsm_details": ahsm.get("explanation", ahsm.get("category", "")) if isinstance(ahsm, dict) else "",
                "cim_score": cim_score,
                "cim_details": cim.get("explanation", cim.get("category", "")) if isinstance(cim, dict) else "",
                "baseline_emissions": emissions.get("baseline_tco2e", 0),
                "construction_emissions": emissions.get("project_construction_tco2e", 0),
                "operation_emissions": emissions.get("project_operation_tco2e_per_year", 0),
                "net_emissions": emissions.get("net_difference_tco2e", 0),
                "legal_summary": analysis_results.get("legal_summary", "No legal assessment available."),
                "following_similar_reports": similar_text,
            })
            
            summary = response.content if hasattr(response, 'content') else str(response)
            logger.info("Generated executive summary using LLM")
            return summary
            
        except Exception as e:
            logger.warning(f"Failed to generate executive summary with LLM: {e}. Using fallback.")
            return self._fallback_executive_summary(analysis_results, project_context)

    def generate_biodiversity_narrative(
        self,
        biodiversity_data: Dict[str, Any],
        project_context: Dict[str, Any],
    ) -> str:
        """
        Write biodiversity assessment narrative.
        
        Args:
            biodiversity_data: Biodiversity analysis results
            project_context: Project metadata
            
        Returns:
            Generated biodiversity narrative text
        """
        if not self.enabled or not self.llm:
            return self._fallback_biodiversity_narrative(biodiversity_data)
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a biodiversity expert writing EIA report sections. 
Write clear, professional narratives that explain biodiversity assessments in plain language
while maintaining scientific accuracy."""),
                ("human", """Write a biodiversity assessment narrative based on the following analysis:

**Project:** {project_name} ({project_type})
**Location:** {country}
**Analysis Area:** {aoi_area} km²

**Biodiversity Assessment Results:**
- Sensitivity Score: {score}/100
- Category: {category}
- Protected Area Overlap: {overlap_pct}%
- Protected Sites Count: {site_count}
- Fragmentation Index: {fragmentation_index}
- Forest Ratio: {forest_ratio}%

**Additional Context:**
{details}

Write a 3-4 paragraph biodiversity assessment narrative that:
1. Describes the biodiversity characteristics of the site
2. Explains the significance of the sensitivity score and key indicators
3. Discusses potential impacts on protected species and habitats
4. Highlights conservation considerations and recommendations""")
            ])
            
            score = biodiversity_data.get("score", 0)
            category = biodiversity_data.get("category", "unknown")
            overlap_pct = biodiversity_data.get("protected_overlap_pct", 0)
            site_count = biodiversity_data.get("protected_site_count", 0)
            fragmentation_index = biodiversity_data.get("fragmentation_index", 0)
            forest_ratio = biodiversity_data.get("forest_ratio", 0) * 100 if biodiversity_data.get("forest_ratio") else 0
            
            chain = prompt | self.llm
            response = chain.invoke({
                "project_name": project_context.get("name", "Unknown Project"),
                "project_type": project_context.get("type", "Unknown"),
                "country": project_context.get("country", "Unknown"),
                "aoi_area": project_context.get("aoi_area_km2", 0),
                "score": score,
                "category": category,
                "overlap_pct": overlap_pct,
                "site_count": site_count,
                "fragmentation_index": fragmentation_index,
                "forest_ratio": forest_ratio,
                "details": biodiversity_data.get("explanation", ""),
            })
            
            narrative = response.content if hasattr(response, 'content') else str(response)
            logger.info("Generated biodiversity narrative using LLM")
            return narrative
            
        except Exception as e:
            logger.warning(f"Failed to generate biodiversity narrative with LLM: {e}. Using fallback.")
            return self._fallback_biodiversity_narrative(biodiversity_data)

    def explain_ml_prediction(
        self,
        model_name: str,
        prediction: Dict[str, Any],
        feature_importance: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        Explain ML model predictions in plain language.
        
        Args:
            model_name: Name of the ML model (e.g., "RESM", "AHSM", "CIM", "Biodiversity")
            prediction: Model prediction results
            feature_importance: Optional feature importance scores
            
        Returns:
            Plain language explanation of the prediction
        """
        if not self.enabled or not self.llm:
            return self._fallback_ml_explanation(model_name, prediction)
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an AI/ML expert who explains model predictions to non-technical stakeholders.
Translate technical ML outputs into clear, actionable insights."""),
                ("human", """Explain the following {model_name} model prediction in plain language:

**Model:** {model_name}
**Prediction Score:** {score}/100
**Category:** {category}

**Key Features:**
{features}

{feature_importance_text}

**Prediction Details:**
{details}

Write a 2-3 paragraph explanation that:
1. Explains what the model predicted and what it means
2. Describes which factors most influenced the prediction
3. Provides actionable insights for stakeholders
4. Uses plain language, avoiding technical jargon""")
            ])
            
            score = prediction.get("score", 0)
            category = prediction.get("category", "unknown")
            details = prediction.get("explanation", "")
            
            # Format features
            features_text = ""
            if isinstance(prediction, dict):
                for key, value in prediction.items():
                    if key not in ["score", "category", "explanation"] and isinstance(value, (int, float, str)):
                        features_text += f"- {key}: {value}\n"
            
            # Format feature importance
            feature_importance_text = ""
            if feature_importance:
                feature_importance_text = "\n**Most Important Factors:**\n"
                sorted_features = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)
                for feature, importance in sorted_features[:5]:
                    feature_importance_text += f"- {feature}: {importance:.3f}\n"
            
            chain = prompt | self.llm
            response = chain.invoke({
                "model_name": model_name,
                "score": score,
                "category": category,
                "features": features_text or "N/A",
                "feature_importance_text": feature_importance_text,
                "details": details,
            })
            
            explanation = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"Generated ML explanation for {model_name} using LLM")
            return explanation
            
        except Exception as e:
            logger.warning(f"Failed to generate ML explanation with LLM: {e}. Using fallback.")
            return self._fallback_ml_explanation(model_name, prediction)

    def generate_legal_recommendations(
        self,
        legal_findings: Dict[str, Any],
        compliance_status: Dict[str, Any],
        project_context: Dict[str, Any],
    ) -> str:
        """
        Generate recommendations based on legal compliance findings.
        
        Args:
            legal_findings: Legal evaluation results
            compliance_status: Compliance status for each rule
            project_context: Project metadata
            
        Returns:
            Generated recommendations text
        """
        if not self.enabled or not self.llm:
            return self._fallback_legal_recommendations(legal_findings, compliance_status)
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a legal compliance expert specializing in environmental regulations.
Provide clear, actionable recommendations based on legal compliance assessments."""),
                ("human", """Generate legal compliance recommendations based on the following assessment:

**Project:** {project_name} ({project_type})
**Country:** {country}
**Jurisdiction:** {jurisdiction}

**Legal Compliance Summary:**
{legal_summary}

**Compliance Status:**
{compliance_details}

**Violations/Issues:**
{violations}

**Critical Findings:**
{critical_findings}

Write a 3-4 paragraph recommendations section that:
1. Summarizes the overall compliance status
2. Identifies critical issues that require immediate attention
3. Provides specific, actionable recommendations for compliance
4. Suggests mitigation measures and next steps
5. Highlights any required permits or consultations""")
            ])
            
            # Format compliance details
            compliance_text = ""
            violations_text = ""
            critical_text = ""
            
            if isinstance(compliance_status, dict):
                for rule_name, status in compliance_status.items():
                    if isinstance(status, dict):
                        is_compliant = status.get("compliant", True)
                        explanation = status.get("explanation", "")
                        
                        if is_compliant:
                            compliance_text += f"✅ {rule_name}: Compliant - {explanation}\n"
                        else:
                            violations_text += f"❌ {rule_name}: Non-compliant - {explanation}\n"
                            if status.get("critical", False):
                                critical_text += f"- {rule_name}: {explanation}\n"
            
            if not violations_text:
                violations_text = "No violations identified."
            
            if not critical_text:
                critical_text = "No critical issues identified."
            
            chain = prompt | self.llm
            response = chain.invoke({
                "project_name": project_context.get("name", "Unknown Project"),
                "project_type": project_context.get("type", "Unknown"),
                "country": project_context.get("country", "Unknown"),
                "jurisdiction": project_context.get("country", "Unknown"),
                "legal_summary": str(legal_findings.get("summary", "No legal assessment available.")),
                "compliance_details": compliance_text or "No compliance details available.",
                "violations": violations_text,
                "critical_findings": critical_text,
            })
            
            recommendations = response.content if hasattr(response, 'content') else str(response)
            logger.info("Generated legal recommendations using LLM")
            return recommendations
            
        except Exception as e:
            logger.warning(f"Failed to generate legal recommendations with LLM: {e}. Using fallback.")
            return self._fallback_legal_recommendations(legal_findings, compliance_status)

    # Fallback methods
    def _fallback_executive_summary(
        self,
        analysis_results: Dict[str, Any],
        project_context: Dict[str, Any],
    ) -> str:
        """Fallback executive summary when LLM is unavailable."""
        project_name = project_context.get("name", "Unknown Project")
        project_type = project_context.get("type", "Unknown")
        
        biodiversity = analysis_results.get("biodiversity", {})
        biodiversity_score = biodiversity.get("score", 0) if isinstance(biodiversity, dict) else 0
        
        return f"""Executive Summary - {project_name}

This Environmental Impact Assessment evaluates the proposed {project_type} project located in {project_context.get('country', 'Unknown')}.

Key Findings:
- Biodiversity Sensitivity Score: {biodiversity_score}/100
- The assessment evaluates potential environmental impacts and compliance with applicable regulations.

Recommendations:
- Review detailed findings in subsequent sections
- Consult with environmental authorities as required
- Implement recommended mitigation measures
"""

    def _fallback_biodiversity_narrative(self, biodiversity_data: Dict[str, Any]) -> str:
        """Fallback biodiversity narrative when LLM is unavailable."""
        score = biodiversity_data.get("score", 0)
        category = biodiversity_data.get("category", "unknown")
        overlap_pct = biodiversity_data.get("protected_overlap_pct", 0)
        
        return f"""Biodiversity Assessment

The biodiversity sensitivity analysis for the project area indicates a {category} sensitivity level with a score of {score}/100. The assessment evaluated protected area overlap ({overlap_pct}%), habitat fragmentation, and forest coverage to determine the potential impact on local biodiversity.

The findings suggest {'significant' if score > 70 else 'moderate' if score > 40 else 'low'} biodiversity sensitivity, indicating the level of potential impact on protected species and habitats. Consideration should be given to site-specific conservation measures and potential mitigation strategies.
"""

    def _fallback_ml_explanation(self, model_name: str, prediction: Dict[str, Any]) -> str:
        """Fallback ML explanation when LLM is unavailable."""
        score = prediction.get("score", 0)
        category = prediction.get("category", "unknown")
        
        return f"""Model Explanation: {model_name}

The {model_name} model predicted a score of {score}/100, categorizing the assessment as {category}. This prediction is based on multiple environmental factors including land cover, protected area proximity, and habitat characteristics.

Higher scores indicate {'greater' if model_name in ['RESM', 'Biodiversity'] else 'higher'} {'suitability' if model_name == 'RESM' else 'sensitivity' if model_name == 'Biodiversity' else 'risk'} for the proposed project. The model integrates various geospatial and environmental datasets to provide a comprehensive assessment.
"""

    def _fallback_legal_recommendations(
        self,
        legal_findings: Dict[str, Any],
        compliance_status: Dict[str, Any],
    ) -> str:
        """Fallback legal recommendations when LLM is unavailable."""
        summary = legal_findings.get("summary", "No legal assessment available.")
        
        violations = []
        if isinstance(compliance_status, dict):
            for rule_name, status in compliance_status.items():
                if isinstance(status, dict) and not status.get("compliant", True):
                    violations.append(rule_name)
        
        recommendations_text = f"""Legal Compliance Recommendations

{summary}

"""
        
        if violations:
            recommendations_text += f"Critical Issues Identified:\n"
            for violation in violations:
                recommendations_text += f"- {violation}: Review compliance requirements\n"
            
            recommendations_text += "\nRecommendations:\n"
            recommendations_text += "- Address non-compliance issues before proceeding\n"
            recommendations_text += "- Consult with relevant authorities\n"
            recommendations_text += "- Obtain required permits and approvals\n"
        else:
            recommendations_text += "Compliance Status: No violations identified.\n\nRecommendations:\n"
            recommendations_text += "- Proceed with standard permit applications\n"
            recommendations_text += "- Maintain compliance monitoring throughout project lifecycle\n"
        
        return recommendations_text
