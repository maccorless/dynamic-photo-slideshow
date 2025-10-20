# Video Selection Fix - Use Cached Videos

## Problem Fixed

Videos were being selected differently than photos, causing inconsistency and ignoring the cache.

---

## Before Fix

### Photo Selection
```
1. Pick random from 2,545 cached items
2. Use it
```

### Video Selection
```
1. Pick random from 2,545 cached items
2. Detect it's a video
3. THROW IT AWAY
4. Search entire Photos library (1,558 videos)
5. Pick random from library
6. Use it
```

**Issues:**
- ❌ Videos ignored the cache
- ❌ Videos used different filter (`video_person_filter` vs `filter_people_names`)
- ❌ Videos didn't benefit from cache refresh
- ❌ Inconsistent behavior

---

## After Fix

### Both Photos and Videos
```
1. Pick random from 2,545 cached items
2. Use it (whether photo or video)
```

**Benefits:**
- ✅ Videos use the cache
- ✅ Videos use same filter as photos (person='Ally')
- ✅ Videos benefit from automatic cache refresh
- ✅ Consistent behavior
- ✅ Faster (no library search)
- ✅ Simpler code

---

## Code Change

**File:** `slideshow_controller.py` lines 436-443

**Before:**
```python
if self._is_video_content(photo):
    self.logger.info(f"[SLIDE-CREATION] Random selection was video, getting filtered video instead")
    # Use filtered video selection instead of random video
    filtered_video = self._get_filtered_video()
    if filtered_video:
        return self._create_slide_from_video(filtered_video, 0)
    else:
        self.logger.warning(f"[SLIDE-CREATION] No filtered video available, falling back to photo")
        # Fall back to getting a photo instead
        photo, photo_index = self._get_random_photo_only()
        if photo:
            return self._create_slide_from_photo(photo, photo_index)
        return None
else:
    self.logger.info(f"[SLIDE-CREATION] Creating photo slide: {photo.get('filename', 'unknown')}")
    return self._create_slide_from_photo(photo, photo_index)
```

**After:**
```python
if self._is_video_content(photo):
    self.logger.info(f"[SLIDE-CREATION] Random selection was video: {photo.get('filename', 'unknown')}")
    # Use the cached video directly (respects same filter as photos)
    return self._create_slide_from_video(photo, photo_index)
else:
    self.logger.info(f"[SLIDE-CREATION] Creating photo slide: {photo.get('filename', 'unknown')}")
    return self._create_slide_from_photo(photo, photo_index)
```

**Changes:**
- Removed call to `_get_filtered_video()` (library search)
- Removed fallback logic
- Use cached video directly
- Simplified from 16 lines to 6 lines

---

## Impact on Your Slideshow

### Cache Contents
```
Total: 2,545 items (all with person='Ally')
  - Photos: 2,488 (97.8%)
  - Videos: 23 (0.9%)
  - Live Photos: 34 (1.3%)
```

### Video Frequency

**Before fix:**
- Videos selected from entire library (1,558 videos)
- Frequency: Unknown (depends on library composition)
- Might not have Ally

**After fix:**
- Videos selected from cache (23 Ally videos)
- Frequency: 23/2,545 = 0.9%
- Expected: 1 video every ~111 slides
- All videos have Ally ✅

---

## Cache Refresh Behavior

### New Videos Tomorrow

**Scenario:** You create a new video with Ally tomorrow

**Before fix:**
- Photos: Would appear after cache refresh (1 hour)
- Videos: Would appear immediately (searches library)
- Inconsistent!

**After fix:**
- Photos: Appear after cache refresh (1 hour)
- Videos: Appear after cache refresh (1 hour)
- Consistent! ✅

**Timeline:**
```
Today 5:00 PM:  Start slideshow (2,545 items cached)
Tomorrow 9:00 AM: Create new video with Ally
Tomorrow 10:00 AM: Cache refresh (every 1 hour)
                   → Finds 2,546 items
                   → New video now in cache
Tomorrow 10:01 AM: New video can appear in slideshow!
```

---

## Configuration Changes

### `video_person_filter` No Longer Used

**Before fix:**
```json
{
  "filter_people_names": ["Ally"],    // For photos
  "video_person_filter": "Ally"       // For videos (separate)
}
```

**After fix:**
```json
{
  "filter_people_names": ["Ally"]     // For BOTH photos and videos
}
```

The `video_person_filter` setting is now ignored. Videos use the same filter as photos.

### `video_local_only` Still Applies

The `video_local_only` setting still works during initial cache load:

```python
# photo_manager.py - when loading photos
if photo.ismissing or not os.path.exists(photo.path):
    # Skip iCloud-only videos
    continue
```

---

## Deprecated Code

### `_get_filtered_video()` Method

**Status:** Still exists but no longer called  
**Location:** `slideshow_controller.py` lines 875-934  
**Can be removed:** Yes, in future cleanup

This method is no longer used after the fix. It can be safely removed in a future refactoring.

---

## Testing

### What to Test

1. **Video frequency** - Should see ~1 video per 111 slides
2. **Video filtering** - All videos should have Ally
3. **Cache refresh** - New videos appear after 1 hour
4. **No errors** - Videos play correctly from cache

### Expected Logs

**When video is selected:**
```
[SLIDE-CREATION] Creating normal slide (not test video)
[SLIDE-CREATION] Random selection was video: ABC123.mov
```

**No more:**
```
[SLIDE-CREATION] Random selection was video, getting filtered video instead
[VIDEO-FILTER] Filtering videos - person: 'Ally', local_only: True
[VIDEO-FILTER] Found 23 videos with person 'Ally'
```

---

## Benefits Summary

### Performance
- ✅ Faster video selection (no library search)
- ✅ Reduced API calls to Photos library
- ✅ Less memory usage (no duplicate video metadata)

### Consistency
- ✅ Videos use same filter as photos
- ✅ Videos benefit from cache refresh
- ✅ Predictable behavior

### Simplicity
- ✅ Simpler code (6 lines vs 16 lines)
- ✅ One selection mechanism for all content
- ✅ Easier to understand and maintain

### Correctness
- ✅ Videos respect person filter
- ✅ New videos appear after cache refresh
- ✅ No separate video configuration needed

---

## Migration Notes

### No Configuration Changes Required

Your existing configuration will work without changes:
- `filter_people_names: ["Ally"]` applies to both photos and videos
- `video_person_filter` is ignored (can be removed)
- `video_local_only` still works during cache load

### No Data Migration Required

The cache is rebuilt on every startup, so no migration needed.

---

## Rollback

If you need to rollback this change:

```bash
git revert <commit-hash>
```

Or manually restore the old code from git history.

---

## Future Enhancements

### Possible Improvements

1. **Remove `_get_filtered_video()` method** - No longer needed
2. **Remove `video_person_filter` config** - No longer used
3. **Add video frequency control** - Allow adjusting video percentage
4. **Add video-specific filters** - If needed, implement in cache load

---

## Status

✅ **IMPLEMENTED**  
📅 **Date:** October 17, 2025  
🔧 **File:** `slideshow_controller.py` lines 436-443  
📝 **Lines changed:** 16 → 6 (10 lines removed)
