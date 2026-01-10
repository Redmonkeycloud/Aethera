#!/bin/bash
# Master script to generate all training data and pretrain all models

set -e

echo "=========================================="
echo "AETHERA Model Setup Script"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Generate training data for all models"
echo "2. Validate training data quality"
echo "3. Pretrain all models"
echo ""
echo "=========================================="
echo ""

# Step 1: Generate training data
echo "Step 1: Generating training data for all models..."
python scripts/prepare_training_data.py --models all --n-samples 2000 --format parquet --validate

echo ""
echo "Step 2: Pretraining all models..."
python scripts/pretrain_all_models.py --models all

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Training data location: data2/{resm,ahsm,cim}/training.parquet"
echo "Pretrained models location: models/pretrained/{model_name}/"
echo ""
echo "Models are now ready for fast inference!"

