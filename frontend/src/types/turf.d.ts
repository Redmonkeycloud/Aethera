declare module '@turf/turf' {
  import { Feature, FeatureCollection, Polygon } from 'geojson'
  
  export type { Feature, FeatureCollection, Polygon }

  export function area(feature: Feature | FeatureCollection): number
  export function bbox(feature: Feature | FeatureCollection): [number, number, number, number]
  export function buffer(
    feature: Feature | FeatureCollection,
    radius: number,
    options?: { units?: string; steps?: number }
  ): Feature | FeatureCollection
  export function centroid(feature: Feature | FeatureCollection): Feature
  export function intersect(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): Feature | FeatureCollection | null
  export function union(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): Feature | FeatureCollection
  export function difference(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): Feature | FeatureCollection | null
  export function point(coordinates: [number, number], properties?: Record<string, unknown>): Feature
  export function polygon(coordinates: number[][][], properties?: Record<string, unknown>): Feature
  export function feature(geojson: Feature | FeatureCollection | GeoJSON.Geometry | GeoJSON.Feature | GeoJSON.FeatureCollection): Feature
  export function featureCollection(features: Feature[]): FeatureCollection
  export function booleanPointInPolygon(
    point: Feature,
    polygon: Feature | FeatureCollection
  ): boolean
  export function distance(
    from: Feature | [number, number],
    to: Feature | [number, number],
    options?: { units?: string }
  ): number
  export function length(
    feature: Feature | FeatureCollection,
    options?: { units?: string }
  ): number
  export function simplify(
    feature: Feature | FeatureCollection,
    options?: { tolerance?: number; highQuality?: boolean }
  ): Feature | FeatureCollection
  export function transformScale(
    feature: Feature | FeatureCollection,
    factor: number,
    options?: { origin?: [number, number] }
  ): Feature | FeatureCollection
  export function transformRotate(
    feature: Feature | FeatureCollection,
    angle: number,
    options?: { pivot?: [number, number] }
  ): Feature | FeatureCollection
  export function transformTranslate(
    feature: Feature | FeatureCollection,
    distance: number,
    direction: number,
    options?: { units?: string; zTranslation?: number }
  ): Feature | FeatureCollection
  export function circle(
    center: Feature | [number, number],
    radius: number,
    options?: { steps?: number; units?: string; properties?: Record<string, unknown> }
  ): Feature
  export function lineString(
    coordinates: [number, number][],
    properties?: Record<string, unknown>
  ): Feature
  export function bboxPolygon(bbox: [number, number, number, number]): Feature
  export function center(feature: Feature | FeatureCollection): Feature
  export function centerOfMass(feature: Feature | FeatureCollection): Feature
  export function envelope(feature: Feature | FeatureCollection): Feature
  export function extent(feature: Feature | FeatureCollection): [number, number, number, number]
  export function square(bbox: [number, number, number, number]): Feature
  export function rectangle(
    bbox: [number, number, number, number],
    options?: { properties?: Record<string, unknown> }
  ): Feature
  export function combine(featureCollection: FeatureCollection): FeatureCollection
  export function merge(featureCollection: FeatureCollection): Feature
  export function xor(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): Feature | FeatureCollection
  export function bearing(
    start: Feature | [number, number],
    end: Feature | [number, number]
  ): number
  export function destination(
    origin: Feature | [number, number],
    distance: number,
    bearing: number,
    options?: { units?: string }
  ): Feature
  export function midpoint(
    point1: Feature | [number, number],
    point2: Feature | [number, number]
  ): Feature
  export function along(
    line: Feature,
    distance: number,
    options?: { units?: string }
  ): Feature
  export function nearestPoint(
    targetPoint: Feature,
    points: FeatureCollection
  ): Feature
  export function nearestPointOnLine(
    line: Feature,
    point: Feature,
    options?: { units?: string }
  ): Feature
  export function pointOnFeature(feature: Feature | FeatureCollection): Feature
  export function pointsWithinPolygon(
    points: FeatureCollection,
    polygons: Feature | FeatureCollection
  ): FeatureCollection
  export function within(
    points: FeatureCollection,
    polygons: Feature | FeatureCollection
  ): FeatureCollection
  export function contains(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function crosses(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function disjoint(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function equal(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function overlaps(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function touches(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function booleanPointOnLine(
    point: Feature,
    line: Feature,
    options?: { ignoreEndVertices?: boolean }
  ): boolean
  export function booleanWithin(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function booleanOverlap(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function booleanCrosses(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function booleanDisjoint(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function booleanContains(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function booleanTouches(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function booleanEqual(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
  export function booleanIntersects(
    feature1: Feature | FeatureCollection,
    feature2: Feature | FeatureCollection
  ): boolean
}
