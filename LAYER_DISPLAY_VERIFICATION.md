# Layer Display Verification - Complete Pipeline Check

## ✅ Fixed Issues Summary

### 1. **Layer ID Mismatch** - FIXED
- **Before**: `ProjectPage` hardcoded `'aoi-draw-layer'` but `AoiDisplay` creates `'aoi-display-layer'`
- **After**: Dynamic layer discovery finds all layers by ID automatically

### 2. **Dynamic Layer Discovery** - IMPLEMENTED
- **Before**: Layers were hardcoded, BaseLayers never appeared in LayerControl
- **After**: `ProjectPage` automatically discovers all layers from map:
  - `'aoi-display-layer'` → "AOI"
  - `'base-natura2000-layer'` → "Natura 2000"
  - `'base-corine-layer'` → "CORINE"

### 3. **Layer Discovery Timing** - IMPROVED
- **Before**: Only discovered on map load
- **After**: 
  - Discovers on map load
  - Listens to `styledata` event (fires when layers added)
  - Periodic check every 2 seconds as fallback

### 4. **Layer Toggle Functionality** - FIXED
- **Before**: Toggle only updated state, not actual map layers
- **After**: Toggles both fill and outline layers on the map

## 📋 Complete Pipeline Flow

### **AOI Layer (GeoJSON Upload)**
```
1. User uploads GeoJSON
   ↓
2. AoiUpload.tsx → FileReader → JSON.parse()
   ↓
3. setAoiGeometry() → useAppStore (Zustand)
   ↓
4. AoiDisplay.tsx subscribes to aoiGeometry
   ↓
5. Creates source 'aoi-display' (GeoJSON)
   ↓
6. Creates layers:
   - 'aoi-display-layer' (fill, blue, opacity 0.5)
   - 'aoi-display-layer-outline' (line, blue, width 3)
   ↓
7. source.setData({ features: [aoiGeometry] })
   ↓
8. map.fitBounds() → zooms to AOI
   ↓
9. ProjectPage discovers layer via styledata event
   ↓
10. LayerControl displays "AOI" checkbox in top-right
```

### **Base Layers (CORINE/Natura 2000)**
```
1. BaseLayers.tsx checks /layers/available
   ↓
2. If available, fetches /layers/natura2000 or /layers/corine
   ↓
3. Backend (layers.py) loads shapefile/GPKG
   ↓
4. Backend reprojects to EPSG:4326 (if needed)
   ↓
5. Backend returns GeoJSON FeatureCollection
   ↓
6. BaseLayers creates source 'base-natura2000' or 'base-corine'
   ↓
7. BaseLayers creates layers:
   - 'base-natura2000-layer' (fill, red, opacity 0.4)
   - 'base-natura2000-layer-outline' (line, red, width 2)
   - 'base-corine-layer' (fill, green, opacity 0.3)
   - 'base-corine-layer-outline' (line, green, width 1.5)
   ↓
8. map.fitBounds() → zooms to layer extent
   ↓
9. ProjectPage discovers layers via styledata event
   ↓
10. LayerControl displays "Natura 2000" and "CORINE" checkboxes
```

### **Layer Control (Top Right Corner)**
```
1. ProjectPage maintains layers state (initially empty)
   ↓
2. useEffect discovers layers from map.getStyle().layers
   ↓
3. Filters out:
   - 'simple-tiles' (base raster)
   - Layers ending in '-outline' (shown with parent)
   ↓
4. Maps layer IDs to friendly names
   ↓
5. Updates layers state
   ↓
6. LayerControl receives layers prop
   ↓
7. Renders checkboxes in top-right corner
   ↓
8. User toggles checkbox
   ↓
9. handleLayerToggle() updates:
   - Map layer visibility (fill + outline)
   - State for UI consistency
```

## 🔍 Verification Checklist

### ✅ Layers Appear on Map
- [x] AOI layer created with correct ID: `'aoi-display-layer'`
- [x] Base layers created with correct IDs: `'base-natura2000-layer'`, `'base-corine-layer'`
- [x] Layers have visible colors and opacity
- [x] Layers are moved to top (not hidden behind base tiles)
- [x] Source data is set correctly (GeoJSON FeatureCollection)

### ✅ Layers Appear in LayerControl (Top Right)
- [x] Dynamic discovery finds all layers
- [x] Layer names mapped correctly:
  - `'aoi-display-layer'` → "AOI"
  - `'base-natura2000-layer'` → "Natura 2000"
  - `'base-corine-layer'` → "CORINE"
- [x] Discovery triggers on:
  - Map load
  - `styledata` event (when layers added)
  - Periodic check (fallback every 2s)

### ✅ Layer Toggle Works
- [x] Checkbox toggles actual map layer visibility
- [x] Both fill and outline layers toggle together
- [x] State updates for UI consistency

## 🐛 Potential Issues & Solutions

### Issue: Layers not discovered immediately
**Solution**: Added periodic check every 2 seconds as fallback

### Issue: styledata event might not fire
**Solution**: MapLibre automatically fires `styledata` when `map.addLayer()` is called

### Issue: Layers hidden behind base tiles
**Solution**: Layers are moved to top using `map.moveLayer()`

### Issue: Invalid coordinates (CRS mismatch)
**Solution**: 
- Backend reprojects to EPSG:4326
- Frontend validates coordinate ranges (-180 to 180, -90 to 90)

## 📝 Files Modified

1. **frontend/src/pages/ProjectPage.tsx**
   - Removed hardcoded layer list
   - Added dynamic layer discovery
   - Improved handleLayerToggle to update map layers
   - Added periodic discovery check

2. **frontend/src/components/Map/AoiDisplay.tsx**
   - Split setup and update logic
   - Improved timing and error handling
   - Added coordinate validation

3. **frontend/src/components/Map/BaseLayers.tsx**
   - Already had correct layer IDs
   - No changes needed (already correct)

4. **frontend/src/components/Map/LayerControl.tsx**
   - Already correct (just displays layers from props)

## ✅ Final Status

**All critical issues have been fixed:**
- ✅ Layer ID mismatch resolved
- ✅ Dynamic layer discovery implemented
- ✅ Layers appear on map
- ✅ Layers appear in LayerControl (top right)
- ✅ Layer toggle functionality works

The pipeline is now complete and functional!

