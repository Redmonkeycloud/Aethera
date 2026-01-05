# Backend Logs - Where to Find Them

## Quick Answer

**Backend logs appear in your terminal/console where you started the FastAPI server.**

## How Backend Logging Works

The backend uses two logging mechanisms:

### 1. **Console Logs (Primary)**
- **Location**: The terminal where you run `uvicorn`
- **Format**: Rich formatted output (colored, easy to read)
- **When**: All log messages appear here in real-time

### 2. **File Logs (Optional)**
- **Location**: `{log_dir}/aethera.log` (if `log_dir` is configured)
- **Format**: Plain text with timestamps
- **When**: Only if `configure_logging(log_dir=...)` is called

## Viewing Logs

### During Development

When you run the backend with:
```bash
uvicorn backend.src.api.app:app --reload
```

**All logs appear in that terminal window**, including:
- API requests (from FastAPI/uvicorn)
- Application logs (from `get_logger()`)
- Errors and exceptions
- Task execution logs

### Example Log Output

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     127.0.0.1:54321 - "GET /tasks/53f12486-a986-4f78-be89-9d2fa7e734be HTTP/1.1" 500
ERROR:    Error getting task status: Task not found
```

### Finding the 500 Error

When you see:
```
:8000/tasks/53f12486-a986-4f78-be89-9d2fa7e734be:1  Failed to load resource: the server responded with a status of 500
```

**Check your backend terminal** for the error message. It will show something like:
```
ERROR:    Error getting task status: <actual error message>
```

## Common Log Locations

### FastAPI/Uvicorn Logs
- **Console**: Wherever you ran `uvicorn`
- **No file by default** (unless you configure it)

### Application Logs
- **Console**: Same terminal as uvicorn
- **File**: Only if configured with `configure_logging(log_dir=Path(...))`

### Celery Worker Logs
- **Console**: Wherever you run `celery -A backend.src.workers.celery_app worker`
- **File**: Depends on Celery configuration

## Enabling File Logging (Optional)

If you want logs saved to a file, modify `backend/src/api/app.py`:

```python
from pathlib import Path
from src.logging_utils import configure_logging

# Add this before creating the app
configure_logging(log_dir=Path("./logs"))

app = FastAPI(...)
```

Then logs will be saved to `./logs/aethera.log`.

## Debugging the 500 Error

1. **Check your backend terminal** - the error message will be there
2. **Look for stack traces** - they show exactly what failed
3. **Check task status** - the error is likely in `backend/src/api/routes/tasks.py:get_task_status()`

Common causes:
- Task doesn't exist in TaskTracker
- Celery/Redis not running
- TaskTracker not properly initialized
- Database connection issue

## Quick Commands

```bash
# View logs in real-time (if using file logging)
tail -f logs/aethera.log

# Search for errors
grep ERROR logs/aethera.log

# Search for specific task ID
grep "53f12486-a986-4f78-be89-9d2fa7e734be" logs/aethera.log
```

