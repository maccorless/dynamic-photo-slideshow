# Cross-Machine Compatibility

## Your Questions

1. **If I run this on another machine where the video cache is not built, will it error?**
2. **Will the filename be the same in the photos cache on another machine?**

---

## Short Answers

1. ✅ **No, it will NOT error** - Videos will be automatically exported on-demand
2. ✅ **Yes, filenames will be the same** - Uses UUID-based naming that's consistent across machines

---

## Detailed Explanation

### How Photos Are Identified

**Each photo/video in Apple Photos has a UUID (Universally Unique Identifier):**

```python
# photo_manager.py line 407
photo_data = {
    'uuid': photo.uuid,        # e.g., "ABC123-DEF456-..."
    'filename': photo.filename, # e.g., "IMG_1234.mov"
    'path': photo.path,        # Machine-specific path
    ...
}
```

**Key points:**
- `uuid`: **Same across all machines** (synced via iCloud)
- `filename`: **Same across all machines** (synced via iCloud)
- `path`: **Different on each machine** (local file system path)

---

## Video Cache Behavior

### Video Cache Location

```python
# photo_manager.py line 693
cache_dir = os.path.join(os.path.expanduser('~'), '.photo_slideshow_cache', 'videos')
# → /Users/ken/.photo_slideshow_cache/videos/
```

### Video Cache Filename

```python
# photo_manager.py lines 696-701
photo_uuid = photo_data.get('uuid', '')  # e.g., "ABC123-DEF456-..."
cached_path = os.path.join(cache_dir, f"{photo_uuid}.mov")
# → /Users/ken/.photo_slideshow_cache/videos/ABC123-DEF456-....mov
```

**The cache filename is based on UUID, which is the same across machines!**

---

## What Happens on Another Machine

### Scenario: Run Slideshow on Machine 2

**Machine 1 (your current machine):**
```
~/.photo_slideshow_cache/videos/
  ├── ABC123-DEF456.mov  (cached video 1)
  ├── XYZ789-GHI012.mov  (cached video 2)
  └── ...
```

**Machine 2 (new machine):**
```
~/.photo_slideshow_cache/videos/
  (empty - no cache yet)
```

### First Time Video Plays on Machine 2

**Step 1: Cache lookup**
```python
# photo_manager.py line 704-709
cached_path = os.path.join(cache_dir, f"{photo_uuid}.mov")
if os.path.exists(cached_path):
    # Cache hit - use cached video
    return cached_path
```
**Result:** Cache miss (file doesn't exist yet)

**Step 2: Export video**
```python
# photo_manager.py line 714-718
self.logger.info(f"Exporting video: {photo_data.get('filename', 'unknown')}...")
export_paths = osxphoto.export(cache_dir, filename=f"{photo_uuid}.mov", overwrite=True)
```
**Result:** Video exported to `~/.photo_slideshow_cache/videos/ABC123-DEF456.mov`

**Step 3: Play video**
```python
# Video now cached and plays normally
```

**Step 4: Next time**
```python
# Cache hit! Uses cached video (no export needed)
```

---

## Error Handling

### No Errors on Missing Cache

The code handles missing cache gracefully:

```python
# photo_manager.py lines 703-709
# Check if already cached
cached_path = os.path.join(cache_dir, f"{photo_uuid}.mov")
if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
    # Cache hit
    return cached_path

# Cache miss - export video (no error)
export_paths = osxphoto.export(cache_dir, filename=f"{photo_uuid}.mov")
```

**No error thrown - just exports the video!**

---

## Filename Consistency Across Machines

### UUID-Based Naming

**Machine 1:**
```python
photo.uuid = "ABC123-DEF456-GHI789"
cached_filename = f"{photo.uuid}.mov"
# → ABC123-DEF456-GHI789.mov
```

**Machine 2:**
```python
photo.uuid = "ABC123-DEF456-GHI789"  # Same UUID!
cached_filename = f"{photo.uuid}.mov"
# → ABC123-DEF456-GHI789.mov  # Same filename!
```

### Why UUIDs Are Consistent

Apple Photos syncs UUIDs across devices via iCloud:
- ✅ Same photo on all devices has same UUID
- ✅ UUID never changes
- ✅ UUID is unique to that specific photo/video

---

## Photo Cache vs Video Cache

### Photo Cache (In-Memory)

**Location:** RAM (not on disk)  
**Contents:** Photo metadata (uuid, filename, path, etc.)  
**Persistence:** Cleared on exit, rebuilt on startup  
**Cross-machine:** Each machine builds its own cache from Photos library

**Example photo cache entry:**
```python
{
    'uuid': 'ABC123-DEF456',
    'filename': 'IMG_1234.mov',
    'path': '/Users/ken/Pictures/Photos Library.photoslibrary/...',  # Machine-specific!
    'media_type': 'video',
    ...
}
```

### Video Cache (On Disk)

**Location:** `~/.photo_slideshow_cache/videos/`  
**Contents:** Exported video files  
**Persistence:** Stays on disk across runs  
**Cross-machine:** Each machine has its own cache (different paths)

**Example video cache:**
```
Machine 1: /Users/ken/.photo_slideshow_cache/videos/ABC123-DEF456.mov
Machine 2: /Users/alice/.photo_slideshow_cache/videos/ABC123-DEF456.mov
           (same filename, different path)
```

---

## First Run on New Machine

### What Happens

1. **Slideshow starts**
   - Loads Photos library
   - Builds photo cache (2,545 items with person='Ally')
   - Cache includes 23 videos

2. **First video is selected**
   - Random selection picks a video
   - Checks video cache: `/Users/alice/.photo_slideshow_cache/videos/ABC123.mov`
   - Cache miss (file doesn't exist)
   - **Exports video** (takes 1-3 seconds)
   - Caches to disk
   - Plays video

3. **Second time same video is selected**
   - Checks video cache
   - Cache hit! (file exists)
   - Plays immediately (no export)

### Performance

**First time each video plays:**
- Export time: 1-3 seconds
- One-time cost per video
- Logs: "Exporting video: IMG_1234.mov..."

**Subsequent times:**
- Cache hit: instant
- No export needed
- Logs: "Using cached video: ..."

---

## Cache Portability

### Can You Copy Cache Between Machines?

**Short answer:** No, not recommended.

**Why:**
- UUIDs are the same
- But file paths in photo cache are different
- Videos would need re-export anyway (different Photos library location)

**Better approach:**
- Let each machine build its own cache
- Videos export on-demand (automatic)
- Cache builds up over time

---

## Example: Same Video on Two Machines

### Machine 1 (Mac Mini)
```python
Photo Cache Entry:
{
    'uuid': 'ABC123-DEF456',
    'filename': 'IMG_1234.mov',
    'path': '/Users/ken/Pictures/Photos Library.photoslibrary/originals/A/ABC123.mov',
    'needs_export': False  # Has direct path
}

Video Cache:
/Users/ken/.photo_slideshow_cache/videos/ABC123-DEF456.mov
```

### Machine 2 (MacBook)
```python
Photo Cache Entry:
{
    'uuid': 'ABC123-DEF456',  # Same UUID!
    'filename': 'IMG_1234.mov',  # Same filename!
    'path': '/Users/alice/Pictures/Photos Library.photoslibrary/originals/A/ABC123.mov',
    'needs_export': False  # Different path!
}

Video Cache:
/Users/alice/.photo_slideshow_cache/videos/ABC123-DEF456.mov  # Same filename!
```

**Both machines:**
- ✅ Same UUID
- ✅ Same cached filename
- ✅ Same video content
- ❌ Different local paths

---

## Error Scenarios

### Scenario 1: Video Not in iCloud Photos

**Problem:** Video exists on Machine 1 but not synced to Machine 2

**What happens:**
```python
# Machine 2 tries to load video
photo = photos_db.photos(uuid='ABC123')
if photo.ismissing:
    # Video not available locally
    # Filtered out during cache load
```

**Result:** Video not in cache on Machine 2 (filtered out)

### Scenario 2: Export Fails

**Problem:** Video can't be exported

**What happens:**
```python
# photo_manager.py lines 723-730
if export_paths:
    return export_paths[0]
else:
    self.logger.error(f"Failed to export video")
    return None
```

**Result:** Video skipped, slideshow continues with next item

### Scenario 3: Disk Space Full

**Problem:** No space for video cache

**What happens:**
- Export fails
- Error logged
- Video skipped
- Slideshow continues

**No crash!**

---

## Configuration Across Machines

### Same Configuration File

If you copy `~/.photo_slideshow_config.json` to Machine 2:

```json
{
  "filter_people_names": ["Ally"],
  "cache_refresh_check_interval": 3600,
  ...
}
```

**Works perfectly!**
- Same filter applies
- Same settings
- Each machine builds its own photo cache
- Each machine builds its own video cache

---

## Summary

### Question 1: Will it error on another machine?

✅ **No errors!**

**What happens:**
1. Photo cache rebuilt from local Photos library
2. Video cache empty initially
3. Videos export on-demand (1-3 seconds each)
4. Cached videos reused on subsequent plays
5. No crashes, no errors

### Question 2: Will filenames be the same?

✅ **Yes, filenames are consistent!**

**Why:**
- Based on UUID (synced via iCloud)
- Same photo = same UUID = same cached filename
- Example: `ABC123-DEF456.mov` on all machines

**But:**
- Local paths are different
- Each machine has its own cache directory
- Cache not portable between machines

---

## Best Practices

### Setting Up on New Machine

1. **Install slideshow** (git clone)
2. **Copy config** (`~/.photo_slideshow_config.json`)
3. **Run slideshow** (first time)
4. **Let cache build** (videos export on-demand)
5. **Enjoy!**

### Cache Management

**Cache location:**
```bash
~/.photo_slideshow_cache/videos/
```

**To clear cache:**
```bash
rm -rf ~/.photo_slideshow_cache/videos/*
```

**To check cache size:**
```bash
du -sh ~/.photo_slideshow_cache/videos/
```

---

## Code References

**UUID-based caching:**
- `photo_manager.py` lines 696-709 (cache lookup)
- `photo_manager.py` lines 717-718 (export with UUID filename)

**Photo metadata:**
- `photo_manager.py` lines 406-417 (uuid, filename, path)

**Export handling:**
- `photo_manager.py` lines 444-450 (needs_export flag)
- `photo_manager.py` lines 686-730 (`_export_video_temporarily()`)
