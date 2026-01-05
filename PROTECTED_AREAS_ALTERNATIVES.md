# Protected Areas Data Sources - Commercial Use Alternatives

## Issue with WDPA

WDPA (World Database on Protected Areas) has **commercial use restrictions**. For commercial use, they direct to IBAT (Integrated Biodiversity Assessment Tool), which requires a license.

## Alternative Sources (Commercial Use Friendly)

### 1. **Natura 2000 (Already Available!)**

✅ **Status**: Already in your dataset  
✅ **Commercial Use**: Allowed (EEA data)  
✅ **License**: EEA standard re-use policy (commercial use permitted)

**Location**: `data2/protected_areas/natura2000/`

- **Coverage**: European Union (includes Italy and Greece)
- **Format**: Shapefile
- **Advantage**: Already clipped to Italy (49.6 MB)
- **Limitation**: Only EU protected areas (SPAs, SACs), not all protected areas

**Use Case**: Natura 2000 covers the most important biodiversity protection sites in EU countries, which is perfect for Italy and Greece.

### 2. **Country-Specific Government Sources**

#### Italy - Protected Areas
- **Source**: Italian Ministry of Environment
- **URL**: https://www.minambiente.it/pagina/aree-protette
- **License**: Check individual license, often public domain or open license
- **Format**: Various (may need to check available formats)

#### Greece - Protected Areas  
- **Source**: Greek Ministry of Environment
- **URL**: https://ypen.gov.gr/
- **License**: Check individual license, often public domain
- **Format**: Various

**Advantage**: Country-specific data may have more permissive licenses
**Limitation**: Need to download separately for each country

### 3. **OpenStreetMap (OSM) - Protected Areas**

✅ **Commercial Use**: Allowed  
✅ **License**: ODbL (Open Database License) - allows commercial use with attribution

**Tags to Extract**:
- `boundary=protected_area`
- `leisure=nature_reserve`
- `leisure=protected_area`

**How to Extract**:
- Use OSM data (you're already downloading for cities)
- Filter by protected area tags
- Convert to shapefile

**Advantage**: Free, commercial use allowed, comprehensive
**Limitation**: User-generated, may have gaps or inconsistencies

### 4. **IUCN Protected Areas (Partial Alternative)**

- **Source**: IUCN
- **License**: Varies by dataset
- **Note**: Some datasets may have restrictions
- **Check**: Individual dataset licenses

### 5. **CORINE Land Cover - Protected Areas Indicator**

- **Source**: CORINE (already have)
- **Coverage**: Land use classification includes protected areas indicators
- **Note**: Not a direct replacement, but can identify protected land cover types

## Recommendation

### For Italy and Greece (EU Countries):

**Use Natura 2000** - Already available and suitable for commercial use!

**Why Natura 2000 is Sufficient:**
1. ✅ Already in your dataset
2. ✅ Commercial use allowed (EEA license)
3. ✅ Covers most important biodiversity protection sites
4. ✅ Already clipped to Italy (49.6 MB)
5. ✅ Can clip to Greece (once GADM is available)

**Natura 2000 covers:**
- Special Protection Areas (SPAs) - Birds Directive
- Special Areas of Conservation (SACs) - Habitats Directive
- These are the most legally protected areas in EU countries

### If You Need Additional Protected Areas:

1. **OSM Protected Areas** (Recommended for commercial use):
   - Extract from OpenStreetMap data
   - Free, commercial use allowed (ODbL)
   - Comprehensive coverage

2. **Country-Specific Sources**:
   - Check Italian/Greek government websites
   - Often have more permissive licenses
   - May include additional protected area types

## Action Plan

### Option 1: Use Natura 2000 Only (Recommended)
- ✅ Already available
- ✅ Commercial use allowed
- ✅ Covers critical protected areas
- **Action**: No additional download needed!

### Option 2: Add OSM Protected Areas
- Extract from OSM data (you're downloading anyway)
- Add to complement Natura 2000
- Free commercial use

### Option 3: Skip WDPA
- For commercial projects, WDPA requires IBAT license (paid)
- Natura 2000 + OSM should cover needs for Italy/Greece

## Conclusion

**For commercial use in Italy and Greece, use Natura 2000** (already available). It's sufficient for most environmental impact assessments and is already in your dataset!

If you need additional coverage, extract protected areas from OpenStreetMap data, which allows commercial use under ODbL license.

