# Installing Tippecanoe on Windows

## Problem

The `pip install tippecanoe` command fails on Windows because tippecanoe needs to be compiled, which requires build tools and `make` (not available on Windows by default).

**⚠️ IMPORTANT:** The latest releases (including 2.79.0) **do NOT include pre-built Windows binaries**. They only provide source code.

## Solution Options

### Option 1: Build from Source (Recommended if you have Visual Studio)

**Requirements:**
- Git for Windows: https://git-scm.com/download/win
- CMake: https://cmake.org/download/
- Visual Studio 2022 with "Desktop development with C++" workload: https://visualstudio.microsoft.com/downloads/

**Steps:**

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/felt/tippecanoe.git
   cd tippecanoe
   ```

2. **Build:**
   ```powershell
   mkdir build
   cd build
   cmake ..
   cmake --build . --config Release
   ```

3. **Find the executable:**
   The `tippecanoe.exe` will be in: `build\Release\tippecanoe.exe`

4. **Add to PATH (optional):**
   - Copy the path to the `Release` folder
   - Add it to your system PATH environment variable

### Option 2: Use Python-Based Alternative (Easier, No Compilation)

Our tile generation script (`scripts/generate_corine_tiles.py`) has a Python fallback that doesn't require tippecanoe. It uses `vt2geojson` and other Python libraries to generate tiles.

**Just run:**
```bash
cd D:\AETHERA_2.0
python scripts/generate_corine_tiles.py --country ITA --method python
```

This will work without installing tippecanoe!

### Option 3: Use Docker (If Available)

If you have Docker installed, you can use tippecanoe in a Docker container:

```bash
docker run -v D:\AETHERA_2.0\data2:/data maptiler/tippecanoe tippecanoe -o /data/corine/tiles/ITA/corine_ITA.mbtiles -z14 -Z0 --layer=corine /data/corine/corine_ITA.geojson
```

## Recommendation

**For most users, Option 2 (Python-based) is the easiest** - no compilation needed, just Python libraries!

