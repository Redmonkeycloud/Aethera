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

  // Setup layers once when map loads
  useEffect(() => {
    if (!map) return

    const setupLayers = () => {
      if (!map.loaded()) {
        console.log('[AoiDisplay] Map not loaded yet, waiting...')
        return false
      }

      // Add source if it doesn't exist
      if (!map.getSource(sourceId)) {
        console.log('[AoiDisplay] Adding source:', sourceId)
        try {
          map.addSource(sourceId, {
            type: 'geojson',
            data: {
              type: 'FeatureCollection',
              features: [],
            },
          })
          console.log('[AoiDisplay] Source added successfully')
        } catch (err) {
          console.error('[AoiDisplay] Error adding source:', err)
          return false
        }
      }

      // Add layers if they don't exist
      if (!map.getLayer(layerId)) {
        console.log('[AoiDisplay] Adding fill layer:', layerId)
        try {
          // Find insertion point (after base layers, before other layers)
          let beforeId: string | undefined
          const allLayers = map.getStyle().layers || []
          // Try to insert after base layers
          for (const layer of allLayers) {
            if (layer.id === 'simple-tiles' || layer.id.startsWith('base-')) {
              beforeId = layer.id
            }
          }

          map.addLayer({
            id: layerId,
            type: 'fill',
            source: sourceId,
            paint: {
              'fill-color': '#3b82f6', // Blue color
              'fill-opacity': 0.5,
            },
            layout: {
              visibility: 'visible',
            },
          }, beforeId)
          console.log('[AoiDisplay] Fill layer added successfully')
        } catch (err) {
          console.error('[AoiDisplay] Error adding fill layer:', err)
          return false
        }

        console.log('[AoiDisplay] Adding outline layer:', `${layerId}-outline`)
        try {
          map.addLayer({
            id: `${layerId}-outline`,
            type: 'line',
            source: sourceId,
            paint: {
              'line-color': '#2563eb',
              'line-width': 3,
              'line-opacity': 0.8,
            },
            layout: {
              visibility: 'visible',
            },
          }, layerId)
          console.log('[AoiDisplay] Outline layer added successfully')
        } catch (err) {
          console.error('[AoiDisplay] Error adding outline layer:', err)
          return false
        }
      }

      return true
    }

    // Try to setup immediately if map is loaded
    if (map.loaded()) {
      setupLayers()
    } else {
      // Wait for map to load
      const handleLoad = () => {
        setupLayers()
      }
      map.once('load', handleLoad)
      
      // Also try after a delay in case load event already fired
      const timer = setTimeout(() => {
        if (map.loaded()) {
          setupLayers()
        }
      }, 100)

      return () => {
        clearTimeout(timer)
        map.off('load', handleLoad)
      }
    }
  }, [map])

  // Update source data when geometry changes
  useEffect(() => {
    if (!map) return
    
    // If map not loaded, wait for it
    if (!map.loaded()) {
      const handleLoad = () => {
        // Re-run this effect when map loads
        // This will be handled by the dependency array
      }
      map.once('load', handleLoad)
      return () => {
        map.off('load', handleLoad)
      }
    }

    const source = map.getSource(sourceId) as maplibregl.GeoJSONSource | null
    if (!source) {
      // Source not ready yet - first useEffect should set it up
      // Don't do anything here, just wait
      return
    }

    if (aoiGeometry) {
      console.log('[AoiDisplay] Updating geometry')
      const geometry = aoiGeometry.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon
      
      // Validate coordinates
      if (geometry.type === 'Polygon') {
        const coords = geometry.coordinates[0]
        if (coords.length > 0) {
          const [firstLon, firstLat] = coords[0] as [number, number]
          if (firstLon < -180 || firstLon > 180 || firstLat < -90 || firstLat > 90) {
            console.error('[AoiDisplay] INVALID COORDINATES!', { lon: firstLon, lat: firstLat })
            return
          }
          console.log('[AoiDisplay] Valid coordinates, first point:', { lon: firstLon, lat: firstLat })
        }
      }
      
      // Update source data
      source.setData({
        type: 'FeatureCollection',
        features: [aoiGeometry],
      })
      console.log('[AoiDisplay] Source data updated')

      // Fit bounds immediately
      try {
        const bounds = new maplibregl.LngLatBounds()
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
          console.log('[AoiDisplay] Map fitted to bounds')
        }
      } catch (err) {
        console.error('[AoiDisplay] Failed to fit bounds:', err)
      }

      // Trigger repaint
      map.triggerRepaint()
    } else {
      console.log('[AoiDisplay] Clearing geometry')
      source.setData({
        type: 'FeatureCollection',
        features: [],
      })
    }
  }, [map, aoiGeometry, sourceId])

  return null
}

