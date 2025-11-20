import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useAppStore } from '../store/useAppStore'
import * as turf from '@turf/turf'

export default function AoiUpload() {
  const { setAoiGeometry } = useAppStore()

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return

      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string
          const geojson = JSON.parse(text)

          // Validate and extract geometry
          let feature: GeoJSON.Feature | null = null
          
          if (geojson.type === 'Feature') {
            feature = geojson as GeoJSON.Feature
          } else if (geojson.type === 'FeatureCollection' && geojson.features.length > 0) {
            feature = geojson.features[0] as GeoJSON.Feature
          } else if (geojson.type === 'Polygon' || geojson.type === 'MultiPolygon') {
            feature = turf.feature(geojson) as GeoJSON.Feature
          } else {
            throw new Error('Invalid GeoJSON format. Expected Feature, FeatureCollection, or Polygon/MultiPolygon')
          }

          if (feature && feature.geometry) {
            console.log('[AoiUpload] Setting AOI geometry from upload:', feature)
            console.log('[AoiUpload] Geometry type:', feature.geometry.type)
            setAoiGeometry(feature)
            alert('GeoJSON loaded successfully! The AOI should appear on the map.')
          } else {
            throw new Error('No valid geometry found in GeoJSON')
          }
        } catch (err) {
          alert('Failed to parse GeoJSON file: ' + (err instanceof Error ? err.message : 'Unknown error'))
        }
      }
      reader.readAsText(file)
    },
    [setAoiGeometry]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/json': ['.json', '.geojson'],
    },
    multiple: false,
  })

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-primary-500 bg-primary-50'
          : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
      }`}
    >
      <input {...getInputProps()} />
      <div className="space-y-2">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        {isDragActive ? (
          <p className="text-primary-600 font-medium">Drop the GeoJSON file here...</p>
        ) : (
          <>
            <p className="text-gray-600">
              Drag & drop a GeoJSON file here, or click to select
            </p>
            <p className="text-xs text-gray-500">Supports .json and .geojson files</p>
          </>
        )}
      </div>
    </div>
  )
}

