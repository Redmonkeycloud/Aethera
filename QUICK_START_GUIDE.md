# Quick Start Guide - Testing AETHERA

## Prerequisites

1. **Docker Desktop** must be running
   - Make sure Docker Desktop is started before running services
   - Docker is needed for PostgreSQL and optionally Redis

2. **Python Virtual Environment** activated
   - Located at: `backend/venv/`
   - VS Code tasks will activate it automatically

## Starting Services

### Option 1: VS Code Tasks (Recommended) ✅

1. **Make sure Docker Desktop is running**
   - Open Docker Desktop application
   - Wait until it's fully started (whale icon in system tray)

2. **Start All Services**:
   - Press `Ctrl+Shift+P` (Command Palette)
   - Type: `Tasks: Run Task`
   - Select: **"Start All Services"**

   This will automatically start:
   - ✅ PostgreSQL (Docker) - Port 55432
   - ✅ Redis (Docker) - Port 6379
   - ✅ Celery Worker - Background task processor
   - ✅ FastAPI Server - http://localhost:8000
   - ✅ Frontend Dev Server - http://localhost:3000 (or Vite default port)

3. **Verify Services**:
   - Check terminal windows that open
   - FastAPI: Look for "Uvicorn running on http://localhost:8000"
   - Celery: Look for "celery@... ready"
   - Frontend: Look for "Local: http://localhost:XXXX"

### Option 2: Manual Start

**Step 1: Start Docker Services**
```powershell
# Start PostgreSQL
docker-compose up -d db

# Start Redis (if not using VS Code task)
docker run -d -p 6379:6379 --name aethera-redis redis:7-alpine
```

**Step 2: Start Backend Services**
```powershell
# Terminal 1 - Celery Worker
cd D:\Aethera_original
.\backend\venv\Scripts\Activate.ps1
celery -A backend.src.workers.celery_app worker --pool=solo --loglevel=info

# Terminal 2 - FastAPI Server
cd D:\Aethera_original
.\backend\venv\Scripts\Activate.ps1
uvicorn backend.src.api.app:app --host localhost --port 8000 --reload
```

**Step 3: Start Frontend** (optional for testing)
```powershell
cd D:\Aethera_original\frontend
npm run dev
```

## What Gets Started

| Service | Port | Purpose | Required |
|---------|------|---------|----------|
| **PostgreSQL** | 55432 | Database (projects, runs, reports, security) | ✅ Yes |
| **Redis** | 6379 | Task queue for Celery | ✅ Yes |
| **FastAPI** | 8000 | Backend API | ✅ Yes |
| **Celery Worker** | - | Processes async tasks | ✅ Yes |
| **Frontend** | 3000+ | Web UI | Optional |

## Verification

### Check Docker Services
```powershell
docker ps
# Should show: aethera-postgres and aethera-redis
```

### Check API
- Open browser: http://localhost:8000/docs
- Should show FastAPI interactive documentation

### Check Health
```powershell
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

## Common Issues

### ❌ "Docker daemon is not running"
**Solution**: Start Docker Desktop application first, then try again.

### ❌ "Port 8000 already in use"
**Solution**: 
- Stop the service using port 8000
- Or change port in tasks.json: `--port 8001`

### ❌ "Cannot connect to PostgreSQL"
**Solution**:
- Check Docker is running: `docker ps`
- Start PostgreSQL: `docker-compose up -d db`
- Wait 5-10 seconds for PostgreSQL to initialize

### ❌ "Redis connection error"
**Solution**:
- Check Redis is running: `docker ps | findstr redis`
- Start Redis: `docker start aethera-redis`
- Or create it: `docker run -d -p 6379:6379 --name aethera-redis redis:7-alpine`

### ❌ "Module not found" errors
**Solution**:
- Activate virtual environment: `.\backend\venv\Scripts\Activate.ps1`
- Install dependencies: `cd backend && pip install -e .`

## Testing the Fixes

After starting services, test the layer loading:

1. **Open Frontend**: http://localhost:3000 (or port shown in terminal)
2. **Check API**: http://localhost:8000/docs
3. **Test Layers Endpoint**: http://localhost:8000/layers/available
   - Should return: `{"natura2000": true/false, "corine": true/false}`
4. **Test Layer Loading**: http://localhost:8000/layers/natura2000
   - Should return GeoJSON if dataset is available

## Stopping Services

### VS Code Task
- Press `Ctrl+Shift+P`
- Type: `Tasks: Run Task`
- Select: **"Stop All Services"**

### Manual
```powershell
# Stop Docker containers
docker stop aethera-postgres aethera-redis

# Close terminal windows for Celery and FastAPI
# (Press Ctrl+C in each terminal)
```

---

**Note**: Docker Desktop must be running before using "Start All Services" task!

