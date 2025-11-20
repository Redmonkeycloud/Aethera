import { useState } from 'react'
import maplibregl from 'maplibre-gl'

interface Layer {
  id: string
  name: string
  visible: boolean
  source?: string
}

interface LayerControlProps {
  map: maplibregl.Map
  layers: Layer[]
  onLayerToggle: (layerId: string, visible: boolean) => void
}

export default function LayerControl({ map, layers, onLayerToggle }: LayerControlProps) {
  const [isOpen, setIsOpen] = useState(true)

  const handleToggle = (layerId: string, visible: boolean) => {
    if (map.getLayer(layerId)) {
      map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none')
    }
    onLayerToggle(layerId, visible)
  }

  return (
    <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-4 min-w-[200px]">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-gray-800">Layers</h3>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-gray-500 hover:text-gray-700"
        >
          {isOpen ? '−' : '+'}
        </button>
      </div>
      {isOpen && (
        <div className="space-y-2">
          {layers.map((layer) => (
            <label key={layer.id} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={layer.visible}
                onChange={(e) => handleToggle(layer.id, e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">{layer.name}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  )
}

