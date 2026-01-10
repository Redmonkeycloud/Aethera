# Celery & Redis Setup - Fixing the 500 Error

## The Problem

When you click "Start Analysis", you see:
```
INFO:     127.0.0.1:63711 - "POST /projects/.../runs HTTP/1.1" 202 Accepted
INFO:     127.0.0.1:63711 - "GET /tasks/53f12486-a986-4f78-be89-9d2fa7e734be HTTP/1.1" 500 Internal Server Error
```

**The task is queued successfully (202), but checking its status fails (500).**

## Root Cause

**Redis is not running or not accessible.**

Celery uses Redis as a message broker to:
1. Queue tasks (this works - you get 202)
2. Track task status (this fails - you get 500)

## Solution

### Option 1: Install and Run Redis (Recommended)

#### Windows

1. **Download Redis for Windows:**
   - Option A: Use WSL2 (Windows Subsystem for Linux) - recommended
   - Option B: Download from: https://github.com/microsoftarchive/redis/releases
   - Option C: Use Docker: `docker run -d -p 6379:6379 redis:latest`

2. **If using WSL2:**
   ```bash
   # In WSL2 terminal
   sudo apt update
   sudo apt install redis-server
   sudo service redis-server start
   ```

3. **If using Docker:**
   ```powershell
   docker run -d -p 6379:6379 --name redis redis:latest
   ```

4. **Verify Redis is running:**
   ```powershell
   # Test connection (if you have redis-cli)
   redis-cli ping
   # Should return: PONG
   ```

#### Linux/Mac

```bash
# Install Redis
sudo apt install redis-server  # Ubuntu/Debian
brew install redis            # Mac

# Start Redis
sudo service redis-server start  # Ubuntu/Debian
brew services start redis       # Mac

# Verify
redis-cli ping
# Should return: PONG
```

### Option 2: Use a Different Redis URL

If Redis is running on a different host/port, set the environment variable:

```powershell
# Windows PowerShell
$env:REDIS_URL="redis://your-redis-host:6379/0"

# Or create/edit .env file in backend directory
REDIS_URL=redis://localhost:6379/0
```

### Option 3: Run Celery Worker (Required for Tasks to Execute)

Even after Redis is running, **tasks won't execute** unless you also run a Celery worker:

```powershell
# In backend directory, with venv activated
cd D:\Aethera_original\backend
.\venv\Scripts\Activate.ps1

# Run Celery worker
celery -A backend.src.workers.celery_app worker --loglevel=info --pool=solo
```

**Note:** On Windows, you MUST use `--pool=solo` (multiprocessing doesn't work on Windows).

## Complete Setup Checklist

1. ✅ **Redis is running** (check with `redis-cli ping`)
2. ✅ **Backend API is running** (`uvicorn backend.src.api.app:app --reload`)
3. ✅ **Celery worker is running** (`celery -A backend.src.workers.celery_app worker --pool=solo`)

## Testing

After Redis is running, try "Start Analysis" again. The 500 error should be replaced with:
- **200 OK** with task status (PENDING, PROCESSING, COMPLETED, etc.)

## Error Messages

With the improved error handling, you'll now see helpful messages in your backend logs:

- **"Cannot connect to Celery broker (Redis)"** → Redis is not running
- **"Cannot get task state from Celery broker"** → Redis connection issue
- **Other errors** → Check the full traceback in logs

## Quick Test

```powershell
# Test Redis connection from Python
python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); print(r.ping())"
# Should print: True
```

If this fails, Redis is not running or not accessible.

