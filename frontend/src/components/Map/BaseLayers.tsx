import { useEffect, useState } from 'react'
import maplibregl from 'maplibre-gl'
import axios from 'axios'
import bbox from '@turf/bbox'

interface BaseLayersProps {
  map: maplibregl.Map
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function BaseLayers({ map }: BaseLayersProps) {
  const [availableLayers, setAvailableLayers] = useState<Record<string, boolean>>({})
  const [loadedLayers, setLoadedLayers] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (!map || !map.loaded()) return

    // Check which layers are available
    console.log('[BaseLayers] Checking available layers...')
    axios
      .get<Record<string, boolean>>(`${API_BASE_URL}/layers/available`)
      .then((response: { data: Record<string, boolean> }) => {
        console.log('[BaseLayers] Available layers:', response.data)
        setAvailableLayers(response.data)
      })
      .catch((err: unknown) => {
        console.error('[BaseLayers] Could not check available layers:', err)
        if (axios.isAxiosError(err)) {
          console.error('[BaseLayers] Error details:', {
            status: err.response?.status,
            statusText: err.response?.statusText,
            data: err.response?.data,
            url: err.config?.url,
          })
        }
      })
  }, [map])

  // Auto-load available layers
  useEffect(() => {
    if (!map || !map.loaded()) return
    if (Object.keys(availableLayers).length === 0) return // Wait for availability check

    const loadLayer = async (layerName: 'natura2000' | 'corine') => {
      const sourceId = `base-${layerName}`
      if (map.getSource(sourceId)) {
        console.log(`[BaseLayers] ${layerName} already loaded`)
        return
      }
      if (loadedLayers.has(layerName)) {
        console.log(`[BaseLayers] ${layerName} already in loaded set`)
        return
      }

      try {
        console.log(`[BaseLayers] Loading ${layerName} from ${API_BASE_URL}/layers/${layerName}`)
        const response = await axios.get<GeoJSON.FeatureCollection>(
          `${API_BASE_URL}/layers/${layerName}`,
          {
            responseType: 'json',
          }
        )

        // Validate GeoJSON structure
        if (!response.data || response.data.type !== 'FeatureCollection') {
          console.error(`[BaseLayers] Invalid GeoJSON structure for ${layerName}:`, response.data)
          return
        }

        const features = response.data.features || []
        console.log(`[BaseLayers] ${layerName} loaded: ${features.length} features`)

        if (features.length === 0) {
          console.warn(`[BaseLayers] ${layerName} has no features, skipping layer creation`)
          return
        }

        // Log sample coordinates for debugging
        if (features.length > 0 && features[0].geometry) {
          const firstGeom = features[0].geometry
          if (firstGeom.type === 'Polygon' && firstGeom.coordinates[0]?.[0]) {
            const [lon, lat] = firstGeom.coordinates[0][0] as [number, number]
            console.log(`[BaseLayers] ${layerName} sample coordinates: lon=${lon.toFixed(6)}, lat=${lat.toFixed(6)}`)
            
            // Validate coordinate range
            if (lon < -180 || lon > 180 || lat < -90 || lat > 90) {
              console.error(`[BaseLayers] ${layerName} has invalid coordinates! lon=${lon}, lat=${lat}`)
              return
            }
          }
        }

        const layerId = `base-${layerName}-layer`

        if (!map.getSource(sourceId)) {
          console.log(`[BaseLayers] Adding source: ${sourceId}`)
          map.addSource(sourceId, {
            type: 'geojson',
            data: response.data,
          })

          // Wait for source to be ready
          map.once('sourcedata', () => {
            console.log(`[BaseLayers] Source data loaded for ${sourceId}`)
          })

          // Add fill layer with higher visibility
          console.log(`[BaseLayers] Adding fill layer: ${layerId}`)
          map.addLayer({
            id: layerId,
            type: 'fill',
            source: sourceId,
            paint: {
              'fill-color': layerName === 'natura2000' ? '#ef4444' : '#10b981',
              'fill-opacity': layerName === 'natura2000' ? 0.4 : 0.3, // Increased from 0.2/0.15
            },
            layout: {
              visibility: 'visible',
            },
          })

          // Add outline layer with better visibility
          console.log(`[BaseLayers] Adding outline layer: ${layerId}-outline`)
          map.addLayer({
            id: `${layerId}-outline`,
            type: 'line',
            source: sourceId,
            paint: {
              'line-color': layerName === 'natura2000' ? '#dc2626' : '#059669',
              'line-width': layerName === 'natura2000' ? 2 : 1.5, // Increased from 1.5/1
              'line-opacity': 0.8, // Increased from 0.6
            },
            layout: {
              visibility: 'visible',
            },
          })

          // Move layers to top to ensure visibility
          try {
            const allLayers = map.getStyle().layers || []
            const lastLayer = allLayers[allLayers.length - 1]
            if (lastLayer && lastLayer.id !== layerId) {
              map.moveLayer(layerId, lastLayer.id)
              map.moveLayer(`${layerId}-outline`, lastLayer.id)
              console.log(`[BaseLayers] Moved ${layerName} layers to top`)
            }
          } catch (err) {
            console.warn(`[BaseLayers] Could not move layers to top:`, err)
          }

          // Fit map to layer bounds
          try {
            const bounds = bbox(response.data) as [number, number, number, number]
            if (bounds && bounds.length === 4) {
              map.fitBounds(
                [
                  [bounds[0], bounds[1]],
                  [bounds[2], bounds[3]],
                ] as [[number, number], [number, number]],
                {
                  padding: 50,
                  maxZoom: 10,
                }
              )
              console.log(`[BaseLayers] Fitted map to ${layerName} bounds:`, bounds)
            }
          } catch (err) {
            console.warn(`[BaseLayers] Could not fit bounds for ${layerName}:`, err)
          }

          setLoadedLayers((prev) => {
            const newSet = new Set(prev)
            newSet.add(layerName)
            return newSet
          })

          console.log(`[BaseLayers] Successfully loaded ${layerName} layer`)
        }
      } catch (err) {
        console.error(`[BaseLayers] Failed to load ${layerName} layer:`, err)
        if (axios.isAxiosError(err)) {
          console.error(`[BaseLayers] ${layerName} error details:`, {
            status: err.response?.status,
            statusText: err.response?.statusText,
            data: err.response?.data,
            url: err.config?.url,
            message: err.message,
          })
        }
      }
    }

    if (availableLayers.natura2000 && !loadedLayers.has('natura2000')) {
      console.log('[BaseLayers] Triggering natura2000 load')
      void loadLayer('natura2000')
    }
    if (availableLayers.corine && !loadedLayers.has('corine')) {
      console.log('[BaseLayers] Triggering corine load')
      void loadLayer('corine')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, availableLayers])

  return null
}

