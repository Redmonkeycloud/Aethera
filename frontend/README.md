# AETHERA Frontend (Placeholder)

This directory will host the React + TypeScript + MapLibre application for project creation, AOI upload/drawing, scenario management, interactive geospatial visualization, indicator dashboards, and export tools.

Planned stack:
- Vite + React 19 + TypeScript
- MapLibre GL JS + Deck.GL
- Tailwind CSS + Radix UI
- Zustand/Redux Toolkit for state
- TanStack Query for API calls

### Backend endpoints already available
- `GET /projects` / `POST /projects` – manage lightweight project records.
- `GET /runs` – enumerate completed processing runs.
- `GET /runs/{run_id}` – retrieve run metadata plus relative URLs for GeoJSON layers (e.g., `/runs/{run_id}/biodiversity/sensitivity`).
- `GET /runs/{run_id}/biodiversity/{layer}` – download the GeoJSON for `sensitivity`, `natura`, or `overlap`.

The map components should request these endpoints to populate the layer list and fetch the GeoJSON for rendering.

Setup instructions will be added once the frontend scaffold is generated.

