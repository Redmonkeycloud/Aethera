# Model Pretraining Guide

## Overview

To avoid server timeouts and speed up analysis runs, all ML models can be pretrained and saved to disk. This document explains how to generate training data, pretrain models, and use pretrained models in your analyses.

## Quick Start

### Generate Training Data and Pretrain All Models

**PowerShell (Windows):**
```powershell
python scripts/setup_models_and_training_data.ps1
```

**Bash (Linux/Mac):**
```bash
bash scripts/setup_models_and_training_data.sh
```

**Or manually:**
```bash
# Step 1: Generate training data
python scripts/prepare_training_data.py --models all --n-samples 2000 --format parquet --validate

# Step 2: Pretrain models
python scripts/pretrain_all_models.py --models all
```

## Detailed Steps

### 1. Generate Training Data

Generate training data for all models:

```bash
python scripts/prepare_training_data.py --models all --n-samples 2000 --format parquet --validate
```

**Options:**
- `--models`: Models to generate data for (`resm`, `ahsm`, `cim`, `biodiversity`, or `all`)
- `--n-samples`: Number of training samples (default: 2000)
- `--format`: Output format (`parquet` or `csv`, default: `parquet`)
- `--validate`: Enable data quality validation

**Output:**
- `data2/resm/training.parquet`
- `data2/ahsm/training.parquet`
- `data2/cim/training.parquet`
- `data2/biodiversity/training.csv` (if generated)

### 2. Validate Training Data (Optional)

Validate training data quality:

```bash
python scripts/validate_training_data.py data2/resm/training.parquet --model resm
python scripts/validate_training_data.py data2/ahsm/training.parquet --model ahsm
python scripts/validate_training_data.py data2/cim/training.parquet --model cim
```

**Checks:**
- Missing values
- Outliers (IQR method)
- Label distributions
- Class imbalance (for classification)
- Feature ranges
- Constant features
- Data consistency

### 3. Pretrain Models

Pretrain all models and save them:

```bash
python scripts/pretrain_all_models.py --models all
```

**Options:**
- `--models`: Models to pretrain (`resm`, `ahsm`, `cim`, `biodiversity`, or `all`)
- `--skip-existing`: Skip models that are already pretrained
- `--force-synthetic`: Force use of synthetic data instead of training files

**Output:**
- `models/pretrained/resm/ensemble.pkl` (trained models)
- `models/pretrained/resm/metadata.json` (model metadata)
- `models/pretrained/resm/config.json` (model configuration)
- Similar files for `ahsm`, `cim`, and `biodiversity`

### 4. Use Pretrained Models (Future Integration)

**Note:** Model loading from pretrained files is currently infrastructure-ready but not yet integrated into the analysis pipeline. Models are currently trained on-demand during analysis runs.

**Future Integration:**
- Update model initialization to check for pretrained models
- Load pretrained models if available
- Fall back to on-demand training if pretrained models not found
- Add model versioning and compatibility checks

## Training Data Details

### RESM (Renewable Energy Suitability Model)

**Features:**
- Land cover ratios (natural habitat, impervious surface, agricultural)
- Environmental KPIs (fragmentation, connectivity, ecosystem services)
- Distance to receptors (protected areas, settlements)
- **Weather features** (solar GHI, wind speed, temperature)
- Project type indicators

**Labels:**
- `suitability_score` (0-100): Suitability score based on domain expertise

**Label Generation Rules:**
- Land use: 25% weight (agricultural > natural > impervious)
- Environmental constraints: 20% weight (protected areas reduce suitability)
- Weather resources: 25% weight (if available)
- Infrastructure: 10% weight (moderate distance ideal)
- Environmental quality: 20% weight (connectivity, ecosystem services)

### AHSM (Asset Hazard Susceptibility Model)

**Features:**
- Forest/water/impervious ratios
- Habitat fragmentation indices
- Water regulation capacity
- Soil erosion risk
- Distance to water bodies
- Ecosystem service values

**Labels:**
- `hazard_risk` (0-4): Risk level (very_low to very_high)

**Label Generation Rules:**
- Flood risk: 30% weight
- Wildfire risk: 25% weight
- Landslide risk: 25% weight
- Urban risk: 20% weight

### CIM (Cumulative Impact Model)

**Features:**
- RESM, AHSM, and Biodiversity scores
- Environmental KPIs
- GHG emissions intensity
- Land use efficiency
- Protected area overlap

**Labels:**
- `cumulative_impact_class` (0-4): Impact class (negligible to very_high)

**Label Generation Rules:**
- Biodiversity: 45% weight (highest priority)
- RESM: 30% weight
- AHSM: 25% weight

## Model Metadata

Each pretrained model includes metadata:

```json
{
  "model_name": "resm",
  "dataset_source": "data2/resm/training.parquet",
  "n_features": 17,
  "n_models": 3,
  "vector_fields": ["aoi_area_ha", "natural_habitat_ratio", ...]
}
```

## Benefits

1. **Faster Analysis Runs**
   - No training delays during analysis
   - Instant model loading
   - Reduced server resource usage

2. **Prevents Timeouts**
   - Training happens offline
   - Analysis runs complete faster
   - Better user experience

3. **Model Versioning**
   - Track model versions
   - Compare model performance
   - Reproducible results

4. **Quality Control**
   - Validate training data before training
   - Ensure data quality
   - Identify issues early

## Retraining Models

When new training data is added:

1. Generate new training data:
   ```bash
   python scripts/prepare_training_data.py --models resm --validate
   ```

2. Retrain models:
   ```bash
   python scripts/pretrain_all_models.py --models resm
   ```

3. Models will automatically use new training data if available

## Troubleshooting

### Training Data Generation Fails

- Check that required datasets are available (CORINE, Natura2000, etc.)
- Verify `data2/` directory structure
- Check file permissions

### Model Pretraining Fails

- Ensure training data exists
- Check Python dependencies (joblib, scikit-learn)
- Verify sufficient disk space
- Check memory availability (models require RAM during training)

### Validation Warnings

- Review validation report for data quality issues
- Consider increasing `--n-samples` if data quality is low
- Check for class imbalance (for classification models)
- Review outlier counts

## Next Steps

1. **Integrate Pretrained Model Loading**
   - Update `RESMEnsemble`, `AHSMEnsemble`, etc. to load pretrained models
   - Add model version compatibility checks
   - Implement fallback to on-demand training

2. **Model Registry**
   - Track model versions
   - Compare model performance
   - Enable model rollback

3. **Automated Retraining**
   - Schedule periodic retraining
   - Monitor data drift
   - Automatically retrain when new data is available

## References

- Training Data Generation: `scripts/prepare_training_data.py`
- Model Pretraining: `scripts/pretrain_all_models.py`
- Data Validation: `scripts/validate_training_data.py`
- Weather Data Setup: `docs/WEATHER_DATA_SETUP.md`

