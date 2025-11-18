import { useEffect } from 'react'
import maplibregl from 'maplibre-gl'
import { useAppStore } from '../../store/useAppStore'

interface AoiDisplayProps {
  map: maplibregl.Map
}

export default function AoiDisplay({ map }: AoiDisplayProps) {
  const { aoiGeometry } = useAppStore()
  const sourceId = 'aoi-display'
  const layerId = 'aoi-display-layer'

  useEffect(() => {
    if (!map) return

    // Wait for map to be fully loaded
    const setupLayers = () => {
      if (!map || !map.loaded()) {
        return
      }

      // Add source and layer if they don't exist
      if (!map.getSource(sourceId)) {
        map.addSource(sourceId, {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: [],
          },
        })
      }

      if (!map.getLayer(layerId)) {
        map.addLayer({
          id: layerId,
          type: 'fill',
          source: sourceId,
          paint: {
            'fill-color': '#3b82f6',
            'fill-opacity': 0.3,
          },
        })

        map.addLayer({
          id: `${layerId}-outline`,
          type: 'line',
          source: sourceId,
          paint: {
            'line-color': '#3b82f6',
            'line-width': 2,
          },
        })
      }

      // Update source data when AOI geometry changes
      const source = map.getSource(sourceId) as maplibregl.GeoJSONSource
      if (aoiGeometry) {
        source.setData({
          type: 'FeatureCollection',
          features: [aoiGeometry],
        })

        // Fit map to AOI bounds
        try {
          const bounds = new maplibregl.LngLatBounds()
          const geometry = aoiGeometry.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon
          
          let coords: [number, number][] = []
          if (geometry.type === 'Polygon') {
            coords = geometry.coordinates[0] as [number, number][]
          } else if (geometry.type === 'MultiPolygon') {
            coords = geometry.coordinates[0][0] as [number, number][]
          }

          if (coords.length > 0) {
            coords.forEach((coord) => {
              bounds.extend(coord)
            })
            map.fitBounds(bounds, {
              padding: 50,
              maxZoom: 12,
            })
          }
        } catch (err) {
          console.error('Failed to fit bounds:', err)
        }
      } else {
        source.setData({
          type: 'FeatureCollection',
          features: [],
        })
      }
    }

    if (map.loaded()) {
      setupLayers()
    } else {
      map.once('load', setupLayers)
      // Also try after a short delay in case the event already fired
      const timer = setTimeout(() => {
        if (map.loaded()) {
          setupLayers()
        }
      }, 100)
      return () => {
        clearTimeout(timer)
        map.off('load', setupLayers)
      }
    }
  }, [map, aoiGeometry])

  return null
}

