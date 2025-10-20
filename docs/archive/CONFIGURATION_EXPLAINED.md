# Configuration Explained - Album Names and Filters

## Current Configuration

### Your Active Settings (`~/.photo_slideshow_config.json`)

```json
{
  "album_name": "All Photos",
  "photo_limit": 0,
  "people_filter": "",
  "places_filter": "",
  "keywords_filter": "",
  "filter_logic": "AND"
}
```

---

## Album Name Configuration

### Setting: `album_name`

**Current Value:** `"All Photos"`  
**Default:** `"All Photos"` (in both config.py and config_schema.json)  
**Location in UI:** Advanced tab → Album Name

### What It Does:

The slideshow looks for an album in Apple Photos with this exact name (case-insensitive) and loads photos from it.

**"All Photos"** is a special built-in album in Apple Photos that contains every photo in your library.

### How It Works:

```python
# photo_manager.py lines 149-167
# 1. Search for album by name
for album in self.photos_db.albums:
    if str(album_title).lower() == self.album_name.lower():
        target_album = album
        break

# 2. If album found, load photos from it
if target_album:
    album_photos = target_album.photos
    # Process each photo...

# 3. If album NOT found, fall back to filter-based loading
else:
    return self._load_photos_with_filters()
```

### Important Behavior:

- ✅ **Album found** → Loads photos from that album
- ⚠️ **Album not found** → Falls back to loading ALL photos with filters applied
- ⚠️ **Album empty** → Falls back to random photos from entire library

---

## Filter System

### When Filters Are Used

Filters are used in **two scenarios**:

#### 1. **Explicit Filter Mode** (lines 138-146)
If ANY of these settings are configured:
- `filter_by_people` is True
- `filter_people_names` is not empty
- `filter_by_places` is not empty
- `filter_by_keywords` is not empty

Then the album is **ignored** and filters are used instead.

#### 2. **Album Fallback** (line 166)
If the specified album is not found, filters are used as fallback.

---

## Available Filters

### 1. People Filter

**Settings:**
- `people_filter` (schema) → maps to `filter_people_names` (config.py)
- `filter_by_people` (config.py only, not in schema)

**Current Value:** `""` (empty = disabled)

**How to Use:**
```json
{
  "people_filter": "John,Jane,Alice"
}
```

**What It Does:**
```python
# photo_manager.py lines 246-268
# Uses osxphotos direct search
for person_name in filter_people_names:
    person_photos = self.photos_db.photos(persons=[person_name.strip()])
    filtered_photos.extend(person_photos)
```

**Matching Logic:**
- Searches for photos containing ANY of the specified people (OR logic)
- Uses osxphotos' built-in person detection
- Partial name matching supported (e.g., "John" matches "John Smith")
- Removes duplicates if same photo has multiple people

**Example:**
- `"people_filter": "Alice"` → Photos with Alice
- `"people_filter": "Alice,Bob"` → Photos with Alice OR Bob

---

### 2. Places Filter

**Setting:** `places_filter` (schema) → maps to `filter_by_places` (config.py)

**Current Value:** `""` (empty = disabled)

**How to Use:**
```json
{
  "places_filter": "Paris,London,Tokyo"
}
```

**What It Does:**
```python
# photo_manager.py lines 357-373
# Checks photo's place name
place_name = photo.place.name
# Substring matching
return any(place_filter.lower() in place_name_lower for place_filter in filter_places)
```

**Matching Logic:**
- Substring matching (e.g., "Paris" matches "Paris, France")
- Case-insensitive
- Default is OR logic (any place matches)
- Can be changed to AND logic with `filter_logic` setting

**Example:**
- `"places_filter": "Paris"` → Photos taken in Paris
- `"places_filter": "Paris,France"` → Photos with "Paris" OR "France" in location

---

### 3. Keywords Filter

**Setting:** `keywords_filter` (schema) → maps to `filter_by_keywords` (config.py)

**Current Value:** `""` (empty = disabled)

**How to Use:**
```json
{
  "keywords_filter": "vacation,beach,sunset"
}
```

**What It Does:**
```python
# photo_manager.py lines 375-381
# Checks photo's keywords
photo_keywords = [k.lower() for k in photo.keywords]
return any(keyword.lower() in photo_keywords for keyword in filter_keywords)
```

**Matching Logic:**
- Exact keyword matching (not substring)
- Case-insensitive
- OR logic (any keyword matches)

**Example:**
- `"keywords_filter": "vacation"` → Photos tagged with "vacation"
- `"keywords_filter": "vacation,beach"` → Photos tagged with "vacation" OR "beach"

---

### 4. Filter Logic

**Setting:** `filter_logic` (schema) → maps to `overall_filter_logic` (config.py)

**Current Value:** `"AND"`  
**Options:** `"AND"` or `"OR"`

**What It Does:**

Controls how multiple filter types are combined:

- **`"AND"`** (default): Photo must match ALL active filters
  - Example: People filter AND Places filter AND Keywords filter
  
- **`"OR"`**: Photo must match ANY active filter
  - Example: People filter OR Places filter OR Keywords filter

**Example:**
```json
{
  "people_filter": "Alice",
  "places_filter": "Paris",
  "filter_logic": "AND"
}
```
Result: Photos with Alice AND taken in Paris

```json
{
  "people_filter": "Alice",
  "places_filter": "Paris",
  "filter_logic": "OR"
}
```
Result: Photos with Alice OR taken in Paris

---

## Hidden Filters (Always Applied)

### 1. Photo Filters - In `_extract_photo_metadata()` (lines 383-388)

These filters are **always applied** to photos regardless of settings:

```python
# Skip hidden photos
if photo.hidden:
    return None

# Skip RAW images
if photo.has_raw:
    return None
```

**What Gets Filtered Out:**
- ✅ Hidden photos (marked as hidden in Photos)
- ✅ RAW images (CR2, NEF, ARW, etc.)

### 2. Video Filters - In `config.py` (lines 58-59)

 **IMPORTANT: Videos have a HARDCODED filter!**

```python
'video_person_filter': 'Ally',  # Person name to filter videos
'video_local_only': True,       # Only use locally available videos
```

**What This Does:**
- Only videos with "Ally" are shown in the slideshow
- Only locally available videos (not iCloud-only)
- This is set in `config.py` defaults, NOT in your user config
- This setting is NOT exposed in the settings UI (not in schema)

**How It Works:**
```python
# slideshow_controller.py lines 878-894
person_filter = self.config.get('video_person_filter')  # Gets 'Ally'

if person_filter:
    # Search for videos with this person
    all_photos = self.photo_manager.photos_db.photos(persons=[person_filter])
    candidate_videos = [p for p in all_photos if p.ismovie]
```

**To Disable This Filter:**
You need to add to your `~/.photo_slideshow_config.json`:
```json
{
  "video_person_filter": null
}
```

Or set it to empty string:
```json
{
  "video_person_filter": ""
}
```

---

## Photo Limit

**Setting:** `photo_limit` (schema) → maps to `max_photos_limit` (config.py)

**Current Value:** `0` (no limit)  
**Default:** `0` (schema) vs `500` (config.py)

**What It Does:**

Limits the maximum number of photos loaded:
- `0` = No limit (load all matching photos)
- `> 0` = Load up to this many photos

**Note:** This setting is defined in config.py but **not actually enforced** in the current code. The filter system loads all matching photos regardless of this setting.

---

## Complete Flow Diagram

```
START
  ↓
Check if any filters are active?
  ├─ YES → Use _load_photos_with_filters()
  │         ↓
  │         1. Apply people filter (if set)
  │         2. Apply places filter (if set)
  │         3. Apply keywords filter (if set)
  │         4. Combine with filter_logic (AND/OR)
  │         5. Always skip hidden & RAW
  │         6. Shuffle if shuffle_photos=true
  │         ↓
  │         RETURN filtered photos
  │
  └─ NO → Use album-based loading
            ↓
            Search for album by name
            ├─ FOUND → Load photos from album
            │          ↓
            │          Skip hidden & RAW
            │          ↓
            │          RETURN album photos
            │
            └─ NOT FOUND → Fall back to _load_photos_with_filters()
                           (loads ALL photos with filters)
```

---

## Configuration Examples

### Example 1: Use Specific Album (Current Setup)

```json
{
  "album_name": "All Photos",
  "people_filter": "",
  "places_filter": "",
  "keywords_filter": ""
}
```

**Result:** Loads all photos from "All Photos" album (which is everything)

---

### Example 2: Filter by People Only

```json
{
  "album_name": "All Photos",
  "people_filter": "Alice,Bob",
  "places_filter": "",
  "keywords_filter": ""
}
```

**Result:** 
- Ignores "All Photos" album
- Loads only photos with Alice OR Bob
- Uses entire library, not album

---

### Example 3: Filter by People AND Place

```json
{
  "album_name": "All Photos",
  "people_filter": "Alice",
  "places_filter": "Paris",
  "filter_logic": "AND"
}
```

**Result:**
- Ignores "All Photos" album
- Loads photos with Alice AND taken in Paris

---

### Example 4: Multiple Filters with OR Logic

```json
{
  "album_name": "All Photos",
  "people_filter": "Alice",
  "places_filter": "Paris",
  "keywords_filter": "vacation",
  "filter_logic": "OR"
}
```

**Result:**
- Ignores "All Photos" album
- Loads photos with Alice OR taken in Paris OR tagged "vacation"

---

### Example 5: Use Custom Album (No Filters)

```json
{
  "album_name": "Family Photos",
  "people_filter": "",
  "places_filter": "",
  "keywords_filter": ""
}
```

**Result:**
- Loads photos from "Family Photos" album
- If album doesn't exist, falls back to ALL photos

---

## Key Mappings (Schema ↔ Config.py)

| Schema Name (UI) | Config.py Name | Notes |
|------------------|----------------|-------|
| `album_name` | `album_name` | Same name ✅ |
| `people_filter` | `filter_people_names` | Different name ⚠️ |
| `places_filter` | `filter_by_places` | Different name ⚠️ |
| `keywords_filter` | `filter_by_keywords` | Different name ⚠️ |
| `filter_logic` | `overall_filter_logic` | Different name ⚠️ |
| `photo_limit` | `max_photos_limit` | Different name ⚠️ |

These mappings are handled by `settings_manager.py` in the `KEY_MAPPING` dictionaries.

---

## Important Notes

### 1. Album vs Filters - Mutually Exclusive

**If ANY filter is set → Album is IGNORED**

```python
# photo_manager.py lines 138-146
use_filters = (
    self.config.get('filter_by_people', False) or 
    self.config.get('filter_people_names', []) or
    self.config.get('filter_by_places', []) or 
    self.config.get('filter_by_keywords', [])
)

if use_filters:
    return self._load_photos_with_filters()  # Album ignored!
```

### 2. Empty Filters = No Filtering

If all filter fields are empty (`""`), the album is used.

### 3. Fallback Behavior

If album doesn't exist:
- Falls back to filter-based loading
- If no filters set, loads ALL photos from library
- Shuffles if `shuffle_photos` is true

### 4. Hidden Filters Always Apply

Photos are ALWAYS filtered to exclude:
- Hidden photos
- RAW images

This happens regardless of your settings.

### 5. osxphotos Does the Heavy Lifting

All photo selection uses osxphotos library:
- `osxphotos.PhotosDB()` - Connects to Photos library
- `photos_db.albums` - Lists all albums
- `photos_db.photos(persons=[...])` - Searches by person
- `photo.place`, `photo.keywords` - Metadata access

---

## How to Change Settings

### Option 1: Settings UI (Recommended)

1. Start slideshow
2. Press **Cmd+S** (macOS) or **Ctrl+S** (Windows/Linux)
3. Navigate to appropriate tab:
   - **Advanced** → Album Name
   - **Filters** → People, Places, Keywords, Filter Logic
   - **Photos** → Photo Limit
4. Make changes
5. Close settings (ESC) - auto-saves
6. Restart slideshow if needed

### Option 2: Edit Config File

```bash
nano ~/.photo_slideshow_config.json

# Make changes, save
# Restart slideshow
```

---

## Summary

**Current Configuration:**
- ✅ Album: "All Photos" (built-in, contains everything)
- ✅ People Filter: Disabled (empty)
- ✅ Places Filter: Disabled (empty)
- ✅ Keywords Filter: Disabled (empty)
- ✅ Filter Logic: AND
- ✅ Photo Limit: 0 (no limit)
- ⚠️ **Video Person Filter: "Ally" (HARDCODED in config.py)**
- ✅ Video Local Only: True

**What's Happening:**
- Slideshow loads photos from "All Photos" album
- No filtering applied to photos (except hidden & RAW)
- All photos in your library are available
- Photos are shuffled randomly
- ⚠️ **Videos are filtered to only show "Ally"**
- Videos must be locally available (not iCloud-only)

**To Filter Photos:**
- Set `people_filter` to names (e.g., "Alice,Bob")
- OR set `places_filter` to locations (e.g., "Paris,London")
- OR set `keywords_filter` to tags (e.g., "vacation,beach")
- Album will be ignored once any filter is set!

**To Disable Video Filter:**
- Add to `~/.photo_slideshow_config.json`: `"video_person_filter": null`
- Or set to empty string: `"video_person_filter": ""`
