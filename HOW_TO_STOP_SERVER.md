# How to Stop the API Server

## Quick Method (Windows PowerShell)

1. **Find the process using port 8000:**
   ```powershell
   netstat -ano | findstr :8000
   ```
   Look for the PID (Process ID) in the last column.

2. **Stop the process:**
   ```powershell
   Stop-Process -Id <PID> -Force
   ```
   Replace `<PID>` with the actual process ID you found.

## Alternative Methods

### Method 1: Task Manager
1. Press `Ctrl + Shift + Esc` to open Task Manager
2. Go to the "Details" tab
3. Find `python.exe` processes
4. Look for one using port 8000 (check "Command line" column if visible)
5. Right-click → End Task

### Method 2: PowerShell One-Liner
```powershell
Get-Process | Where-Object {$_.Id -eq (Get-NetTCPConnection -LocalPort 8000).OwningProcess} | Stop-Process -Force
```

### Method 3: If Running in Terminal
- If you started the server in a terminal window (not background):
  - Go to that terminal window
  - Press `Ctrl + C` to stop it

## Restart the Server

After stopping, restart with:
```powershell
cd D:\Aethera_original\backend
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

## Check if Server is Running

```powershell
curl http://localhost:8000/docs
```

If you get a response, the server is running!

