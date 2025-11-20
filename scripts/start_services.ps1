# Start AETHERA Services
# This script starts Redis, Celery worker, and FastAPI server

param(
    [switch]$Background = $false,
    [string]$RedisPort = "6379",
    [string]$ApiPort = "8000",
    [string]$ApiHost = "localhost"
)

$ErrorActionPreference = "Continue"

Write-Host "Starting AETHERA Services..." -ForegroundColor Green
Write-Host ""

# Check if Redis is already running (check Docker first, then local)
Write-Host "Checking Redis..." -ForegroundColor Yellow
$redisRunning = $false

# Check Docker Redis
try {
    $dockerCheck = docker exec aethera-redis redis-cli ping 2>&1
    if ($LASTEXITCODE -eq 0 -and $dockerCheck -match "PONG") {
        Write-Host "✓ Redis is running in Docker" -ForegroundColor Green
        $redisRunning = $true
    }
} catch {
    # Docker Redis not running, continue
}

# Check local Redis if Docker Redis is not running
if (-not $redisRunning) {
    try {
        $redisCheck = redis-cli ping 2>&1
        if ($LASTEXITCODE -eq 0 -and $redisCheck -match "PONG") {
            Write-Host "✓ Redis is already running locally" -ForegroundColor Green
            $redisRunning = $true
        }
    } catch {
        # Redis not found locally
    }
}

# If Redis is not running, try to start Docker Redis
if (-not $redisRunning) {
    Write-Host "Redis is not running. Checking if Docker Redis container exists..." -ForegroundColor Yellow
    try {
        $containerCheck = docker ps -a --filter "name=aethera-redis" --format "{{.Names}}" 2>&1
        if ($containerCheck -match "aethera-redis") {
            Write-Host "Starting existing Docker Redis container..." -ForegroundColor Yellow
            docker start aethera-redis 2>&1 | Out-Null
            Start-Sleep -Seconds 2
            Write-Host "✓ Redis started from Docker container" -ForegroundColor Green
        } else {
            Write-Host "⚠ Redis is not running. Please start it manually:" -ForegroundColor Red
            Write-Host "  docker run -d -p 6379:6379 --name aethera-redis redis:7-alpine" -ForegroundColor Gray
            Write-Host ""
            Write-Host "Continuing anyway - services may fail if Redis is not available..." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ Could not check Docker. Please ensure Redis is running on port $RedisPort" -ForegroundColor Yellow
    }
}

Write-Host ""

# Start Celery worker
Write-Host "Starting Celery worker..." -ForegroundColor Yellow
$projectRoot = Split-Path -Parent $PSScriptRoot
$celeryScript = "cd '$projectRoot'; .\backend\venv\Scripts\Activate.ps1; celery -A backend.src.workers.celery_app worker --pool=solo --loglevel=info"

if ($Background) {
    Start-Process powershell -ArgumentList @("-NoExit", "-Command", $celeryScript)
    Write-Host "✓ Celery worker started in background window" -ForegroundColor Green
} else {
    Write-Host "Starting Celery worker in new window..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList @("-NoExit", "-Command", $celeryScript)
    Start-Sleep -Seconds 2
}

Write-Host ""

# Start FastAPI server
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
$apiScript = "cd '$projectRoot'; .\backend\venv\Scripts\Activate.ps1; uvicorn backend.src.api.app:app --host $ApiHost --port $ApiPort --reload"

if ($Background) {
    Start-Process powershell -ArgumentList @("-NoExit", "-Command", $apiScript)
    Write-Host "✓ FastAPI server started in background window" -ForegroundColor Green
} else {
    Write-Host "Starting FastAPI server in new window..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList @("-NoExit", "-Command", $apiScript)
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
