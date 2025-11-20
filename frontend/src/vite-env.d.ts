/// <reference types="vite/client" />

// GeoJSON types
declare namespace GeoJSON {
  interface Geometry {
    type: string
    coordinates: unknown
  }

  interface Feature {
    type: 'Feature'
    geometry: Geometry
    properties?: Record<string, unknown>
  }

  interface FeatureCollection {
    type: 'FeatureCollection'
    features: Feature[]
  }
}
