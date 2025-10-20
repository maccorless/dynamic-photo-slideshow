# How Videos Fit Into Photo Selection

## TL;DR - The Problem

**Videos are selected differently than photos, and it's causing issues!**

- **Photos:** Selected randomly from the 2,545-item cache
- **Videos:** Selected by searching the ENTIRE Photos library again
- **Result:** Videos bypass the cache and use a different selection mechanism

---

## Current Video Selection Flow

### Step 1: Random Selection from Cache
```python
# slideshow_controller.py line 432
photo, photo_index = self._get_random_photo()
```

This picks a random item from the 2,545 cached items (photos + videos).

### Step 2: Check If It's a Video
```python
# slideshow_controller.py line 437
if self._is_video_content(photo):
    # It's a video!
```

Checks if `media_type == 'video'`.

### Step 3: **PROBLEM - Throw Away That Video and Search Library Again**
```python
# slideshow_controller.py line 438-440
self.logger.info("[SLIDE-CREATION] Random selection was video, getting filtered video instead")
filtered_video = self._get_filtered_video()
```

**This is the issue!** Instead of using the randomly selected video from the cache, it:
1. Throws away the cached video
2. Searches the ENTIRE Photos library again
3. Applies `video_person_filter` (which is `null` in your config)
4. Picks a random video from the entire library

---

## What `_get_filtered_video()` Does

### Code Analysis (`slideshow_controller.py` lines 875-934)

```python
def _get_filtered_video(self):
    person_filter = self.config.get('video_person_filter')  # null for you
    local_only = self.config.get('video_local_only', True)
    
    if person_filter:
        # Search library for videos with that person
        all_photos = self.photo_manager.photos_db.photos(persons=[person_filter])
        candidate_videos = [p for p in all_photos if p.ismovie]
    else:
        # NO PERSON FILTER - Get ALL videos from library
        all_photos = self.photo_manager.photos_db.photos()
        candidate_videos = [p for p in all_photos if p.ismovie]
    
    # Filter for local availability
    if local_only:
        candidate_videos = [v for v in candidate_videos if v.path exists]
    
    # Pick random video
    selected_video = random.choice(candidate_videos)
    return selected_video
```

### Your Configuration
```json
{
  "video_person_filter": null,
  "video_local_only": true,
  "filter_people_names": ["Ally"]
}
```

**What happens:**
1. `video_person_filter` is `null` → Searches ALL videos in library
2. Finds 1,558 videos (entire library)
3. Filters to locally available → ~1,558 videos
4. Picks random from those 1,558

**But your cache only has 23 Ally videos!**

---

## The Inconsistency

### Photos (Working Correctly)
```
Startup:
  → Load all photos with person='Ally' (2,545 items including 23 videos)
  → Store in cache

Every Photo Slide:
  → Pick random from 2,545 cached items
  → Show it
```

### Videos (Working Incorrectly)
```
Startup:
  → Load all photos with person='Ally' (2,545 items including 23 videos)
  → Store in cache

Every Video Slide:
  → Pick random from 2,545 cached items
  → Detect it's a video
  → THROW IT AWAY
  → Search entire library (1,558 videos)
  → Pick random from entire library
  → Show it (might not be Ally!)
```

---

## Why This Design Exists

Looking at the code history, this was likely implemented to support:

1. **Separate video filtering** - Allow different person filter for videos vs photos
2. **Video-specific settings** - `video_person_filter` and `video_local_only`
3. **Backward compatibility** - When video support was added later

**But it creates an inconsistency:**
- Photos respect `filter_people_names`
- Videos use `video_person_filter` (separate setting)

---

## Your Current Situation

### What You Have
```json
{
  "filter_people_names": ["Ally"],     // Filters photos to Ally
  "video_person_filter": null          // Videos NOT filtered
}
```

### What's Happening
1. **Photos:** Only Ally (2,488 photos from cache)
2. **Videos:** Random from entire library (1,558 videos)
3. **Result:** Videos might not have Ally!

### Your Cache Contents
```
Total cached: 2,545 items
  - Photos: 2,488 (person='Ally')
  - Videos: 23 (person='Ally')
  - Live Photos: 34 (person='Ally')
```

But when a video is selected, it ignores these 23 cached Ally videos and searches all 1,558 videos in your library!

---

## The Fix

### Option 1: Set `video_person_filter` to "Ally" ✅ RECOMMENDED

```json
{
  "filter_people_names": ["Ally"],
  "video_person_filter": "Ally"
}
```

**Result:**
- Photos: Filtered to Ally (from cache)
- Videos: Filtered to Ally (from library search)
- Consistent filtering!

### Option 2: Use Cached Videos (Code Change Required)

Modify `slideshow_controller.py` line 437-442 to use the cached video instead of searching:

```python
if self._is_video_content(photo):
    # Use the cached video instead of searching
    return self._create_slide_from_video(photo, photo_index)
```

**Benefits:**
- Consistent with photo selection
- Faster (no library search)
- Uses same filter as photos

**Drawbacks:**
- Removes ability to have separate video filter
- Requires code change

### Option 3: Remove Video Special Handling (Code Change Required)

Remove the special video handling entirely and treat videos like photos:

```python
# Just use the randomly selected item, whether photo or video
return self._create_slide_from_photo(photo, photo_index)
```

Then update `_create_slide_from_photo` to handle videos.

---

## Recommended Action

**Set `video_person_filter` to "Ally" in your config:**

```bash
python3 << 'EOF'
import json

with open('/Users/ken/.photo_slideshow_config.json', 'r') as f:
    config = json.load(f)

config['video_person_filter'] = 'Ally'

with open('/Users/ken/.photo_slideshow_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Set video_person_filter to 'Ally'")
EOF
```

**This will:**
- Keep current architecture
- Ensure videos are also filtered to Ally
- No code changes needed
- Consistent filtering across photos and videos

---

## Summary

### Current Behavior
```
Random selection → Is it video? 
  → YES: Throw away, search entire library (1,558 videos)
  → NO: Use cached photo (2,488 photos)
```

### With `video_person_filter: "Ally"`
```
Random selection → Is it video?
  → YES: Throw away, search library for Ally videos (23 videos)
  → NO: Use cached photo (2,488 photos)
```

### Ideal Behavior (Would Require Code Change)
```
Random selection → Use it (whether photo or video)
  → All 2,545 items treated equally
  → Videos: 23 (0.9% chance)
  → Photos: 2,522 (99.1% chance)
```

---

## Video Frequency

### Current (with `video_person_filter: null`)
- Selects from 1,558 videos (entire library)
- Unknown frequency (depends on library composition)

### With `video_person_filter: "Ally"`
- Selects from 23 Ally videos
- Still uses library search (not cache)
- Frequency: ~1 video every 111 slides (0.9%)

### If Using Cache (Code Change)
- Selects from 2,545 cached items (23 are videos)
- Frequency: ~1 video every 111 slides (0.9%)
- More consistent with photo selection

---

## Code References

**Video Selection Logic:**
- `slideshow_controller.py` lines 437-449 (video detection and special handling)
- `slideshow_controller.py` lines 875-934 (`_get_filtered_video()`)

**Video Detection:**
- `slideshow_controller.py` lines 1032-1046 (`_is_video_content()`)

**Cache Contents:**
- `photo_manager.py` line 309 (`self.photos_cache = photos`)
- Contains 2,545 items (2,488 photos + 23 videos + 34 live photos)
