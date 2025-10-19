# Album Name Configuration

## Current Configuration

**Album Name:** `"All Photos"`

This is configured in:
- `~/.photo_slideshow_config.json`: `"album_name": "All Photos"`
- `config_schema.json`: Default is `"All Photos"`
- `config.py`: Default is now `"All Photos"` (was `"photoframe"`)

---

## What is "All Photos"?

**"All Photos"** is a **built-in album in Apple Photos** that contains every photo in your library. It should always exist and doesn't need to be created manually.

### Advantages:
- ✅ Always exists (no manual setup required)
- ✅ Contains all photos in your library
- ✅ Automatically updated when you add/remove photos
- ✅ No need to manually add photos to an album

---

## How Album Selection Works

### 1. Album Verification (photo_manager.py)

When the slideshow starts, it:

1. Connects to Apple Photos library
2. Lists all available albums
3. Searches for album matching `album_name` (case-insensitive)
4. If found → Uses that album
5. If NOT found → Shows warning and uses **all photos as fallback**

### 2. Fallback Behavior

**Important:** If the specified album doesn't exist, the slideshow **still works** by using all photos from your library as a fallback.

```python
# photo_manager.py line 120
return True  # Allow fallback
```

This means:
- ✅ Slideshow never fails due to missing album
- ✅ Always has photos to display
- ⚠️ May show more photos than intended if album doesn't exist

---

## Changing the Album

### Option 1: Use Settings UI (Recommended)

1. Start the slideshow
2. Press **Cmd+S** (macOS) or **Ctrl+S** (Windows/Linux)
3. Find **"Album Name"** setting
4. Change to any album name from your Photos library
5. Close settings (ESC)
6. Restart slideshow

### Option 2: Edit Config File Directly

```bash
# Edit the config file
nano ~/.photo_slideshow_config.json

# Change album_name:
{
  "album_name": "Vacation Photos",
  ...
}

# Save and restart slideshow
```

### Option 3: Create a Custom Album

If you want to use a specific set of photos:

1. Open **Photos** app
2. Create a new album: **File → New Album**
3. Name it (e.g., "Slideshow Photos")
4. Add photos to it
5. Change `album_name` in settings to match

### Option 4: Create a Smart Album

For automatic filtering:

1. Open **Photos** app
2. Create Smart Album: **File → New Smart Album**
3. Name it (e.g., "Recent Favorites")
4. Set criteria (e.g., "Date is in the last 30 days" AND "Favorite is true")
5. Change `album_name` in settings to match

---

## Common Album Names

### Built-in Albums (Always Available)
- `"All Photos"` - Every photo in your library
- `"Favorites"` - Photos you've marked as favorites
- `"Recents"` - Recently added photos
- `"Videos"` - All videos
- `"Selfies"` - Photos detected as selfies
- `"Live Photos"` - Live photos
- `"Portrait"` - Portrait mode photos
- `"Panoramas"` - Panoramic photos
- `"Screenshots"` - Screenshots
- `"Bursts"` - Burst photo sequences

### Custom Albums
Any album you've created in Photos app will work.

---

## Troubleshooting

### Problem: "Album not found" warning

**Logs show:**
```
WARNING - Album 'My Album' not found.
INFO - Available albums: All Photos, Favorites, Recents, ...
INFO - Using all photos from library as fallback for now...
```

**Solutions:**

1. **Check album name spelling**
   - Album names are case-insensitive
   - But spelling must match exactly
   - Check available albums in the log message

2. **Verify album exists in Photos**
   ```bash
   # List all albums
   osxphotos query --albums
   ```

3. **Use a built-in album**
   - Change to `"All Photos"` (always works)
   - Or `"Favorites"`, `"Recents"`, etc.

4. **Create the album**
   - Open Photos app
   - Create album with exact name
   - Add photos to it
   - Restart slideshow

---

## Changes Made

### 1. Updated Default Album Name

**File:** `config.py` (line 19)

**Before:**
```python
"album_name": "photoframe",
```

**After:**
```python
"album_name": "All Photos",
```

**Why:** "All Photos" is a built-in album that always exists, so users don't need to create a custom album.

---

### 2. Improved Error Messages

**File:** `photo_manager.py` (lines 112-120)

**Before:**
```python
self.logger.warning(f"Album '{self.album_name}' not found.")
self.logger.info("To create a Smart Album named 'photoframe':")
self.logger.info("1. Open Photos → File → New Smart Album")
self.logger.info("2. Name it 'photoframe' and set your criteria")
self.logger.info("3. Restart the slideshow")
```

**After:**
```python
self.logger.warning(f"Album '{self.album_name}' not found.")
self.logger.info(f"Available albums: {', '.join(album_names[:10])}")
if len(album_names) > 10:
    self.logger.info(f"... and {len(album_names) - 10} more")
self.logger.info("To use a specific album:")
self.logger.info("1. Open settings (Cmd+S) and change 'Album Name'")
self.logger.info("2. Or create a new album/Smart Album in Photos app")
self.logger.info("Using all photos from library as fallback for now...")
```

**Why:** 
- Shows available albums so user knows what to choose
- References the settings UI (Cmd+S) for easy changes
- More generic instructions (not tied to "photoframe")

---

## Example Configurations

### Use All Photos (Default)
```json
{
  "album_name": "All Photos"
}
```

### Use Only Favorites
```json
{
  "album_name": "Favorites"
}
```

### Use Custom Album
```json
{
  "album_name": "Family Photos"
}
```

### Use Smart Album with Filters
```json
{
  "album_name": "Recent Vacation",
  "filter_by_people": true,
  "filter_people_names": ["John", "Jane"]
}
```

---

## Status: ✅ CONFIGURED

Current setup:
1. ✅ Default album is "All Photos" (built-in, always exists)
2. ✅ Fallback behavior ensures slideshow always works
3. ✅ Improved error messages show available albums
4. ✅ Easy to change via settings UI (Cmd+S)
5. ✅ Case-insensitive album matching
6. ✅ Supports both regular albums and Smart Albums

**The slideshow will work out-of-the-box with "All Photos"!** 🎉
