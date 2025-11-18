# VS Code Tasks - Quick Start Guide

VS Code tasks allow you to start all AETHERA services with a single command!

## How to Use

### Method 1: Command Palette (Easiest)
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type: `Tasks: Run Task`
3. Select: **"Start All Services"**

This will automatically:
- ✅ Start Docker Redis (or create it if it doesn't exist)
- ✅ Start Celery Worker (in a dedicated terminal)
- ✅ Start FastAPI Server (in a dedicated terminal)
- ✅ Start Frontend Dev Server (in a dedicated terminal)

### Method 2: Keyboard Shortcut
You can add a keyboard shortcut:
1. Press `Ctrl+K Ctrl+S` to open Keyboard Shortcuts
2. Search for: `workbench.action.tasks.runTask`
3. Add your preferred shortcut (e.g., `Ctrl+Alt+S`)

### Method 3: Terminal Menu
1. Go to: **Terminal → Run Task...**
2. Select: **"Start All Services"**

## Available Tasks

### Individual Tasks
- **Start Redis (Create if not exists)** - Starts Docker Redis container
- **Start Celery Worker** - Starts the Celery worker for async tasks
- **Start FastAPI Server** - Starts the backend API server (port 8000)
- **Start Frontend Dev Server** - Starts the Vite dev server (port 3000)

### Compound Tasks
- **Start All Services** - Starts all services in parallel
- **Stop All Services** - Stops all running services

## Stopping Services

### Method 1: Task
1. Press `Ctrl+Shift+P`
2. Type: `Tasks: Run Task`
3. Select: **"Stop All Services"**

### Method 2: Manual
- Close the terminal windows
- Or use: `docker stop aethera-redis` for Redis

## Troubleshooting

### Services don't start
- Make sure Docker is running
- Check that Python virtual environment is activated
- Verify Node.js is installed for the frontend

### Port already in use
- Stop the service using that port
- Or change the port in the task configuration

### Tasks not showing up
- Reload VS Code window: `Ctrl+Shift+P` → "Developer: Reload Window"
- Check that `.vscode/tasks.json` exists in the workspace root

## Customization

You can edit `.vscode/tasks.json` to:
- Change ports
- Add environment variables
- Modify command arguments
- Add new tasks

## Benefits

✅ **One-click start** - No more opening 4 terminals manually  
✅ **Organized terminals** - Each service in its own terminal  
✅ **Easy to stop** - Stop all services with one command  
✅ **Integrated** - Works seamlessly with VS Code  
✅ **Cross-platform** - Works on Windows, Mac, and Linux  

