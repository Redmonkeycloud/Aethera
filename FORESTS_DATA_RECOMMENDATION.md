# Forests Data Recommendation

## 🎯 Recommendation: Extract from CORINE (Already Available!)

**Best Option**: Use the existing CORINE dataset and extract forests using the provided script.

### Why Extract from CORINE?

1. ✅ **Already have CORINE data** - No additional download needed!
2. ✅ **Free and open license** - Copernicus open data license
3. ✅ **Commercial use allowed** - No restrictions
4. ✅ **Script already exists** - `scripts/extract_forests_from_corine.py`
5. ✅ **Good quality** - CORINE forest classifications are well-established
6. ✅ **Vector format** - Shapefile output (compatible with your workflow)

### CORINE Forest Classes:
- **311**: Broad-leaved forest
- **312**: Coniferous forest  
- **313**: Mixed forest

### How to Extract:

```bash
# Extract forests for Italy
python scripts/extract_forests_from_corine.py --country ITA

# Extract forests for Greece (after downloading CORINE GRC)
python scripts/extract_forests_from_corine.py --country GRC
```

**Output**: `data2/forests/forests_ITA.shp` and `forests_GRC.shp`

---

## Alternative: Copernicus High Resolution Forest Layers

If you need **more detailed forest data** (e.g., tree cover density percentages, forest type at higher resolution), you can use:

### Option: Tree Cover Density (High Resolution Layers)

**Location on CLMS Portfolio**: 
- Go to: https://land.copernicus.eu/en/products?tab=explore
- Under **"Full-coverage Land Cover & Use"** → Click **"Tree Cover and Forests"**
- Select **"Tree Cover Density"**

**Details**:
- **Resolution**: 100m (or 20m for newer versions)
- **Format**: Raster (GeoTIFF)
- **Coverage**: Europe
- **Use case**: Detailed tree cover percentage mapping
- **License**: Copernicus open data license (commercial use OK)

**When to use**:
- Need tree cover density percentages (0-100%)
- Need higher resolution than CORINE (CORINE is ~100m minimum mapping unit)
- Need quantitative forest cover data

**Download steps**:
1. Navigate to: https://land.copernicus.eu/pan-european/high-resolution-layers/forests
2. Register/Login (free registration required)
3. Select "Tree Cover Density" product
4. Download Europe-wide raster (GeoTIFF)
5. Clip to country boundaries if needed
6. Save as: `data2/forests/tree_cover_density_ITA.tif`

---

## Comparison

| Feature | CORINE Forests (Recommended) | Tree Cover Density (HR) |
|---------|------------------------------|-------------------------|
| **Status** | ✅ Already available | ⬇️ Need to download |
| **Format** | Vector (Shapefile) | Raster (GeoTIFF) |
| **Resolution** | ~100m minimum | 100m (or 20m) |
| **Data Type** | Forest classes | Tree cover % |
| **Extraction** | ✅ Script ready | ⬇️ Manual processing |
| **License** | Copernicus (commercial OK) | Copernicus (commercial OK) |
| **File Size** | Small (extracted vector) | Large (raster) |

---

## Recommendation Summary

### For Your Use Case (Environmental Impact Assessment):

**Use CORINE Forest Extraction** - It's:
- Already available (no download needed)
- Quick to extract (script ready)
- Good quality for EIA purposes
- Vector format (easy to work with)
- Covers all forest types you need

### When to Consider High Resolution Layers:

Only if you need:
- Quantitative tree cover density percentages
- Higher spatial resolution
- Detailed forest structure analysis

For most environmental impact assessments, **CORINE forest extraction is sufficient and recommended**.

---

## Next Steps

1. ✅ Use CORINE extraction script (no download needed)
2. ⬇️ Only download Tree Cover Density if you need quantitative density data

**Action**: Run the extraction script - no need to download from CLMS portfolio!

