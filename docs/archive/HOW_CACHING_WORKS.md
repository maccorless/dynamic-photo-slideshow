# How Photo Caching and Selection Works

## Overview
The slideshow uses **in-memory caching** with **random selection on every slide**. Here's exactly how it works:

---

## Photo Loading Process (On Startup)

### 1. **Load All Matching Photos** (`photo_manager.py` line 128-310)

When the slideshow starts:

```python
def load_photos(self):
    # 1. Connect to Photos library via osxphotos
    # 2. Apply filters (person='Ally' in your case)
    # 3. Load ALL matching photos into memory
    # 4. Shuffle the list randomly
    # 5. Store in self.photos_cache (in-memory list)
```

**For your configuration:**
- Searches entire Photos library (14,773 total items)
- Filters to person='Ally' (finds 2,598 items)
- Filters out hidden/RAW (keeps 2,545 items)
- **Shuffles the 2,545 items randomly** (line 301)
- Stores all 2,545 in memory (`self.photos_cache`)

**Key Point:** The list is shuffled ONCE at startup, but selection is random on every slide.

---

## Photo Selection Process (Every Slide)

### 2. **Random Selection on Every Slide** (`photo_manager.py` line 484-488)

```python
def get_random_photo_index(self) -> int:
    """Get a random photo index."""
    if not self.photos_cache:
        return 0
    return random.randint(0, len(self.photos_cache) - 1)
```

**On every single slide:**
1. Calls `random.randint(0, 2544)` - picks a random number
2. Returns photo at that index from `photos_cache`
3. **Completely random** - no tracking of what was shown

**This means:**
- ✅ You CAN see the same photo multiple times in one session
- ✅ You CAN see photos in any order
- ✅ Every photo has equal probability on every slide
- ✅ Selection is truly random, not sequential

---

## What Gets Cached?

### In-Memory Cache (`self.photos_cache`)
**Type:** Python list in RAM  
**Contents:** 2,545 photo metadata dictionaries  
**Lifetime:** Exists only while slideshow is running  
**Cleared:** When slideshow exits

**Each cached item contains:**
```python
{
    'uuid': 'ABC123...',
    'filename': 'IMG_1234.jpeg',
    'path': '/path/to/photo',
    'media_type': 'image' or 'video',
    'orientation': 'portrait' or 'landscape',
    'date': datetime object,
    'location': (lat, lon),
    ...
}
```

### Persistent Cache (`~/.photo_slideshow_cache.json`)
**Type:** JSON file on disk  
**Contents:** Location data only (GPS → place names)  
**Purpose:** Avoid repeated API calls for location lookups  
**Does NOT contain:** Photo list or selection history

---

## Cache Behavior Across Runs

### What Happens on Each Startup:

1. **Fresh Load Every Time**
   ```python
   # Line 308-309
   self.photos_cache = None  # Clear old cache
   self.photos_cache = photos  # Load fresh from Photos library
   ```

2. **New Random Shuffle**
   ```python
   # Line 300-301
   if self.config.get('shuffle_photos', True):
       random.shuffle(photos)
   ```

3. **Random Selection**
   - Every slide: `random.randint(0, len(photos_cache)-1)`
   - No memory of previous sessions
   - No memory of previous slides (except navigation history)

---

## Your Question: "Select randomly from ALL matching photos on every run"

### ✅ **YES, that's exactly how it works!**

**On every run:**
1. Loads all 2,545 Ally photos fresh from Photos library
2. Shuffles them randomly
3. Stores in memory

**On every slide:**
1. Picks a random index: `random.randint(0, 2544)`
2. Shows that photo
3. No tracking (except 50-item navigation history)

**This means:**
- ✅ Every run starts fresh (no persistent selection state)
- ✅ Every slide is randomly selected from all 2,545 photos
- ✅ You could see the same photo twice in one session (random chance)
- ✅ Different order every time you run the slideshow

---

## Navigation History (Not a Cache)

**Purpose:** Allow back button to work  
**Type:** In-memory list (max 50 items)  
**Contents:** Recently shown slides (for back navigation)  
**Does NOT affect:** Random selection of new slides

```python
# config: photo_history_cache_size: 50
# Only stores last 50 slides for back button
# Does NOT prevent showing same photo again
```

---

## Configuration Options

### `shuffle_photos` (default: true)
```json
{
  "shuffle_photos": true
}
```
- **true:** Shuffles photo list at startup (current behavior)
- **false:** Photos in order from Photos library (still random selection)

### `max_photos_limit` (default: 500, yours: 0)
```json
{
  "max_photos_limit": 0
}
```
- **0:** Load ALL matching photos (your setting - 2,545 photos)
- **N:** Load only first N photos after filtering

---

## Performance Notes

### Memory Usage
- **2,545 photos × ~2KB metadata each = ~5MB RAM**
- Very lightweight - only metadata, not image data
- Images loaded on-demand when displayed

### Startup Time
- Loads all 2,545 photos in ~2-3 seconds
- One-time cost at startup
- Fast random selection during slideshow

---

## Summary

**Your current setup:**

```
Startup:
  → Load all 2,545 Ally photos from library
  → Shuffle randomly
  → Store in memory

Every Slide:
  → random.randint(0, 2544)
  → Show that photo
  → Repeat

Every Run:
  → Fresh load
  → New shuffle
  → New random sequence
```

**Result:** ✅ Truly random selection from all matching photos on every run and every slide!

---

## If You Want Different Behavior

### Option 1: Sequential (No Repeats Until All Shown)
Would require code changes to track shown photos and remove from pool.

### Option 2: Weighted Random (Favor Less Recently Shown)
Would require code changes to track timestamps and apply weights.

### Option 3: Current Behavior (Truly Random)
✅ Already implemented - no changes needed!

---

## Code References

**Photo Loading:**
- `photo_manager.py` lines 128-310 (`load_photos()`, `_load_photos_with_filters()`)

**Random Selection:**
- `photo_manager.py` lines 484-488 (`get_random_photo_index()`)
- `slideshow_controller.py` lines 846-859 (`_get_random_photo()`)

**Shuffling:**
- `photo_manager.py` line 301 (`random.shuffle(photos)`)

**Cache Storage:**
- `photo_manager.py` line 41 (`self.photos_cache = []`)
- `photo_manager.py` line 309 (`self.photos_cache = photos`)
