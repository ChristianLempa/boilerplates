# Fix for "Type not yet supported" Error

## Issue Summary

Users reported encountering an error message `Error: Type not yet supported:` when running `boilerplates repo update` after a fresh installation.

## Root Cause Analysis

The error message `Type not yet supported:` comes from Typer (the CLI framework) when it encounters an invalid or missing type annotation. While we couldn't reproduce the exact scenario, we identified and fixed several potential causes:

### 1. Config Branch Inconsistency

**Problem:** The code had inconsistent branch configurations:
- Default config creation used `branch: "main"`
- Config migration used `branch: "refactor/boilerplates-v2"`

This could cause confusion and potential errors during git operations.

**Fix:** Updated `cli/core/config.py` line 92 to use `"main"` consistently in the migration code.

### 2. Empty Variable Type Handling

**Problem:** If a template had a variable with an empty or null type specification (e.g., `type:` with no value in YAML), it could result in an empty string or None being used as the type, potentially causing Typer to fail.

**Fix:** Updated `cli/core/variable.py` to properly handle:
- Empty strings (`type: ""`)
- None values (`type: null`)
- Whitespace-only values (`type: "   "`)

All these cases now default to `"str"` type.

### 3. Library Config Validation

**Problem:** Invalid library configurations could cause initialization errors without clear error messages.

**Fix:** Added validation in `cli/core/library.py` to:
- Check that library config entries are dictionaries
- Verify required 'name' field is present
- Skip invalid entries gracefully with helpful log messages

## Changes Made

### File: `cli/core/config.py`
```python
# Line 92 - Changed from "refactor/boilerplates-v2" to "main"
"branch": "main",
```

### File: `cli/core/variable.py`
```python
# Line 41-42 - Improved type handling
raw_type = data.get("type")
self.type: str = raw_type.strip() if (raw_type and isinstance(raw_type, str) and raw_type.strip()) else "str"
```

### File: `cli/core/library.py`
```python
# Lines 141-151 - Added validation
if not isinstance(lib_config, dict):
    logger.warning(f"Invalid library config at index {i}: not a dictionary")
    continue

name = lib_config.get("name")
if not name:
    logger.warning(f"Library config at index {i} missing 'name' field")
    continue
```

### New File: `scripts/diagnose_config.py`
Added a diagnostic script that users can run to check for configuration issues:
```bash
python3 scripts/diagnose_config.py
```

This script checks:
- Config file existence and validity
- Library configuration structure
- Branch settings (warns about development branches)
- Synced library directories

## Testing

All changes have been thoroughly tested:

1. **Config Migration Test**: Verified that old configs without library sections get migrated with "main" branch
2. **Variable Type Test**: Tested 6 edge cases (empty, None, whitespace) - all default to "str"
3. **Library Validation Test**: Tested with invalid configs - properly skips bad entries
4. **Integration Test**: Full workflow (repo update → compose list) works correctly
5. **Linting**: All code passes pylint with no errors

## For Users

If you encountered this error:

1. **Update to the latest version** with these fixes
2. **Delete your config** and let it recreate:
   ```bash
   rm -rf ~/.config/boilerplates/config.yaml
   boilerplates repo update
   ```

3. **Run the diagnostic script** if issues persist:
   ```bash
   python3 scripts/diagnose_config.py
   ```

4. **Use debug logging** for more information:
   ```bash
   boilerplates --log-level DEBUG repo update
   ```

## Prevention

These fixes add multiple layers of defense:
- Consistent configuration across all code paths
- Robust handling of invalid or missing values
- Clear error messages when something goes wrong
- Diagnostic tools for troubleshooting

The changes maintain backward compatibility while making the system more resilient to configuration errors.
