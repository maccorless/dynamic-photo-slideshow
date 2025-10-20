# Settings Window Implementation - Clean Architecture

## Overview
Settings window integration using pygame_gui for runtime configuration changes.

---

## Architecture Flow

```
User presses Cmd-S
    ↓
main_pygame.py: _open_settings()
    ↓
Checks if settings_window is initialized
    ↓
Pauses slideshow
    ↓
Calls display_manager.show_settings()
    ↓
pygame_display_manager.py: show_settings()
    ↓
settings_window.py: show()
    ↓
Creates pygame_gui UI elements
    ↓
Event Loop processes events:
    - display_manager.handle_events() filters events for settings
    - settings_window.handle_event() processes UI interactions
    - settings_window.update() updates UI state
    - settings_window.draw() renders UI
    ↓
User changes setting
    ↓
settings_window saves to SettingsManager
    ↓
SettingsManager saves to config.json
    ↓
settings_window._apply_live_setting() updates controller.config
    ↓
User closes settings (ESC or OK button)
    ↓
settings_window.hide() + on_close_callback()
    ↓
Slideshow resumes
```

---

## Key Components

### 1. main_pygame.py

**Initialization (lines 322-329):**
```python
# Create settings manager
settings_manager = SettingsManager()

# Create pygame-compatible controller
controller = PygameSlideshowController(config, photo_manager, display_manager, path_config)

# Initialize settings window with controller and settings manager
display_manager.set_controller(controller.controller, settings_manager)
```

**Opening Settings (lines 89-112):**
```python
def _open_settings(self) -> None:
    """Open settings window (pause slideshow first)."""
    # Check if settings window is initialized
    if self.display_manager.settings_window is None:
        self.logger.error("[SETTINGS] Settings window not initialized yet")
        return
    
    # Pause the slideshow if not already paused
    if not self.controller.is_paused:
        self.controller.toggle_pause()
    
    # Set callback to resume when settings close
    def on_settings_close():
        if self.controller.is_paused:
            self.controller.toggle_pause()
    
    self.display_manager.settings_window.set_on_close_callback(on_settings_close)
    self.display_manager.show_settings()
```

**Event Loop (lines 124-226):**
```python
# Handle pygame events
# Note: display_manager.handle_events() already processes settings window events
# and filters them out if settings are open
events = self.display_manager.handle_events()

for event in events:
    # Process slideshow events (only if settings not open)
    ...

# Update and draw settings window if open
if self.display_manager.is_settings_open():
    time_delta = clock.tick(60) / 1000.0  # Higher FPS for UI
    self.display_manager.settings_window.update(time_delta)
    self.display_manager.settings_window.draw()
    pygame.display.flip()
else:
    clock.tick(30)  # Normal FPS for slideshow
```

**Cmd-S Handler (lines 156-162):**
```python
elif event.key == pygame.K_s:
    mods = pygame.key.get_mods()
    if (mods & pygame.KMOD_META) or (mods & pygame.KMOD_CTRL):
        self.logger.info("Cmd+S/Ctrl+S pressed - opening settings")
        self._open_settings()
        continue
```

---

### 2. pygame_display_manager.py

**Initialization (lines 86-102):**
```python
# Settings window (will be initialized with settings_manager later)
self.settings_manager = None
self.settings_window = None

def set_controller(self, controller, settings_manager):
    """Set the controller reference and settings manager for live settings updates."""
    self.settings_manager = settings_manager
    self.settings_window = SettingsWindow(self.screen, settings_manager, controller)
    self.logger.info("Settings window initialized with shared settings manager and controller")
```

**Event Filtering (lines 929-942):**
```python
def handle_events(self) -> List[pygame.event.Event]:
    """Handle pygame events and return them for processing."""
    events = pygame.event.get()
    
    # If settings window is open, let it handle events first
    if self.settings_window is not None and self.settings_window.is_open():
        filtered_events = []
        for event in events:
            if not self.settings_window.handle_event(event):
                # Event not handled by settings window, pass it through
                filtered_events.append(event)
        return filtered_events
    
    return events
```

**Settings Window Control (lines 1434-1452):**
```python
def show_settings(self) -> None:
    """Show the settings window."""
    if self.settings_window is None:
        self.logger.error("Cannot show settings: settings_window not initialized")
        return
    self.settings_window.show()

def hide_settings(self) -> None:
    """Hide the settings window."""
    if self.settings_window is None:
        self.logger.error("Cannot hide settings: settings_window not initialized")
        return
    self.settings_window.hide()

def is_settings_open(self) -> bool:
    """Check if settings window is currently open."""
    return self.settings_window is not None and self.settings_window.is_open()
```

---

### 3. settings_window.py

**Event Handling (lines 252-309):**
```python
def handle_event(self, event: pygame.event.Event) -> bool:
    """Handle pygame events for the settings window."""
    if not self.is_visible or not self.manager:
        return False
    
    # Let UI manager process the event
    handled = self.manager.process_events(event)
    
    # Handle keyboard events
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            self.hide()
            return True
        elif event.key == pygame.K_TAB:
            # Tab key handled by pygame_gui for field navigation
            pass
    
    # Handle UI button clicks, text entry, dropdowns, etc.
    ...
    
    return handled
```

**Live Settings Application (lines 375-409):**
```python
def _apply_live_setting(self, group: str, setting: str, value: Any) -> None:
    """Apply settings that can be changed without restart."""
    if not self.controller:
        return
    
    # Only apply Display settings live
    if group == 'display':
        if setting == 'slideshow_interval':
            self.controller.config.set('SLIDESHOW_INTERVAL', value)
        elif setting == 'max_video_duration':
            self.controller.config.set('VIDEO_MAX_DURATION', value)
        # ... other settings
```

---

## Data Flow

### Settings Save Flow:
1. User changes value in UI
2. `handle_event()` detects UI event (checkbox, text entry, dropdown)
3. Calls `_handle_checkbox_toggle()`, `_handle_integer_change()`, or `_handle_enum_change()`
4. Calls `settings_manager.set_setting(group, setting, value)`
5. SettingsManager validates and saves to config.json
6. Calls `_apply_live_setting()` to update running slideshow
7. Updates `controller.config` for immediate effect

### Settings Load Flow:
1. SettingsManager loads config.json on startup
2. Settings window reads current values from SettingsManager
3. UI widgets display current values
4. Controller uses config values for slideshow behavior

---

## Key Design Decisions

### ✅ Single SettingsManager Instance
- Created once in main()
- Shared between display_manager and settings_window
- Ensures consistent state

### ✅ Event Filtering
- `display_manager.handle_events()` filters events when settings open
- Prevents slideshow from processing events meant for settings
- Settings window gets first chance to handle all events

### ✅ Null Safety
- All settings_window access checks for None first
- Graceful degradation if not initialized
- Clear error messages in logs

### ✅ Pause/Resume
- Slideshow paused before showing settings
- Resumed via callback when settings close
- Prevents timer conflicts

### ✅ Live Updates
- Display settings apply immediately
- Config updated in real-time
- No restart required for common settings

---

## Testing Checklist

- [ ] App starts without crash
- [ ] Cmd-S opens settings immediately
- [ ] Settings window displays current values
- [ ] Tab key navigates between fields
- [ ] Changing slideshow_interval updates timer
- [ ] Changing max_video_duration affects videos
- [ ] Toggling checkboxes works
- [ ] ESC closes settings
- [ ] OK button closes settings
- [ ] Settings persist to config.json
- [ ] Settings persist across app restarts
- [ ] Slideshow pauses when settings open
- [ ] Slideshow resumes when settings close
- [ ] No duplicate event processing
- [ ] Settings window renders at 60 FPS
- [ ] Slideshow runs at 30 FPS when settings closed

---

## Common Issues (Now Fixed)

### ❌ "Settings window not initialized yet"
**Cause:** set_controller() not called before Cmd-S pressed
**Fix:** Call set_controller() in main() before start_slideshow()

### ❌ Settings don't save
**Cause:** Multiple SettingsManager instances
**Fix:** Create single instance, pass to set_controller()

### ❌ Settings window doesn't appear
**Cause:** update() and draw() not called in event loop
**Fix:** Added update/draw calls when is_settings_open()

### ❌ Duplicate event processing
**Cause:** Events processed in both handle_events() and main loop
**Fix:** Removed duplicate processing, rely on handle_events() filtering

### ❌ Tab key doesn't work
**Cause:** Events not reaching pygame_gui manager
**Fix:** Ensure manager.process_events() called in handle_event()

---

## File Summary

**Modified Files:**
- main_pygame.py (added settings integration)
- pygame_display_manager.py (added settings window management)
- settings_window.py (created new)
- settings_manager.py (created new)
- config_schema.json (created new)

**Lines of Code:**
- main_pygame.py: ~25 lines added
- pygame_display_manager.py: ~50 lines added
- settings_window.py: ~450 lines (new file)
- settings_manager.py: ~330 lines (new file)
- config_schema.json: ~200 lines (new file)

**Total:** ~1055 lines for complete settings system
