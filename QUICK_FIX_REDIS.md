# Quick Fix: Redis Connection Error

## The Problem

When you click "🚀 Start Analysis", you see:
```
ConnectionError: Error 10061 connecting to localhost:6379
```

**Redis is not running!** The analysis uses Celery (async task queue), which requires Redis.

## Quick Solution (Choose One)

### Option 1: Docker (Easiest - Recommended)

If you have Docker installed:

```powershell
# Start Redis in Docker
docker run -d -p 6379:6379 --name aethera-redis redis:7-alpine
```

**That's it!** Redis will run in the background.

**To stop Redis:**
```powershell
docker stop aethera-redis
```

**To start it again later:**
```powershell
docker start aethera-redis
```

**To remove it:**
```powershell
docker stop aethera-redis
docker rm aethera-redis
```

### Option 2: WSL2 (If you have Windows Subsystem for Linux)

```bash
# In WSL2 terminal
sudo apt update
sudo apt install redis-server
sudo service redis-server start

# To start it again later
sudo service redis-server start
```

### Option 3: Windows Native (Advanced)

1. Download Redis for Windows: https://github.com/microsoftarchive/redis/releases
2. Extract and run `redis-server.exe`
3. Keep the window open while using AETHERA

## Also Start Celery Worker (Required)

Even with Redis running, **you also need a Celery worker** to process the analysis tasks:

**Open a NEW terminal and run:**

```powershell
cd D:\AETHERA_2.0
celery -A backend.src.workers.celery_app worker --pool=solo --loglevel=info
```

**Keep this terminal open** - it processes the analysis tasks.

## Complete Setup Checklist

You need **3 terminals running**:

1. ✅ **Redis** (Option 1-3 above)
2. ✅ **Backend API** (already running)
   ```powershell
   python -m uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8001 --reload
   ```
3. ✅ **Celery Worker** (NEW - required for analysis)
   ```powershell
   celery -A backend.src.workers.celery_app worker --pool=solo --loglevel=info
   ```
4. ✅ **Frontend** (Streamlit - already running)
   ```powershell
   cd frontend
   python -m streamlit run app.py
   ```

## Verify Redis is Running

```powershell
# Test Redis connection (if you have redis-cli)
redis-cli ping
# Should return: PONG

# Or test from Python
python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); print('Redis OK!' if r.ping() else 'Redis NOT OK')"
```

## After Starting Redis + Celery

Try "🚀 Start Analysis" again. It should work!

## Summary

**What you need:**
- Redis running (use Docker: `docker run -d -p 6379:6379 --name aethera-redis redis:7-alpine`)
- Celery worker running (`celery -A backend.src.workers.celery_app worker --pool=solo --loglevel=info`)

**Why:**
- Backend queues tasks → Redis
- Celery worker reads from Redis → Executes analysis
- Frontend checks status → Redis

All 3 services must be running for analysis to work!

