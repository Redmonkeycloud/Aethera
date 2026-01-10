# Windows Installation Guide

## Installing Dependencies on Windows

### Issue: Fiona requires GDAL

On Windows, `fiona` requires GDAL to build from source, which can be problematic. However, since AETHERA uses `pyogrio` (a faster, more modern alternative) for most vector I/O operations, `fiona` has been removed from the dependencies.

### Installation Steps

1. **Install the project without dependencies first:**
   ```powershell
   cd backend
   pip install -e . --no-deps
   ```

2. **Install LangChain packages:**
   ```powershell
   pip install langchain langchain-core langchain-community langchain-groq langchain-openai
   ```

3. **Install remaining dependencies:**
   ```powershell
   pip install asyncpg boto3 markdown openpyxl python-docx reportlab rioxarray structlog typer xarray
   ```

4. **Optional: Install weasyprint (may have additional dependencies):**
   ```powershell
   pip install weasyprint
   ```

### Alternative: Using Conda

If you encounter issues with pip, consider using Conda which handles GDAL dependencies better:

```powershell
conda install -c conda-forge geopandas pyogrio rasterio fiona
pip install -e .
```

### Verifying Installation

Test that LangChain is working:

```powershell
cd D:\AETHERA_2.0
$env:PYTHONPATH='D:\AETHERA_2.0'
python -c "from backend.src.reporting.langchain_llm import LangChainLLMService; llm = LangChainLLMService(); print(f'LLM enabled: {llm.enabled}')"
```

### Note on Fiona

If you specifically need `fiona` for some functionality:
1. Install GDAL first from [GIS Internals](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)
2. Or use Conda: `conda install -c conda-forge gdal fiona`
3. Then install: `pip install fiona`

For most AETHERA use cases, `pyogrio` is sufficient and faster.
