import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { projectsApi, runsApi, type RunSummary } from '../api/client'
import MapView from '../components/Map/MapView'
import { useMapInstance } from '../components/Map/useMapInstance'
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
  const memoizedHandleMapLoad = React.useCallback(handleMapLoad, [handleMapLoad])
  const { setSelectedProject } = useAppStore()
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null)
  const [layers, setLayers] = useState<Array<{ id: string; name: string; visible: boolean }>>([
    { id: 'aoi-display-layer', name: 'AOI', visible: true },
  ])

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

  // Discover layers from map
  useEffect(() => {
    if (!mapInstance || !mapInstance.loaded()) return

    const discoverLayers = () => {
      const discoveredLayers: Array<{ id: string; name: string; visible: boolean }> = []
      
      // Layer name mapping
      const layerNames: Record<string, string> = {
        'aoi-display-layer': 'AOI',
        'base-natura2000-layer': 'Natura 2000',
        'base-corine-layer': 'CORINE Land Cover',
      }

      // Check for known layers
      const knownLayerIds = [
        'aoi-display-layer',
        'base-natura2000-layer',
        'base-corine-layer',
      ]

      knownLayerIds.forEach((layerId) => {
        const layer = mapInstance.getLayer(layerId)
        if (layer) {
          const visibility = mapInstance.getLayoutProperty(layerId, 'visibility') as string
          discoveredLayers.push({
            id: layerId,
            name: layerNames[layerId] || layerId,
            visible: visibility !== 'none',
          })
          console.log(`Discovered layer: ${layerId} (${layerNames[layerId] || layerId})`)
        }
      })

      // Debug: log all layers on the map
      const allLayers = mapInstance.getStyle()?.layers || []
      console.log('All layers on map:', allLayers.map((l: { id: string }) => l.id))

      // Always update layers state (even if empty, to show AOI at minimum)
      setLayers(discoveredLayers.length > 0 ? discoveredLayers : [
        { id: 'aoi-display-layer', name: 'AOI', visible: true }
      ])
    }

    // Discover layers immediately
    discoverLayers()

    // Discover layers after delays to catch layers loaded asynchronously
    const timer1 = setTimeout(discoverLayers, 500)
    const timer2 = setTimeout(discoverLayers, 1500)
    const timer3 = setTimeout(discoverLayers, 3000)
    
    // Also discover when map style/data loads
    const handleStyleData = () => discoverLayers()
    const handleData = () => discoverLayers()
    
    mapInstance.on('styledata', handleStyleData)
    mapInstance.on('data', handleData)

    return () => {
      clearTimeout(timer1)
      clearTimeout(timer2)
      clearTimeout(timer3)
      mapInstance.off('styledata', handleStyleData)
      mapInstance.off('data', handleData)
    }
  }, [mapInstance])

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
    setLayers((prev: typeof layers) =>
      prev.map((l: typeof layers[0]) => (l.id === layerId ? { ...l, visible } : l))
    )
  }

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

