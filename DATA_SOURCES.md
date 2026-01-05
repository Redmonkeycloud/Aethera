# Geospatial Data Sources for Italy and Greece

This document lists authoritative data sources for geospatial datasets covering Italy and Greece.

## Data Categories

### 1. CORINE Land Cover
- **Source**: Copernicus Land Monitoring Service
- **URL**: https://land.copernicus.eu/pan-european/corine-land-cover
- **Format**: Vector (Shapefile/GeoPackage)
- **Coverage**: Europe (including Italy and Greece)
- **Update Frequency**: Every 6 years
- **License**: Copernicus Open Access Hub license

### 2. Natura 2000 Protected Areas
- **Source**: European Environment Agency (EEA)
- **URL**: https://www.eea.europa.eu/data-and-maps/data/natura-11
- **Format**: Vector (Shapefile/GeoPackage)
- **Coverage**: EU member states (Italy and Greece included)
- **Update Frequency**: Annual
- **License**: EEA standard re-use policy

### 3. Protected Areas (Additional)
- **Italy - Protected Areas**:
  - **Source**: Italian Ministry of Environment
  - **URL**: https://www.minambiente.it/pagina/aree-protette
  - Alternative: ProtectedPlanet (UNEP-WCMC)
  - **URL**: https://www.protectedplanet.net/country/ITA
  
- **Greece - Protected Areas**:
  - **Source**: Greek Ministry of Environment
  - **URL**: https://ypen.gov.gr/
  - Alternative: ProtectedPlanet (UNEP-WCMC)
  - **URL**: https://www.protectedplanet.net/country/GRC

### 4. Rivers and Water Bodies
- **EU-Hydro**:
  - **Source**: Copernicus Land Monitoring Service
  - **URL**: https://land.copernicus.eu/imagery-in-situ/eu-hydro
  - **Format**: Vector
  - **Coverage**: Europe
  
- **Waterbase - Rivers**:
  - **Source**: EEA
  - **URL**: https://www.eea.europa.eu/data-and-maps/data/waterbase-rivers-10

### 5. Forests
- **Tree Cover Density**:
  - **Source**: Copernicus Land Monitoring Service
  - **URL**: https://land.copernicus.eu/pan-european/high-resolution-layers/forests
  - **Coverage**: Europe
  
- **Forest Type**:
  - **Source**: Copernicus
  - **URL**: https://land.copernicus.eu/pan-european/high-resolution-layers/forests/forest-type-1

### 6. Agricultural Lands
- **CORINE Land Cover** (includes agricultural categories)
- **LUCAS Survey Data**:
  - **Source**: Eurostat
  - **URL**: https://ec.europa.eu/eurostat/web/lucas

### 7. Cities and Urban Areas
- **Urban Atlas**:
  - **Source**: Copernicus Land Monitoring Service
  - **URL**: https://land.copernicus.eu/local/urban-atlas
  - **Format**: Vector
  - **Coverage**: Major European cities
  
- **Degree of Urbanisation**:
  - **Source**: Eurostat
  - **URL**: https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/administrative-units-statistical-units/degurba

### 8. Biodiversity and Endangered Species
- **GBIF (Global Biodiversity Information Facility)**:
  - **URL**: https://www.gbif.org/
  - **API**: https://api.gbif.org/v1/
  - **Coverage**: Global (Italy and Greece included)
  - **Format**: API/CSV with coordinates
  
- **IUCN Red List**:
  - **Source**: International Union for Conservation of Nature
  - **URL**: https://www.iucnredlist.org/
  - **Format**: API/Shapefile for species ranges
  
- **EU Birds Directive Reporting**:
  - **Source**: EEA
  - **URL**: https://www.eea.europa.eu/data-and-maps/data/article-12-database-birds-directive-2009-147-ec-2

## Data Download Recommendations

### Priority Datasets (Country-Specific)
1. **CORINE Land Cover** - Already have, but may need country-specific clips
2. **Natura 2000** - Already have, but may need country-specific clips
3. **Protected Areas** - Download from ProtectedPlanet or national sources
4. **Rivers** - EU-Hydro or OpenStreetMap
5. **Cities** - Urban Atlas or OpenStreetMap

### Secondary Datasets
6. **Forests** - Copernicus High Resolution Layers
7. **Agricultural Lands** - Extract from CORINE or use LUCAS
8. **Biodiversity** - GBIF API for species occurrences

## Next Steps
1. Create download scripts for each data source
2. Organize data in `data2/` directory with clear folder structure
3. Tag files with country codes (ITA, GRC) and data type
4. Create metadata files for each dataset

