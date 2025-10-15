#!/usr/bin/env python3
"""
Quick utility to enable video failure test mode on a running slideshow.

This script can be imported in a Python console while the slideshow is running
to enable test mode for simulating video failures.

Usage (in Python console while slideshow is running):
    import enable_video_test_mode
    enable_video_test_mode.enable_load_failure()
    # or
    enable_video_test_mode.enable_codec_failure()
"""

import logging
import sys

logger = logging.getLogger(__name__)

# Instructions for enabling test mode
INSTRUCTIONS = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    VIDEO ERROR HANDLING TEST MODE                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

To test video error handling on your running slideshow:

1. Start your slideshow:
   python main_pygame.py

2. Open a Python console (in another terminal):
   python

3. Get reference to the display manager:
   
   # You'll need to access the display manager from the running slideshow
   # This depends on how you've structured your main_pygame.py
   
   # If you can access it, enable test mode with:
   display_manager.enable_video_failure_test_mode('load')
   
   # Or use one of these shortcuts:
   display_manager.enable_video_failure_test_mode('codec')
   
4. Navigate to any video in the slideshow

5. Observe the error handling:
   - Red error message displayed on screen
   - Detailed error in logs
   - Countdown continues working
   - Slideshow advances normally

6. Disable test mode:
   display_manager.disable_video_failure_test_mode()

═══════════════════════════════════════════════════════════════════════════════

ALTERNATIVE: Create a corrupted video file for testing:

1. Create corrupted video:
   echo "not a real video file" > /tmp/test_bad_video.mp4

2. Add to your Photos library or reference directly

3. Navigate to it in slideshow to trigger error handling

═══════════════════════════════════════════════════════════════════════════════
"""

def print_instructions():
    """Print instructions for enabling test mode."""
    print(INSTRUCTIONS)

def enable_load_failure():
    """Enable test mode for simulating video load failures."""
    print("🧪 To enable LOAD FAILURE test mode:")
    print("   display_manager.enable_video_failure_test_mode('load')")
    print("   # Next video will fail with 'Video not found' error")

def enable_codec_failure():
    """Enable test mode for simulating codec errors."""
    print("🧪 To enable CODEC FAILURE test mode:")
    print("   display_manager.enable_video_failure_test_mode('codec')")
    print("   # Next video will fail with 'unsupported codec' error")

def disable_test_mode():
    """Disable test mode."""
    print("✅ To disable test mode:")
    print("   display_manager.disable_video_failure_test_mode()")
    print("   # Resume normal video playback")

if __name__ == "__main__":
    print_instructions()
    print("\n💡 TIP: Import this module in a Python console:")
    print("   >>> import enable_video_test_mode")
    print("   >>> enable_video_test_mode.print_instructions()")
