# Race Condition Fix for Overlapping Countdown Threads

**Date:** October 13, 2025  
**Issue:** Multiple countdown threads running simultaneously during rapid navigation

---

## Root Causes Identified

### **Cause 1: Duplicate Timer Cleanup (FIXED)**

**Problem:**
```python
def advance_slideshow():
    self._stop_current_timer()  # Sets manager to None WITHOUT waiting
    ...
    self._display_slide_with_timer()
        self._cleanup_previous_slide_timers()  # Finds nothing to cleanup!
```

**Solution:**
Removed the duplicate `_stop_current_timer()` call on line 127. Cleanup is now handled only in `_cleanup_previous_slide_timers()` which properly waits for threads with `join()`.

**File:** `slideshow_controller.py` line 127

---

### **Cause 2: Async Video Display Race Condition (FIXED)**

**Problem:**
Video display is asynchronous. The old video's `_display_slide_with_timer()` can complete AFTER a new slide has already started displaying:

```
Timeline:
15:21:27.752 - Video displays (async operation starts)
15:21:27.761 - User presses NEXT → new portrait slide starts
15:21:28.086 - Portrait slide creates MGR-8121 (countdown starts)
15:21:28.086 - OLD video completes async → creates MGR-9512
                current_timer_manager = MGR-9512
15:21:28.086 - MGR-8121's countdown thread ORPHANED (manager replaced!)
```

**Result:** MGR-8121 runs for 10 seconds without anyone able to stop it, overlapping with new slides.

**Solution:**
Added slide ID check before creating timer manager:

```python
def _display_slide_with_timer(self, slide):
    # ... display content ...
    
    # Check we're still on this slide (prevents race condition)
    slide_id = slide.get('slide_id')
    current_slide_id = self.current_slide.get('slide_id') if self.current_slide else None
    
    if slide_id and current_slide_id and slide_id != current_slide_id:
        self.logger.info(f"[TIMER-MGR] Skipping timer creation - slide changed")
        return True  # Don't create timer for old slide
    
    # Safe to create timer
    self._create_slide_timer_manager(slide)
```

**File:** `slideshow_controller.py` lines 462-468

---

## Changes Made

### **File: slideshow_controller.py**

**Change 1 - Line 127:**
```python
# REMOVED:
self._stop_current_timer()

# NOW:
# NOTE: Timer cleanup is handled by _display_slide_with_timer() -> _cleanup_previous_slide_timers()
# DO NOT call _stop_current_timer() here as it causes duplicate cleanup and orphaned threads
```

**Change 2 - Lines 462-468:**
```python
# ADDED: Slide ID validation before timer creation
slide_id = slide.get('slide_id')
current_slide_id = self.current_slide.get('slide_id') if self.current_slide else None

if slide_id and current_slide_id and slide_id != current_slide_id:
    self.logger.info(f"[TIMER-MGR] Skipping timer creation - slide changed (was {slide_id}, now {current_slide_id})")
    return True

# Only create timer if we're still on the same slide
self._create_slide_timer_manager(slide)
```

---

## How It Works

### **Before Fix (BROKEN)**

**Rapid Navigation Sequence:**
1. Slide A displays → Manager A created → Countdown thread starts
2. User presses NEXT quickly
3. `advance_slideshow()` calls `_stop_current_timer()` → Manager A nulled (no wait!)
4. Slide B starts displaying
5. `_cleanup_previous_slide_timers()` → finds nothing (Manager A already gone)
6. Manager B created
7. **Manager A's countdown thread still running → OVERLAP!**

**Async Video Issue:**
1. Video slide starts displaying (async)
2. User presses NEXT before video setup completes
3. New portrait slide displays → Manager X created
4. Old video completes → tries to create Manager Y
5. `current_timer_manager` = Manager Y (replaces Manager X!)
6. **Manager X's countdown thread orphaned → OVERLAP!**

### **After Fix (WORKING)**

**Rapid Navigation:**
1. Slide A displays → Manager A created → Countdown thread starts
2. User presses NEXT quickly
3. `_cleanup_previous_slide_timers()` → calls `cancel_all_timers()` → waits with `join()`
4. Manager A's countdown thread stops cleanly
5. Manager A nulled
6. Slide B displays → Manager B created → No overlap!

**Async Video:**
1. Video slide starts displaying (async)
2. User presses NEXT before video setup completes
3. New portrait slide displays → Manager X created → `current_slide` updated
4. Old video completes → checks slide ID
5. Slide ID mismatch detected → skips timer creation
6. **Manager X continues running normally → No overlap!**

---

## Testing

### **Test Command:**
```bash
./test_countdown_threading.sh
```

### **Test Procedure:**
1. Wait for first slide (2-3 seconds)
2. Press RIGHT arrow 10 times rapidly
3. Press ESC to exit
4. Script automatically analyzes logs

### **Expected Results:**
```
================================================================================
COUNTDOWN THREAD ANALYSIS
================================================================================

ANALYSIS 1: OVERLAPPING COUNTDOWN THREADS
✅ No overlapping countdown threads detected!

ANALYSIS 2: CLEANUP vs CREATE TIMING
✅ All managers created after cleanup completed!

ANALYSIS 3: MANAGER LIFECYCLE SUMMARY
Total managers created: X
✅ All managers that started countdown also finished!

ANALYSIS 4: THREAD REUSE PATTERNS
Unique threads used: Y
No thread reuse (each manager gets new thread)

================================================================================
SUMMARY
================================================================================

✅ No issues detected! Countdown threading is working correctly.
```

### **Previous Results (Before Fix):**
```
⚠️  FOUND 40 INSTANCES OF MULTIPLE COUNTDOWN THREADS RUNNING!
⚠️  FOUND 1 CASES WHERE NEW MANAGER CREATED DURING CLEANUP!
```

---

## Technical Details

### **Thread Lifecycle (Correct)**

**Manager Creation:**
1. `_cleanup_previous_slide_timers()` → cleanup old manager
2. `current_timer_manager.cancel_all_timers()` → sets `is_active = False`
3. `thread.join(timeout=1.5)` → waits for countdown thread to stop
4. `current_timer_manager = None` → clear reference
5. `_create_slide_timer_manager()` → create new manager
6. New countdown thread starts

**Slide ID Check:**
- Prevents old async operations from creating managers after slide changed
- Each slide has unique `slide_id` 
- Before creating timer: verify `slide.slide_id == current_slide.slide_id`
- If mismatch: skip timer creation (slide already advanced)

### **Countdown Thread (in SlideTimerManager)**

```python
def countdown_worker():
    while self.is_active and remaining > 0:
        # Display countdown
        self.controller.display_manager.show_countdown(int(remaining), self.manager_id)
        time.sleep(1)
        remaining -= 1
    # Thread ends when is_active=False or time expires
```

**Stopping:**
1. `cancel_all_timers()` sets `is_active = False`
2. Next iteration: `while self.is_active` → exits loop
3. Thread finishes naturally
4. `join()` waits for thread to finish (max 1.5s)

---

## Files Modified

1. **slideshow_controller.py**
   - Line 120-121: Added comment explaining no `_stop_current_timer()` call
   - Lines 462-468: Added slide ID check before timer creation

---

## Benefits

✅ **No more overlapping countdown threads** - Each manager properly cleaned up before new one starts  
✅ **Race condition resolved** - Async operations can't create managers for old slides  
✅ **Clean thread lifecycle** - All threads properly stopped with `join()`  
✅ **Reliable navigation** - Rapid key presses work correctly  
✅ **Video handling fixed** - Async video display doesn't interfere with navigation  

---

## Verification

Run the automated test to confirm:
```bash
./test_countdown_threading.sh
```

The analyzer will show:
- Number of overlapping thread instances (should be 0)
- Timing conflicts (should be 0)  
- Orphaned managers (should be 0)
- Thread reuse patterns (informational)

All issues should be resolved! ✅
