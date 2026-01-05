# AI in AETHERA - Complete Explanation

## Overview

AETHERA uses **Machine Learning (ML) models** to predict environmental impacts and assess project suitability. The AI components are integrated into the analysis pipeline that runs when you start an analysis with coordinates.

## When AI Runs

AI models run **automatically** during the analysis pipeline, triggered when you:
1. Input coordinates (AOI)
2. Click "🚀 Start Analysis"
3. The backend processes the analysis asynchronously

The AI models are part of the `backend/src/main_controller.py` pipeline.

---

## The 4 AI/ML Models

### 1. 🌿 **Biodiversity AI Model** (Mandatory)

**Purpose**: Predicts biodiversity sensitivity and habitat impact

**What it does**:
- Analyzes protected area overlaps
- Assesses habitat fragmentation
- Predicts sensitivity scores (0-100)
- Categorizes as: `low`, `moderate`, `high`, `very_high`

**Technical Details**:
- **Type**: Classification (Ensemble)
- **Algorithms**: Logistic Regression, Random Forest, Gradient Boosting
- **Input Features**:
  - Protected area overlap percentage
  - Habitat fragmentation index
  - Forest ratio
  - Land cover types
  - Distance to water/roads
  - Connectivity index

**Output**:
- Sensitivity score (0-100)
- Sensitivity category
- Confidence level
- Key drivers (explanation of why)
- GeoJSON layer for map visualization

**Location**: `ai/models/biodiversity.py`

---

### 2. ⚡ **RESM (Renewable/Resilience Suitability Model)**

**Purpose**: Predicts how suitable a location is for renewable energy projects

**What it does**:
- Scores site suitability (0-100)
- Considers project type (solar, wind, hydro)
- Assesses land use compatibility
- Categorizes as: `very_low`, `low`, `moderate`, `high`, `very_high`

**Technical Details**:
- **Type**: Regression (Ensemble)
- **Algorithms**: Ridge Regression, Random Forest, Gradient Boosting
- **Input Features**:
  - Agricultural land ratio
  - Distance to protected areas
  - Soil erosion risk
  - Land use efficiency
  - Environmental KPIs
  - Project type

**Output**:
- Suitability score (0-100)
- Suitability category
- Key drivers (e.g., "High agricultural land ratio", "Sufficient distance from protected areas")

**Location**: `ai/models/resm.py`

---

### 3. 🚨 **AHSM (Asset Hazard Susceptibility Model)**

**Purpose**: Predicts risk from natural hazards (floods, wildfires, landslides, coastal erosion)

**What it does**:
- Multi-hazard risk assessment
- Scores susceptibility (0-100)
- Categorizes risk levels
- Identifies which hazards are most relevant

**Technical Details**:
- **Type**: Classification (Ensemble)
- **Algorithms**: Logistic Regression, Random Forest, Gradient Boosting
- **Input Features**:
  - Land cover types
  - Water regulation capacity
  - Soil erosion risk
  - Environmental indicators
  - Elevation/slope data

**Output**:
- Hazard susceptibility score (0-100)
- Risk category
- Hazard breakdown (flood, wildfire, etc.)

**Location**: `ai/models/ahsm.py`

---

### 4. 📊 **CIM (Cumulative Impact Model)**

**Purpose**: Integrates all models to predict overall cumulative environmental impact

**What it does**:
- Combines RESM, AHSM, and Biodiversity scores
- Predicts overall impact level
- Provides holistic assessment
- Categorizes as: `negligible`, `low`, `moderate`, `high`, `very_high`

**Technical Details**:
- **Type**: Classification (Ensemble)
- **Algorithms**: Logistic Regression, Random Forest, Gradient Boosting
- **Input Features**:
  - RESM score
  - AHSM score
  - Biodiversity score
  - Protected area overlap
  - Habitat fragmentation
  - Ecosystem service value
  - GHG emissions intensity
  - Net carbon balance

**Output**:
- Cumulative impact score (0-100)
- Impact category
- Key drivers (e.g., "High biodiversity sensitivity", "High hazard susceptibility")

**Location**: `ai/models/cim.py`

---

## How AI Models Work

### Ensemble Approach

All models use **ensemble methods** - combining multiple algorithms:
1. **Train 3 models** (Logistic Regression, Random Forest, Gradient Boosting)
2. **Make predictions** with each model
3. **Average/combine** predictions for final result
4. **Provide confidence** based on agreement between models

### Training Data

**Option 1: External Training Data**
- Models can load training data from CSV/Parquet files
- Located in: `data2/biodiversity/training.csv` (or similar)
- Used to train models on real-world examples

**Option 2: Synthetic Data (Fallback)**
- If no training data available, models generate synthetic training data
- Based on statistical distributions
- Ensures models always work, even without training data

### Feature Engineering

Before AI predictions, the system:
1. **Processes geospatial data** (CORINE, Natura 2000, etc.)
2. **Calculates features** (overlaps, distances, ratios, KPIs)
3. **Extracts numerical features** for ML models
4. **Passes features** to models for prediction

**Example Features**:
- `protected_overlap_pct`: 15.3%
- `fragmentation_index`: 0.42
- `distance_to_protected_km`: 2.5
- `forest_ratio`: 0.35
- `soil_erosion_risk`: 0.23

---

## Analysis Pipeline Flow

When you start an analysis, here's the sequence:

```
1. Input: AOI Coordinates
   ↓
2. Geospatial Processing
   - Load CORINE land cover
   - Load Natura 2000 (protected areas)
   - Clip to AOI
   - Calculate land cover statistics
   ↓
3. Feature Engineering
   - Calculate overlaps
   - Compute distances
   - Calculate environmental KPIs
   - Build feature vectors
   ↓
4. AI Model Predictions (Automatically)
   ├─ Biodiversity AI → sensitivity score
   ├─ RESM → suitability score  
   ├─ AHSM → hazard susceptibility score
   └─ CIM → cumulative impact score
   ↓
5. Save Results
   - JSON files with predictions
   - GeoJSON layers for visualization
   - Metadata and explanations
   ↓
6. Available via API
   - GET /runs/{run_id}/results
   - GET /runs/{run_id}/biodiversity/prediction
   - GET /runs/{run_id}/indicators/resm
   - GET /runs/{run_id}/indicators/ahsm
   - GET /runs/{run_id}/indicators/cim
```

---

## Where to See AI Results

### In the Frontend

1. **Run Results Page** (`pages/4_📈_Run.py`):
   - View all predictions
   - See scores and categories
   - Read explanations

2. **API Endpoints**:
   - `/runs/{run_id}/results` - All results (including AI predictions)
   - `/runs/{run_id}/indicators/resm` - RESM prediction
   - `/runs/{run_id}/indicators/ahsm` - AHSM prediction
   - `/runs/{run_id}/indicators/cim` - CIM prediction
   - `/runs/{run_id}/biodiversity/prediction` - Biodiversity prediction

### Output Files

Results are saved in: `data/{run_id}/processed/`

- `biodiversity/prediction.json` - Biodiversity AI results
- `resm_prediction.json` - RESM results
- `ahsm_prediction.json` - AHSM results
- `cim_prediction.json` - CIM results

---

## Example Output

### Biodiversity Prediction
```json
{
  "score": 75.5,
  "sensitivity": "high",
  "confidence": 0.85,
  "drivers": [
    "Protected overlap 12.3%",
    "Fragmentation index 0.52",
    "Forest ratio 0.41"
  ],
  "dataset_source": "external"
}
```

### RESM Prediction
```json
{
  "score": 68.2,
  "category": "moderate",
  "confidence": 0.78,
  "drivers": [
    "High agricultural land ratio (suitable for development)",
    "Sufficient distance from protected areas"
  ]
}
```

---

## Technical Stack

- **Libraries**: scikit-learn, numpy, pandas
- **Algorithms**: Logistic Regression, Random Forest, Gradient Boosting
- **Training**: Can use external data or synthetic generation
- **Inference**: Real-time predictions during analysis
- **Storage**: Predictions saved as JSON, metadata in PostgreSQL

---

## Summary

**AI is the "brain" of AETHERA** - it automatically:
1. ✅ Analyzes your coordinates/AOI
2. ✅ Processes geospatial data
3. ✅ Makes intelligent predictions about:
   - Biodiversity sensitivity
   - Site suitability
   - Hazard risks
   - Cumulative impacts
4. ✅ Provides scores, categories, and explanations
5. ✅ Saves results for visualization and reporting

**You don't need to do anything special** - just provide coordinates and start the analysis. The AI models run automatically as part of the pipeline!

