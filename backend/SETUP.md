# Backend Setup Guide

## Prerequisites

- **Python 3.11+** (currently you have 3.10.5 - may need to upgrade)
- **pip** (package manager, comes with Python)

## Quick Setup

### 1. Create Virtual Environment

```powershell
cd D:\Aethera_original\backend
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

### 3. Install Dependencies

```powershell
pip install -e .
```

This installs all dependencies from `pyproject.toml`.

### 4. Verify Installation

```powershell
uvicorn --version
```

Should show uvicorn version.

## Running the Backend

After setup, you can run:

```powershell
# Make sure virtual environment is activated
uvicorn backend.src.api.app:app --reload
```

## Python Version Issue

**Current**: Python 3.10.5  
**Required**: Python 3.11+

### Option 1: Try Anyway (May Work)

The backend might work with Python 3.10. Try installing:

```powershell
cd D:\Aethera_original\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .
```

### Option 2: Upgrade Python (Recommended)

1. Download Python 3.11+ from https://www.python.org/downloads/
2. Install it (check "Add Python to PATH")
3. Restart terminal
4. Verify: `python --version` should show 3.11+
5. Then follow setup steps above

## Troubleshooting

### "uvicorn is not recognized"

- Make sure virtual environment is activated
- Run `pip install -e .` in the backend directory
- Verify with `uvicorn --version`

### "Execution Policy" Error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Import Errors

Make sure you're in the project root (`D:\Aethera_original`) when running uvicorn, not in the `backend` directory.

