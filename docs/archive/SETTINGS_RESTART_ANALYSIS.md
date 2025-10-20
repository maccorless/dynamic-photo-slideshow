# Settings Restart Requirements Analysis

## Settings That CAN Be Applied Live (No Restart)

### Display Settings:
1. **slideshow_interval** ✅ LIVE
   - Read dynamically in `_calculate_slideshow_timer()`
   - Applied to next slide immediately
   - Can update `config.SLIDESHOW_INTERVAL` in memory

2. **max_video_duration** ✅ LIVE
   - Read dynamically in `_calculate_slideshow_timer()`
   - Applied to next video immediately
   - Can update `config.VIDEO_MAX_DURATION` in memory

3. **show_countdown_timer** ✅ LIVE
   - Checked in `pygame_display_manager.show_countdown()`
   - Can update `config.show_countdown_timer` in memory
   - Takes effect on next countdown display

4. **show_date_overlay** ✅ LIVE
   - Checked in display methods
   - Can update `config.show_date_overlay` in memory
   - Takes effect on next slide

5. **show_location_overlay** ✅ LIVE
   - Checked in display methods
   - Can update `config.show_location_overlay` in memory
   - Takes effect on next slide

## Settings That REQUIRE Restart

### Photos Settings:
1. **portrait_pairing_enabled** ❌ RESTART REQUIRED
   - Checked once during slide creation
   - Affects slide composition logic
   - Changing mid-slideshow could cause inconsistent behavior

2. **min_people_for_pairing** ❌ RESTART REQUIRED
   - Used during photo filtering/selection
   - Affects which photos are eligible

3. **photo_limit** ❌ RESTART REQUIRED
   - Applied during `load_photos()`
   - Would require reloading entire photo library

### Voice Settings:
1. **voice_commands_enabled** ❌ RESTART REQUIRED
   - Voice service started at initialization
   - Would need to start/stop service dynamically

2. **voice_confidence_threshold** ⚠️ MAYBE LIVE
   - Could potentially update in voice service
   - But safer to require restart

3. **voice_*_keywords** ❌ RESTART REQUIRED
   - Keywords loaded at voice service initialization
   - Would need to reload keyword matchers

### Filters Settings:
1. **people_filter** ❌ RESTART REQUIRED
   - Applied during `load_photos()`
   - Filters photo library at load time

2. **places_filter** ❌ RESTART REQUIRED
   - Applied during `load_photos()`
   - Filters photo library at load time

3. **keywords_filter** ❌ RESTART REQUIRED
   - Applied during `load_photos()`
   - Filters photo library at load time

4. **filter_logic** ❌ RESTART REQUIRED
   - Applied during `load_photos()`
   - Changes how filters combine

### Advanced Settings:
1. **album_name** ❌ RESTART REQUIRED
   - Used during photo manager initialization
   - Would require reloading entire photo library

2. **cache_size** ❌ RESTART REQUIRED
   - Cache initialized at startup
   - Changing size would require cache rebuild

3. **log_level** ❌ RESTART REQUIRED
   - Logging configured at startup
   - Would need to reconfigure all loggers

4. **navigation_history_size** ⚠️ MAYBE LIVE
   - Could potentially resize history array
   - But safer to require restart

### Video Settings:
1. **video_audio_enabled** ⚠️ MAYBE LIVE
   - Passed to ffplay at video start
   - Could apply to next video

2. **video_test_mode** ❌ RESTART REQUIRED
   - Affects slide selection logic
   - Changes fundamental slideshow behavior

## Summary

**Can Apply Live (5 settings):**
- slideshow_interval
- max_video_duration
- show_countdown_timer
- show_date_overlay
- show_location_overlay

**Require Restart (19+ settings):**
- All Photos settings (3)
- All Voice settings (6)
- All Filters settings (4)
- All Advanced settings (4)
- Most Video settings (2)

## Implementation Strategy

### Phase 1: Display Tab Only (Current)
- All 5 Display settings can be applied live
- Update config object in memory when changed
- No restart button needed for Display tab

### Phase 2: Other Tabs (Future)
- Show warning message when restart-required setting is changed
- Change OK button to "Restart" button
- Clicking "Restart" exits app with special exit code
- Wrapper script can detect exit code and restart app

### Code Changes Needed

1. **Mark settings in schema:**
```json
"slideshow_interval": {
  "type": "integer",
  "requires_restart": false,  // NEW FIELD
  ...
}
```

2. **Track restart-required changes:**
```python
self.restart_required = False
self.restart_required_settings = []
```

3. **Update button dynamically:**
```python
if self.restart_required:
    self.ok_button.set_text("Restart Required")
    self.show_restart_warning()
```

4. **Apply live settings immediately:**
```python
def _apply_live_setting(self, group, setting, value):
    """Apply settings that don't require restart."""
    if group == 'display':
        if setting == 'slideshow_interval':
            self.controller.config.SLIDESHOW_INTERVAL = value
        elif setting == 'max_video_duration':
            self.controller.config.VIDEO_MAX_DURATION = value
        # ... etc
```
