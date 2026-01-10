# AETHERA Python-Only Installation Guide

This guide will help you install and run the Python-only version of AETHERA on the `solopython` branch.

## ✅ What Has Been Created

The `solopython` branch now includes:

1. **Streamlit Frontend** (`frontend/`)
   - `app.py` - Main Streamlit application
   - `pages/` - Four main pages (Home, New Project, Project, Run)
   - `src/api_client.py` - Backend API client
   - `requirements.txt` - Python dependencies
   - `.streamlit/config.toml` - Streamlit configuration

2. **Documentation**
   - `SOLOPYTHON_README.md` - Branch-specific documentation
   - `frontend/README.md` - Frontend documentation
   - `frontend/SETUP_PYTHON.md` - Setup guide

## 📦 Required Libraries

The frontend requires these Python packages (already in `requirements.txt`):

- `streamlit>=1.32.0` - Web framework
- `streamlit-folium>=0.15.0` - Interactive maps
- `folium>=0.15.0` - Map library
- `requests>=2.32.0` - HTTP client
- `pandas>=2.2.0` - Data manipulation
- `geopandas>=0.14.0` - Geospatial data
- `shapely>=2.0.0` - Geometric operations
- `pyyaml>=6.0.0` - YAML parsing
- `python-dateutil>=2.8.2` - Date utilities

## 🚀 Quick Installation

### Step 1: Checkout the Branch

```bash
git checkout solopython
```

### Step 2: Install Frontend Dependencies

```bash
cd frontend
pip install -r requirements.txt
```

### Step 3: Install Backend Dependencies (if not already done)

```bash
cd ../backend
pip install -e .
```

### Step 4: Start Services

**Terminal 1 - Database:**
```bash
docker compose up -d db
```

**Terminal 2 - Backend API:**
```bash
uvicorn backend.src.api.app:app --reload
```

**Terminal 3 - Celery Worker (optional, for async tasks):**
```bash
celery -A backend.src.workers.celery_app worker --loglevel=info
```

**Terminal 4 - Streamlit Frontend:**
```bash
cd frontend
streamlit run app.py
```

### Step 5: Access the Application

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📝 Project Structure

```
AETHERA_2.0/
├── backend/                 # FastAPI backend (unchanged)
│   └── src/
├── frontend/                # Streamlit frontend (NEW)
│   ├── app.py              # Main app
│   ├── requirements.txt    # Dependencies
│   ├── pages/              # Streamlit pages
│   │   ├── 1_🏠_Home.py
│   │   ├── 2_➕_New_Project.py
│   │   ├── 3_📊_Project.py
│   │   └── 4_📈_Run.py
│   └── src/
│       ├── api_client.py   # API client
│       └── components.py   # Components
└── ...
```

## ✅ Verification

After installation, verify everything works:

1. **Check Streamlit installation:**
   ```bash
   streamlit --version
   ```

2. **Test imports:**
   ```bash
   python -c "import streamlit; import requests; print('✓ Dependencies OK')"
   ```

3. **Start the app:**
   ```bash
   cd frontend
   streamlit run app.py
   ```

4. **Check backend connection:**
   - Visit http://localhost:8501
   - Try creating a project
   - If you see connection errors, verify the backend is running

## 🎯 Next Steps

1. Read `SOLOPYTHON_README.md` for branch-specific information
2. Read `frontend/README.md` for frontend usage
3. Explore the Streamlit app at http://localhost:8501
4. Review the API client in `frontend/src/api_client.py`

## 🔧 Troubleshooting

### Import Errors
- Make sure you're in a virtual environment
- Install all dependencies: `pip install -r requirements.txt`
- Check Python version (3.10+ required)

### Connection Errors
- Verify backend is running: `curl http://localhost:8000`
- Check `API_URL` environment variable
- Review backend logs for errors

### Port Conflicts
- Change Streamlit port: `streamlit run app.py --server.port 8502`
- Change backend port in uvicorn command

## 📚 Additional Resources

- Streamlit Documentation: https://docs.streamlit.io/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Main AETHERA README: `README.md`

