# Data Source Decisions

## Summary

We have decided on the following data sources for Italy and Greece:

### ✅ Forests: CORINE Land Cover (Extract Forest Classes)

**Decision**: Extract forest areas from existing CORINE dataset

**Method**: 
- Use script: `scripts/extract_forests_from_corine.py`
- Extract CORINE classes 311, 312, 313 (Broad-leaved, Coniferous, Mixed forests)

**Status**: 
- ✅ Italy: Already extracted (`data2/forests/forests_ITA.shp`)
- ⬇️ Greece: Extract after CORINE GRC is downloaded

**Advantages**:
- ✅ Already have CORINE data
- ✅ No additional download needed
- ✅ Vector format (easy to use)
- ✅ Commercial use allowed
- ✅ Good quality for EIA purposes

---

### ✅ Protected Areas: Natura 2000 (Substitute for WDPA)

**Decision**: Use Natura 2000 instead of WDPA

**Status**: 
- ✅ Already available: `data2/protected_areas/natura2000/`
- ✅ Italy: Already clipped (`natura2000_ITA.shp` - 49.6 MB)
- ⬇️ Greece: Can clip from full dataset

**Why Natura 2000 instead of WDPA**:
- ✅ Already in dataset (no download needed)
- ✅ Commercial use allowed (EEA license)
- ✅ Covers most important protected areas in EU
- ✅ Smaller file size (49.6 MB vs several GB for WDPA)
- ✅ Perfect for Italy and Greece (EU countries)

**What Natura 2000 covers**:
- Special Protection Areas (SPAs) - Birds Directive
- Special Areas of Conservation (SACs) - Habitats Directive
- These are the most legally protected areas in EU countries

**WDPA Status**: ❌ Not needed - skipped due to commercial restrictions

---

### ⚠️ Important Note

**CORINE cannot substitute WDPA/Natura 2000 for protected areas**

CORINE is a **land cover classification** dataset (describes what's on the ground: forests, agricultural land, urban areas, etc.), not a **protected areas** dataset (designated conservation areas).

- **CORINE**: Tells you "this area is forest" or "this area is agricultural land"
- **Natura 2000/WDPA**: Tells you "this area is a legally protected conservation site"

These serve different purposes:
- Use **CORINE** for: Land cover analysis, forest extraction, land use mapping
- Use **Natura 2000** for: Protected areas mapping, biodiversity protection sites, legal compliance

---

## Data Source Summary Table

| Data Category | Source | Status | Location |
|--------------|--------|--------|----------|
| **Forests** | CORINE (extract classes 311, 312, 313) | ✅ ITA done, ⬇️ GRC pending | `data2/forests/forests_*.shp` |
| **Protected Areas** | Natura 2000 | ✅ Available | `data2/protected_areas/natura2000/` |
| **Land Cover** | CORINE | ✅ ITA done, ⬇️ GRC pending | `data2/corine/corine_*.shp` |

---

## Next Steps

1. ✅ **Forests ITA**: Already extracted (no action needed)
2. ⬇️ **Forests GRC**: Extract after CORINE GRC is downloaded
3. ✅ **Protected Areas ITA**: Already available (no action needed)
4. ⬇️ **Protected Areas GRC**: Can clip from full Natura 2000 dataset

**All decisions finalized - no additional downloads needed for these categories!**

