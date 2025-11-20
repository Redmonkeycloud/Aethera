# Start Celery Worker (Windows-safe)
# This script ensures Celery uses the 'solo' pool on Windows

param(
    [string]$LogLevel = "info"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting Celery worker (Windows-safe mode)..." -ForegroundColor Yellow
Write-Host "  Pool: solo (required for Windows)" -ForegroundColor Gray
Write-Host "  Log Level: $LogLevel" -ForegroundColor Gray
Write-Host ""

# Activate virtual environment
if (Test-Path "$projectRoot\backend\venv\Scripts\Activate.ps1") {
    & "$projectRoot\backend\venv\Scripts\Activate.ps1"
} else {
    Write-Host "ERROR: Virtual environment not found at $projectRoot\backend\venv" -ForegroundColor Red
    exit 1
}

# Set PYTHONPATH
$env:PYTHONPATH = $projectRoot

# Start Celery worker with explicit solo pool
# The --pool=solo flag is REQUIRED on Windows
Write-Host "Starting worker..." -ForegroundColor Green
celery -A backend.src.workers.celery_app worker --pool=solo --loglevel=$LogLevel

