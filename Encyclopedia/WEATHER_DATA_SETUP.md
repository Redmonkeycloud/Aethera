# Weather Data Setup Guide

This guide explains how to download and set up weather/climate data for the RESM (Renewable Energy Suitability Model).

## Global Solar Atlas - GHI Data

### Download Location
Visit: https://globalsolaratlas.info/download/europe-and-central-asia

### What to Download

1. **Global Horizontal Irradiance (GHI) Raster Data**
   - **Dataset Name**: `LTAym_AvgDailyTotals` (Long-Term Average Yearly Mean Average Daily Totals)
   - **Format**: **GeoTIFF** - **Required** (do NOT use AAIGRID format)
   - **File Size**: ~3.59 GB for Europe/Central Asia region
   - **Units**: kWh/m²/day (annual average daily totals)
   - **What to download**: Look for "Gis data - LTAym_AvgDailyTotals (GeoTIFF)" option

2. **Data Type**: Long-term average (typically 2000-2020 or similar period)

### File Naming and Location

Save the downloaded file to: `data2/weather/`

**Recommended filenames:**
- `solar_ghi_europe.tif` (for full Europe/Central Asia region)
- `solar_ghi_ITA.tif` (for Italy-specific data)
- `solar_ghi_GRC.tif` (for Greece-specific data)

**The system automatically discovers files matching these patterns:**
- `solar_ghi*.tif`
- `solar_ghi*.nc`
- `solar_ghi_{COUNTRY}.tif` (country-specific)

### Data Format Details

The GHI data should contain:
- **Units**: kWh/m²/day (preferred) or W/m² (will be converted)
- **CRS**: EPSG:4326 (WGS84) or any standard geographic CRS
- **Values**: Annual average solar irradiance

The system will automatically:
- Extract GHI values at AOI centroids
- Convert units if needed (W/m² → kWh/m²/day)
- Handle CRS transformations

## Global Wind Atlas - Wind Speed Data

### Download Location
Visit: https://globalwindatlas.info/

### What to Download

1. **Wind Speed at 100m Height**
   - **Metric**: Mean wind speed (m/s)
   - **Height**: 100m above ground level
   - **Format**: GeoTIFF (.tif) or NetCDF (.nc)
   - **Resolution**: Highest available (typically 1km or 250m)

### File Naming

Save to: `data2/weather/`

**Recommended filename:**
- `wind_speed_100m_europe.tif`
- `wind_speed_100m_ITA.tif` (country-specific)

## Copernicus CDS - ERA5 Reanalysis Data (Optional)

For comprehensive weather data including temperature and precipitation:

1. **Setup CDS API**: https://cds.climate.copernicus.eu/api-how-to
2. **Variables to download**:
   - `2m_temperature` - Air temperature at 2m
   - `10m_wind_speed` - Wind speed at 10m (can be extrapolated to 100m)
   - `surface_solar_radiation` - Solar radiation

3. **Script**: Use `scripts/download_weather_data.py` (requires API key setup)

## Verification

After downloading, verify the files are detected:

```bash
python -c "from backend.src.datasets.catalog import DatasetCatalog; cat = DatasetCatalog('data2'); print('Solar:', cat.weather_solar_ghi()); print('Wind:', cat.weather_wind_speed())"
```

## Usage in RESM Model

Once weather data is downloaded, the RESM model will automatically:
1. Extract weather features during analysis runs
2. Include solar GHI, wind speed, and temperature in suitability predictions
3. Fall back to default values if data is not available

The weather features improve model accuracy, especially for:
- **Solar projects**: Solar GHI is a critical factor
- **Wind projects**: Wind speed is essential for suitability assessment
- **General suitability**: Temperature affects both solar and wind efficiency

## References

- Global Solar Atlas: https://globalsolaratlas.info/
- Global Wind Atlas: https://globalwindatlas.info/
- Copernicus CDS: https://cds.climate.copernicus.eu/

