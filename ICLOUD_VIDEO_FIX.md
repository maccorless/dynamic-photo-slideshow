# iCloud Video Fix - Filter Out Non-Local Videos

## Problem

On machines where Photos library isn't fully synced, videos that are still in iCloud (not downloaded locally) are being added to the cache. When the slideshow tries to play them, you get "video not found" errors.

---

## Root Cause

**Current code** (`photo_manager.py` lines 444-453):

```python
# Handle videos that need to be exported from Apple Photos
if not photo_data['path'] or photo_data['path'] == '':
    if media_type == 'video' and hasattr(photo, 'export'):
        # For videos without direct paths, we'll handle export during display
        photo_data['needs_export'] = True
        photo_data['osxphoto_object'] = photo
    else:
        # Reject photo due to missing path
        return None
```

**What's missing:**
- ❌ No check for `photo.ismissing` (iCloud-only items)
- ❌ No check for `photo.path` existence on disk
- ❌ Videos in iCloud are added to cache even though they can't be played

---

## The Fix

Add a check to filter out iCloud-only videos during cache load:

```python
# _extract_photo_metadata() method

# Check if photo/video is available locally
if hasattr(photo, 'ismissing') and photo.ismissing:
    self.logger.debug(f"Rejecting {media_type} - not downloaded from iCloud: {photo.filename}")
    return None

# For videos, also check if path exists
if media_type == 'video':
    if not photo.path or not os.path.exists(photo.path):
        # Check if it can be exported
        if hasattr(photo, 'export'):
            self.logger.debug(f"Video needs export: {photo.filename}")
            photo_data['needs_export'] = True
            photo_data['osxphoto_object'] = photo
        else:
            self.logger.debug(f"Rejecting video - not locally available: {photo.filename}")
            return None
```

---

## Where to Add the Check

**File:** `photo_manager.py`  
**Location:** After line 388 (after hidden/RAW check)

**Before:**
```python
def _extract_photo_metadata(self, photo) -> Optional[Dict[str, Any]]:
    try:
        # Skip hidden photos and RAW images
        if photo.hidden or photo.has_raw:
            return None

        # Determine media type
        media_type = 'image'
        if photo.ismovie:
            media_type = 'video'
        ...
```

**After:**
```python
def _extract_photo_metadata(self, photo) -> Optional[Dict[str, Any]]:
    try:
        # Skip hidden photos and RAW images
        if photo.hidden or photo.has_raw:
            return None

        # Determine media type
        media_type = 'image'
        if photo.ismovie:
            media_type = 'video'
        elif photo.live_photo:
            media_type = 'live_photo'

        # Skip items not downloaded from iCloud
        if hasattr(photo, 'ismissing') and photo.ismissing:
            self.logger.debug(f"Skipping {media_type} not downloaded from iCloud: {photo.filename}")
            return None
        
        # For videos, verify local availability
        if media_type == 'video' and self.config.get('video_local_only', True):
            if not photo.path or not os.path.exists(photo.path):
                self.logger.debug(f"Skipping video not locally available: {photo.filename}")
                return None
        ...
```

---

## Configuration Option

The fix respects the existing `video_local_only` configuration:

```json
{
  "video_local_only": true  // Default - only use locally available videos
}
```

**If `true`:** Only videos downloaded locally are added to cache  
**If `false`:** All videos added (may cause errors on unsynced machines)

---

## Impact

### Before Fix

**Machine with partial iCloud sync:**
```
Loading photos...
Found 2,598 photos with person 'Ally'
  - 2,488 photos (all local)
  - 23 videos (some in iCloud, some local)
  - 34 live photos (all local)

During slideshow:
  → Video selected
  → "Video not found" error
  → Slideshow continues (skips video)
```

### After Fix

**Machine with partial iCloud sync:**
```
Loading photos...
Found 2,598 photos with person 'Ally'
Skipping video not downloaded from iCloud: IMG_1234.mov
Skipping video not downloaded from iCloud: IMG_5678.mov
...
Found 2,580 photos matching criteria
  - 2,488 photos (all local)
  - 8 videos (only locally available ones)
  - 34 live photos (all local)

During slideshow:
  → Video selected
  → Plays successfully (all cached videos are local)
```

---

## Testing

### How to Test

1. **On machine with partial sync:**
   - Start slideshow
   - Check logs for "Skipping video not downloaded from iCloud"
   - Verify no "video not found" errors during playback

2. **On fully synced machine:**
   - Should work as before
   - All videos available
   - No videos skipped

### Expected Logs

**Before fix:**
```
2025-10-17 18:10:15 - photo_manager - INFO - Found 2598 photos with person 'Ally'
2025-10-17 18:10:15 - photo_manager - INFO - Found 2545 photos matching all filter criteria
...
2025-10-17 18:15:30 - slideshow_controller - ERROR - Video not found: /path/to/video.mov
```

**After fix:**
```
2025-10-17 18:10:15 - photo_manager - INFO - Found 2598 photos with person 'Ally'
2025-10-17 18:10:15 - photo_manager - DEBUG - Skipping video not downloaded from iCloud: IMG_1234.mov
2025-10-17 18:10:15 - photo_manager - DEBUG - Skipping video not downloaded from iCloud: IMG_5678.mov
2025-10-17 18:10:15 - photo_manager - INFO - Found 2530 photos matching all filter criteria
...
(No video errors during playback)
```

---

## Alternative: Download Videos First

Instead of filtering them out, you could download them:

### Option 1: Manual Download
1. Open Photos app
2. Select videos with Ally
3. Right-click → Download Original

### Option 2: Automatic Download Script
```python
# download_ally_videos.py
from osxphotos import PhotosDB

db = PhotosDB()
photos = db.photos(persons=['Ally'])
videos = [p for p in photos if p.ismovie and p.ismissing]

print(f"Found {len(videos)} videos to download")
for video in videos:
    print(f"Downloading: {video.filename}")
    # Trigger download by accessing the file
    _ = video.path
```

---

## Recommended Approach

**For machines with partial sync:**
1. ✅ Apply the fix (filter out iCloud-only videos)
2. Let iCloud sync complete naturally
3. Videos will automatically appear in cache after sync

**For fully synced machines:**
- No change needed
- Fix has no impact (all videos already local)

---

## Code Change Required

**File:** `photo_manager.py`  
**Method:** `_extract_photo_metadata()`  
**Location:** After line 395 (after media_type determination)

**Add these lines:**
```python
# Skip items not downloaded from iCloud
if hasattr(photo, 'ismissing') and photo.ismissing:
    self.logger.debug(f"Skipping {media_type} not downloaded from iCloud: {photo.filename}")
    return None

# For videos, verify local availability
if media_type == 'video' and self.config.get('video_local_only', True):
    if not photo.path or not os.path.exists(photo.path):
        self.logger.debug(f"Skipping video not locally available: {photo.filename}")
        return None
```

---

## Summary

**Problem:** Videos in iCloud (not downloaded) are added to cache → "video not found" errors

**Solution:** Filter out iCloud-only videos during cache load

**Benefits:**
- ✅ No "video not found" errors
- ✅ Only locally available videos in cache
- ✅ Works on partially synced machines
- ✅ Respects `video_local_only` config
- ✅ Videos automatically appear after iCloud sync completes

**Would you like me to implement this fix?**
