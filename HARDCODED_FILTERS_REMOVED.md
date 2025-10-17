# Hardcoded Filters Removed - Using "allyslideshow" Smart Album

## Changes Made

### 1. Removed Hardcoded "Ally" Video Filter

**File:** `config.py` (line 58)

**Before:**
```python
'video_person_filter': 'Ally',  # Person name to filter videos
```

**After:**
```python
'video_person_filter': None,  # Person name to filter videos (None for no filter)
```

**Effect:** Videos are no longer filtered by person name by default.

---

### 2. Updated User Config to Use "allyslideshow" Smart Album

**File:** `~/.photo_slideshow_config.json`

**Changes:**
```json
{
  "album_name": "allyslideshow",
  "video_person_filter": null,
  "filter_by_people": false,
  "filter_people_names": [],
  "filter_by_places": [],
  "filter_by_keywords": []
}
```

**Effect:** 
- Slideshow loads from "allyslideshow" Smart Album (2563 items)
- No additional filtering applied
- Both photos and videos from the album will be shown

---

## Current Configuration

### Album Selection
- **Album:** `allyslideshow` (Smart Album with 2563 items)
- **Source:** Apple Photos Smart Album

### Filters (All Disabled)
- ✅ **Photo people filter:** Disabled (`filter_people_names: []`)
- ✅ **Photo places filter:** Disabled (`filter_by_places: []`)
- ✅ **Photo keywords filter:** Disabled (`filter_by_keywords: []`)
- ✅ **Video person filter:** Disabled (`video_person_filter: null`)

### What Gets Loaded
- ✅ All photos from "allyslideshow" Smart Album
- ✅ All videos from "allyslideshow" Smart Album
- ❌ Hidden photos (always excluded)
- ❌ RAW images (always excluded)

---

## Verification

Tested configuration loading:
```bash
python3 -c "from config import SlideshowConfig; c = SlideshowConfig(); c.load_config(); print('Album:', c.get('album_name')); print('Video filter:', c.get('video_person_filter'))"
```

**Output:**
```
Album: allyslideshow
Video filter: None
```

✅ Configuration is correct!

---

## How It Works

### 1. Album Loading (photo_manager.py)

```python
# Searches for album by name (case-insensitive)
for album in self.photos_db.albums:
    if album_title.lower() == "allyslideshow":
        target_album = album
        break

# Loads all photos/videos from that album
album_photos = target_album.photos
```

### 2. No Additional Filtering

Since all filter settings are disabled:
```python
use_filters = (
    self.config.get('filter_by_people', False) or      # False
    self.config.get('filter_people_names', []) or      # []
    self.config.get('filter_by_places', []) or         # []
    self.config.get('filter_by_keywords', [])          # []
)
# Result: use_filters = False
```

The slideshow uses album-based loading, not filter-based loading.

### 3. Video Loading (slideshow_controller.py)

```python
person_filter = self.config.get('video_person_filter')  # None

if person_filter:
    # Filter videos by person
else:
    # Load all videos from album (no filtering)
```

---

## What Changed from Before

### Before:
- ❌ Hardcoded "Ally" filter in config.py
- ❌ Loading from "All Photos" album (entire library)
- ❌ Videos filtered to only show "Ally"
- ❌ Photos showing everyone (but from entire library)

### After:
- ✅ No hardcoded filters
- ✅ Loading from "allyslideshow" Smart Album (2563 items)
- ✅ Videos show everyone in the album
- ✅ Photos show everyone in the album
- ✅ Only items in your Smart Album are shown

---

## Smart Album Benefits

Using a Smart Album gives you flexibility:

1. **Centralized Control:** Manage what's in the slideshow from Photos app
2. **Dynamic Updates:** Smart Album automatically updates based on its rules
3. **No Code Changes:** Adjust criteria in Photos without touching code
4. **Mix of Content:** Can include both photos and videos

### Your "allyslideshow" Smart Album:
- Contains 2563 items
- Likely has rules set in Photos app (e.g., date range, people, keywords, etc.)
- Automatically maintained by Photos

---

## To Change What's Shown

### Option 1: Modify Smart Album Rules (Recommended)
1. Open Photos app
2. Find "allyslideshow" in sidebar
3. Right-click → Edit Smart Album
4. Adjust criteria (people, dates, keywords, etc.)
5. Changes apply immediately to slideshow

### Option 2: Use Different Album
Change in settings (Cmd+S) or edit config:
```json
{
  "album_name": "SomeOtherAlbum"
}
```

### Option 3: Add Filters
Enable filters in settings (Cmd+S) or edit config:
```json
{
  "filter_people_names": ["Person1", "Person2"],
  "filter_by_places": ["Paris", "London"]
}
```
**Note:** Filters will override album selection!

---

## Restart Required

**To apply these changes:**

```bash
# Stop current slideshow (ESC or Cmd+Q)
# Then restart:
./slideshow_env/bin/python main_pygame.py
```

---

## Expected Behavior

After restart, the slideshow will:

1. ✅ Connect to Photos library
2. ✅ Search for "allyslideshow" Smart Album
3. ✅ Load all 2563 items from that album
4. ✅ Show both photos and videos
5. ✅ No filtering by person, place, or keyword
6. ✅ Shuffle randomly (if shuffle_photos is true)
7. ✅ Display each item for configured duration

---

## Log Messages to Look For

When you restart, check logs for:

```
INFO - Found X albums in Photos library
INFO - Album 'allyslideshow' found in Photos library
INFO - Found 2563 photos in album 'allyslideshow'
INFO - Successfully processed 2563 photos from album 'allyslideshow'
```

If album not found:
```
WARNING - Album 'allyslideshow' not found.
INFO - Available albums: All Photos, Favorites, ...
```

---

## Status: ✅ COMPLETE

Changes applied:
1. ✅ Removed hardcoded "Ally" filter from config.py
2. ✅ Updated user config to use "allyslideshow" album
3. ✅ Disabled all additional filters
4. ✅ Verified configuration loads correctly

**Ready to restart the slideshow!** 🎉
