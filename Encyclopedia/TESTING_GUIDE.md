# Testing Guide

## Quick Start - Test Existing Functionality

### Step 1: Start Backend API

Open a terminal and run:

```powershell
cd D:\AETHERA_2.0
python -m uvicorn backend.src.api.app:app --host 0.0.0.0 --port 8001 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Step 2: Start Frontend (Streamlit)

Open a **new terminal** and run:

```powershell
cd D:\AETHERA_2.0\frontend
streamlit run app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
```

### Step 3: Test in Browser

1. Open http://localhost:8501 in your browser
2. Navigate to "➕ New Project"
3. Create a test project:
   - **Project Name**: Test Project
   - **Country**: Italy
   - **Sector**: Renewable Energy
4. Click "Create Project"
5. Go to the project page
6. Define an AOI (Area of Interest) by drawing on the map or uploading GeoJSON
7. Check the "Map View" tab

### Step 4: Test Layers

On the Map View tab, you should see:

✅ **Natura 2000** checkbox - Should load Italian Natura 2000 sites (red polygons)
✅ **CORINE** checkbox - Should load CORINE land cover for Italy (green polygons)
✅ **AOI** checkbox - Should show your defined area of interest (blue polygon)

**What to verify:**
- [ ] Map loads without errors
- [ ] Natura 2000 layer displays (should be fast since it's country-clipped: 49.6 MB)
- [ ] CORINE layer displays (may take a moment, ~237 MB or uses Europe-wide GPKG with clipping)
- [ ] AOI displays correctly
- [ ] Layers can be toggled on/off
- [ ] No timeout errors

### Step 5: Test with Different Country

1. Create a new project with Country: Greece
2. Test if layers load correctly for Greece
3. Note: Greece may use Europe-wide datasets with dynamic clipping

## Current Implementation Status

### ✅ Working Features

- **Backend API endpoints:**
  - `/layers/natura2000?country=ITA` - Returns Italian Natura 2000 sites
  - `/layers/corine?country=ITA` - Returns CORINE land cover (clipped or full)
  - `/layers/available` - Lists available layers

- **Frontend:**
  - Project creation
  - AOI definition
  - Map display with Folium
  - Layer toggles for Natura 2000 and CORINE
  - Country-based layer filtering

### 📦 Available But Not Yet Integrated

The following datasets are available in `data2/` but not yet added to the backend/frontend:

1. **Urban Atlas** (Cities)
   - `data2/cities/urban_atlas/UA_2018_ITA.gpkg` (3.17 GB)
   - `data2/cities/urban_atlas/UA_2018_GRC.gpkg` (439 MB)

2. **GBIF Biodiversity**
   - `data2/biodiversity/gbif_occurrences_ITA.csv` (7.34 GB)

3. **Rivers**
   - `data2/rivers/HydroRIVERS_v10_eu_shp/HydroRIVERS_v10_eu.shp` (144.5 MB)

4. **Agricultural Lands**
   - `data2/agricultural/agricultural_lands_ITA.shp` (101.7 MB)

5. **Forests**
   - `data2/forests/forests_ITA.shp` (107.3 MB)

## Troubleshooting

### Backend Won't Start

**Error: `ModuleNotFoundError`**
```powershell
# Install missing dependencies
pip install fastapi uvicorn geopandas shapely
```

**Error: `FileNotFoundError: No CORINE dataset found`**
- Check that `data2/corine/` contains CORINE files
- Check `backend/src/config/base_settings.py` - `data_sources_dir` should point to `data2`

### Frontend Won't Start

**Error: `ModuleNotFoundError: No module named 'streamlit'`**
```powershell
cd frontend
pip install -r requirements.txt
```

### Layers Don't Load

**Timeout errors:**
- Check backend logs for errors
- Verify dataset files exist in `data2/`
- For large datasets, ensure country filtering is working (should use smaller country-specific files)

**404 errors:**
- Check that dataset files exist
- Verify `data_sources_dir` path in backend settings

### Map Doesn't Display

- Check browser console for JavaScript errors
- Verify `streamlit-folium` and `folium` are installed
- Check that backend is running and accessible

## Next Steps After Testing

Once basic functionality is confirmed working:

1. **Add Urban Atlas support:**
   - Add `urban_atlas()` method to `DatasetCatalog`
   - Create `/layers/urban_atlas` API endpoint
   - Add Urban Atlas checkbox to frontend

2. **Add other datasets:**
   - Rivers, Agricultural Lands, Forests, GBIF
   - Follow the same pattern as CORINE/Natura 2000

3. **Performance optimization:**
   - Pre-clip large datasets to countries
   - Cache frequently accessed layers
   - Add pagination for very large datasets (like GBIF)

## Quick Test Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can create a new project
- [ ] Can define an AOI
- [ ] Map displays correctly
- [ ] Natura 2000 layer loads for Italy
- [ ] CORINE layer loads for Italy
- [ ] AOI displays on map
- [ ] Layer toggles work
- [ ] No timeout or 404 errors

