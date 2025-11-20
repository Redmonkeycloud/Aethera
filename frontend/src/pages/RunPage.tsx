import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { runsApi } from '../api/client'
import MapView from '../components/Map/MapView'
import { useMapInstance } from '../components/Map/useMapInstance'
import LayerControl from '../components/Map/LayerControl'
import IndicatorPanel from '../components/IndicatorPanel'
import ResultDownload from '../components/ResultDownload'
import { useAppStore } from '../store/useAppStore'

// GeoJSON type definition - use standard GeoJSON type
type GeoJSONFeatureCollection = GeoJSON.FeatureCollection

export default function RunPage(): React.JSX.Element {
  const { runId } = useParams<{ runId: string }>()
  const { mapInstance, handleMapLoad } = useMapInstance()
  const { setSelectedRun } = useAppStore()
  const [layers, setLayers] = useState<
    Array<{ id: string; name: string; visible: boolean; source?: string }>
  >([])
  const [, setBiodiversityLayers] = useState<
    Record<string, GeoJSONFeatureCollection>
  >({})

  const { data: run, isLoading: runLoading } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => runsApi.get(runId!),
    enabled: !!runId,
  })

  const { data: results } = useQuery<Record<string, unknown>>({
    queryKey: ['run-results', runId],
    queryFn: () => runsApi.getResults(runId!) as Promise<Record<string, unknown>>,
    enabled: !!runId,
  })

  const { data: legal } = useQuery<{
    overall_compliant?: boolean
    critical_violations?: Array<{ rule_name: string }>
  }>({
    queryKey: ['run-legal', runId],
    queryFn: () => runsApi.getLegal(runId!) as Promise<{
      overall_compliant?: boolean
      critical_violations?: Array<{ rule_name: string }>
    }>,
    enabled: !!runId,
    retry: false,
  })

  useEffect(() => {
    if (run) {
      setSelectedRun(run)
    }
  }, [run, setSelectedRun])

  // Load biodiversity layers
  useEffect(() => {
    if (!run || !mapInstance) return

    const loadLayers = async () => {
      const biodiversityLayers = run.outputs?.biodiversity_layers || {}
      const newLayers: typeof layers = []
      const loadedLayers: Record<string, GeoJSONFeatureCollection> = {}

      for (const [layerName] of Object.entries(biodiversityLayers)) {
        try {
          const layerData = await runsApi.getBiodiversityLayer(run.run_id, layerName)
          loadedLayers[layerName] = layerData as GeoJSONFeatureCollection

          const sourceId = `biodiversity-${layerName}`
          const layerId = `biodiversity-${layerName}-layer`

          if (!mapInstance.getSource(sourceId)) {
            mapInstance.addSource(sourceId, {
              type: 'geojson',
              data: layerData,
            })

            mapInstance.addLayer({
              id: layerId,
              type: 'fill',
              source: sourceId,
              paint: {
                'fill-color': layerName === 'sensitivity' ? '#ef4444' : '#3b82f6',
                'fill-opacity': 0.5,
              },
            })

            mapInstance.addLayer({
              id: `${layerId}-outline`,
              type: 'line',
              source: sourceId,
              paint: {
                'line-color': layerName === 'sensitivity' ? '#dc2626' : '#2563eb',
                'line-width': 1,
              },
            })

            newLayers.push({
              id: layerId,
              name: layerName.charAt(0).toUpperCase() + layerName.slice(1),
              visible: true,
            })
          }
        } catch (err) {
          console.error(`Failed to load layer ${layerName}:`, err)
        }
      }

      setLayers(newLayers)
      setBiodiversityLayers(loadedLayers)
    }

    loadLayers()
  }, [run, mapInstance])

  const handleLayerToggle = (layerId: string, visible: boolean) => {
    if (mapInstance) {
      if (mapInstance.getLayer(layerId)) {
        mapInstance.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none')
      }
      if (mapInstance.getLayer(`${layerId}-outline`)) {
        mapInstance.setLayoutProperty(
          `${layerId}-outline`,
          'visibility',
          visible ? 'visible' : 'none'
        )
      }
    }
    setLayers((prev: typeof layers) =>
      prev.map((l: { id: string; name: string; visible: boolean; source?: string }) => 
        l.id === layerId ? { ...l, visible } : l
      )
    )
  }

  if (runLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Run Not Found</h1>
          <p className="text-gray-600">The run you're looking for doesn't exist.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex" style={{ height: 'calc(100vh - 8rem)', minHeight: '500px' }}>
      {/* Left Sidebar */}
      <div className="w-96 bg-gray-50 border-r border-gray-200 overflow-y-auto p-4 space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Run {run.run_id}</h1>
          <div className="text-sm text-gray-600 space-y-1">
            <div>Type: {run.project_type}</div>
            <div>Status: {run.status}</div>
            <div>Created: {new Date(run.created_at).toLocaleString()}</div>
          </div>
        </div>

        <IndicatorPanel run={run} results={results} />

        {legal && (
          <div className="card">
            <h3 className="font-semibold mb-2">Legal Compliance</h3>
            <div className="space-y-2">
              <div
                className={`px-3 py-2 rounded ${
                  legal.overall_compliant
                    ? 'bg-green-50 text-green-800'
                    : 'bg-red-50 text-red-800'
                }`}
              >
                {legal.overall_compliant ? '✓ Compliant' : '✗ Non-compliant'}
              </div>
              {legal.critical_violations && legal.critical_violations.length > 0 && (
                <div className="text-sm">
                  <div className="font-medium text-red-700">Critical Violations:</div>
                  <ul className="list-disc list-inside text-red-600">
                    {legal.critical_violations.map((v, i) => (
                      <li key={i}>{v.rule_name}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        <ResultDownload runId={run.run_id} />
      </div>

      {/* Map Area */}
      <div className="flex-1 relative" style={{ height: '100%', minHeight: '500px' }}>
        <MapView onMapLoad={handleMapLoad} initialCenter={[10.0, 50.0]} initialZoom={6}>
          {mapInstance && (
            <LayerControl
              map={mapInstance}
              layers={layers}
              onLayerToggle={handleLayerToggle}
            />
          )}
        </MapView>
      </div>
    </div>
  )
}

