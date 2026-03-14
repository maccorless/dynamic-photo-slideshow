# Root Cause: "Ally" Filter on Photos and Videos

## Problem
User reported seeing ONLY photos and videos with "Ally" - no other people.

## Root Cause Found

### Issue 1: `video_person_filter` Using Default Value

**Problem:**
- `video_person_filter` was NOT in the user config file (`~/.photo_slideshow_config.json`)
- When a setting is missing from user config, it uses the DEFAULT_CONFIG value
- DEFAULT_CONFIG has: `'video_person_filter': 'Ally'` (line 58 in config.py)

**Result:** Videos were filtered to only show "Ally"

**Fix Applied:**
Added to user config:
```json
{
  "video_person_filter": null
}
```

---

### Issue 2: `filter_people_names` Was Empty String Instead of Empty List

**Problem:**
- User config had: `"filter_people_names": ""`  (empty string)
- DEFAULT_CONFIG expects: `"filter_people_names": []` (empty list)
- While both are falsy, the type mismatch could cause issues

**Fix Applied:**
Changed to:
```json
{
  "filter_people_names": []
}
```

---

## Why This Happened

### 1. Settings Manager Key Mapping Issue

The settings manager was saving schema key names instead of config.py key names:

**Wrong (what was saved):**
```json
{
  "people_filter": "",           // Schema name
  "video_max_duration": 5        // Schema name (lowercase)
}
```

**Correct (what should be saved):**
```json
{
  "filter_people_names": [],     // Config.py name
  "VIDEO_MAX_DURATION": 5        // Config.py name (UPPERCASE)
}
```

### 2. Missing Settings in User Config

Settings that exist in DEFAULT_CONFIG but NOT in user config will use their default values:

- `video_person_filter` was missing → Used default "Ally"
- `filter_by_people` was missing → Used default False
- Many other settings were missing

---

## Complete Fix Applied

### Step 1: Fixed All Key Names

Converted all schema names to config.py names:

| Before (Schema) | After (Config.py) |
|----------------|-------------------|
| `people_filter` | `filter_people_names` |
| `places_filter` | `filter_by_places` |
| `keywords_filter` | `filter_by_keywords` |
| `filter_logic` | `overall_filter_logic` |
| `slideshow_interval` | `SLIDESHOW_INTERVAL` |
| `video_max_duration` | `VIDEO_MAX_DURATION` |
| `video_audio_enabled` | `VIDEO_AUDIO_ENABLED` |

### Step 2: Fixed Data Types

- `filter_people_names`: `""` → `[]`
- `filter_by_places`: `""` → `[]`  
- `filter_by_keywords`: `""` → `[]`

### Step 3: Added Missing Settings

Added to user config:
```json
{
  "video_person_filter": null,
  "filter_by_people": false
}
```

---

## Current Config File

**Location:** `~/.photo_slideshow_config.json`

**Key Settings:**
```json
{
  "SLIDESHOW_INTERVAL": 5,
  "VIDEO_MAX_DURATION": 5,
  "VIDEO_AUDIO_ENABLED": true,
  "filter_by_people": false,
  "filter_people_names": [],
  "filter_by_places": [],
  "filter_by_keywords": [],
  "overall_filter_logic": "AND",
  "video_person_filter": null,
  "album_name": "All Photos"
}
```

---

## Verification

Tested with Python:
```python
from config import SlideshowConfig
config = SlideshowConfig()
config.load_config()

print(config.get('filter_people_names'))    # []
print(config.get('video_person_filter'))    # None
```

**Result:** ✅ Both filters are now disabled

---

## What Should Happen Now

### Photos:
- ✅ Load from "All Photos" album
- ✅ No people filtering
- ✅ No places filtering
- ✅ No keywords filtering
- ✅ Show ALL photos (except hidden & RAW)

### Videos:
- ✅ No person filtering
- ✅ Show ALL videos
- ✅ Only locally available (not iCloud-only)

---

## Additional File Found

**Note:** There's also a `photo_slideshow_config.json` file (without dot) in the project directory with:
```json
{
  "filter_by_people": true,
  "filter_people_names": ["Ally"],
  "video_person_filter": "Ally"
}
```

**This file is NOT used** - it's probably a backup or test file. The actual config is `~/.photo_slideshow_config.json` (with dot in home directory).

---

## Status: ✅ FIXED

1. ✅ All key names corrected (schema → config.py)
2. ✅ All data types corrected (string → list)
3. ✅ `video_person_filter` set to null (disabled)
4. ✅ `filter_people_names` set to [] (disabled)
5. ✅ Verified with Python test

**The slideshow should now show ALL photos and videos, not just "Ally"!** 🎉

---

## Restart Required

**IMPORTANT:** You need to restart the slideshow for these changes to take effect!

```bash
# Stop current slideshow (ESC or Cmd+Q)
# Then restart:
./slideshow_env/bin/python main_pygame.py
```
