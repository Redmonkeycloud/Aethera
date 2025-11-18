# Legal Rules Engine

The Legal Rules Engine evaluates project metrics against country-specific EIA regulations and compliance requirements.

## Overview

The Legal Rules Engine:
- Loads country-specific rules from YAML/JSON files
- Evaluates project metrics against these rules
- Generates compliance status reports
- Integrates with the main analysis pipeline

## Architecture

### Components

1. **Rule Parser** (`backend/src/legal/parser.py`)
   - Parses YAML/JSON rule files into `RuleSet` objects
   - Validates rule structure

2. **Rule Evaluator** (`backend/src/legal/evaluator.py`)
   - Evaluates rules against project metrics
   - Uses JSONLogic for complex condition evaluation
   - Falls back to simple evaluation if JSONLogic is not available

3. **Rule Loader** (`backend/src/legal/loader.py`)
   - Loads country-specific rule files
   - Caches loaded rules
   - Lists available countries

4. **Rule Data Structures** (`backend/src/legal/rules.py`)
   - `LegalRule`: Represents a single rule
   - `RuleSet`: Collection of rules for a country

## Rule File Format

Rule files are stored in `backend/src/config/legal_rules/` and named by country code (e.g., `DEU.yaml`).

### Example Rule File Structure

```yaml
country_code: DEU
country_name: Germany
version: "1.0.0"
metadata:
  jurisdiction: "Federal Republic of Germany"
  applicable_laws:
    - "Bundesnaturschutzgesetz (BNatSchG)"
    - "Umweltverträglichkeitsprüfungsgesetz (UVPG)"
  last_updated: "2025-01-01"

rules:
  - id: "deu_bio_natura_overlap"
    name: "Natura 2000 Site Overlap"
    description: "Projects overlapping Natura 2000 sites require special assessment"
    category: "biodiversity"
    severity: "critical"
    condition:
      and:
        - protected_overlap_pct:
            ">": 0
        - protected_overlap_pct:
            ">=": 1.0
    message_template: "Project overlaps {protected_overlap_pct:.2f}% of Natura 2000 site. Critical assessment required."
    references:
      - "FFH-Richtlinie Art. 6(3)"
      - "BNatSchG § 34"
```

### Rule Fields

- **id**: Unique identifier for the rule
- **name**: Human-readable name
- **description**: Explanation of what the rule checks
- **category**: Rule category (e.g., "biodiversity", "emissions", "land_use")
- **severity**: "critical", "high", "medium", "low", or "informational"
- **condition**: JSONLogic expression or simple comparison
- **message_template**: Template string with placeholders (e.g., `{field_name}`)
- **references**: List of legal references (optional)

### Condition Syntax

#### Simple Comparisons

```yaml
condition:
  biodiversity_score:
    ">": 70
```

Supported operators: `>`, `<`, `>=`, `<=`, `==`, `!=`

#### Logical Operators

```yaml
condition:
  and:
    - protected_overlap_pct:
        ">": 0
    - protected_overlap_pct:
        ">=": 1.0
```

```yaml
condition:
  or:
    - distance_to_protected_km:
        "<": 0.5
    - biodiversity_score:
        ">": 80
```

#### JSONLogic (Advanced)

When `jsonlogic-python` is installed, you can use full JSONLogic syntax:

```yaml
condition:
  ">":
    - var: "biodiversity_score"
    - 70
```

See [JSONLogic documentation](http://jsonlogic.com/) for more examples.

## Available Project Metrics

The following metrics are available for rule evaluation:

- `protected_overlap_pct`: Percentage of AOI overlapping protected areas
- `distance_to_protected_km`: Distance to nearest protected area (km)
- `biodiversity_score`: Biodiversity sensitivity score (0-100)
- `project_operation_tco2e_per_year`: Annual operational emissions (tCO2e)
- `ghg_emissions_intensity`: GHG emissions intensity (tCO2e/ha)
- `forest_ratio`: Ratio of forest cover
- `aoi_area_ha`: Area of AOI (hectares)
- `natural_habitat_ratio`: Ratio of natural habitat
- `distance_to_water_km`: Distance to nearest water body (km)
- `distance_to_settlement_km`: Distance to nearest settlement (km)
- `cim_score`: Cumulative impact score (0-100)
- `ahsm_score`: Asset hazard susceptibility score (0-100)

## Usage

### Command Line

```bash
python -m backend.src.main_controller \
  --aoi test_aoi.geojson \
  --project-type solar \
  --country DEU
```

### Programmatic

```python
from backend.src.legal import LegalEvaluator, LegalEvaluationResult
from backend.src.legal.loader import LegalRulesLoader

# Load rules for a country
loader = LegalRulesLoader()
rule_set = loader.load_country_rules("DEU")

if rule_set:
    # Prepare project metrics
    project_metrics = {
        "biodiversity_score": 75.0,
        "protected_overlap_pct": 5.2,
        # ... other metrics
    }
    
    # Evaluate
    evaluator = LegalEvaluator(rule_set)
    result = evaluator.evaluate(project_metrics)
    
    print(f"Overall compliant: {result.overall_compliant}")
    print(f"Critical violations: {len(result.critical_violations)}")
```

## Output Format

The legal evaluation result includes:

- **overall_compliant**: Boolean indicating if project passes all critical rules
- **summary**: Statistics (total rules, passed, failed, violations, warnings)
- **statuses**: Detailed status for each rule
- **critical_violations**: List of critical rule violations
- **warnings**: List of high/medium severity violations
- **informational**: List of low/informational violations

Results are saved to `legal_evaluation.json` in the run output directory.

## Adding New Country Rules

1. Create a new YAML file in `backend/src/config/legal_rules/`
2. Name it using ISO 3166-1 alpha-3 country code (e.g., `FRA.yaml` for France)
3. Define rules following the format above
4. Test with sample project metrics

## Dependencies

- **jsonlogic-python**: Optional but recommended for complex rule evaluation
  - Install with: `pip install jsonlogic-python`
  - If not installed, the engine falls back to simple evaluation

## Integration

The Legal Rules Engine is automatically integrated into the main analysis pipeline:

1. Rules are loaded based on `--country` argument or `country`/`country_code` in run config
2. Project metrics are automatically collected from analysis results
3. Evaluation results are saved to `legal_evaluation.json`
4. Compliance summary is added to the run manifest

## Future Enhancements

- Support for rule versioning and updates
- Rule validation and testing framework
- Integration with legal database for automatic rule updates
- Multi-jurisdiction support (federal + state/provincial rules)
- Rule conflict resolution
- Custom rule sets per project type

