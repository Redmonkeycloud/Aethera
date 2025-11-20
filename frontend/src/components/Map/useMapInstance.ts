import { useState } from 'react'
import type { Map } from 'maplibre-gl'

export function useMapInstance() {
  const [mapInstance, setMapInstance] = useState<Map | null>(null)

  const handleMapLoad = (map: Map) => {
    setMapInstance(map)
  }

  return { mapInstance, handleMapLoad }
}

