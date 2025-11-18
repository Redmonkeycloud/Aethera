# Start AETHERA Services
# This script starts Redis, Celery worker, and FastAPI server

param(
    [switch]$Background = $false,
    [string]$RedisPort = "6379",
    [string]$ApiPort = "8000",
    [string]$ApiHost = "localhost"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting AETHERA Services..." -ForegroundColor Green
Write-Host ""

# Check if Redis is already running
Write-Host "Checking Redis..." -ForegroundColor Yellow
try {
    $redisCheck = redis-cli ping 2>&1
    if ($LASTEXITCODE -eq 0 -and $redisCheck -eq "PONG") {
        Write-Host "✓ Redis is already running" -ForegroundColor Green
    } else {
        Write-Host "Starting Redis server..." -ForegroundColor Yellow
        if ($Background) {
            Start-Process redis-server -WindowStyle Hidden
            Start-Sleep -Seconds 2
            Write-Host "✓ Redis started in background" -ForegroundColor Green
        } else {
            Write-Host "Starting Redis in new window..." -ForegroundColor Yellow
            Start-Process redis-server
            Start-Sleep -Seconds 2
        }
    }
} catch {
    Write-Host "⚠ Redis not found. Please install Redis or start it manually." -ForegroundColor Red
    Write-Host "  Download: https://redis.io/download" -ForegroundColor Gray
}

Write-Host ""

# Start Celery worker
Write-Host "Starting Celery worker..." -ForegroundColor Yellow
$celeryScript = @"
cd $PSScriptRoot\..
celery -A backend.src.workers.celery_app worker --loglevel=info
"@

if ($Background) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $celeryScript
    Write-Host "✓ Celery worker started in background window" -ForegroundColor Green
} else {
    Write-Host "Starting Celery worker in new window..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $celeryScript
    Start-Sleep -Seconds 2
}

Write-Host ""

# Start FastAPI server
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
$apiScript = @"
cd $PSScriptRoot\..
uvicorn backend.src.api.app:app --host $ApiHost --port $ApiPort --reload
"@

if ($Background) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiScript
    Write-Host "✓ FastAPI server started in background window" -ForegroundColor Green
} else {
    Write-Host "Starting FastAPI server in new window..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiScript
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All services started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  • Redis:     localhost:$RedisPort" -ForegroundColor White
Write-Host "  • Celery:    Processing tasks" -ForegroundColor White
Write-Host "  • FastAPI:   http://$ApiHost`:$ApiPort" -ForegroundColor White
Write-Host "  • API Docs:  http://$ApiHost`:$ApiPort/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

if (-not $Background) {
    Write-Host "Press any key to exit this script (services will continue running)..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

