import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { projectsApi, runsApi, type RunSummary } from '../api/client'
import MapView, { useMapInstance } from '../components/Map/MapView'
import AoiDrawTool from '../components/Map/AoiDrawTool'
import AoiDisplay from '../components/Map/AoiDisplay'
import BaseLayers from '../components/Map/BaseLayers'
import LayerControl from '../components/Map/LayerControl'
import AoiUpload from '../components/AoiUpload'
import CoordinateInput from '../components/CoordinateInput'
import ScenarioForm from '../components/ScenarioForm'
import RunStatusPolling from '../components/RunStatusPolling'
import { useAppStore } from '../store/useAppStore'

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { mapInstance, handleMapLoad } = useMapInstance()
  
  // Memoize the map load handler to prevent re-renders
  const memoizedHandleMapLoad = React.useCallback(handleMapLoad, [])
  const { setSelectedProject } = useAppStore()
  const [drawingEnabled, setDrawingEnabled] = useState(false)
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null)
  const [layers, setLayers] = useState<Array<{ id: string; name: string; visible: boolean }>>([])

  const { data: project, isLoading: projectLoading, error: projectError } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
    retry: 1,
    retryDelay: 1000,
  })

  const { data: runs } = useQuery({
    queryKey: ['runs', projectId],
    queryFn: () => runsApi.list().then((runs: RunSummary[]) => runs.filter((r: RunSummary) => r.project_id === projectId)),
    enabled: !!projectId,
  })

  // Update selected project in store when project data changes
  useEffect(() => {
    if (project) {
      setSelectedProject(project)
    }
  }, [project, setSelectedProject])

  // Cleanup: clear selected project when component unmounts or projectId changes
  useEffect(() => {
    return () => {
      setSelectedProject(null)
    }
  }, [projectId, setSelectedProject])

  const handleRunCreated = (taskId: string) => {
    setActiveTaskId(taskId)
  }

  const handleRunComplete = (runId: string) => {
    setActiveTaskId(null)
    navigate(`/runs/${runId}`)
  }

  const handleRunError = (error: string) => {
    alert('Run failed: ' + error)
    setActiveTaskId(null)
  }

  const handleLayerToggle = (layerId: string, visible: boolean) => {
    if (mapInstance) {
      // Toggle the actual map layer
      if (mapInstance.getLayer(layerId)) {
        mapInstance.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none')
      }
      // Also toggle outline layer if it exists
      const outlineLayerId = `${layerId}-outline`
      if (mapInstance.getLayer(outlineLayerId)) {
        mapInstance.setLayoutProperty(outlineLayerId, 'visibility', visible ? 'visible' : 'none')
      }
    }
    // Update state
    setLayers((prev) =>
      prev.map((l) => (l.id === layerId ? { ...l, visible } : l))
    )
  }

  // Dynamically discover layers from the map
  useEffect(() => {
    if (!mapInstance || !mapInstance.loaded()) return

    const discoverLayers = () => {
      const discoveredLayers: Array<{ id: string; name: string; visible: boolean }> = []
      const allLayers = mapInstance.getStyle().layers || []

      // Layer name mapping
      const layerNames: Record<string, string> = {
        'aoi-display-layer': 'AOI',
        'base-natura2000-layer': 'Natura 2000',
        'base-corine-layer': 'CORINE',
      }

      // Discover relevant layers
      for (const layer of allLayers) {
        // Skip base raster layer
        if (layer.id === 'simple-tiles') continue
        
        // Skip outline layers (we'll show them with their parent)
        if (layer.id.endsWith('-outline')) continue

        const name = layerNames[layer.id] || layer.id.replace(/-layer$/, '').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
        const visibility = mapInstance.getLayoutProperty(layer.id, 'visibility') as string
        const visible = visibility !== 'none'

        discoveredLayers.push({
          id: layer.id,
          name,
          visible,
        })
      }

      // Update layers state if changed
      setLayers((prev) => {
        // Check if layers actually changed
        if (prev.length !== discoveredLayers.length) {
          return discoveredLayers
        }
        const prevIds = new Set(prev.map(l => l.id))
        const newIds = new Set(discoveredLayers.map(l => l.id))
        if (prevIds.size !== newIds.size || [...prevIds].some(id => !newIds.has(id))) {
          return discoveredLayers
        }
        return prev
      })
    }

    // Discover layers when map loads
    if (mapInstance.loaded()) {
      discoverLayers()
    } else {
      mapInstance.once('load', discoverLayers)
    }

    // Re-discover when style changes (layers added/removed)
    const handleStyleChange = () => {
      setTimeout(discoverLayers, 100) // Small delay to ensure layers are added
    }
    mapInstance.on('styledata', handleStyleChange)
    
    // Also periodically check for new layers (in case styledata doesn't fire)
    // This is a fallback for async layer additions
    const intervalId = setInterval(() => {
      if (mapInstance.loaded()) {
        discoverLayers()
      }
    }, 2000) // Check every 2 seconds

    return () => {
      mapInstance.off('styledata', handleStyleChange)
      clearInterval(intervalId)
    }
  }, [mapInstance])

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading project...</p>
        </div>
      </div>
    )
  }

  if (projectError) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
            <h1 className="text-2xl font-bold text-red-800 mb-2">Error Loading Project</h1>
            <p className="text-red-600 mb-4">
              {projectError instanceof Error ? projectError.message : 'Failed to connect to the API'}
            </p>
            <p className="text-gray-600 text-sm">
              Make sure the backend API is running at http://localhost:8000
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Project Not Found</h1>
          <p className="text-gray-600">The project you're looking for doesn't exist.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex" style={{ height: 'calc(100vh - 8rem)', minHeight: '500px' }}>
      {/* Left Sidebar */}
      <div className="w-96 bg-gray-50 border-r border-gray-200 overflow-y-auto p-4 space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{project.name}</h1>
          {project.country && (
            <p className="text-sm text-gray-600">Country: {project.country}</p>
          )}
        </div>

        <div className="space-y-4">
          <div>
            <h2 className="font-semibold mb-2">Define Area of Interest (AOI)</h2>
            <div className="space-y-2">
              <button
                onClick={() => setDrawingEnabled(!drawingEnabled)}
                className={`btn w-full ${
                  drawingEnabled ? 'btn-primary' : 'btn-secondary'
                }`}
              >
                {drawingEnabled ? 'Stop Drawing' : 'Start Drawing'}
              </button>
              <div className="text-xs text-gray-500 text-center">or</div>
              <AoiUpload />
              <div className="text-xs text-gray-500 text-center">or</div>
              <CoordinateInput />
            </div>
          </div>

          {activeTaskId ? (
            <RunStatusPolling
              taskId={activeTaskId}
              onComplete={handleRunComplete}
              onError={handleRunError}
            />
          ) : (
            <ScenarioForm projectId={projectId!} onRunCreated={handleRunCreated} />
          )}

          {runs && runs.length > 0 && (
            <div>
              <h2 className="font-semibold mb-2">Previous Runs</h2>
              <div className="space-y-2">
                    {runs.map((run: RunSummary) => (
                  <button
                    key={run.run_id}
                    onClick={() => navigate(`/runs/${run.run_id}`)}
                    className="w-full text-left card hover:shadow-md transition-shadow"
                  >
                    <div className="font-medium">{run.project_type}</div>
                    <div className="text-xs text-gray-500">
                      {new Date(run.created_at).toLocaleDateString()}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Map Area */}
      <div 
        className="flex-1 relative" 
        style={{ 
          height: 'calc(100vh - 8rem)', 
          minHeight: '500px',
          width: '100%',
          position: 'relative'
        }}
      >
        <MapView onMapLoad={memoizedHandleMapLoad} initialCenter={[10.0, 50.0]} initialZoom={6}>
          {mapInstance && (
            <>
              <BaseLayers map={mapInstance} />
              <AoiDisplay map={mapInstance} />
              <AoiDrawTool map={mapInstance} enabled={drawingEnabled} />
              <LayerControl
                map={mapInstance}
                layers={layers}
                onLayerToggle={handleLayerToggle}
              />
            </>
          )}
        </MapView>
      </div>
    </div>
  )
}

