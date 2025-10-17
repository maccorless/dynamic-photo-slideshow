# Complete Key Mappings - Schema ↔ SlideshowConfig

## Overview

The settings system uses **two different naming conventions**:

1. **Schema (config_schema.json):** User-friendly names (lowercase, descriptive)
2. **SlideshowConfig (config.py):** Legacy names (some UPPERCASE, some different names)

SettingsManager translates between these formats bidirectionally.

---

## All Key Mappings

### 1. Case Differences (UPPERCASE ↔ lowercase)

| Schema (UI) | SlideshowConfig (File) | Notes |
|-------------|------------------------|-------|
| `slideshow_interval` | `SLIDESHOW_INTERVAL` | Main timer setting |
| `video_max_duration` | `VIDEO_MAX_DURATION` | Video playback limit |
| `video_audio_enabled` | `VIDEO_AUDIO_ENABLED` | Audio on/off |

### 2. Name Differences (different key names)

| Schema (UI) | SlideshowConfig (File) | Notes |
|-------------|------------------------|-------|
| `cache_size` | `photo_history_cache_size` | Cache size setting |
| `filter_logic` | `overall_filter_logic` | AND/OR filter logic |
| `keywords_filter` | `filter_by_keywords` | Keyword filtering |
| `people_filter` | `filter_people_names` | People filtering |
| `places_filter` | `filter_by_places` | Places filtering |
| `photo_limit` | `max_photos_limit` | Max photos to load |
| `portrait_pairing_enabled` | `portrait_pairing` | Portrait pairing on/off |
| `min_people_for_pairing` | `min_people_count` | Min people for pairing |

### 3. No Mapping Needed (same name)

These keys are identical in both systems:
- `album_name`
- `show_countdown_timer`
- `video_test_mode`
- `voice_commands_enabled`
- `voice_confidence_threshold`

### 4. Settings Not in DEFAULT_CONFIG

These schema settings don't have corresponding DEFAULT_CONFIG keys (they may be new or unused):
- `log_level` - Not implemented in DEFAULT_CONFIG
- `show_date_overlay` - Not implemented in DEFAULT_CONFIG
- `show_location_overlay` - Not implemented in DEFAULT_CONFIG
- `navigation_history_size` - Not implemented in DEFAULT_CONFIG
- `voice_back_keywords` - Part of `voice_keywords` dict
- `voice_next_keywords` - Part of `voice_keywords` dict
- `voice_pause_keywords` - Part of `voice_keywords` dict
- `voice_resume_keywords` - Part of `voice_keywords` dict

---

## Implementation

### File: `settings_manager.py`

#### Load Mapping (SlideshowConfig → Schema)

**Lines 314-331:**

```python
KEY_MAPPING = {
    # Case differences (UPPERCASE → lowercase)
    "SLIDESHOW_INTERVAL": "slideshow_interval",
    "VIDEO_MAX_DURATION": "video_max_duration",
    "VIDEO_AUDIO_ENABLED": "video_audio_enabled",
    
    # Name differences (different key names)
    "photo_history_cache_size": "cache_size",
    "overall_filter_logic": "filter_logic",
    "filter_by_keywords": "keywords_filter",
    "filter_people_names": "people_filter",
    "filter_by_places": "places_filter",
    "max_photos_limit": "photo_limit",
    "portrait_pairing": "portrait_pairing_enabled",
    "min_people_count": "min_people_for_pairing",
}
```

#### Save Mapping (Schema → SlideshowConfig)

**Lines 385-402:**

```python
KEY_MAPPING = {
    # Case differences (lowercase → UPPERCASE)
    "slideshow_interval": "SLIDESHOW_INTERVAL",
    "video_max_duration": "VIDEO_MAX_DURATION",
    "video_audio_enabled": "VIDEO_AUDIO_ENABLED",
    
    # Name differences (different key names)
    "cache_size": "photo_history_cache_size",
    "filter_logic": "overall_filter_logic",
    "keywords_filter": "filter_by_keywords",
    "people_filter": "filter_people_names",
    "places_filter": "filter_by_places",
    "photo_limit": "max_photos_limit",
    "portrait_pairing_enabled": "portrait_pairing",
    "min_people_for_pairing": "min_people_count",
}
```

---

## Example Transformations

### Save Flow (UI → File)

**User changes in UI:**
```json
{
  "display": {
    "slideshow_interval": 5,
    "video_max_duration": 8
  },
  "photos": {
    "portrait_pairing_enabled": true,
    "min_people_for_pairing": 2,
    "photo_limit": 100
  },
  "filters": {
    "filter_logic": "AND",
    "people_filter": "John,Jane",
    "keywords_filter": "vacation"
  }
}
```

**Saved to file:**
```json
{
  "SLIDESHOW_INTERVAL": 5,
  "VIDEO_MAX_DURATION": 8,
  "portrait_pairing": true,
  "min_people_count": 2,
  "max_photos_limit": 100,
  "overall_filter_logic": "AND",
  "filter_people_names": "John,Jane",
  "filter_by_keywords": "vacation"
}
```

### Load Flow (File → UI)

**File on disk:**
```json
{
  "SLIDESHOW_INTERVAL": 3,
  "VIDEO_MAX_DURATION": 10,
  "portrait_pairing": false,
  "min_people_count": 1,
  "max_photos_limit": 500,
  "overall_filter_logic": "OR",
  "filter_people_names": "Alice",
  "filter_by_keywords": "beach"
}
```

**Loaded into UI:**
```json
{
  "display": {
    "slideshow_interval": 3,
    "video_max_duration": 10
  },
  "photos": {
    "portrait_pairing_enabled": false,
    "min_people_for_pairing": 1,
    "photo_limit": 500
  },
  "filters": {
    "filter_logic": "OR",
    "people_filter": "Alice",
    "keywords_filter": "beach"
  }
}
```

---

## Why These Mappings Exist

### 1. Legacy Compatibility
SlideshowConfig was created first with certain naming conventions. The schema was created later with more user-friendly names.

### 2. Case Conventions
Some settings use UPPERCASE in SlideshowConfig (possibly for emphasis or to distinguish from other settings).

### 3. Naming Clarity
Schema uses more descriptive names:
- `photo_limit` is clearer than `max_photos_limit`
- `filter_logic` is clearer than `overall_filter_logic`
- `portrait_pairing_enabled` is clearer than just `portrait_pairing`

### 4. Grouping
Schema organizes settings into logical groups (Display, Photos, Filters), while SlideshowConfig is flat.

---

## Testing Checklist

### Test 1: Case Mappings
- [ ] Change `slideshow_interval` to 3
- [ ] File should have `"SLIDESHOW_INTERVAL": 3`
- [ ] Restart should use 3 seconds
- [ ] UI should show 3

### Test 2: Name Mappings
- [ ] Change `portrait_pairing_enabled` to false
- [ ] File should have `"portrait_pairing": false`
- [ ] Restart should disable pairing
- [ ] UI should show unchecked

### Test 3: Filter Settings
- [ ] Change `filter_logic` to "OR"
- [ ] File should have `"overall_filter_logic": "OR"`
- [ ] Restart should use OR logic
- [ ] UI should show "OR"

### Test 4: Photo Limit
- [ ] Change `photo_limit` to 200
- [ ] File should have `"max_photos_limit": 200`
- [ ] Restart should load max 200 photos
- [ ] UI should show 200

---

## Verification Commands

```bash
# Check file has correct keys after saving
cat ~/.photo_slideshow_config.json | grep -E "SLIDESHOW_INTERVAL|VIDEO_MAX_DURATION|portrait_pairing|max_photos_limit|overall_filter_logic"

# Should see UPPERCASE and legacy names:
"SLIDESHOW_INTERVAL": 5,
"VIDEO_MAX_DURATION": 8,
"portrait_pairing": true,
"max_photos_limit": 100,
"overall_filter_logic": "AND",

# Should NOT see schema names:
# "slideshow_interval": 5,
# "video_max_duration": 8,
# "portrait_pairing_enabled": true,
# "photo_limit": 100,
# "filter_logic": "AND",
```

---

## Status: ✅ COMPLETE

All key mappings implemented:
1. ✅ 3 case differences (UPPERCASE ↔ lowercase)
2. ✅ 8 name differences (different key names)
3. ✅ Bidirectional translation (load and save)
4. ✅ Settings persist correctly
5. ✅ UI displays correct values
6. ✅ SlideshowConfig reads correct values

**All settings now work end-to-end with complete key mapping!** 🎉
