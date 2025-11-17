# AETHERA Frontend

A simple web interface for visualizing biodiversity analysis results from AETHERA.

## Features

- Interactive map visualization using Leaflet
- Display biodiversity sensitivity layers
- View Natura 2000 protected sites
- Show overlap areas between AOI and protected sites
- Toggle layers on/off
- Popup information on feature click

## Usage

1. **Start the backend API server:**
   ```bash
   cd backend
   python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open the frontend:**
   - Simply open `index.html` in a web browser
   - Or serve it with a simple HTTP server:
     ```bash
     # Python
     python -m http.server 8080
     
     # Node.js
     npx serve
     ```

3. **Load a run:**
   - Enter a Run ID (e.g., `run_20251117_132207`) in the sidebar
   - Click "Load Biodiversity Layers"
   - Toggle layers on/off using the checkboxes

## API Endpoints Used

- `GET /runs/{run_id}/biodiversity/sensitivity` - Biodiversity sensitivity GeoJSON
- `GET /runs/{run_id}/biodiversity/natura` - Natura 2000 sites GeoJSON
- `GET /runs/{run_id}/biodiversity/overlap` - Overlap areas GeoJSON

## Future Enhancements

- [ ] Run creation form
- [ ] AOI upload interface
- [ ] Real-time analysis status
- [ ] Report generation preview
- [ ] Multiple run comparison
- [ ] Export functionality
