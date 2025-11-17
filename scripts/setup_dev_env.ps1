# Development environment setup script for AETHERA (PowerShell)

Write-Host "🚀 Setting up AETHERA development environment..." -ForegroundColor Cyan

# Check Python version
$pythonVersion = python --version 2>&1
if (-not $pythonVersion) {
    Write-Host "❌ Error: Python not found. Install Python 3.11+ from python.org" -ForegroundColor Red
    exit 1
}

$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
        Write-Host "❌ Error: Python 3.11+ required. Found: $pythonVersion" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Python version: $pythonVersion" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Cyan
& .venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "⬆️  Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install backend dependencies
Write-Host "📥 Installing backend dependencies..." -ForegroundColor Cyan
Set-Location backend
pip install -e ".[dev]"
Set-Location ..

# Install pre-commit
Write-Host "🔧 Installing pre-commit hooks..." -ForegroundColor Cyan
pip install pre-commit
pre-commit install

# Check Docker
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "🐳 Docker found. Starting services..." -ForegroundColor Cyan
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Docker compose failed. Make sure Docker Desktop is running." -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Docker not found. Install Docker Desktop to run the database." -ForegroundColor Yellow
}

# Initialize database if Docker is running
if (docker ps 2>&1 | Select-String -Pattern "postgres" -Quiet) {
    Write-Host "🗄️  Initializing database..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2  # Wait for postgres to be ready
    Set-Location backend
    python -m src.db.init_db
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Database initialization failed. Check Docker logs." -ForegroundColor Yellow
    }
    Set-Location ..
} else {
    Write-Host "⚠️  Database not running. Start Docker and run: make db-init" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Development environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Activate virtual environment: .venv\Scripts\Activate.ps1"
Write-Host "  2. Run tests: make test"
Write-Host "  3. Start API server: cd backend; uvicorn src.api.app:app --reload"
Write-Host ""
Write-Host "See DEVELOPMENT.md for more information."

