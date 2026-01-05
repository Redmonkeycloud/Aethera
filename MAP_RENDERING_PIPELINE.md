# Map Rendering Pipeline - Complete Flow

## Overview
This document traces the exact pipeline for displaying GeoJSON files on the map and in the layer control.

---

## 1. GeoJSON Upload Pipeline

### Entry Point: `AoiUpload.tsx`
```
User drops/uploads file
  ↓
onDrop callback (line 9-37)
  ↓
FileReader.readAsText(file) (line 34)
  ↓
JSON.parse(text) (line 18)
  ↓
Validate GeoJSON format (lines 21-29):
  - If Feature → use directly
  - If FeatureCollection → use first feature
  - If Polygon/MultiPolygon → convert with turf.feature()
  ↓
setAoiGeometry(geojson) (lines 22, 24, 26)
```

### State Management: `store/useAppStore.ts`
```
setAoiGeometry(geometry) called (line 19)
  ↓
Zustand store updates aoiGeometry state (line 16)
  ↓
All components subscribed to aoiGeometry re-render
```

---

## 2. Map Display Pipeline

### Component Hierarchy: `ProjectPage.tsx` (lines 190-203)
```
<MapView>
  ↓
  {mapInstance && (
    <>
      <BaseLayers map={mapInstance} />      // CORINE/Natura layers
      <AoiDisplay map={mapInstance} />      // AOI GeoJSON display
      <AoiDrawTool map={mapInstance} />     // Drawing tool
      <LayerControl map={mapInstance} />    // Layer visibility control
    </>
  )}
</MapView>
```

### Map Initialization: `MapView.tsx`
```
useEffect (line 23)
  ↓
Creates MapLibre map instance (line 49)
  ↓
Sets up base style with 'simple-tiles' raster layer (lines 51-73)
  ↓
Map 'load' event fires (line 91)
  ↓
onMapLoad callback → useMapInstance hook (line 86-87)
  ↓
mapInstance state set in ProjectPage (line 19)
  ↓
Child components receive mapInstance prop
```

### AOI Display: `AoiDisplay.tsx`
```
Component mounts with map prop
  ↓
useEffect watches [map, aoiGeometry] (line 14)
  ↓
setupLayers() function (line 18):
  
  Step 1: Wait for map.loaded() (line 19)
  
  Step 2: Add source 'aoi-display' if not exists (lines 24-31)
    - Type: 'geojson'
    - Initial data: empty FeatureCollection
  
  Step 3: Add layers if not exists (lines 34-53):
    - Layer 'aoi-display-layer' (fill, red #ff0000, opacity 0.7)
    - Layer 'aoi-display-layer-outline' (line, black #000000, width 4)
  
  Step 4: Update source data if aoiGeometry exists (lines 56-93):
    - source.setData({ type: 'FeatureCollection', features: [aoiGeometry] })
    - Calculate bounds from coordinates
    - map.fitBounds(bounds)
    - Force visibility and move layers to top
```

**CRITICAL ISSUE FOUND:**
- `AoiDisplay` creates layers: `'aoi-display-layer'` and `'aoi-display-layer-outline'`
- But `ProjectPage` hardcodes layer list with: `'aoi-draw-layer'` (line 27)
- **MISMATCH**: LayerControl tries to toggle `'aoi-draw-layer'` which doesn't exist!

---

## 3. Layer Control Pipeline

### Layer State: `ProjectPage.tsx` (lines 26-28)
```
const [layers, setLayers] = useState([
  { id: 'aoi-draw-layer', name: 'AOI', visible: true },  // ❌ WRONG ID!
])
```

### Layer Control: `LayerControl.tsx`
```
Receives layers prop from ProjectPage (line 17)
  ↓
Renders checkbox for each layer (lines 40-49)
  ↓
handleToggle called on checkbox change (line 20)
  ↓
map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none') (line 22)
  ↓
onLayerToggle callback updates ProjectPage state (line 24)
```

**PROBLEM:**
- LayerControl tries to toggle `'aoi-draw-layer'`
- But AoiDisplay creates `'aoi-display-layer'`
- So the toggle does nothing!

---

## 4. Base Layers Pipeline (CORINE/Natura)

### BaseLayers Component: `BaseLayers.tsx`
```
Component mounts with map prop
  ↓
useEffect 1: Check available layers (lines 15-27)
  - GET /layers/available
  - Sets availableLayers state
  
useEffect 2: Auto-load layers (lines 30-99)
  - Watches availableLayers
  - For each available layer (natura2000, corine):
    - GET /layers/{layerName}
    - Add source 'base-{layerName}'
    - Add fill layer 'base-{layerName}-layer'
    - Add outline layer 'base-{layerName}-layer-outline'
    - Fit map to bounds
```

---

## Root Causes of "Nothing Showing" Issue

### Issue #1: Layer ID Mismatch
- **AoiDisplay** creates: `'aoi-display-layer'`
- **ProjectPage** expects: `'aoi-draw-layer'`
- **Result**: LayerControl can't find the layer to toggle

### Issue #2: Layer Discovery Not Dynamic
- `ProjectPage` hardcodes layer list
- Should discover layers from map dynamically
- BaseLayers layers are never added to LayerControl

### Issue #3: Timing Issues
- `AoiDisplay` useEffect runs when `map` and `aoiGeometry` change
- But `map.loaded()` might not be true when geometry is set
- Retry logic exists but may not be sufficient

### Issue #4: Source Data Update
- `source.setData()` is called
- But MapLibre might not repaint immediately
- `map.triggerRepaint()` is called but may not be enough

---

## Fix Strategy

1. **Fix Layer ID Mismatch:**
   - Change `ProjectPage` layer state to use `'aoi-display-layer'`
   - OR change `AoiDisplay` to use `'aoi-draw-layer'`

2. **Dynamic Layer Discovery:**
   - Query map.getStyle().layers to discover all layers
   - Filter to relevant layers (aoi, corine, natura)
   - Update LayerControl dynamically

3. **Ensure Source Data Updates:**
   - Wait for 'sourcedata' event after setData()
   - Use map.once('sourcedata') to ensure data is loaded

4. **Verify Layer Visibility:**
   - Check layer exists before setting visibility
   - Log layer state for debugging

