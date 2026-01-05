# Quick Start Guide - Python-Only AETHERA

## Current Status

✅ **Streamlit frontend dependencies installed**  
✅ **FastAPI and uvicorn installed**  
✅ **pydantic-settings installed**

## Starting the Application

You need **two terminal windows** running simultaneously:

### Terminal 1: Backend API

```powershell
cd D:\AETHERA_2.0
python -m uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Wait until you see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Terminal 2: Streamlit Frontend

```powershell
cd D:\AETHERA_2.0\frontend
python -m streamlit run app.py
```

Wait until you see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

## Troubleshooting Import Errors

If the backend fails to start with import errors, install the missing packages:

1. **Note the missing module name** from the error message
2. **Install it:**
   ```powershell
   pip install <module-name>
   ```
3. **Try starting the backend again**

Common dependencies that may be needed:
- `pydantic-settings` ✅ (already installed)
- `pyyaml` (for YAML config files)
- Other dependencies as errors appear

## Minimal vs Full Setup

**Minimal Setup (Current):**
- Basic API endpoints (projects, runs, tasks) should work
- Some routes requiring geospatial libraries (geopandas, rasterio) may fail
- Good for testing the frontend connection

**Full Setup:**
- Install all backend dependencies: `cd backend && pip install -e .`
- Requires GDAL setup on Windows (can be complex)
- All features available

## Verify It's Working

1. **Backend:** Visit http://localhost:8000
   - Should show: `{"status":"ok","service":"AETHERA API",...}`

2. **Backend Docs:** Visit http://localhost:8000/docs
   - Should show FastAPI interactive documentation

3. **Frontend:** Visit http://localhost:8501
   - Should show "AETHERA Projects" page
   - No connection errors

## Next Steps

Once both services are running:
1. Create a project in the Streamlit frontend
2. Upload or define an AOI (Area of Interest)
3. Create an analysis run
4. View results

