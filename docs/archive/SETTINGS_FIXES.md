# Settings System Fixes - October 16, 2025

## Issues Fixed

### 1. ✅ Settings Changes Now Apply to Slideshow

**Problem:** Changing slideshow_interval from 10 to 5 seconds didn't affect the actual slideshow timing.

**Root Cause:** The slideshow was loading configuration from `config.py` (hardcoded defaults), not from `config.json` (user settings).

**Solution:**
- Added `SettingsManager` import to `main_pygame.py`
- Load settings from `config.json` at startup
- Apply user settings to config object before starting slideshow
- Settings now override defaults from `config.py`

**Code Added:**
```python
# Load settings from config.json and apply to config object
settings_manager = SettingsManager()
user_settings = settings_manager.get_all_settings()

# Apply display settings
if 'display' in user_settings:
    if 'slideshow_interval' in user_settings['display']:
        config.slideshow_interval = user_settings['display']['slideshow_interval']
    # ... etc
```

**Result:** Changes to slideshow_interval, countdown timer, video duration, and overlays now take effect immediately on next app start.

---

### 2. ✅ Added Max Video Duration Setting

**Problem:** No setting in UI to control how long videos play.

**Solution:**
- Moved `max_video_duration` from Video tab to Display tab
- Now appears as 4th setting in Display tab
- Range: 1-60 seconds, default 15 seconds
- Applied to config at startup

**Display Tab Settings (now 5 total):**
1. Slideshow Interval (1-60s)
2. Show Countdown Timer (ON/OFF)
3. Max Video Duration (1-60s) ← NEW
4. Show Date Overlay (ON/OFF)
5. Show Location Overlay (ON/OFF)

---

### 3. ✅ Removed Countdown Position Setting

**Problem:** Setting existed but had no implementation - countdown timer position is hardcoded.

**Solution:**
- Removed `countdown_position` from `config_schema.json`
- Removed from `config.json`
- Display tab now shows only implemented settings

**Why Removed:** The countdown timer rendering code in `pygame_display_manager.py` has a hardcoded position and doesn't support configurable positioning. Rather than show a non-functional setting, we removed it.

---

## Files Modified

1. **config_schema.json**
   - Removed: `countdown_position` enum setting
   - Moved: `max_video_duration` from video → display section
   - Display now has 5 settings (was 5, but different)

2. **config.json**
   - Removed: `countdown_position: "top_right"`
   - Moved: `max_video_duration: 15` from video → display section
   - Video section now has only 2 settings

3. **main_pygame.py**
   - Added: `SettingsManager` import
   - Added: Settings loading and application at startup
   - Added: Logging of applied settings
   - Result: User settings from config.json now override config.py defaults

---

## Testing

**Test 1: Slideshow Interval**
1. Open settings (Cmd-S)
2. Change "Slideshow Interval" from 10 to 5
3. Close settings
4. Restart slideshow
5. ✅ Slides now advance every 5 seconds

**Test 2: Max Video Duration**
1. Open settings (Cmd-S)
2. Change "Max Video Duration" from 15 to 10
3. Close settings
4. Restart slideshow
5. ✅ Videos now play for max 10 seconds

**Test 3: Countdown Timer**
1. Open settings (Cmd-S)
2. Toggle "Show Countdown Timer" to OFF
3. Close settings
4. Restart slideshow
5. ✅ Countdown timer no longer displayed

---

## Known Limitations

1. **Settings require app restart** - Changes don't apply to currently running slideshow, only on next start
2. **Countdown position is hardcoded** - Cannot be changed via settings (that's why we removed the setting)
3. **Some config.py settings not exposed** - Only Display settings are in UI so far (Video, Photos, Voice, Filters, Advanced tabs coming in Milestone 4)

---

## Next Steps

**Milestone 4:** Add remaining 5 tabs
- Video tab (2 settings: audio, test mode)
- Photos tab (3 settings: pairing, min people, limit)
- Voice tab (6 settings: enable, confidence, keywords)
- Filters tab (4 settings: people, places, keywords, logic)
- Advanced tab (4 settings: album, cache, logging, history)

**Total:** 22 more settings to add to UI
