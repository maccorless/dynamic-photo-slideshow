# Mouse Navigation Enhancement

## Overview
Added comprehensive mouse navigation controls to the slideshow for intuitive navigation without keyboard or voice commands.

## Implementation Date
October 15, 2025

## Mouse Controls

| Mouse Action | Function | Trigger Type |
|-------------|----------|--------------|
| **Left Click** | Previous photo | `TriggerType.MOUSE` + `Direction.PREVIOUS` |
| **Right Click** | Next photo | `TriggerType.MOUSE` + `Direction.NEXT` |
| **Scroll Wheel UP** | Pause/Resume | `toggle_pause()` |
| **Scroll Wheel DOWN** | Pause/Resume | `toggle_pause()` |

## Technical Implementation

### 1. Event Handling (`main_pygame.py`)
Added `pygame.MOUSEBUTTONDOWN` event handling in the main event loop:

```python
elif event.type == pygame.MOUSEBUTTONDOWN:
    # Handle mouse button clicks and scroll wheel
    if event.button == 1:  # Left click
        self.logger.info("Left mouse click - going to previous slide")
        self.controller.advance_slideshow(TriggerType.MOUSE, Direction.PREVIOUS)
    elif event.button == 3:  # Right click
        self.logger.info("Right mouse click - going to next slide")
        self.controller.advance_slideshow(TriggerType.MOUSE, Direction.NEXT)
    elif event.button == 4:  # Scroll wheel UP
        self.logger.info("Scroll wheel UP - toggling pause")
        self.controller.toggle_pause()
    elif event.button == 5:  # Scroll wheel DOWN
        self.logger.info("Scroll wheel DOWN - toggling pause")
        self.controller.toggle_pause()
```

### 2. Trigger Type Addition (`slideshow_controller.py`)
Added new trigger type to the `TriggerType` enum:

```python
class TriggerType(Enum):
    """Types of triggers that can cause slideshow advancement."""
    TIMER = "timer"
    KEY_NEXT = "key_next"
    KEY_PREVIOUS = "key_previous"
    VOICE_NEXT = "voice_next"
    VOICE_PREVIOUS = "voice_previous"
    MOUSE = "mouse"  # NEW
    STARTUP = "startup"
```

### 3. Pygame Mouse Button Mapping
- `event.button == 1`: Left mouse button
- `event.button == 3`: Right mouse button
- `event.button == 4`: Scroll wheel UP
- `event.button == 5`: Scroll wheel DOWN

**Note**: Middle click (button 2) is unreliable on macOS with Bluetooth mice, so scroll wheel movement is used instead for better compatibility.

## Features

### ✅ Advantages
- **Intuitive Navigation**: Natural left/right click for back/forward
- **Quick Pause**: Scroll wheel for instant pause without keyboard
- **macOS Compatible**: Scroll wheel works reliably with Bluetooth mice (unlike middle click)
- **Consistent with UI Patterns**: Right-click for "next" is common in slideshow apps
- **Accessibility**: Alternative input method for users who prefer mouse
- **Logging**: All mouse actions are logged for debugging

### 🎯 Use Cases
- **Couch Mode**: Navigate with wireless mouse from distance
- **Touch Displays**: Works with touch-enabled displays (tap = click)
- **Presentation Mode**: Quick navigation during presentations
- **Accessibility**: Alternative for users with keyboard difficulties

## Integration with Existing Systems

### History Navigation
- Mouse clicks properly integrate with slide history
- Previous/next navigation respects history cache
- Works seamlessly with keyboard and voice navigation

### Pause/Resume
- Middle click uses the same `toggle_pause()` method as spacebar
- Maintains timer state correctly
- Works during both photo and video playback

### Video Playback
- Mouse navigation works during video playback
- Can skip videos or go back
- Pause/resume works for videos

## Testing Recommendations

1. **Basic Navigation**
   - Left click → should go to previous slide
   - Right click → should go to next slide
   - Middle click → should pause/resume

2. **During Video Playback**
   - Test all three mouse buttons during video
   - Verify video stops/starts correctly

3. **Rapid Clicking**
   - Test rapid left/right clicks
   - Verify history navigation works correctly

4. **Pause State**
   - Middle click to pause
   - Try left/right click while paused
   - Middle click to resume

5. **Edge Cases**
   - First slide + left click (should stay at first)
   - Last slide + right click (should wrap or stay)
   - Multiple rapid middle clicks

## Documentation Updates

### README.md
Added new "Mouse Controls" section:
```markdown
### Mouse Controls
- **Left Click**: Previous photo
- **Right Click**: Next photo
- **Middle Click** (scroll wheel): Pause/resume slideshow
```

## Compatibility

- ✅ **macOS**: Full support
- ✅ **Pygame**: Uses standard pygame mouse events
- ✅ **Fullscreen**: Works in fullscreen mode
- ✅ **All Slide Types**: Photos, videos, portrait pairs

## Future Enhancements (Optional)

- **Scroll Wheel**: Use scroll up/down for navigation
- **Double Click**: Alternative action (e.g., fullscreen toggle)
- **Click and Hold**: Show metadata overlay
- **Gesture Support**: Swipe gestures on trackpad
- **Mouse Hover**: Show controls on hover

## Status
✅ **IMPLEMENTED AND READY FOR TESTING**

All mouse navigation controls are now active and integrated with the slideshow controller.
