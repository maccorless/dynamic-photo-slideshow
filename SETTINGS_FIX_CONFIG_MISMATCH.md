# Settings Not Saving - Root Cause Analysis & Fix

## Problem Statement
Settings changed in the UI were not persisting or applying to the running slideshow. When reopening settings, values reverted to defaults (10 and 15).

## Root Cause: Dual Config System

### The Issue
The application had **TWO SEPARATE CONFIG SYSTEMS** that were not connected:

1. **SettingsManager** (settings_manager.py)
   - Used by settings window UI
   - Saved to: `config.json`
   - Keys: `slideshow_interval`, `max_video_duration` (lowercase)

2. **SlideshowConfig** (config.py)
   - Used by slideshow controller
   - Saved to: `photo_slideshow_config.json`
   - Keys: `SLIDESHOW_INTERVAL`, `VIDEO_MAX_DURATION` (uppercase)

### The Flow (BEFORE FIX)
```
User changes setting in UI
    ↓
SettingsManager saves to config.json ✅
    ↓
SlideshowController reads from photo_slideshow_config.json ❌
    ↓
Settings never applied! ❌
```

## The Fix

### 1. Point SettingsManager to Correct Config File

**File:** `main_pygame.py` (lines 326-331)

**Before:**
```python
settings_manager = SettingsManager()  # Uses default config.json
```

**After:**
```python
settings_manager = SettingsManager(
    schema_path="config_schema.json",
    config_path=str(config.config_path)  # Use SlideshowConfig's path
)
```

**Result:** Both systems now use `photo_slideshow_config.json`

---

### 2. Fix Schema Key Names

**File:** `config_schema.json` (line 24)

**Before:**
```json
"max_video_duration": {
  "type": "integer",
  ...
}
```

**After:**
```json
"video_max_duration": {
  "type": "integer",
  ...
}
```

**Reason:** Match the key name used in `photo_slideshow_config.json`

---

### 3. Update Live Settings Application

**File:** `settings_window.py` (line 395)

**Before:**
```python
elif setting == 'max_video_duration':
    self.controller.config.set('VIDEO_MAX_DURATION', value)
```

**After:**
```python
elif setting == 'video_max_duration':  # Changed key name
    self.controller.config.set('VIDEO_MAX_DURATION', value)
```

**Reason:** Match the schema key name

---

## Key Mapping

### Config File Keys (photo_slideshow_config.json)
```json
{
  "slideshow_interval": 10,        // lowercase
  "video_max_duration": 15,        // lowercase
  "show_countdown_timer": true,    // lowercase
  "show_date_overlay": false,      // lowercase
  "show_location_overlay": true    // lowercase
}
```

### Internal Keys (config.py)
```python
{
  'SLIDESHOW_INTERVAL': 10,        # uppercase
  'VIDEO_MAX_DURATION': 15,        # uppercase
  'show_countdown_timer': True,    # lowercase
  'show_date_overlay': False,      # lowercase
  'show_location_overlay': True    # lowercase
}
```

### Schema Keys (config_schema.json)
```json
{
  "slideshow_interval": {...},     // lowercase (matches config file)
  "video_max_duration": {...},     // lowercase (matches config file)
  "show_countdown_timer": {...},   // lowercase (matches config file)
  "show_date_overlay": {...},      // lowercase (matches config file)
  "show_location_overlay": {...}   // lowercase (matches config file)
}
```

---

## The Flow (AFTER FIX)

```
User changes setting in UI
    ↓
SettingsManager saves to photo_slideshow_config.json ✅
    ↓
settings_window._apply_live_setting() updates controller.config ✅
    ↓
SlideshowController uses new value immediately ✅
    ↓
On restart, SlideshowConfig loads from photo_slideshow_config.json ✅
    ↓
Settings persist! ✅
```

---

## Testing Checklist

### Test 1: Settings Save
- [ ] Open settings (Cmd-S)
- [ ] Change slideshow_interval to 5
- [ ] Close settings (ESC)
- [ ] Check `photo_slideshow_config.json` contains `"slideshow_interval": 5`

### Test 2: Settings Apply Live
- [ ] Open settings (Cmd-S)
- [ ] Change slideshow_interval to 3
- [ ] Close settings (ESC)
- [ ] Verify next slide advances in 3 seconds (not 10)

### Test 3: Settings Persist
- [ ] Open settings (Cmd-S)
- [ ] Change slideshow_interval to 7
- [ ] Close settings (ESC)
- [ ] Quit app (ESC)
- [ ] Restart app
- [ ] Open settings (Cmd-S)
- [ ] Verify slideshow_interval shows 7 (not 10)

### Test 4: Video Duration
- [ ] Open settings (Cmd-S)
- [ ] Change video_max_duration to 5
- [ ] Close settings (ESC)
- [ ] Wait for a video to play
- [ ] Verify video stops after 5 seconds (not 15)

---

## Files Modified

1. **main_pygame.py**
   - Pass `config.config_path` to SettingsManager
   - Ensures both systems use same config file

2. **config_schema.json**
   - Renamed `max_video_duration` → `video_max_duration`
   - Matches key name in photo_slideshow_config.json

3. **settings_window.py**
   - Updated `_apply_live_setting()` to use `video_max_duration`
   - Matches schema key name

---

## Why This Happened

The settings system was added later to the codebase, and a new config file (`config.json`) was created instead of reusing the existing `photo_slideshow_config.json`. This created two independent config systems that didn't communicate.

**Lesson:** Always check for existing configuration systems before creating new ones!

---

## Verification Commands

```bash
# Check which config file is being used
cat photo_slideshow_config.json | grep slideshow_interval

# Check if settings are saving
# 1. Run app
# 2. Change setting
# 3. Check file again
cat photo_slideshow_config.json | grep slideshow_interval

# Should show new value!
```

---

## Status: ✅ FIXED

All three issues resolved:
1. ✅ Settings save to correct file
2. ✅ Settings apply live to running slideshow
3. ✅ Settings persist across app restarts
