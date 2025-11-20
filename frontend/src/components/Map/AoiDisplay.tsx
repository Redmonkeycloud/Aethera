import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import { useAppStore } from '../../store/useAppStore'

interface AoiDisplayProps {
  map: maplibregl.Map
}

export default function AoiDisplay({ map }: AoiDisplayProps) {
  const { aoiGeometry } = useAppStore()
  const sourceId = 'aoi-display'
  const layerId = 'aoi-display-layer'
  const setupCompleteRef = useRef(false)

  // Set up layers once when map loads
  useEffect(() => {
    if (!map) return

    const setupLayers = () => {
      if (!map || !map.loaded()) {
        console.log('[AoiDisplay] Map not loaded yet')
        return false
      }

      console.log('[AoiDisplay] Setting up layers...')

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
        // Find the best layer to add after (prefer base layers, fallback to simple-tiles)
        let beforeId: string | undefined = 'simple-tiles'
        if (map.getLayer('base-corine-layer')) {
          beforeId = 'base-corine-layer'
        } else if (map.getLayer('base-natura2000-layer')) {
          beforeId = 'base-natura2000-layer'
        }

        console.log('[AoiDisplay] Adding fill layer:', layerId, 'before:', beforeId)
        try {
          map.addLayer({
            id: layerId,
            type: 'fill',
            source: sourceId,
            paint: {
              'fill-color': '#3b82f6',
              'fill-opacity': 0.5, // Increased opacity for better visibility
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
              'line-color': '#2563eb', // Darker blue for better visibility
              'line-width': 3, // Thicker line
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

      setupCompleteRef.current = true
      console.log('[AoiDisplay] Layers setup complete, setupCompleteRef =', setupCompleteRef.current)
      
      // If there's already geometry, update it now
      if (aoiGeometry) {
        console.log('[AoiDisplay] Geometry exists, updating now...')
        const source = map.getSource(sourceId) as maplibregl.GeoJSONSource | null
        if (source) {
          updateGeometry(source, aoiGeometry)
        }
      }
      
      return true
    }

    if (map.loaded()) {
      setupLayers()
    } else {
      const handleLoad = () => {
        setupLayers()
      }
      map.once('load', handleLoad)
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
  }, [map, aoiGeometry])

  // Update source data when AOI geometry changes
  useEffect(() => {
    if (!map) {
      console.log('[AoiDisplay] No map instance')
      return
    }

    // Wait for setup to complete
    const tryUpdate = () => {
      if (!map.loaded()) {
        console.log('[AoiDisplay] Map not loaded yet, retrying in 100ms...')
        setTimeout(tryUpdate, 100)
        return
      }

      if (!setupCompleteRef.current) {
        console.log('[AoiDisplay] Setup not complete, retrying in 100ms...')
        setTimeout(tryUpdate, 100)
        return
      }

      const source = map.getSource(sourceId) as maplibregl.GeoJSONSource | null
      if (!source) {
        console.error('[AoiDisplay] Source not found:', sourceId, '- retrying...')
        setTimeout(tryUpdate, 100)
        return
      }

      console.log('[AoiDisplay] Geometry changed, current aoiGeometry:', aoiGeometry)
      updateGeometry(source, aoiGeometry)
    }

    tryUpdate()
  }, [map, aoiGeometry])

  const updateGeometry = (source: maplibregl.GeoJSONSource, geometry: GeoJSON.Feature | null) => {
    if (!map || !map.loaded()) {
      console.log('[AoiDisplay] updateGeometry: Map not ready')
      return
    }

    try {
      if (geometry) {
        console.log('[AoiDisplay] Updating source with geometry:', geometry)
        console.log('[AoiDisplay] Geometry type:', geometry.geometry?.type)
        console.log('[AoiDisplay] Geometry coordinates:', geometry.geometry?.type === 'Polygon' 
          ? (geometry.geometry as GeoJSON.Polygon).coordinates[0]?.length + ' points'
          : 'N/A')

        // Ensure layers are visible and on top
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, 'visibility', 'visible')
          console.log('[AoiDisplay] Fill layer visibility set to visible')
          // Move layer to top to ensure it's visible
          try {
            const allLayers = map.getStyle().layers || []
            const lastLayer = allLayers[allLayers.length - 1]
            if (lastLayer && lastLayer.id !== layerId) {
              map.moveLayer(layerId, lastLayer.id)
              console.log('[AoiDisplay] Moved fill layer to top')
            }
          } catch (err) {
            console.warn('[AoiDisplay] Could not move layer to top:', err)
          }
        }
        if (map.getLayer(`${layerId}-outline`)) {
          map.setLayoutProperty(`${layerId}-outline`, 'visibility', 'visible')
          console.log('[AoiDisplay] Outline layer visibility set to visible')
          // Move outline layer to top
          try {
            const allLayers = map.getStyle().layers || []
            const lastLayer = allLayers[allLayers.length - 1]
            if (lastLayer && lastLayer.id !== `${layerId}-outline`) {
              map.moveLayer(`${layerId}-outline`, lastLayer.id)
              console.log('[AoiDisplay] Moved outline layer to top')
            }
          } catch (err) {
            console.warn('[AoiDisplay] Could not move outline layer to top:', err)
          }
        }

        source.setData({
          type: 'FeatureCollection',
          features: [geometry],
        })
        console.log('[AoiDisplay] Source data updated successfully')
        console.log('[AoiDisplay] Source features count:', 1)

        // Force a repaint and check layer state
        map.triggerRepaint()
        
        // Verify layers exist and are visible
        const fillLayer = map.getLayer(layerId)
        const outlineLayer = map.getLayer(`${layerId}-outline`)
        console.log('[AoiDisplay] Fill layer exists:', !!fillLayer, 'Visibility:', fillLayer ? map.getLayoutProperty(layerId, 'visibility') : 'N/A')
        console.log('[AoiDisplay] Outline layer exists:', !!outlineLayer, 'Visibility:', outlineLayer ? map.getLayoutProperty(`${layerId}-outline`, 'visibility') : 'N/A')

        // Fit map to AOI bounds
        try {
          const bounds = new maplibregl.LngLatBounds()
          const geom = geometry.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon
          
          let coords: [number, number][] = []
          if (geom.type === 'Polygon') {
            coords = geom.coordinates[0] as [number, number][]
          } else if (geom.type === 'MultiPolygon') {
            coords = geom.coordinates[0][0] as [number, number][]
          }

          if (coords.length > 0) {
            coords.forEach((coord) => {
              bounds.extend(coord as [number, number])
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
      } else {
        console.log('[AoiDisplay] Clearing geometry')
        source.setData({
          type: 'FeatureCollection',
          features: [],
        })
      }
    } catch (err) {
      console.error('[AoiDisplay] Error updating geometry:', err)
    }
  }

  return null
}
