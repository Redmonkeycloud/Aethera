/// <reference types="vite/client" />

// GeoJSON types
declare namespace GeoJSON {
  interface Geometry {
    type: string
    coordinates: unknown
  }

  interface Polygon {
    type: 'Polygon'
    coordinates: [number, number][][]
  }

  interface MultiPolygon {
    type: 'MultiPolygon'
    coordinates: [number, number][][][]
  }

  interface Feature {
    type: 'Feature'
    geometry: Geometry | Polygon | MultiPolygon
    properties?: Record<string, unknown>
  }

  interface FeatureCollection {
    type: 'FeatureCollection'
    features: Feature[]
  }
}
