# Stop AETHERA Services

$ErrorActionPreference = "Continue"

Write-Host "Stopping AETHERA Services..." -ForegroundColor Yellow
Write-Host ""

# Stop Redis
Write-Host "Stopping Redis..." -ForegroundColor Yellow
try {
    $null = redis-cli shutdown 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Redis stopped" -ForegroundColor Green
    } else {
        Write-Host "  Redis not running" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Redis not running or not installed" -ForegroundColor Gray
}

Write-Host ""

# Stop Celery
Write-Host "Stopping Celery worker..." -ForegroundColor Yellow
try {
    $celeryProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
            $cmdLine -like "*celery*celery_app*"
        } catch {
            $false
        }
    }
    if ($celeryProcesses) {
        $celeryProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Celery stopped" -ForegroundColor Green
    } else {
        Write-Host "  Celery not running" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Could not check Celery status" -ForegroundColor Gray
}

Write-Host ""

# Stop FastAPI
Write-Host "Stopping FastAPI server..." -ForegroundColor Yellow
try {
    $apiProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
            $cmdLine -like "*uvicorn*app:app*"
        } catch {
            $false
        }
    }
    if ($apiProcesses) {
        $apiProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] FastAPI stopped" -ForegroundColor Green
    } else {
        Write-Host "  FastAPI not running" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Could not check FastAPI status" -ForegroundColor Gray
}

Write-Host ""

# Stop Frontend (Vite)
Write-Host "Stopping Frontend dev server..." -ForegroundColor Yellow
try {
    $frontendProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
            $cmdLine -like "*vite*" -or $cmdLine -like "*npm*dev*"
        } catch {
            $false
        }
    }
    if ($frontendProcesses) {
        $frontendProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Frontend stopped" -ForegroundColor Green
    } else {
        Write-Host "  Frontend not running" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Could not check Frontend status" -ForegroundColor Gray
}

Write-Host ""

# Stop Docker Redis
Write-Host "Stopping Docker Redis..." -ForegroundColor Yellow
try {
    docker stop aethera-redis 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Docker Redis stopped" -ForegroundColor Green
    } else {
        Write-Host "  Docker Redis not running" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Docker Redis not running" -ForegroundColor Gray
}

Write-Host ""
Write-Host "All services stopped!" -ForegroundColor Green
