import { create } from 'zustand'
import { Project, RunDetail } from '../api/client'

interface AppState {
  selectedProject: Project | null
  selectedRun: RunDetail | null
  aoiGeometry: GeoJSON.Feature | null
  setSelectedProject: (project: Project | null) => void
  setSelectedRun: (run: RunDetail | null) => void
  setAoiGeometry: (geometry: GeoJSON.Feature | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  selectedProject: null,
  selectedRun: null,
  aoiGeometry: null,
  setSelectedProject: (project) => set({ selectedProject: project }),
  setSelectedRun: (run) => set({ selectedRun: run }),
  setAoiGeometry: (geometry) => set({ aoiGeometry: geometry }),
}))

