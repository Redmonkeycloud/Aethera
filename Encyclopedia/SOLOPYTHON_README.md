# AETHERA 2.0 - Python-Only Branch (solopython)

This branch contains a Python-only implementation of AETHERA, using Streamlit for the frontend instead of React/TypeScript.

## Overview

The `solopython` branch provides a complete Python stack for AETHERA:
- **Backend**: FastAPI (Python) - unchanged from main branch
- **Frontend**: Streamlit (Python) - replaces React/TypeScript frontend

## Key Differences from Main Branch

### Frontend Technology Stack

| Component | Main Branch | solopython Branch |
|-----------|-------------|-------------------|
| Frontend Framework | React + TypeScript | Streamlit (Python) |
| Build Tool | Vite | None (Streamlit handles it) |
| Maps | MapLibre GL JS | Streamlit map / streamlit-folium |
| State Management | Zustand | Streamlit session state |
| Styling | Tailwind CSS | Streamlit's built-in styling |

### Benefits of Python-Only Approach

1. **Single Language**: Entire codebase in Python
2. **Simpler Setup**: No Node.js/npm required
3. **Faster Development**: Streamlit's rapid prototyping
4. **Easier Deployment**: Single environment to manage
5. **Better Integration**: Direct Python-to-Python communication

### Trade-offs

1. **Less Interactive Maps**: Streamlit maps are simpler than MapLibre
2. **Different UI Paradigm**: Streamlit uses a different interaction model
3. **Less Customization**: Streamlit has more limited styling options

## Installation

### Prerequisites

- Python 3.10 or higher
- Backend API dependencies (see main README)
- PostgreSQL + PostGIS (via Docker Compose)

### Setup Steps

1. **Clone and checkout the branch:**
   ```bash
   git checkout solopython
   ```

2. **Set up backend (same as main branch):**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. **Set up frontend:**
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

4. **Start services:**
   ```bash
   # Start database
   docker compose up -d db
   
   # Initialize database
   python -m backend.src.db.init_db --dsn postgresql://aethera:aethera@localhost:55432/aethera
   
   # Start backend API (in one terminal)
   uvicorn backend.src.api.app:app --reload
   
   # Start Celery worker (in another terminal)
   celery -A backend.src.workers.celery_app worker --loglevel=info
   
   # Start Streamlit frontend (in another terminal)
   cd frontend
   streamlit run app.py
   ```

5. **Access the application:**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Project Structure

```
AETHERA_2.0/
├── backend/              # FastAPI backend (unchanged)
│   └── src/
│       └── api/
├── frontend/             # Streamlit frontend (Python-only)
│   ├── app.py           # Main Streamlit app
│   ├── requirements.txt # Frontend dependencies
│   ├── pages/           # Streamlit pages
│   │   ├── 1_🏠_Home.py
│   │   ├── 2_➕_New_Project.py
│   │   ├── 3_📊_Project.py
│   │   └── 4_📈_Run.py
│   └── src/
│       ├── api_client.py  # Backend API client
│       └── components.py  # Reusable components
└── ... (rest same as main branch)
```

## Usage

The application workflow is the same as the main branch:

1. **Create a Project**: Navigate to "New Project" and fill in details
2. **Define AOI**: Upload a GeoJSON file or enter coordinates
3. **Run Analysis**: Configure project type and country, then start analysis
4. **View Results**: Explore KPIs, legal compliance, and download exports

## Development

### Adding New Pages

Create new files in `frontend/pages/` following Streamlit's naming convention:
- Use numbers for ordering: `5_📄_Reports.py`
- Emoji prefixes for visual identification

### Modifying API Client

Edit `frontend/src/api_client.py` to add new endpoints or modify existing API calls.

### Running Tests

Backend tests remain the same. Frontend testing would use Streamlit's testing framework:
```bash
# Backend tests (same as main)
cd backend
pytest

# Frontend tests (if added)
cd frontend
pytest  # If test files are created
```

## Migration Notes

If migrating from the React frontend:
- API endpoints remain the same
- Data models are unchanged
- Only the UI layer differs

## Known Limitations

1. **Map Functionality**: Streamlit's built-in maps are simpler. For advanced mapping, consider:
   - `streamlit-folium` for interactive Folium maps
   - `pydeck` for advanced 3D visualizations
   - Custom Streamlit components wrapping MapLibre (requires JavaScript bridge)

2. **Real-time Updates**: Streamlit uses polling/reruns instead of WebSockets. Task status polling is implemented but may feel less responsive than the React version.

3. **File Uploads**: Currently supports GeoJSON uploads. For other formats, additional processing may be needed.

## Future Enhancements

Possible improvements:
- Enhanced map visualization with streamlit-folium or pydeck
- Custom Streamlit components for advanced interactions
- Better error handling and user feedback
- Performance optimizations for large datasets
- Export to more formats directly from Streamlit

## Contributing

When contributing to this branch:
- Maintain Python-only approach (no JavaScript/TypeScript)
- Follow Streamlit best practices
- Keep API client compatible with backend
- Test with the FastAPI backend

## Questions?

See the main README.md for general project documentation, or the frontend/README.md for Streamlit-specific details.

