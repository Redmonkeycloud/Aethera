# Starting the Backend API

The backend API needs to be running for the Streamlit frontend to work.

## Quick Start

### Option 1: Minimal Setup (Basic API functionality)

1. **Install minimal dependencies:**
   ```powershell
   pip install fastapi uvicorn pydantic
   ```

2. **Start the server:**
   ```powershell
   cd D:\AETHERA_2.0
   python -m uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Verify it's running:**
   - Open browser to: http://localhost:8000
   - Or check: http://localhost:8000/docs

### Option 2: Full Setup (All features)

Some routes may need additional dependencies. If you see import errors:

1. **Install backend dependencies** (may require GDAL setup):
   ```powershell
   cd D:\AETHERA_2.0\backend
   pip install -e .
   ```

   Note: This may fail on Windows due to GDAL/fiona requirements. The basic API should still work without full geospatial dependencies.

2. **Start the server:**
   ```powershell
   cd D:\AETHERA_2.0
   python -m uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

## Running Both Services

You need **two terminals**:

**Terminal 1 - Backend API:**
```powershell
cd D:\AETHERA_2.0
python -m uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Streamlit Frontend:**
```powershell
cd D:\AETHERA_2.0\frontend
python -m streamlit run app.py
```

## Verify Everything Works

1. **Check backend:** http://localhost:8000
   - Should show: `{"status":"ok","service":"AETHERA API","version":"0.1.0","docs":"/docs"}`

2. **Check frontend:** http://localhost:8501
   - Should show the AETHERA Projects page

3. **If you see connection errors in Streamlit:**
   - Make sure backend is running on port 8000
   - Check for error messages in the backend terminal
   - Some routes may need additional dependencies installed

## Troubleshooting

- **Port already in use:** Change port with `--port 8001`
- **Import errors:** Some routes may need additional packages, but basic project/runs endpoints should work
- **GDAL errors:** Ignore if you just need basic API functionality

