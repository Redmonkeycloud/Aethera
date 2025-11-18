# Frontend Setup Guide

## Prerequisites

The frontend requires **Node.js 18+** and **npm** (or pnpm/yarn) to be installed.

## Installing Node.js

### Option 1: Official Installer (Recommended)

1. **Download Node.js**:
   - Visit: https://nodejs.org/
   - Download the **LTS version** (Long Term Support)
   - Choose the Windows Installer (.msi) for your system (64-bit recommended)

2. **Install Node.js**:
   - Run the downloaded installer
   - Follow the installation wizard
   - **Important**: Make sure to check "Add to PATH" option during installation
   - Complete the installation

3. **Verify Installation**:
   ```powershell
   node --version
   npm --version
   ```
   Both commands should show version numbers (e.g., `v20.10.0` and `10.2.3`)

### Option 2: Using Chocolatey (If you have it)

```powershell
choco install nodejs-lts
```

### Option 3: Using Winget (Windows Package Manager)

```powershell
winget install OpenJS.NodeJS.LTS
```

## After Installation

1. **Close and reopen your terminal** (PowerShell/Command Prompt)
   - This ensures PATH changes are loaded

2. **Verify installation**:
   ```powershell
   node --version
   npm --version
   ```

3. **Navigate to frontend directory**:
   ```powershell
   cd D:\Aethera_original\frontend
   ```

4. **Install dependencies**:
   ```powershell
   npm install
   ```

5. **Start development server**:
   ```powershell
   npm run dev
   ```

## Troubleshooting

### "npm is not recognized" after installation

1. **Restart your terminal** - Close and reopen PowerShell/Command Prompt
2. **Check PATH**:
   ```powershell
   $env:PATH -split ';' | Select-String node
   ```
   Should show Node.js installation path

3. **Manually add to PATH** (if needed):
   - Open System Properties → Environment Variables
   - Add Node.js installation path (usually `C:\Program Files\nodejs\`) to PATH
   - Restart terminal

### Alternative Package Managers

If npm doesn't work, you can use:

**pnpm** (faster, more efficient):
```powershell
npm install -g pnpm
pnpm install
pnpm dev
```

**yarn**:
```powershell
npm install -g yarn
yarn install
yarn dev
```

## Next Steps

Once Node.js is installed and dependencies are installed:

1. **Create `.env` file** in `frontend/` directory:
   ```
   VITE_API_URL=http://localhost:8000
   ```

2. **Start backend services** (in separate terminals):
   ```powershell
   # Terminal 1: Redis
   redis-server

   # Terminal 2: Celery
   celery -A backend.src.workers.celery_app worker --loglevel=info

   # Terminal 3: FastAPI
   uvicorn backend.src.api.app:app --reload
   ```

3. **Start frontend**:
   ```powershell
   cd frontend
   npm run dev
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## System Requirements

- **Node.js**: 18.0.0 or higher
- **npm**: 9.0.0 or higher (comes with Node.js)
- **Windows**: 10 or later
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: ~500MB for node_modules

## Quick Reference

```powershell
# Check Node.js version
node --version

# Check npm version
npm --version

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

