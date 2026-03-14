# How Cache Refresh Works

## TL;DR

✅ **The cache IS automatically refreshed while the slideshow runs!**

- **Default:** Every 1 hour (3600 seconds)
- **Checks:** Photos library for new items
- **Updates:** Adds new photos/videos to cache without restart
- **Configurable:** `cache_refresh_check_interval` setting

---

## Automatic Cache Refresh

### When It Happens

1. **On Startup** (`slideshow_controller.py` line 315)
   ```python
   self.photo_manager.check_and_load_new_photos()
   ```

2. **Every Hour During Slideshow** (`slideshow_controller.py` lines 374-381)
   ```python
   def _check_cache_refresh(self):
       current_time = time.time()
       if current_time - self.last_cache_check >= self.cache_refresh_interval:
           if self.photo_manager.check_and_load_new_photos():
               self.logger.info("New photos detected and loaded during slideshow")
           self.last_cache_check = current_time
   ```

3. **Called Before Every Slide** (`slideshow_controller.py` line 385)
   ```python
   def _get_current_slide(self):
       self._check_cache_refresh()  # Check if it's time to refresh
       # ... then get next slide
   ```

### How It Works

**Step 1: Check if it's time** (every hour by default)
```python
if current_time - last_check >= 3600:  # 1 hour
    # Time to check!
```

**Step 2: Query Photos library for new items**
```python
new_photos = self._load_photos_with_filters()
# Runs the same filter: person='Ally'
# Gets fresh list from Photos library
```

**Step 3: Compare counts**
```python
if len(new_photos) > old_count:
    # New photos/videos found!
    self.photos_cache = new_photos  # Replace cache
    self.logger.info(f"Added {new_photo_count} new photos")
```

**Step 4: Continue slideshow with updated cache**
- No restart needed
- New items immediately available for random selection

---

## Configuration

### Current Setting (Default)
```python
# config.py line 44
'cache_refresh_check_interval': 3600  # 1 hour in seconds
```

### Your Config
You don't have this setting in `~/.photo_slideshow_config.json`, so it uses the default: **1 hour**

### To Change Refresh Interval

Add to `~/.photo_slideshow_config.json`:

```json
{
  "cache_refresh_check_interval": 1800  // 30 minutes
}
```

**Common values:**
- `300` = 5 minutes
- `600` = 10 minutes
- `1800` = 30 minutes
- `3600` = 1 hour (default)
- `7200` = 2 hours

---

## Example Scenario: New Video Tomorrow

### Timeline

**Today 5:00 PM:**
- Start slideshow
- Cache: 2,545 items (2,488 photos + 23 videos + 34 live photos)

**Tomorrow 9:00 AM:**
- You create a new video with Ally
- Slideshow still running

**Tomorrow 10:00 AM (5 hours later):**
- Cache refresh triggers (1 hour intervals)
- Queries Photos library: person='Ally'
- Finds 2,546 items (includes new video!)
- Updates cache: 2,545 → 2,546
- Logs: "Added 1 new photos to cache (now 2546 total)"

**Tomorrow 10:01 AM:**
- Next slide could be the new video!
- Random selection from updated 2,546 items

---

## What Gets Refreshed

### Included in Refresh
✅ New photos with person='Ally'  
✅ New videos with person='Ally'  
✅ New live photos with person='Ally'  
✅ Photos that now have person='Ally' (if you tagged them)

### Not Included
❌ Photos/videos without person='Ally'  
❌ Hidden photos  
❌ RAW images  
❌ Items that don't match your filters

### The Refresh Process
```python
# photo_manager.py lines 524-530
new_photos = self._load_photos_with_filters()
# This runs the SAME filter as startup:
#   - person='Ally'
#   - Exclude hidden
#   - Exclude RAW
#   - Shuffle randomly
```

---

## Performance Impact

### Minimal Impact
- Refresh check: ~0.001 seconds (just time comparison)
- Actual refresh: ~2-3 seconds (only when triggered)
- Happens in background between slides
- No interruption to slideshow

### Frequency
- Check happens before every slide
- Actual refresh only every hour
- If no new photos: instant return

---

## Logging

### When Refresh Happens

You'll see in logs:
```
2025-10-18 10:00:15 - slideshow_controller - DEBUG - Checking for new photos (periodic cache refresh)
2025-10-18 10:00:17 - photo_manager - INFO - Loading new photos incrementally (had 2545 photos)
2025-10-18 10:00:17 - photo_manager - INFO - Found 2546 photos with person 'Ally'
2025-10-18 10:00:17 - photo_manager - INFO - Added 1 new photos to cache (now 2546 total)
2025-10-18 10:00:17 - slideshow_controller - INFO - New photos detected and loaded during slideshow
```

### When No New Photos

You won't see anything (DEBUG level):
```
2025-10-18 11:00:15 - slideshow_controller - DEBUG - Checking for new photos (periodic cache refresh)
# No new photos, no additional logs
```

---

## Manual Refresh

### Force Refresh Without Waiting

If you want to force an immediate refresh, you can:

1. **Restart slideshow** (ESC, then start again)
2. **Wait for next hourly check**
3. **Reduce interval** to check more frequently

### No Manual Refresh Command

Currently there's no keyboard shortcut to force refresh, but you could add one:

```python
# In main_pygame.py event loop:
elif event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
    # Ctrl+R to refresh
    self.controller.photo_manager.check_and_load_new_photos()
```

---

## With Video Code Change

### After Fixing Video Selection

Once we change videos to use the cache (instead of searching library), the refresh will work even better:

**Current (with library search):**
- Photos: Use cache (refreshed hourly)
- Videos: Search library (always fresh, but inconsistent)

**After fix (using cache):**
- Photos: Use cache (refreshed hourly)
- Videos: Use cache (refreshed hourly)
- **Both consistent and both get new items!**

---

## Configuration Options

### Adjust Refresh Interval

**More frequent (every 10 minutes):**
```json
{
  "cache_refresh_check_interval": 600
}
```

**Less frequent (every 4 hours):**
```json
{
  "cache_refresh_check_interval": 14400
}
```

**Very frequent (every minute) - NOT RECOMMENDED:**
```json
{
  "cache_refresh_check_interval": 60
}
```
⚠️ This will query Photos library every minute, which could impact performance.

---

## Summary

### ✅ Your New Videos WILL Be Detected

1. **Create video tomorrow with Ally**
2. **Wait up to 1 hour** (or whatever interval you set)
3. **Cache automatically refreshes**
4. **New video appears in slideshow**
5. **No restart needed!**

### Current Behavior
- ✅ Cache refreshes every 1 hour
- ✅ Includes new photos and videos
- ✅ Applies same filter (person='Ally')
- ✅ Works while slideshow is running
- ✅ No manual intervention needed

### After Video Code Fix
- ✅ Videos will also use cache
- ✅ More consistent behavior
- ✅ Same refresh mechanism
- ✅ New videos appear in random selection

---

## Code References

**Cache Refresh Logic:**
- `slideshow_controller.py` lines 374-381 (`_check_cache_refresh()`)
- `slideshow_controller.py` line 89 (`cache_refresh_interval` default)
- `photo_manager.py` lines 510-536 (`check_and_load_new_photos()`)

**Configuration:**
- `config.py` line 44 (`cache_refresh_check_interval: 3600`)
