# Stop AETHERA Services

$ErrorActionPreference = "Continue"

Write-Host "Stopping AETHERA Services..." -ForegroundColor Yellow
Write-Host ""

# Stop Redis
Write-Host "Stopping Redis..." -ForegroundColor Yellow
try {
    $null = redis-cli shutdown 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Redis stopped" -ForegroundColor Green
    } else {
        Write-Host "  Redis not running" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Redis not running or not installed" -ForegroundColor Gray
}

Write-Host ""

# Stop Celery
Write-Host "Stopping Celery worker..." -ForegroundColor Yellow
$celeryProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*celery*celery_app*"
}
if ($celeryProcesses) {
    $celeryProcesses | Stop-Process -Force
    Write-Host "✓ Celery stopped" -ForegroundColor Green
} else {
    Write-Host "  Celery not running" -ForegroundColor Gray
}

Write-Host ""

# Stop FastAPI
Write-Host "Stopping FastAPI server..." -ForegroundColor Yellow
$apiProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*app:app*"
}
if ($apiProcesses) {
    $apiProcesses | Stop-Process -Force
    Write-Host "✓ FastAPI stopped" -ForegroundColor Green
} else {
    Write-Host "  FastAPI not running" -ForegroundColor Gray
}

Write-Host ""
Write-Host "All services stopped!" -ForegroundColor Green

