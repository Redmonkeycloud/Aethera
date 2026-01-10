# AETHERA Services Setup Guide

This guide explains how to start and manage the AETHERA backend services: Redis, Celery worker, and FastAPI server.

## Quick Start

### Using Make (Recommended)

```bash
# Start all services
make start

# Start in background
make start-background

# Check service status
make check

# Stop all services
make stop
```

### Using Scripts

**Windows (PowerShell):**
```powershell
.\scripts\start_services.ps1
```

**Linux/Mac:**
```bash
bash scripts/start_services.sh
```

### Manual Start

If you prefer to start services manually or need more control:

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - Celery Worker:**
```bash
celery -A backend.src.workers.celery_app worker --loglevel=info
```

**Terminal 3 - FastAPI Server:**
```bash
uvicorn backend.src.api.app:app --reload
```

## Service Details

### 1. Redis Server

**Purpose**: Message broker and result backend for Celery tasks.

**Default Port**: 6379

**Verification**:
```bash
redis-cli ping
# Should return: PONG
```

**Installation**:
- **Windows**: Download from https://redis.io/download or use WSL
- **macOS**: `brew install redis`
- **Linux**: `sudo apt-get install redis-server` (Ubuntu/Debian)

**Configuration**: Edit `redis.conf` if you need to change port or other settings.

### 2. Celery Worker

**Purpose**: Processes async tasks (analysis pipeline execution).

**Command**:
```bash
celery -A backend.src.workers.celery_app worker --loglevel=info
```

**Options**:
- `--loglevel=info` - Set logging level (debug, info, warning, error)
- `--concurrency=4` - Number of worker processes (default: CPU count)
- `--detach` - Run in background (Linux/Mac)
- `--logfile=celery.log` - Log to file
- `--pidfile=celery.pid` - Save PID to file

**Verification**: Check logs for "ready" message indicating worker is connected to Redis.

### 3. FastAPI Server

**Purpose**: HTTP API server for handling requests.

**Command**:
```bash
uvicorn backend.src.api.app:app --reload
```

**Options**:
- `--host localhost` - Bind address (default: 127.0.0.1)
- `--port 8000` - Port number (default: 8000)
- `--reload` - Auto-reload on code changes (development only)
- `--workers 4` - Number of worker processes (production)

**Access Points**:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Service Dependencies

```
┌─────────────┐
│   Client    │
│  (Browser/  │
│   Frontend) │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────┐
│   FastAPI Server     │ ◄─── Requires: Redis + Celery
│  (Port 8000)         │
└──────┬──────────────┘
       │ Queues Tasks
       ▼
┌─────────────────────┐
│   Redis Server       │ ◄─── Required by: FastAPI + Celery
│  (Port 6379)         │
└──────┬──────────────┘
       │ Task Queue
       ▼
┌─────────────────────┐
│  Celery Worker      │ ◄─── Requires: Redis
│  (Executes Tasks)   │
└─────────────────────┘
```

**Start Order**:
1. Redis (must be first)
2. Celery worker (can start after Redis)
3. FastAPI server (can start after Redis)

## Troubleshooting

### Redis Connection Errors

**Problem**: Celery or FastAPI can't connect to Redis.

**Solutions**:
1. Verify Redis is running: `redis-cli ping`
2. Check Redis port (default: 6379)
3. Check firewall settings
4. Verify `REDIS_URL` in environment variables

### Celery Worker Not Processing Tasks

**Problem**: Tasks are queued but not executed.

**Solutions**:
1. Check worker logs for errors
2. Verify worker is connected: `celery -A backend.src.workers.celery_app inspect active`
3. Check Redis connection
4. Verify task is registered: `celery -A backend.src.workers.celery_app inspect registered`

### FastAPI Server Won't Start

**Problem**: Port already in use or import errors.

**Solutions**:
1. Check if port 8000 is in use: `netstat -an | grep 8000` (Linux/Mac) or `netstat -an | findstr 8000` (Windows)
2. Use different port: `uvicorn backend.src.api.app:app --port 8001`
3. Check Python dependencies: `pip install -e backend/`
4. Verify imports: `python -c "from backend.src.api.app import app"`

### Services Stop Unexpectedly

**Problem**: Services crash or stop running.

**Solutions**:
1. Check logs for error messages
2. Verify all dependencies are installed
3. Check system resources (memory, disk space)
4. Review environment variables
5. Check file permissions

## Production Deployment

For production, use:

1. **Process Manager** (PM2, systemd, supervisor):
   ```bash
   # Example with PM2
   pm2 start redis-server --name redis
   pm2 start "celery -A backend.src.workers.celery_app worker" --name celery
   pm2 start "uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8000 --workers 4" --name api
   ```

2. **Docker Compose** (recommended):
   ```yaml
   # docker-compose.yml
   services:
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
     
     celery:
       build: ./backend
       command: celery -A backend.src.workers.celery_app worker
       depends_on:
         - redis
     
     api:
       build: ./backend
       command: uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8000
       ports:
         - "8000:8000"
       depends_on:
         - redis
         - celery
   ```

3. **Environment Variables**:
   ```bash
   REDIS_URL=redis://redis:6379/0
   STORAGE_BACKEND=s3
   S3_BUCKET=your-bucket
   # ... other settings
   ```

## Monitoring

### Check Service Status

```bash
# Using Make
make check

# Manual checks
redis-cli ping
celery -A backend.src.workers.celery_app inspect active
curl http://localhost:8000/docs
```

### View Logs

**Redis**: Check system logs or Redis log file

**Celery**: Check terminal output or log file (if `--logfile` specified)

**FastAPI**: Check terminal output or use logging configuration

### Task Monitoring

```bash
# List active tasks
celery -A backend.src.workers.celery_app inspect active

# List registered tasks
celery -A backend.src.workers.celery_app inspect registered

# Get worker stats
celery -A backend.src.workers.celery_app inspect stats
```

## Next Steps

- See `docs/PHASE5_IMPLEMENTATION.md` for detailed API documentation
- See `README.md` for project overview
- See `docs/LEGAL_RULES_ENGINE.md` for legal rules usage

