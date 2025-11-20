import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import * as turf from '@turf/turf'
import { useAppStore } from '../../store/useAppStore'

interface AoiDrawToolProps {
  map: maplibregl.Map
  enabled: boolean
}

export default function AoiDrawTool({ map, enabled }: AoiDrawToolProps) {
  const { setAoiGeometry } = useAppStore()
  const drawModeRef = useRef<'point' | 'polygon' | null>(null)
  const pointsRef = useRef<[number, number][]>([])
  const markerRef = useRef<maplibregl.Marker | null>(null)
  const sourceId = 'aoi-draw'
  const layerId = 'aoi-draw-layer'

  useEffect(() => {
    if (!map) return

    let cleanupFn: (() => void) | null = null

    // Wait for map to be fully loaded before setting up
    const setupDrawing = () => {
      if (!map || !map.loaded()) {
        return () => {} // Return empty cleanup
      }

      // Clean up previous state first
      if (cleanupFn) {
        cleanupFn()
        cleanupFn = null
      }

      if (map.getLayer(layerId)) {
        map.removeLayer(layerId)
      }
      if (map.getLayer(`${layerId}-outline`)) {
        map.removeLayer(`${layerId}-outline`)
      }
      if (map.getSource(sourceId)) {
        map.removeSource(sourceId)
      }
      if (markerRef.current) {
        markerRef.current.remove()
        markerRef.current = null
      }
      pointsRef.current = []
      drawModeRef.current = null

      if (!enabled) {
        // Just cleanup, don't set up drawing
        if (map.getCanvas()) {
          map.getCanvas().style.cursor = 'default'
        }
        return () => {}
      }

      // Add source and layer
      map.addSource(sourceId, {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [],
        },
      })

      // Find the best layer to add before (prefer aoi-display-layer if it exists, otherwise use simple-tiles)
      let beforeId: string | undefined = 'simple-tiles'
      if (map.getLayer('aoi-display-layer')) {
        beforeId = 'aoi-display-layer'
      } else if (map.getLayer('base-corine-layer')) {
        beforeId = 'base-corine-layer'
      } else if (map.getLayer('base-natura2000-layer')) {
        beforeId = 'base-natura2000-layer'
      }

      map.addLayer({
        id: layerId,
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': '#3b82f6',
          'fill-opacity': 0.3,
        },
      }, beforeId) // Add after base layers but before AOI display if it exists

      map.addLayer({
        id: `${layerId}-outline`,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#3b82f6',
          'line-width': 2,
        },
      }, layerId) // Add after fill layer

      // Set cursor
      map.getCanvas().style.cursor = 'crosshair'

      // Disable map dragging when drawing
      map.dragPan.disable()

      const handleClick = (e: maplibregl.MapMouseEvent) => {
        if (!drawModeRef.current) {
          // Start drawing
          drawModeRef.current = 'polygon'
          pointsRef.current = [[e.lngLat.lng, e.lngLat.lat]]
          
          // Add marker for first point
          const el = document.createElement('div')
          el.className = 'w-3 h-3 bg-blue-500 rounded-full border-2 border-white'
          markerRef.current = new maplibregl.Marker(el)
            .setLngLat(e.lngLat)
            .addTo(map)
        } else {
          // Add point
          pointsRef.current.push([e.lngLat.lng, e.lngLat.lat])
          
          // Update polygon
          if (pointsRef.current.length >= 3) {
            const polygon = turf.polygon([[...pointsRef.current, pointsRef.current[0]]])
            const source = map.getSource(sourceId) as maplibregl.GeoJSONSource
            if (source) {
              source.setData({
                type: 'FeatureCollection',
                features: [polygon],
              })
            }
            
            // Save to store
            setAoiGeometry(polygon)
          }
        }
      }

      const handleDblClick = () => {
        // Finish drawing
        if (pointsRef.current.length >= 3) {
          const polygon = turf.polygon([[...pointsRef.current, pointsRef.current[0]]])
          const source = map.getSource(sourceId) as maplibregl.GeoJSONSource
          if (source) {
            source.setData({
              type: 'FeatureCollection',
              features: [polygon],
            })
          }
          setAoiGeometry(polygon)
        }
        drawModeRef.current = null
        pointsRef.current = []
        if (markerRef.current) {
          markerRef.current.remove()
          markerRef.current = null
        }
        map.getCanvas().style.cursor = 'default'
      }

      map.on('click', handleClick)
      map.on('dblclick', handleDblClick)

      // Return cleanup function
      const cleanup = () => {
        map.off('click', handleClick)
        map.off('dblclick', handleDblClick)
        // Re-enable drag pan
        map.dragPan.enable()
        if (map.getCanvas()) {
          map.getCanvas().style.cursor = 'default'
        }
        if (markerRef.current) {
          markerRef.current.remove()
          markerRef.current = null
        }
      }
      cleanupFn = cleanup
      return cleanup
    }

    if (map.loaded()) {
      cleanupFn = setupDrawing()
    } else {
      const onLoad = () => {
        cleanupFn = setupDrawing()
      }
      map.once('load', onLoad)
      // Also try after a short delay in case the event already fired
      const timer = setTimeout(() => {
        if (map.loaded() && !cleanupFn) {
          cleanupFn = setupDrawing()
        }
      }, 100)
      
      return () => {
        clearTimeout(timer)
        map.off('load', onLoad)
        if (cleanupFn) {
          cleanupFn()
          cleanupFn = null
        }
      }
    }

    // Cleanup on unmount or when dependencies change
    return () => {
      if (cleanupFn) {
        cleanupFn()
        cleanupFn = null
      }
    }
  }, [map, enabled, setAoiGeometry])

  return null
}

