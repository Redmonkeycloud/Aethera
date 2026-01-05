# Starting Backend and Frontend Services

## Option 1: Separate Terminal Windows (Recommended)

### Terminal 1 - Backend API

Open a new terminal/PowerShell window and run:

```powershell
cd D:\AETHERA_2.0
python -m uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8001 --reload
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['D:\\AETHERA_2.0']
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using StatReload
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2 - Frontend (Streamlit)

Open another new terminal/PowerShell window and run:

```powershell
cd D:\AETHERA_2.0\frontend
python -m streamlit run app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

## Option 2: PowerShell Start-Process (Opens New Windows)

Run this single command to start both in separate windows:

```powershell
# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\AETHERA_2.0; python -m uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8001 --reload"

# Wait a moment
Start-Sleep -Seconds 2

# Start Frontend  
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\AETHERA_2.0\frontend; python -m streamlit run app.py"
```

## Verification

Once both are running:

1. **Backend API**: Open http://localhost:8001 in your browser
   - Should show: `{"status":"ok","service":"AETHERA API","version":"0.1.0","docs":"/docs"}`

2. **Frontend**: Open http://localhost:8501 in your browser
   - Should show the AETHERA Projects page

3. **API Docs**: Open http://localhost:8001/docs
   - Should show the FastAPI interactive documentation

## Stopping Services

Press `Ctrl+C` in each terminal window to stop the respective service.

## Troubleshooting

- **Port already in use**: Change port with `--port 8002` (and update frontend `API_BASE_URL`)
- **Import errors**: Make sure all dependencies are installed
- **Module not found**: Check Python path and virtual environment

