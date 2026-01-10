# LangChain & Groq Integration Setup

This document explains how to set up and use LangChain with Groq for LLM-based report generation in AETHERA.

## Overview

AETHERA now includes LangChain integration with Groq for generating:
- **Executive summaries** from analysis results
- **Biodiversity assessment narratives**
- **ML model predictions explained in plain language**
- **Legal compliance recommendations**

## Prerequisites

1. **Groq API Key**: Sign up at [console.groq.com](https://console.groq.com) (free tier available)
2. **LangChain Dependencies**: Already included in `backend/pyproject.toml`

## Configuration

### Environment Variables

Add the following to your `.env` file or environment:

```bash
# LLM Configuration
LLM_PROVIDER=groq                    # Options: "groq", "openai", "ollama"
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant      # Default model
LLM_TEMPERATURE=0.3                  # Temperature for generation (0.0-1.0)
USE_LLM=true                         # Enable/disable LLM generation
```

### Configuration File

The LLM service reads configuration from `backend/src/config/base_settings.py`:

```python
llm_provider: str = "groq"           # Provider to use
groq_api_key: str | None             # API key from environment
groq_model: str = "llama-3.1-8b-instant"
llm_temperature: float = 0.3
use_llm: bool = True
```

## Installation

Install dependencies:

```bash
cd backend
pip install -e .
```

Or install LangChain packages directly:

```bash
pip install langchain langchain-core langchain-community langchain-groq
```

## Usage

### Automatic LLM Generation

LLM generation is automatically enabled when generating reports via the API:

```bash
POST /reports/generate
{
    "run_id": "run_20250105_123456",
    "template_name": "enhanced_report.md.jinja",
    "enable_rag": true,
    "format": "markdown"
}
```

The report engine will automatically:
1. Generate an executive summary
2. Create biodiversity narratives
3. Explain ML model predictions
4. Generate legal compliance recommendations

### On-Demand LLM Generation

Generate specific LLM content sections:

```bash
POST /reports/llm/generate?run_id=run_123&content_type=executive_summary
```

Available content types:
- `executive_summary` - Full executive summary from analysis results
- `biodiversity_narrative` - Biodiversity assessment narrative
- `ml_explanation` - ML model prediction explanation (requires `model_name` parameter)
- `legal_recommendations` - Legal compliance recommendations

Example for ML explanation:

```bash
POST /reports/llm/generate?run_id=run_123&content_type=ml_explanation&model_name=RESM
```

## LLM Providers

### Groq (Recommended - Free Tier)

- **Free Tier**: 30,000 requests/day
- **Speed**: Very fast (GPU-accelerated)
- **Models Available**: 
  - `llama-3.1-8b-instant` (default, recommended)
  - `llama-3.1-70b-versatile`
  - `mixtral-8x7b-32768`

**Setup:**
1. Sign up at [console.groq.com](https://console.groq.com)
2. Get your API key
3. Set `GROQ_API_KEY` environment variable

### OpenAI (Alternative)

If you prefer OpenAI:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
```

Uses `gpt-4o-mini` by default (cost-effective).

### Ollama (Local - No API Key)

For local development without API costs:

```bash
LLM_PROVIDER=ollama
# No API key needed
```

**Setup:**
1. Install [Ollama](https://ollama.ai)
2. Pull a model: `ollama pull mistral`
3. Set `LLM_PROVIDER=ollama`

## Code Examples

### Using LLM Service Directly

```python
from backend.src.reporting.langchain_llm import LangChainLLMService

# Initialize service
llm_service = LangChainLLMService()

# Generate executive summary
summary = llm_service.generate_executive_summary(
    analysis_results={
        "biodiversity": {"score": 57.5, "category": "moderate"},
        "resm": {"score": 75.2, "category": "high"},
        "emissions": {"baseline_tco2e": 1000, "net_difference_tco2e": 500},
    },
    project_context={
        "name": "Wind Farm Project",
        "type": "renewable_energy",
        "country": "ITA",
        "capacity_mw": 100,
    },
)

# Generate biodiversity narrative
narrative = llm_service.generate_biodiversity_narrative(
    biodiversity_data={"score": 57.5, "protected_overlap_pct": 25.0},
    project_context={"name": "Wind Farm", "type": "renewable_energy", "country": "ITA"},
)

# Explain ML prediction
explanation = llm_service.explain_ml_prediction(
    model_name="RESM",
    prediction={"score": 75.2, "category": "high_suitability"},
)
```

### Using ReportEngine with LLM

```python
from backend.src.reporting.engine import ReportEngine
from pathlib import Path

# Initialize engine with LLM enabled
engine = ReportEngine(
    templates_dir=Path("backend/src/reporting/templates"),
    memory_store=memory_store,
    use_rag=True,
    use_llm=True,  # Enable LLM generation
)

# Generate report (automatically uses LLM)
report = engine.generate_report(
    template_name="enhanced_report.md.jinja",
    context=context,
    use_llm=True,
)
```

## Template Integration

The enhanced report template (`enhanced_report.md.jinja`) automatically uses LLM-generated content:

```jinja
## Executive Summary
{% if executive_summary and executive_summary != "Executive summary not available." %}
{{ executive_summary }}  {# LLM-generated #}
{% endif %}

## Biodiversity Assessment
{% if biodiversity_narrative %}
{{ biodiversity_narrative }}  {# LLM-generated #}
{% endif %}

## AI/ML Model Predictions
{% if ai_explanations and ai_explanations.RESM %}
{{ ai_explanations.RESM }}  {# LLM-generated #}
{% endif %}
```

## Troubleshooting

### LLM Service Not Enabled

**Error**: `LLM service is not enabled`

**Solution**: 
1. Check `USE_LLM=true` in environment
2. Verify API key is set: `GROQ_API_KEY=your_key`
3. Check logs for initialization errors

### Import Errors

**Error**: `Failed to import LLM library`

**Solution**: 
```bash
pip install langchain-groq
# or
pip install -e backend/  # Install all dependencies
```

### Rate Limiting

**Error**: Rate limit exceeded

**Solution**:
- Groq free tier: 30,000 requests/day
- Implement request throttling
- Consider using Ollama for local development

### Poor Quality Output

**Solutions**:
- Adjust `LLM_TEMPERATURE` (lower = more consistent, higher = more creative)
- Use better model: `GROQ_MODEL=llama-3.1-70b-versatile`
- Provide more context in prompts
- Enable RAG to use similar historical reports

## Best Practices

1. **Enable RAG**: Use `enable_rag=true` to improve quality with similar historical reports
2. **Cache Results**: LLM generation can be slow; cache results when possible
3. **Error Handling**: Always have fallback text when LLM fails
4. **Rate Limiting**: Monitor API usage to avoid exceeding free tier limits
5. **Temperature**: Use `0.3` for factual reports, `0.7` for creative content

## API Reference

See `backend/src/reporting/langchain_llm.py` for full API documentation.

## Support

For issues or questions:
1. Check logs: `backend/logs/`
2. Verify API key: Test at [console.groq.com](https://console.groq.com)
3. Review LangChain docs: [python.langchain.com](https://python.langchain.com)
