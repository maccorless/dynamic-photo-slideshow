# Config Validation Fix - max_photos_limit

## Problem

Warning appeared on every startup:
```
Invalid value for max_photos_limit: 0. Using default: 500
```

## Root Cause

**Mismatch between schema and validation logic:**

### Schema (config_schema.json)
```json
"photo_limit": {
  "description": "Maximum number of photos to load from the album. Set to 0 for no limit.",
  "default": 0,
  "min": 0,
  "max": 10000
}
```

**Says:** 0 is valid and means "no limit"

### Validation (config.py line 157)
```python
elif key in ["max_photos_limit", ...]:
    return isinstance(value, int) and value > 0
```

**Says:** Value must be greater than 0 (rejects 0)

## The Fix

**File:** `config.py` lines 153-160

**Before:**
```python
elif key in ["max_photos_limit", "min_people_count", "SLIDESHOW_INTERVAL", 
             "CACHE_SIZE_LIMIT_GB", "max_recent_photos", "fallback_photo_limit",
             "min_fallback_photos", "progress_log_interval", "download_batch_size",
             "cache_refresh_check_interval"]:
    return isinstance(value, int) and value > 0
```

**After:**
```python
elif key == "max_photos_limit":
    # 0 means no limit, so allow >= 0
    return isinstance(value, int) and value >= 0
elif key in ["min_people_count", "SLIDESHOW_INTERVAL", 
             "CACHE_SIZE_LIMIT_GB", "max_recent_photos", "fallback_photo_limit",
             "min_fallback_photos", "progress_log_interval", "download_batch_size",
             "cache_refresh_check_interval"]:
    return isinstance(value, int) and value > 0
```

## Changes Made

1. **Separated `max_photos_limit` validation** - Now has its own validation rule
2. **Changed validation to `>= 0`** - Allows 0 as a valid value
3. **Added comment** - Explains that 0 means "no limit"

## Behavior

### Before Fix
- `max_photos_limit: 0` → Invalid → Warning → Uses default 500
- User config ignored

### After Fix
- `max_photos_limit: 0` → Valid ✅ → No warning → Uses 0 (no limit)
- User config respected

## Verification

```bash
./slideshow_env/bin/python3 << 'EOF'
from config import SlideshowConfig
from path_config import PathConfig

config = SlideshowConfig(PathConfig())
config.load_config()

print(f"max_photos_limit: {config.get('max_photos_limit')}")
# Should print: max_photos_limit: 0
# No warnings!
EOF
```

## Status: ✅ FIXED

- ✅ Validation now matches schema
- ✅ 0 is accepted as valid (means "no limit")
- ✅ No more warnings on startup
- ✅ User configuration is respected
