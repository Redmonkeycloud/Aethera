import { useState } from 'react'
import * as turf from '@turf/turf'
import { useAppStore } from '../store/useAppStore'

interface CoordinateInputProps {
  onSuccess?: () => void
}

export default function CoordinateInput({ onSuccess }: CoordinateInputProps) {
  const { setAoiGeometry } = useAppStore()
  const [coordinates, setCoordinates] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [inputMode, setInputMode] = useState<'bbox' | 'polygon'>('bbox')

  const parseCoordinates = (input: string): number[][] | null => {
    try {
      // Remove extra whitespace and split by lines or commas
      const cleaned = input.trim().replace(/\s+/g, ' ')
      const parts = cleaned.split(/[,\n]/).map((p) => p.trim()).filter(Boolean)

      if (parts.length === 0) return null

      const coords: number[][] = []
      for (const part of parts) {
        const pair = part.split(/\s+/).map(Number)
        if (pair.length !== 2 || isNaN(pair[0]) || isNaN(pair[1])) {
          return null
        }
        // Validate longitude (-180 to 180) and latitude (-90 to 90)
        if (pair[0] < -180 || pair[0] > 180 || pair[1] < -90 || pair[1] > 90) {
          return null
        }
        coords.push([pair[0], pair[1]]) // [lng, lat]
      }

      return coords.length >= 3 ? coords : null
    } catch {
      return null
    }
  }

  const handleSubmit = () => {
    setError(null)

    if (!coordinates.trim()) {
      setError('Please enter coordinates')
      return
    }

    const coords = parseCoordinates(coordinates)
    if (!coords) {
      setError('Invalid coordinates. Format: longitude latitude (one per line or comma-separated)')
      return
    }

    try {
      let polygon: turf.Feature<turf.Polygon>

      if (inputMode === 'bbox' && coords.length === 4) {
        // Create bounding box from 4 coordinates
        const [minLng, maxLng] = [Math.min(...coords.map((c) => c[0])), Math.max(...coords.map((c) => c[0]))]
        const [minLat, maxLat] = [Math.min(...coords.map((c) => c[1])), Math.max(...coords.map((c) => c[1]))]
        polygon = turf.bboxPolygon([minLng, minLat, maxLng, maxLat])
      } else if (inputMode === 'polygon' && coords.length >= 3) {
        // Create polygon from coordinates
        // Close the polygon if not already closed
        const closedCoords = coords[0][0] === coords[coords.length - 1][0] &&
          coords[0][1] === coords[coords.length - 1][1]
          ? coords
          : [...coords, coords[0]]
        polygon = turf.polygon([closedCoords])
      } else {
        setError(
          inputMode === 'bbox'
            ? 'Bounding box requires exactly 4 coordinates'
            : 'Polygon requires at least 3 coordinates'
        )
        return
      }

      // Convert to GeoJSON Feature
      const feature: GeoJSON.Feature<GeoJSON.Polygon> = {
        type: 'Feature',
        geometry: polygon.geometry,
        properties: {},
      }

      setAoiGeometry(feature)
      setError(null)
      if (onSuccess) {
        onSuccess()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create polygon')
    }
  }

  return (
    <div className="card space-y-3">
      <div>
        <h3 className="font-semibold mb-2">Enter Coordinates</h3>
        <div className="flex space-x-2 mb-2">
          <button
            type="button"
            onClick={() => setInputMode('bbox')}
            className={`text-xs px-2 py-1 rounded ${
              inputMode === 'bbox'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Bounding Box
          </button>
          <button
            type="button"
            onClick={() => setInputMode('polygon')}
            className={`text-xs px-2 py-1 rounded ${
              inputMode === 'polygon'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Polygon
          </button>
        </div>
      </div>

      <div>
        <label className="block text-xs text-gray-600 mb-1">
          {inputMode === 'bbox'
            ? 'Enter 4 coordinates (one per line): longitude latitude'
            : 'Enter coordinates (one per line, min 3): longitude latitude'}
        </label>
        <textarea
          value={coordinates}
          onChange={(e) => setCoordinates(e.target.value)}
          placeholder={
            inputMode === 'bbox'
              ? '10.0 50.0\n11.0 50.0\n11.0 51.0\n10.0 51.0'
              : '10.0 50.0\n11.0 50.0\n11.0 51.0\n10.0 51.0'
          }
          className="input text-sm font-mono"
          rows={4}
        />
        <p className="text-xs text-gray-500 mt-1">
          Format: longitude latitude (WGS84, decimal degrees)
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
          {error}
        </div>
      )}

      <button
        type="button"
        onClick={handleSubmit}
        className="btn btn-primary w-full text-sm"
      >
        Set AOI from Coordinates
      </button>
    </div>
  )
}

