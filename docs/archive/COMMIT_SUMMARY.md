# Commit Summary - Configuration and Filtering Fixes

## Commit: 70b0d24
**Branch:** photo-video-voice  
**Date:** October 17, 2025

---

## Changes Committed

### 1. **Removed Hardcoded "Ally" Filter**
**File:** `config.py` line 58

```python
# Before:
'video_person_filter': 'Ally',

# After:
'video_person_filter': None,
```

**Impact:** Videos are no longer filtered by default. Users can set person filter via configuration.

---

### 2. **Fixed Config Validation for max_photos_limit**
**File:** `config.py` lines 153-160

```python
# Before:
elif key in ["max_photos_limit", ...]:
    return isinstance(value, int) and value > 0  # Rejected 0

# After:
elif key == "max_photos_limit":
    # 0 means no limit, so allow >= 0
    return isinstance(value, int) and value >= 0
```

**Impact:** No more warnings for `max_photos_limit: 0`. Value of 0 now correctly means "no limit".

---

### 3. **Added Complete Key Mappings**
**File:** `settings_manager.py` lines 314-402

Added bidirectional key mapping between schema and config.py:

**Case Differences (3 mappings):**
- `slideshow_interval` ↔ `SLIDESHOW_INTERVAL`
- `video_max_duration` ↔ `VIDEO_MAX_DURATION`
- `video_audio_enabled` ↔ `VIDEO_AUDIO_ENABLED`

**Name Differences (8 mappings):**
- `people_filter` ↔ `filter_people_names`
- `places_filter` ↔ `filter_by_places`
- `keywords_filter` ↔ `filter_by_keywords`
- `filter_logic` ↔ `overall_filter_logic`
- `photo_limit` ↔ `max_photos_limit`
- `portrait_pairing_enabled` ↔ `portrait_pairing`
- `min_people_for_pairing` ↔ `min_people_count`
- `cache_size` ↔ `photo_history_cache_size`

**Impact:** Settings now persist correctly across restarts. UI and config file use proper key names.

---

### 4. **Improved Album Error Messages**
**File:** `photo_manager.py` lines 112-120

```python
# Before:
self.logger.info("To create a Smart Album named 'photoframe':")
self.logger.info("1. Open Photos → File → New Smart Album")
self.logger.info("2. Name it 'photoframe' and set your criteria")

# After:
self.logger.info(f"Available albums: {', '.join(album_names[:10])}")
self.logger.info("To use a specific album:")
self.logger.info("1. Open settings (Cmd+S) and change 'Album Name'")
self.logger.info("2. Or create a new album/Smart Album in Photos app")
```

**Impact:** More helpful error messages that show available albums and reference the settings UI.

---

### 5. **Removed Project Directory Config File**
**File:** `photo_slideshow_config.json` (deleted)

This file had:
```json
{
  "filter_by_people": true,
  "filter_people_names": ["Ally"]
}
```

**Impact:** Removed conflicting config file that was causing Ally-only filtering. Slideshow now correctly uses `~/.photo_slideshow_config.json`.

---

### 6. **Added Configuration Schema**
**File:** `config_schema.json` (new)

Complete schema with 24 settings across 6 groups:
- Display (5 settings)
- Video (3 settings)
- Photos (3 settings)
- Voice Commands (5 settings)
- Filters (4 settings)
- Advanced (4 settings)

**Impact:** Enables settings UI with proper validation and defaults.

---

### 7. **Added Settings Manager**
**File:** `settings_manager.py` (new, 435 lines)

Features:
- Load/save configuration with JSON persistence
- Schema-based validation
- Auto-save on every change
- Change notification system (observer pattern)
- Revert functionality
- Reset to defaults
- Bidirectional key mapping

**Impact:** Provides robust settings management with proper key translation.

---

## Documentation Added

1. **HARDCODED_FILTERS_REMOVED.md** - Details removal of hardcoded Ally filter
2. **COMPLETE_KEY_MAPPINGS.md** - Complete mapping reference for all 11 key translations
3. **CONFIG_VALIDATION_FIX.md** - Explains max_photos_limit validation fix
4. **CONFIGURATION_EXPLAINED.md** - Comprehensive guide to all configuration options

---

## Issues Fixed

### Issue 1: Only Ally Photos/Videos Showing
**Cause:** Project directory `photo_slideshow_config.json` had Ally filter  
**Fix:** Removed file, slideshow now uses correct config  
**Status:** ✅ Fixed

### Issue 2: Config Validation Warnings
**Cause:** Validation rejected `max_photos_limit: 0`  
**Fix:** Updated validation to accept 0 as valid  
**Status:** ✅ Fixed

### Issue 3: Settings Not Persisting
**Cause:** Key name mismatches between schema and config.py  
**Fix:** Added bidirectional key mapping in settings_manager  
**Status:** ✅ Fixed

---

## To Download on Other Machine

```bash
cd /path/to/photo-slideshow
git fetch origin
git checkout photo-video-voice
git pull origin photo-video-voice
```

Then configure for Ally-only filtering:

```bash
# Edit ~/.photo_slideshow_config.json
{
  "album_name": "All Photos",
  "filter_people_names": ["Ally"]
}
```

Or use settings UI (Cmd+S) to configure.

---

## Testing Performed

1. ✅ Verified config loads without warnings
2. ✅ Verified Ally filter works (2,545 items: 2,488 photos, 23 videos)
3. ✅ Verified no-filter works (4,500 items from entire library)
4. ✅ Verified settings persist across restarts
5. ✅ Verified key mappings work bidirectionally

---

## Files Changed

**Modified:**
- config.py (validation fix, default change)
- photo_manager.py (error message improvements)
- settings_manager.py (new file, key mappings)
- config_schema.json (new file, settings schema)

**Deleted:**
- photo_slideshow_config.json (conflicting config)

**Added:**
- 4 documentation files

**Total:** 9 files changed, 1,817 insertions(+), 87 deletions(-)

---

## Commit Hash

```
70b0d24 - Fix configuration and filtering issues
```

**Pushed to:** origin/photo-video-voice
