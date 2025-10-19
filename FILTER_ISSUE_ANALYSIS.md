# Filter Issue Analysis

## Problem Report

User reports: "it does seem to be showing only photos with ally in it right now"

## Investigation

### 1. Config File Key Names Were Wrong

**Problem:** The config file had schema key names instead of config.py key names.

**Before Fix:**
```json
{
  "people_filter": "",           // WRONG - schema name
  "places_filter": "",           // WRONG - schema name
  "keywords_filter": "",         // WRONG - schema name
  "filter_logic": "AND",         // WRONG - schema name
  "slideshow_interval": 5        // WRONG - should be UPPERCASE
}
```

**After Fix:**
```json
{
  "filter_people_names": "",     // CORRECT - config.py name
  "filter_by_places": "",        // CORRECT - config.py name
  "filter_by_keywords": "",      // CORRECT - config.py name
  "overall_filter_logic": "AND", // CORRECT - config.py name
  "SLIDESHOW_INTERVAL": 5        // CORRECT - UPPERCASE
}
```

**Status:** ✅ FIXED - Ran script to convert all keys to correct names

---

### 2. "Ally" Filter Investigation

**Findings:**

#### Video Filter (CONFIRMED)
- **Location:** `config.py` line 58
- **Setting:** `'video_person_filter': 'Ally'`
- **Effect:** Only videos with "Ally" are shown
- **Status:** ⚠️ HARDCODED in defaults

#### Photo Filter (NOT FOUND)
- **Searched:** All of config.py for "Ally" or "ally"
- **Result:** NO photo filter for "Ally" found
- **Current photo filters:** All empty (`""`)

```json
{
  "filter_people_names": "",     // Empty - no people filter
  "filter_by_places": "",        // Empty - no places filter  
  "filter_by_keywords": ""       // Empty - no keywords filter
}
```

---

## Current Configuration Status

### What Should Be Happening:

1. **Photos:** Load from "All Photos" album (no filtering except hidden/RAW)
2. **Videos:** Only show videos with "Ally" (hardcoded filter)

### Photo Loading Logic:

```python
# photo_manager.py lines 138-146
use_filters = (
    self.config.get('filter_by_people', False) or 
    self.config.get('filter_people_names', []) or
    self.config.get('filter_by_places', []) or 
    self.config.get('filter_by_keywords', [])
)

if use_filters:
    return self._load_photos_with_filters()  # Use filters
else:
    # Load from album
```

**Current State:**
- `filter_by_people`: False (default)
- `filter_people_names`: "" (empty string)
- `filter_by_places`: "" (empty string)
- `filter_by_keywords`: "" (empty string)

**Result:** `use_filters` should be FALSE → Load from album

---

## Possible Explanations for "Only Ally Photos"

### Theory 1: Empty String vs Empty List

**Problem:** The code checks for empty list `[]` but config has empty string `""`

```python
# Line 140
self.config.get('filter_people_names', []) or  # Expects list, gets string

# Empty string "" is falsy in Python
# Empty list [] is also falsy
# So both should work the same
```

**Status:** ❌ NOT THE ISSUE - Both are falsy

---

### Theory 2: Album "All Photos" Doesn't Exist

**Problem:** If "All Photos" album doesn't exist, it falls back to filter mode

```python
# photo_manager.py line 162
if not target_album:
    self.logger.warning(f"Album '{self.album_name}' not found, falling back to all photos")
    return self._load_photos_with_filters()
```

**If filters are empty, this loads ALL photos from library**

**Status:** ⚠️ POSSIBLE - Need to check logs

---

### Theory 3: Portrait Pairing Filter

**Current Settings:**
```json
{
  "portrait_pairing": true,
  "min_people_count": 2
}
```

**Code:** `photo_manager.py` line 27
```python
"min_people_count": 1,  // Default is 1, but user has 2
```

**Effect:** For portrait pairing, photos need at least 2 people

**Status:** ⚠️ POSSIBLE - But this shouldn't filter ALL photos, only affect pairing

---

### Theory 4: Hidden Filter in Photo Metadata Extraction

**Always Applied:**
```python
# photo_manager.py lines 386-388
if photo.hidden:
    return None
if photo.has_raw:
    return None
```

**Status:** ✅ NORMAL - This is expected behavior

---

## Recommended Actions

### 1. Check Logs

Run the slideshow and check for these log messages:

```bash
# Look for album verification
grep "Album.*found" slideshow.log

# Look for filter usage
grep "filter" slideshow.log

# Look for photo loading
grep "Successfully processed" slideshow.log
```

**Key Questions:**
- Is "All Photos" album found?
- Are filters being used?
- How many photos are loaded?

---

### 2. Test with Explicit Album

Try changing to a different album to see if behavior changes:

```json
{
  "album_name": "Recents"  // Or "Favorites"
}
```

---

### 3. Check if "Ally" is in Album Name

**Possibility:** Maybe the album being used is actually named something with "Ally"?

```bash
# Check what album is actually being used
grep "album" ~/.photo_slideshow_config.json
```

**Current:** `"album_name": "All Photos"` ✅

---

### 4. Add Debug Logging

Temporarily add to photo_manager.py to see what's happening:

```python
# After line 143
self.logger.info(f"DEBUG: use_filters = {use_filters}")
self.logger.info(f"DEBUG: filter_by_people = {self.config.get('filter_by_people')}")
self.logger.info(f"DEBUG: filter_people_names = {self.config.get('filter_people_names')}")
self.logger.info(f"DEBUG: filter_by_places = {self.config.get('filter_by_places')}")
self.logger.info(f"DEBUG: filter_by_keywords = {self.config.get('filter_by_keywords')}")
```

---

## Summary

### What We Know:
1. ✅ Config file keys were wrong - FIXED
2. ✅ Video filter for "Ally" exists - CONFIRMED
3. ❌ NO photo filter for "Ally" found in config
4. ❓ User reports photos are filtered to "Ally" - UNEXPLAINED

### Next Steps:
1. Check slideshow logs for actual behavior
2. Verify "All Photos" album exists and is being used
3. Add debug logging to see filter evaluation
4. Test with different album to isolate issue

### Hypothesis:
The issue might be related to:
- Album not found → fallback behavior
- Portrait pairing with min_people_count=2
- Some other filter we haven't identified yet
- OR user might be seeing videos only (which ARE filtered to Ally)
