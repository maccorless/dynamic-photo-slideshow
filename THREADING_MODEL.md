# Threading Model Analysis

**Created:** October 13, 2025  
**Purpose:** Document all threading in the codebase and distinguish main thread vs background threads

---

## Executive Summary

**Main Thread (Synchronous):**
- All pygame operations (display, events, rendering)
- All slide display operations
- Navigation (next/back)
- Pause/resume
- Video playback rendering
- User interaction handling

**Background Threads (Asynchronous):**
1. Timer advancement trigger (schedules main thread work)
2. Countdown display updates (visual only)
3. Voice command recognition (continuous listening)
4. Voice command execution (delayed actions)
5. Video pre-export (startup optimization)

**Critical Pattern:** Background threads NEVER directly modify display or slideshow state. They only set flags or schedule work for the main thread.

---

## Main Thread Execution Path

### **Entry Point**
**File:** `main_pygame.py`  
**Function:** `_pygame_event_loop()` (lines 56-108)

**Responsibilities:**
- Pygame event loop at 30 FPS
- Handle keyboard/mouse events
- Check for timer advancement flags
- Call slideshow controller methods
- Update display

### **Core Slideshow Operations (All Main Thread)**

#### **1. Navigation**
**File:** `slideshow_controller.py`  
**Functions:**
- `advance_slideshow()` - Navigate to next/previous slide
- `_display_slide_with_timer()` - Display slide content
- `_display_slide_content()` - Route to photo/video display
- `_display_single_photo_content()` - Show single photo
- `_display_portrait_pair_content()` - Show portrait pair
- `_display_video_content()` - Show video

**Thread:** MAIN - All called directly from event loop

#### **2. Pause/Resume**
**File:** `slideshow_controller.py`  
**Functions:**
- `toggle_pause()` - Toggle pause state
- `_pause_timer_new()` - Pause timer manager
- `_resume_timer_new()` - Resume timer manager

**Thread:** MAIN - Called from keyboard events

#### **3. Display Operations**
**File:** `pygame_display_manager.py`  
**Functions:**
- `display_photo()` - Render photo to screen
- `_display_video()` - Render video frames
- `show_countdown()` - Update countdown display
- All pygame drawing operations

**Thread:** MAIN - All pygame operations must be on main thread

---

## Background Thread Execution

### **Thread 1: Timer Advancement** ⏱️

**Purpose:** Schedule slide advancement when timer expires  
**File:** `slide_timer_manager.py` lines 62-75  
**Thread Type:** `threading.Timer` (one-shot)

```python
def advance_callback():
    if self.is_active:
        self.controller._schedule_advancement_on_main_thread()

self.advancement_timer = threading.Timer(duration, advance_callback)
self.advancement_timer.start()
```

**What it does:**
1. Wait for slide duration (10s for photos, 12s for videos)
2. When timer expires, call `advance_callback()`
3. Callback sets `timer_advance_requested = True` flag
4. **DOES NOT** call advance_slideshow() directly

**Main thread processing:**
```python
# main_pygame.py lines 96-102
if self.controller.timer_advance_requested:
    self.controller.timer_advance_requested = False
    self.controller.advance_slideshow(TriggerType.TIMER, Direction.NEXT)
```

**Key:** Timer thread only sets a flag; main thread does the actual work

---

### **Thread 2: Countdown Display** 🔢

**Purpose:** Update countdown number every second  
**File:** `slide_timer_manager.py` lines 214-234  
**Thread Type:** `threading.Thread` (continuous daemon)

```python
def countdown_worker():
    while self.is_active and duration_seconds > 0:
        remaining = self.get_remaining_time()
        if remaining <= 0 or not self.is_active:
            break
        self.controller.display_manager.show_countdown(int(remaining))
        time.sleep(1.0)

self.countdown_thread = threading.Thread(target=countdown_worker, daemon=True)
self.countdown_thread.start()
```

**What it does:**
1. Loop every 1 second
2. Calculate remaining time
3. Call `display_manager.show_countdown()`
4. Continues until slide changes

**Display manager processing:**
```python
# pygame_display_manager.py lines 973-1012
def show_countdown(self, remaining_seconds: int):
    # Cache countdown text to avoid re-rendering
    if remaining_seconds != self._last_countdown:
        self._countdown_text = self.font.render(...)
        self._last_countdown = remaining_seconds
    
    self.screen.blit(self._countdown_text, self._countdown_rect)
    if not video_playing:
        pygame.display.flip()
```

**Key:** Thread calls display method, but rendering is thread-safe

**⚠️ ISSUE:** Multiple countdown threads can exist during rapid navigation (see TIMER_ANALYSIS.md)

---

### **Thread 3: Legacy Countdown (DEAD CODE)** 💀

**Purpose:** Old countdown system (unused)  
**File:** `slideshow_controller.py` lines 628-663  
**Thread Type:** `threading.Thread` (continuous daemon)

**Status:** NOT CALLED - Dead code that should be removed

**Risk:** Could be accidentally called, creating dual countdown threads

---

### **Thread 4: Voice Command Recognition** 🎤

**Purpose:** Continuously listen for voice commands  
**File:** `voice_command_service.py` lines 111-135  
**Thread Type:** Background thread managed by `speech_recognition` library

```python
def start_listening():
    self.stop_listening = self.recognizer.listen_in_background(
        self.microphone, 
        self._voice_callback,
        phrase_time_limit=2.0
    )
```

**What it does:**
1. Continuously listen to microphone
2. When audio detected, process in background
3. Call `_voice_callback()` with audio data
4. Recognize speech using Google API
5. Match command and execute

**Callback processing:**
```python
# voice_command_service.py lines 145-204
def _voice_callback(self, recognizer, audio):
    text = self.voice_provider.recognize_speech(audio)
    self._process_voice_command(text)
    # Calls controller methods like pause/resume/next/back
```

**Key:** Voice recognition runs in background, but controller methods are called directly

**⚠️ THREADING ISSUE:** Voice callback calls controller methods from background thread, not main thread

---

### **Thread 5: Voice Command Execution (Delayed)** ⏲️

**Purpose:** Execute voice commands after 1.5s delay for visual feedback  
**File:** `voice_command_service.py` lines 221-252  
**Thread Type:** `threading.Thread` (one-shot daemon)

```python
def _schedule_command_execution(command, keyword):
    def delayed_execution():
        time.sleep(1.5)  # Show overlay first
        self._execute_command(command)
    
    thread = threading.Thread(target=delayed_execution, daemon=True)
    thread.start()
```

**What it does:**
1. Wait 1.5 seconds to show voice overlay
2. Execute command (pause/resume/next/back)
3. Clear overlay

**Key:** Executes controller methods from background thread

**⚠️ THREADING ISSUE:** Calls controller methods from background thread

---

### **Thread 6: Video Pre-Export** 📹

**Purpose:** Pre-export videos at startup for faster playback  
**File:** `photo_manager.py` lines 644-672  
**Thread Type:** `threading.Thread` (one-shot daemon)

```python
def _pre_export_videos(self, videos, max_exports=10):
    def export_videos_background():
        for video in videos[:max_exports]:
            self._export_video_temporarily(video)
    
    export_thread = threading.Thread(target=export_videos_background, daemon=True)
    export_thread.start()
```

**What it does:**
1. Run at startup after photos loaded
2. Export up to 10 videos in background
3. Cache them for instant playback later

**Thread Safety:** ✅ Safe - Only modifies video cache, not display state

---

## Threading Safety Analysis

### ✅ **Thread-Safe Operations**

1. **Timer advancement scheduling**
   - Sets flag only: `timer_advance_requested = True`
   - Main thread checks flag and processes

2. **Video pre-export**
   - Only writes to file cache
   - No display or state modifications

3. **Countdown display (mostly safe)**
   - Only updates countdown text
   - Uses cached rendering to minimize conflicts
   - **Issue:** Multiple threads can call simultaneously

### ⚠️ **Potentially Unsafe Operations**

1. **Voice command callbacks**
   - Calls controller methods directly from background thread
   - Controller methods may touch display state
   - **Risk:** Race conditions with main thread

2. **Voice command delayed execution**
   - Executes controller methods from background thread
   - **Risk:** Threading conflicts

3. **Multiple countdown threads**
   - Multiple threads can call `show_countdown()` simultaneously
   - **Risk:** Erratic countdown display (documented issue)

---

## Threading Best Practices (Current Implementation)

### **Pattern: Flag-Based Scheduling** ✅

**Good Example:** Timer advancement
```python
# Background thread (timer callback)
def advance_callback():
    self.controller._schedule_advancement_on_main_thread()

def _schedule_advancement_on_main_thread(self):
    self.timer_advance_requested = True  # Just set flag

# Main thread (event loop)
if self.controller.timer_advance_requested:
    self.controller.timer_advance_requested = False
    self.controller.advance_slideshow(...)  # Do actual work
```

**Why it works:**
- Background thread only sets a boolean flag
- No display or state modification
- Main thread does all the real work
- Thread-safe by design

### **Anti-Pattern: Direct Controller Calls** ❌

**Bad Example:** Voice commands
```python
# Background thread (voice callback)
def _voice_callback(self, recognizer, audio):
    text = recognize_speech(audio)
    self._process_voice_command(text)  # Calls controller directly
    
def _process_voice_command(self, text):
    self.controller.pause_for_voice_command()  # Controller call from bg thread!
```

**Why it's risky:**
- Background thread calls controller methods
- Controller methods may update display state
- No coordination with main thread
- Potential race conditions

---

## Recommendations

### **High Priority: Fix Voice Command Threading**

**Current (unsafe):**
```python
# Background thread calls controller directly
self.controller.pause_for_voice_command()
```

**Recommended (safe):**
```python
# Background thread sets flag
self.controller.voice_command_requested = 'pause'

# Main thread checks flag
if self.controller.voice_command_requested:
    command = self.controller.voice_command_requested
    self.controller.voice_command_requested = None
    self.controller.execute_voice_command(command)
```

### **Medium Priority: Fix Multiple Countdown Threads**

**Issue:** Old threads don't stop immediately, multiple threads active

**Solution:** Add `thread.join()` to ensure cleanup (see TIMER_ANALYSIS.md)

### **Low Priority: Remove Legacy Countdown Code**

**Issue:** Dead code that creates confusion

**Solution:** Delete lines 619-663 in `slideshow_controller.py`

---

## Summary Table

| Component | Location | Thread Type | Main/Background | Thread-Safe? | Notes |
|-----------|----------|-------------|-----------------|--------------|-------|
| **Pygame Event Loop** | main_pygame.py:56 | Main thread | MAIN | ✅ | Core execution path |
| **Slide Display** | slideshow_controller.py | Main thread | MAIN | ✅ | All display operations |
| **Timer Advancement** | slide_timer_manager.py:74 | threading.Timer | BACKGROUND | ✅ | Sets flag only |
| **Countdown Display** | slide_timer_manager.py:232 | threading.Thread | BACKGROUND | ⚠️ | Multiple threads issue |
| **Legacy Countdown** | slideshow_controller.py:661 | threading.Thread | BACKGROUND | 💀 | Dead code |
| **Voice Recognition** | voice_command_service.py:123 | Background (library) | BACKGROUND | ❌ | Calls controller directly |
| **Voice Execution** | voice_command_service.py:250 | threading.Thread | BACKGROUND | ❌ | Calls controller directly |
| **Video Pre-Export** | photo_manager.py:670 | threading.Thread | BACKGROUND | ✅ | File operations only |

**Legend:**
- ✅ Thread-safe
- ⚠️ Mostly safe with known issues
- ❌ Unsafe - needs fixing
- 💀 Dead code - should be removed

---

## Threading Model Diagram

```
MAIN THREAD (Pygame Event Loop @ 30 FPS)
├─ Handle keyboard/mouse events
├─ Check timer_advance_requested flag
│  └─ If set: advance_slideshow()
├─ Render display (photos/videos)
└─ Update countdown display

BACKGROUND THREADS
│
├─ Timer Advancement (threading.Timer)
│  ├─ Wait for slide duration
│  └─ Set timer_advance_requested flag
│
├─ Countdown Display (threading.Thread)
│  ├─ Calculate remaining time every 1s
│  └─ Call display_manager.show_countdown()
│
├─ Voice Recognition (speech_recognition lib)
│  ├─ Listen to microphone continuously
│  ├─ Recognize speech
│  └─ ❌ Call controller methods directly (UNSAFE)
│
├─ Voice Execution (threading.Thread)
│  ├─ Wait 1.5s for overlay
│  └─ ❌ Call controller methods directly (UNSAFE)
│
└─ Video Pre-Export (threading.Thread)
   ├─ Export videos at startup
   └─ ✅ File operations only (SAFE)
```

---

## Conclusion

**Current State:**
- Main execution path is synchronous (good!)
- Timer advancement uses safe flag-based pattern (good!)
- Countdown display has multiple thread issue (documented)
- Voice commands call controller from background threads (unsafe)

**Alignment with Goal:**
- ✅ Display operations are synchronous to main thread
- ✅ Navigation is synchronous to main thread
- ⚠️ Some background operations need to be converted to flag-based pattern
- ❌ Voice commands violate the synchronous pattern

**Next Steps:**
1. Fix countdown thread cleanup (TIMER_ANALYSIS.md)
2. Convert voice commands to flag-based pattern
3. Remove legacy countdown code
