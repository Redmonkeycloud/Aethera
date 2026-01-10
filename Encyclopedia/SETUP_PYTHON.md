# Python-Only Frontend Setup Guide

This guide helps you set up and run the Streamlit-based Python-only frontend for AETHERA.

## Quick Start

1. **Install dependencies:**
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   streamlit run app.py
   ```

3. **Access the app:**
   - Open your browser to http://localhost:8501

## Prerequisites

- Python 3.10 or higher
- Backend API running on http://localhost:8000
- All backend dependencies installed

## Installation Steps

### 1. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
streamlit --version
python -c "import streamlit; print('Streamlit installed successfully')"
```

## Running the Application

### Start the Backend First

Make sure the backend API is running:

```bash
# Terminal 1: Start backend API
uvicorn backend.src.api.app:app --reload

# Terminal 2: Start Celery worker (if using async tasks)
celery -A backend.src.workers.celery_app worker --loglevel=info
```

### Start the Frontend

```bash
cd frontend
streamlit run app.py
```

The application will automatically open in your default browser.

## Configuration

### Environment Variables

You can configure the API URL:

```bash
# On Windows PowerShell:
$env:API_URL="http://localhost:8000"

# On Linux/Mac:
export API_URL=http://localhost:8000
```

Or create a `.streamlit/secrets.toml` file:

```toml
[api]
url = "http://localhost:8000"
```

### Streamlit Configuration

Edit `.streamlit/config.toml` to customize:
- Port number
- Theme colors
- Server settings

## Troubleshooting

### Import Errors

If you see import errors:
1. Make sure you're in the `frontend` directory
2. Verify all dependencies are installed: `pip list`
3. Check Python version: `python --version` (should be 3.10+)

### Connection Errors

If the frontend can't connect to the backend:
1. Verify the backend is running: `curl http://localhost:8000`
2. Check the API_URL environment variable
3. Ensure no firewall is blocking the connection

### Port Already in Use

If port 8501 is already in use:
```bash
streamlit run app.py --server.port 8502
```

## Development Tips

### Hot Reload

Streamlit automatically reloads when you save files. No need to restart manually.

### Debugging

Enable detailed error messages by setting:
```bash
streamlit run app.py --logger.level=debug
```

### Viewing Logs

Streamlit logs appear in the terminal where you started the app.

## Next Steps

- See `README.md` for application usage
- See `SOLOPYTHON_README.md` for branch-specific documentation
- See main project `README.md` for backend setup

