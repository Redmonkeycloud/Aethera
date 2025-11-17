# Linting Fixes Applied

This document tracks the linting fixes applied to resolve CI/CD failures.

## Configuration Fixes

1. **Updated `pyproject.toml`**:
   - Moved `select` to `[tool.ruff.lint]` section (new ruff format)
   - Added `ignore = ["E501"]` to ignore line length (handled by formatter)

2. **Updated CI workflow**:
   - Fixed path handling for `ai/` and `scripts/` directories
   - Added `--fix` flag to auto-fix issues where possible

## Code Fixes Applied

### Typing Modernization (Python 3.11+)
- Replaced `Dict[X]` → `dict[X]`
- Replaced `List[X]` → `list[X]`
- Replaced `Tuple[X]` → `tuple[X]`
- Replaced `Optional[X]` → `X | None`
- Removed deprecated typing imports

### Import Organization
- Fixed import sorting (standard library → third-party → local)
- Removed unused imports

### File Operations
- Removed unnecessary `"r"` mode argument from `open()` calls

### Other Fixes
- Fixed line length issues (wrapped long lines)
- Fixed import locations (moved imports to top-level)
- Fixed exception handling (added `from err` or `from None`)

## Files Fixed

- `backend/src/analysis/biodiversity.py`
- `backend/src/analysis/land_cover.py`
- `backend/src/api/models.py`
- `backend/src/api/storage.py`

## Remaining Files to Fix

The following files still need manual fixes:
- `backend/src/api/routes/*.py` - Import sorting, line length, exception handling
- `backend/src/config/base_settings.py` - Line length
- `backend/src/datasets/*.py` - Typing, collections.abc imports
- `backend/src/db/*.py` - Typing, unused imports, file modes
- `backend/src/emissions/*.py` - Typing, line length
- `backend/src/gis_handler.py` - Typing, import location
- `backend/src/logging_utils.py` - Typing
- `backend/src/main_controller.py` - Line length, unused variables, import sorting
- `backend/src/reporting/*.py` - Typing
- `backend/src/utils/geometry.py` - collections.abc imports
- `ai/models/*.py` - (if any issues)
- `scripts/*.py` - (if any issues)

## Next Steps

1. Run `ruff check --fix` on remaining files
2. Manually fix issues that can't be auto-fixed
3. Verify CI passes

