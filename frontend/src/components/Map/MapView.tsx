import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

interface MapViewProps {
  initialCenter?: [number, number]
  initialZoom?: number
  onMapLoad?: (map: maplibregl.Map) => void
  children?: React.ReactNode
}

export default function MapView({
  initialCenter = [10.0, 50.0],
  initialZoom = 6,
  onMapLoad,
  children,
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const resizeObserverRef = useRef<ResizeObserver | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)

  useEffect(() => {
    if (!mapContainer.current || map.current) return

    let mounted = true
    let timeoutId: NodeJS.Timeout | null = null

    const initializeMap = () => {
      if (!mapContainer.current || map.current || !mounted) return

      try {
        const container = mapContainer.current
        if (container.offsetHeight === 0 || container.offsetWidth === 0) {
          console.warn('Map container has no dimensions, retrying...')
          timeoutId = setTimeout(() => {
            if (mounted && container.offsetHeight > 0 && container.offsetWidth > 0 && !map.current) {
              initializeMap()
            }
          }, 100)
          return
        }

        console.log('Initializing map with container size:', {
          width: container.offsetWidth,
          height: container.offsetHeight,
        })

        map.current = new maplibregl.Map({
          container: container,
          style: {
            version: 8,
            sources: {
              'raster-tiles': {
                type: 'raster',
                tiles: [
                  'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                ],
                tileSize: 256,
                attribution:
                  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
              },
            },
            layers: [
              {
                id: 'simple-tiles',
                type: 'raster',
                source: 'raster-tiles',
                minzoom: 0,
                maxzoom: 22,
              },
            ],
          },
          center: initialCenter,
          zoom: initialZoom,
        })

        const handleLoad = () => {
          if (!mounted || !map.current) return
          console.log('Map loaded successfully')
          setMapLoaded(true)
          // Trigger resize to ensure map renders correctly
          if (map.current) {
            map.current.resize()
          }
          if (onMapLoad && map.current) {
            onMapLoad(map.current)
          }
        }

        map.current.on('load', handleLoad)

        map.current.on('error', (e) => {
          console.error('Map error:', e)
        })

        // Also trigger resize when container size changes
        resizeObserverRef.current = new ResizeObserver(() => {
          if (map.current && mounted) {
            map.current.resize()
          }
        })

        if (mapContainer.current) {
          resizeObserverRef.current.observe(mapContainer.current)
        }
      } catch (error) {
        console.error('Failed to initialize map:', error)
      }
    }

    initializeMap()

    return () => {
      mounted = false
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect()
        resizeObserverRef.current = null
      }
      if (map.current) {
        try {
          map.current.remove()
        } catch (e) {
          // Ignore errors during cleanup
        }
        map.current = null
      }
      setMapLoaded(false)
    }
  }, []) // Empty dependency array - only initialize once

  return (
    <div className="relative w-full h-full" style={{ height: '100%', width: '100%', position: 'relative' }}>
      <div 
        ref={mapContainer} 
        className="w-full h-full" 
        style={{ height: '100%', width: '100%' }}
      />
      {mapLoaded && children && (
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
          {children}
        </div>
      )}
    </div>
  )
}

export function useMapInstance() {
  const [mapInstance, setMapInstance] = useState<maplibregl.Map | null>(null)

  const handleMapLoad = (map: maplibregl.Map) => {
    setMapInstance(map)
  }

  return { mapInstance, handleMapLoad }
}

