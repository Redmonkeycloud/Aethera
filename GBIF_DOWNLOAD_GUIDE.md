# GBIF Download Guide - Step by Step

## Current Location
You're on: https://www.gbif.org/occurrence/download

## Quick Steps

### Step 1: Set Country Filter

**For Italy:**
1. Find the **"Country"** filter (usually on the left sidebar or top filters)
2. Type: **Italy** or **IT**
3. Select: **Italy (IT)**

**For Greece:**
1. Find the **"Country"** filter
2. Type: **Greece** or **GR**
3. Select: **Greece (GR)**

### Step 2: (Optional) Add Filters to Reduce Size

**⚠️ IMPORTANT**: Full GBIF downloads for a country can be **VERY large** (several GB, millions of records).

**Recommended filters to reduce size:**
- **Has coordinate**: Check "Yes" (only records with geographic coordinates)
- **Basis of record**: Select specific types (e.g., "HumanObservation", "MachineObservation")
- **Year**: Add date range if you only need recent data
- **Taxon**: Filter by specific species groups if needed (e.g., vertebrates, plants, etc.)

**Tip**: Start with "Has coordinate: Yes" - this reduces size significantly and is essential for geospatial analysis.

### Step 3: Choose Download Format

You'll see 4 download options. **Choose: SIMPLE**

**Why SIMPLE?**
- ✅ Has coordinates (required for geospatial analysis)
- ✅ Interpreted data included
- ✅ Tab-delimited CSV format (works perfectly)
- ✅ 8 GB (2 GB zipped) - reasonable size
- ✅ No unnecessary data (multimedia, raw data)

**Why NOT others?**
- ❌ DARWIN CORE ARCHIVE: Too large (25 GB), includes unnecessary data
- ❌ SPECIES LIST: No coordinates - useless for geospatial analysis
- ❌ CUBE: No size info, coordinates conditional

### Step 4: Request Download

1. Click the green **"SIMPLE"** download button
2. You may need to log in or create a GBIF account (free)
3. The download will be prepared

### Step 5: Wait for Email

1. GBIF will send you an email when the download is ready
2. This can take **minutes to hours** depending on dataset size
3. Check your email (and spam folder) for notification

### Step 6: Download the File

1. Click the download link in the email
2. Or go back to: https://www.gbif.org/user/download
3. Find your download request
4. Click **"Download"** button
5. Save the ZIP file to your computer

### Step 7: Extract and Process

**Extract the ZIP file:**
- The ZIP contains one or more CSV/TSV files
- Main file is usually named: `occurrence.txt` or `occurrence.csv`

**Save to project:**
- **Italy**: `data2/biodiversity/gbif_occurrences_ITA.csv`
- **Greece**: `data2/biodiversity/gbif_occurrences_GRC.csv`

**If the file is named `occurrence.txt` or `occurrence.csv`, rename it to the expected name:**
```bash
# After extraction, rename the file
# Windows (PowerShell):
Move-Item "occurrence.txt" "data2\biodiversity\gbif_occurrences_ITA.csv"

# Or manually rename in File Explorer
```

**Note**: SIMPLE format is tab-delimited (TSV), which works fine. Python's pandas can read it as CSV: `pd.read_csv(file, sep='\t')` or just use `.csv` extension - it will work fine.

## File Format

GBIF downloads come as:
- **Format**: CSV or TSV (tab-separated values)
- **Columns**: Many columns (typically 200+ fields)
- **Key columns**: 
  - `decimalLatitude`, `decimalLongitude` (coordinates)
  - `scientificName` (species name)
  - `eventDate` (observation date)
  - `countryCode` (country)
  - And many more...

## File Size Expectations

**Without filters:**
- Italy: Can be **10-50+ GB** (millions of records)
- Greece: Can be **5-20+ GB** (millions of records)

**With "Has coordinate: Yes" filter:**
- Italy: **5-25 GB** (still large, but manageable)
- Greece: **2-10 GB** (more manageable)

**Recommendation**: Use filters to reduce size, especially:
- ✅ **Has coordinate: Yes** (required for geospatial analysis)
- ✅ Add date range (e.g., last 10-20 years)
- ✅ Filter by specific taxa if you only need certain groups

## After Download

1. **Save the file** to the correct location:
   - `data2/biodiversity/gbif_occurrences_ITA.csv`
   - `data2/biodiversity/gbif_occurrences_GRC.csv`

2. **Run organization script**:
   ```bash
   python scripts/download_datasets.py
   ```

3. **Verify the file**:
   - Check file size
   - Try opening with Excel/Python to verify format
   - Check that coordinates columns exist

## Alternative: Use Sample Data (For Testing)

If full downloads are too large, you already have sample data:
- **Italy sample**: `data2/biodiversity/external/gbif_occurrences_ITA_sample.csv` (26.3 MB, 5100 records)
- **Greece sample**: `data2/biodiversity/external/gbif_occurrences_GRC_sample.csv` (28.0 MB, 5100 records)

These were downloaded using: `python scripts/download_gbif_data.py --country ITA`

## Troubleshooting

**Download too large?**
- Add more filters (date range, taxa, etc.)
- Download one country at a time
- Consider using sample data for testing

**File format issues?**
- GBIF files are usually TSV (tab-separated), not CSV
- Python pandas can read both: `pd.read_csv(file, sep='\t')`
- You can rename `.txt` to `.csv` - the extension doesn't matter

**Download taking too long?**
- Large datasets can take hours to prepare
- Check your email for status updates
- GBIF will notify you when ready

## Summary Checklist

- [ ] Set Country filter (Italy or Greece)
- [ ] (Optional) Add "Has coordinate: Yes" filter
- [ ] (Optional) Add date range or other filters
- [ ] Click "Request download"
- [ ] Wait for email notification
- [ ] Download ZIP file when ready
- [ ] Extract ZIP file
- [ ] Rename occurrence file to: `gbif_occurrences_ITA.csv` or `gbif_occurrences_GRC.csv`
- [ ] Move to: `data2/biodiversity/`
- [ ] Run: `python scripts/download_datasets.py`

Good luck with your download! 🐦🦋🌿

