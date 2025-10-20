# Configuration Files Explained

## Overview
There are **5 configuration-related JSON files** in the system. Here's what each one does:

---

## 1. **~/.photo_slideshow_config.json** ⭐ PRIMARY CONFIG
**Location:** `/Users/ken/.photo_slideshow_config.json`  
**Purpose:** Main user configuration file used by the slideshow  
**Used by:** `main_pygame.py`, `config.py`, `photo_manager.py`

**What it does:**
- Stores all user settings (slideshow interval, filters, video settings, etc.)
- Loaded on every slideshow startup
- Modified by settings UI (Cmd+S)
- This is THE configuration file that controls slideshow behavior

**Current settings:**
```json
{
  "album_name": "",
  "filter_people_names": ["Ally"],
  "SLIDESHOW_INTERVAL": 5,
  "VIDEO_MAX_DURATION": 5,
  "portrait_pairing": true,
  ...
}
```

**Why it exists:** User settings need to persist across runs and be editable without modifying code.

---

## 2. **config_schema.json** 📋 SETTINGS SCHEMA
**Location:** `./config_schema.json`  
**Purpose:** Defines the structure and validation rules for all settings  
**Used by:** `settings_manager.py`, `settings_window.py`

**What it does:**
- Defines all 27 available settings
- Specifies types (int, bool, string, enum)
- Sets validation rules (min/max values, allowed options)
- Provides labels and descriptions for settings UI
- Organizes settings into 6 groups (Display, Video, Photos, Voice, Filters, Advanced)

**Example:**
```json
{
  "slideshow_interval": {
    "type": "integer",
    "label": "Slideshow Interval",
    "description": "Time to display each photo",
    "default": 10,
    "min": 1,
    "max": 300,
    "unit": "seconds"
  }
}
```

**Why it exists:** Enables the settings UI to auto-generate controls with proper validation.

---

## 3. **config.json** 🧪 TEST/DEVELOPMENT CONFIG
**Location:** `./config.json`  
**Purpose:** Test configuration for settings UI development  
**Used by:** `settings_manager.py` (default parameter), test scripts

**What it does:**
- Used during development/testing of settings UI
- NOT used by the actual slideshow
- Contains example/test values
- Can be safely deleted or ignored

**Why it exists:** Allows testing settings UI without modifying the real user config.

---

## 4. **~/.photo_slideshow_cache.json** 💾 LOCATION CACHE
**Location:** `/Users/ken/.photo_slideshow_cache.json`  
**Purpose:** Caches location data for photos to avoid repeated API calls  
**Used by:** `cache_manager.py`, `location_service.py`

**What it does:**
- Stores GPS coordinates → location name mappings
- Example: `"36.6518,24.3936": "Santorini, Greece"`
- Reduces API calls to reverse geocoding service
- Improves performance when showing location overlays

**Why it exists:** Location lookups are slow/expensive, so we cache results.

---

## 5. **~/.photo_slideshow_download_signal.json** 📥 DOWNLOAD TRACKER
**Location:** `/Users/ken/.photo_slideshow_download_signal.json`  
**Purpose:** Tracks when new photos are downloaded from iCloud  
**Used by:** `cache_manager.py`, download utilities

**What it does:**
- Signals when new photos have been downloaded
- Triggers photo list refresh in running slideshow
- Contains timestamp and download metadata

**Why it exists:** Allows slideshow to detect and load newly downloaded photos without restart.

---

## 6. **photo_slideshow_config.json.BACKUP** 🗑️ OLD/BACKUP
**Location:** `./photo_slideshow_config.json.BACKUP`  
**Purpose:** Backup of old config file that was causing issues  
**Used by:** Nothing (renamed/disabled)

**What it does:**
- Previously contained hardcoded Ally filter
- Caused slideshow to only show Ally photos
- Renamed to .BACKUP to disable it

**Why it exists:** Historical artifact from debugging. Can be deleted.

---

## Summary Table

| File | Location | Purpose | Used By Slideshow |
|------|----------|---------|-------------------|
| `.photo_slideshow_config.json` | `~/.` | **Main user settings** | ✅ YES - Primary |
| `config_schema.json` | `./` | Settings schema/validation | ✅ YES - Settings UI |
| `config.json` | `./` | Test/dev config | ❌ NO - Testing only |
| `.photo_slideshow_cache.json` | `~/.` | Location cache | ✅ YES - Performance |
| `.photo_slideshow_download_signal.json` | `~/.` | Download tracking | ✅ YES - Auto-refresh |
| `photo_slideshow_config.json.BACKUP` | `./` | Old backup | ❌ NO - Disabled |

---

## Why Multiple Files?

### Separation of Concerns
1. **User Settings** (`~/.photo_slideshow_config.json`) - What the user configures
2. **Schema** (`config_schema.json`) - How settings are structured/validated
3. **Cache** (`~/.photo_slideshow_cache.json`) - Performance optimization data
4. **Signals** (`~/.photo_slideshow_download_signal.json`) - Inter-process communication

### Best Practices
- **User config in home directory** (`~/.`) - Standard Unix convention
- **Schema in project directory** (`./`) - Part of application code
- **Separate cache from config** - Cache can be deleted without losing settings
- **Test config separate from real config** - Safe development/testing

---

## Which File Should You Edit?

**To change slideshow behavior:**
- Edit `~/.photo_slideshow_config.json`
- Or use settings UI (Cmd+S)

**To add new settings:**
- Add to `config_schema.json` (defines the setting)
- Add to `config.py` DEFAULT_CONFIG (provides default value)
- Settings UI will auto-generate controls

**Don't edit:**
- `config.json` (test file, not used by slideshow)
- `.photo_slideshow_cache.json` (auto-managed)
- `.photo_slideshow_download_signal.json` (auto-managed)

---

## Cleanup Recommendations

**Can be deleted:**
- `photo_slideshow_config.json.BACKUP` (old backup, no longer needed)
- `config.json` (test file, only needed for settings UI development)

**Should keep:**
- `~/.photo_slideshow_config.json` (your settings!)
- `config_schema.json` (required for settings UI)
- `~/.photo_slideshow_cache.json` (performance optimization)
- `~/.photo_slideshow_download_signal.json` (auto-refresh feature)
