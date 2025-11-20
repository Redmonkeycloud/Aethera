# WKT Support

AETHERA now supports loading Area of Interest (AOI) data from Well-Known Text (WKT) format in addition to standard vector file formats.

## Supported WKT Formats

### Single Geometry Types
- `POINT`
- `LINESTRING`
- `POLYGON`

### Multi Geometry Types
- `MULTIPOINT`
- `MULTILINESTRING`
- `MULTIPOLYGON`

### Geometry Collections
- `GEOMETRYCOLLECTION` - Contains multiple geometries of different types

## Usage

### WKT String Input

You can pass a WKT string directly to the `--aoi` parameter:

```bash
python -m backend.src.main_controller \
  --aoi "POLYGON((10 50, 20 50, 20 60, 10 60, 10 50))" \
  --project-type solar_farm
```

### WKT File Input

Create a `.wkt` or `.txt` file containing WKT geometries (one per line):

```wkt
POLYGON((10 50, 20 50, 20 60, 10 60, 10 50))
POLYGON((30 50, 40 50, 40 60, 30 60, 30 50))
```

Then reference the file:

```bash
python -m backend.src.main_controller \
  --aoi path/to/aoi.wkt \
  --project-type solar_farm
```

### Multi-Geometry Examples

**MultiPolygon:**
```wkt
MULTIPOLYGON(((10 50, 20 50, 20 60, 10 60, 10 50)), ((30 50, 40 50, 40 60, 30 60, 30 50)))
```

**GeometryCollection:**
```wkt
GEOMETRYCOLLECTION(
  POLYGON((10 50, 20 50, 20 60, 10 60, 10 50)),
  POINT(15 55)
)
```

## Implementation Details

- WKT geometries are automatically assigned CRS `EPSG:4326` (WGS84)
- The system automatically converts to the target CRS (default: `EPSG:3035`)
- Invalid or empty geometries are filtered out
- Multi-geometries and collections are automatically exploded into individual features
- Comments in WKT files (lines starting with `#`) are ignored

## Error Handling

The system provides clear error messages for:
- Invalid WKT syntax
- Empty geometries
- Unsupported geometry types
- Missing or inaccessible files

