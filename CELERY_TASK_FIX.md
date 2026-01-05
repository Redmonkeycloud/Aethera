# Celery Task Fix - Module Import Error

## The Problem

When the Celery worker tries to run the analysis task, you see:
```
ModuleNotFoundError: No module named 'backend.config'
```

This happens because when running `python -m backend.src.main_controller` as a subprocess, Python can't find the `backend` module.

## Root Cause

The subprocess doesn't have the project root in `PYTHONPATH`, so relative imports like `from ..config.base_settings` fail.

## Fix Applied

✅ **Set PYTHONPATH in subprocess** - The task now sets `PYTHONPATH` to include the project root before running the subprocess.

✅ **Improved error handling** - Celery exceptions are now properly formatted with `exc_type` to prevent the "Exception information must include the exception type" error.

## What Changed

### `backend/src/workers/tasks.py`

1. **Added PYTHONPATH setup:**
   ```python
   project_root = Path(__file__).parent.parent.parent.parent
   env = dict(os.environ)
   env["PYTHONPATH"] = str(project_root)
   ```

2. **Improved error formatting:**
   - Added `exc_type` to exception metadata
   - Better logging of subprocess errors
   - Proper traceback formatting

## Testing

After restarting the Celery worker, try "Start Analysis" again. The import error should be resolved.

If you still see errors, check:
1. **Project root path** - Make sure `Path(__file__).parent.parent.parent.parent` points to `D:\Aethera_original` (or `D:\AETHERA_2.0`)
2. **Python environment** - Ensure the subprocess uses the same Python/venv as the worker
3. **Backend structure** - Verify `backend/src/` structure exists

## Note About Directory Names

The error shows `D:\Aethera_original` but your workspace is `D:\AETHERA_2.0`. Make sure:
- The Celery worker is running from the correct directory
- The `project_root` calculation points to the right location
- Both directories have the same `backend/src/` structure

