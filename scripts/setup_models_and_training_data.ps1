# Master script to generate all training data and pretrain all models (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "AETHERA Model Setup Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "1. Generate training data for all models" -ForegroundColor White
Write-Host "2. Validate training data quality" -ForegroundColor White
Write-Host "3. Pretrain all models" -ForegroundColor White
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Generate training data
Write-Host "Step 1: Generating training data for all models..." -ForegroundColor Yellow

# Default sample count kept modest to avoid multi-day runs; override via env var AETHERA_N_SAMPLES
$nSamples = 500
if ($env:AETHERA_N_SAMPLES) {
    try { $nSamples = [int]$env:AETHERA_N_SAMPLES } catch { $nSamples = 500 }
}

Write-Host ("Using n-samples = {0}. Override with `$env:AETHERA_N_SAMPLES" -f $nSamples) -ForegroundColor Cyan

# Generate training data for RESM, AHSM, CIM
python scripts/prepare_training_data.py --models resm ahsm cim --n-samples $nSamples --format parquet --validate --seed 42

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Training data generation failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Generating biodiversity training data..." -ForegroundColor Yellow
python scripts/build_biodiversity_training.py --samples $nSamples --seed 42

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Biodiversity training data generation failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Pretraining all models..." -ForegroundColor Yellow
python scripts/pretrain_all_models.py --models all

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Model pretraining failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Training data location: data2/{resm,ahsm,cim}/training.parquet" -ForegroundColor Cyan
Write-Host "Pretrained models location: models/pretrained/{model_name}/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Models are now ready for fast inference!" -ForegroundColor Green

