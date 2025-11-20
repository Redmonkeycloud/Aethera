# AETHERA Frontend

React + TypeScript + MapLibre frontend application for the AETHERA Environmental Impact Assessment platform.

## Features

- ✅ React 18 + TypeScript + Vite
- ✅ MapLibre GL JS for interactive maps
- ✅ AOI upload and drawing tools
- ✅ Scenario form for analysis configuration
- ✅ Layer controls for map visualization
- ✅ Indicator panels for results display
- ✅ Run status polling
- ✅ Result download (ZIP export)
- ✅ Legal compliance display

## Setup

### Prerequisites

- **Node.js 18+** and npm/pnpm/yarn
  - Download from: https://nodejs.org/ (LTS version recommended)
  - See `SETUP.md` for detailed installation instructions
- Backend API running on `http://localhost:8000`

### Installation

**First time setup**:
1. Install Node.js from https://nodejs.org/ if not already installed
2. Close and reopen your terminal after installation
3. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

**Install dependencies**:
```bash
# Install dependencies
npm install
# or
pnpm install
# or
yarn install
```

> **Note**: If you get "npm is not recognized", Node.js is not installed or not in PATH. See `SETUP.md` for troubleshooting.

### Development

```bash
# Start development server
npm run dev
# or
pnpm dev
# or
yarn dev
```

The application will be available at `http://localhost:3000`

### Build

```bash
# Build for production
npm run build
# or
pnpm build
# or
yarn build
```

### Preview Production Build

```bash
npm run preview
# or
pnpm preview
# or
yarn preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client and types
│   ├── components/    # React components
│   │   ├── Map/       # Map-related components
│   ├── pages/         # Page components
│   ├── store/         # State management (Zustand)
│   ├── App.tsx        # Main app component
│   ├── main.tsx       # Entry point
│   └── index.css      # Global styles
├── public/            # Static assets
├── index.html         # HTML template
├── package.json       # Dependencies
├── tsconfig.json      # TypeScript config
├── vite.config.ts     # Vite config
└── tailwind.config.js # Tailwind CSS config
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

## Usage

1. **Create a Project**: Navigate to the home page and create a new project
2. **Define AOI**: Upload a GeoJSON file or draw an area of interest on the map
3. **Configure Scenario**: Fill out the scenario form (project type, country)
4. **Start Analysis**: Submit the form to queue an analysis run
5. **Monitor Progress**: Watch the run status polling component
6. **View Results**: Once complete, view indicators and map layers
7. **Download**: Export complete results as a ZIP file

## Backend Integration

The frontend communicates with the backend API via:

- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /projects/{id}` - Get project details
- `POST /projects/{id}/runs` - Create analysis run
- `GET /runs/{id}` - Get run details
- `GET /runs/{id}/results` - Get comprehensive results
- `GET /runs/{id}/legal` - Get legal compliance results
- `GET /runs/{id}/export` - Download run package
- `GET /tasks/{task_id}` - Get task status
- `GET /runs/{id}/biodiversity/{layer}` - Get biodiversity GeoJSON layers

## Technologies

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **MapLibre GL JS** - Map rendering
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **React Query** - Data fetching and caching
- **React Router** - Routing
- **Axios** - HTTP client
- **@turf/turf** - Geospatial utilities
- **react-dropzone** - File upload
- **date-fns** - Date formatting

## Development Notes

- The map uses OpenStreetMap tiles by default
- AOI drawing supports polygon creation via click/double-click
- Layer visibility can be toggled via the layer control panel
- Run status is polled every 2 seconds until completion
- All API calls are cached using React Query
