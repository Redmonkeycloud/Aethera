import { useEffect, useState } from 'react'
import maplibregl from 'maplibre-gl'
import axios from 'axios'

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
    axios
      .get<Record<string, boolean>>(`${API_BASE_URL}/layers/available`)
      .then((response) => {
        setAvailableLayers(response.data)
      })
      .catch((err) => {
        console.warn('Could not check available layers:', err)
      })
  }, [map])

  // Auto-load available layers
  useEffect(() => {
    if (!map || !map.loaded()) return

    const loadLayer = async (layerName: 'natura2000' | 'corine') => {
      if (loadedLayers.has(layerName)) return

      try {
        const response = await axios.get<GeoJSON.FeatureCollection>(
          `${API_BASE_URL}/layers/${layerName}`,
          {
            responseType: 'json',
          }
        )

        const sourceId = `base-${layerName}`
        const layerId = `base-${layerName}-layer`

        if (!map.getSource(sourceId)) {
          map.addSource(sourceId, {
            type: 'geojson',
            data: response.data,
          })

          // Add fill layer
          map.addLayer({
            id: layerId,
            type: 'fill',
            source: sourceId,
            paint: {
              'fill-color': layerName === 'natura2000' ? '#ef4444' : '#10b981',
              'fill-opacity': layerName === 'natura2000' ? 0.2 : 0.15,
            },
          })

          // Add outline layer
          map.addLayer({
            id: `${layerId}-outline`,
            type: 'line',
            source: sourceId,
            paint: {
              'line-color': layerName === 'natura2000' ? '#dc2626' : '#059669',
              'line-width': layerName === 'natura2000' ? 1.5 : 1,
              'line-opacity': 0.6,
            },
          })

          setLoadedLayers((prev) => new Set(prev).add(layerName))
        }
      } catch (err) {
        console.error(`Failed to load ${layerName} layer:`, err)
      }
    }

    if (availableLayers.natura2000 && !loadedLayers.has('natura2000')) {
      loadLayer('natura2000')
    }
    if (availableLayers.corine && !loadedLayers.has('corine')) {
      loadLayer('corine')
    }
  }, [map, availableLayers, loadedLayers])

  return null
}

