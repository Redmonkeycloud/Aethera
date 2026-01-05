# AETHERA Frontend (Python-only)

Streamlit-based frontend application for the AETHERA Environmental Impact Assessment platform.

## Overview

This is the Python-only version of the AETHERA frontend, built with Streamlit. It provides a complete web interface for:

- Creating and managing projects
- Defining Areas of Interest (AOI)
- Running environmental impact analyses
- Viewing results, KPIs, and legal compliance
- Exporting analysis packages

## Features

- ✅ Streamlit-based web interface
- ✅ Project management
- ✅ AOI upload and definition
- ✅ Analysis run creation and monitoring
- ✅ Results visualization
- ✅ Legal compliance display
- ✅ Export functionality

## Requirements

- Python 3.10+
- Backend API running on `http://localhost:8000`

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables (optional):**
   ```bash
   export API_URL=http://localhost:8000  # Default
   ```

## Running the Application

1. **Start the backend API** (see main README.md)

2. **Run Streamlit:**
   ```bash
   streamlit run app.py
   ```

   The application will open in your browser at `http://localhost:8501`

## Project Structure

```
frontend/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── pages/                 # Streamlit pages
│   ├── 1_🏠_Home.py      # Home page (project list)
│   ├── 2_➕_New_Project.py  # Create new project
│   ├── 3_📊_Project.py   # Project detail page
│   └── 4_📈_Run.py       # Run results page
└── src/
    ├── api_client.py      # Backend API client
    └── components.py      # Reusable components
```

## Usage

1. **Home Page**: View all projects and create new ones
2. **New Project**: Create a project with name, country, and sector
3. **Project Page**: 
   - Upload or define an AOI (GeoJSON)
   - Create analysis runs
   - Monitor run status
   - View project runs
4. **Run Page**: View comprehensive analysis results, legal compliance, and export data

## API Integration

The frontend communicates with the backend FastAPI service through the `api_client.py` module, which provides:

- `ProjectsAPI`: Project management
- `RunsAPI`: Analysis run management
- `TasksAPI`: Task status monitoring

## Development

### Adding New Pages

Create a new file in the `pages/` directory following Streamlit's naming convention:
- Files starting with numbers control page order
- Emoji prefixes make pages easily identifiable

Example:
```python
# pages/5_📄_Reports.py
import streamlit as st
st.title("Reports")
```

### Modifying API Client

Edit `src/api_client.py` to add new endpoints or modify existing ones.

## Notes

- This is a Python-only implementation using Streamlit
- Maps are currently simplified (full map visualization can be added with streamlit-folium or pydeck)
- Session state is used for navigation and data persistence
- Error handling is built into the API client

## Troubleshooting

**Connection errors:**
- Ensure the backend API is running on port 8000
- Check `API_URL` environment variable if using a different port

**Import errors:**
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.10+ required)

**Page navigation issues:**
- Use `st.switch_page()` for navigation
- Session state persists data between pages
