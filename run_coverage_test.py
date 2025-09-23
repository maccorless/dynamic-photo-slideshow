#!/usr/bin/env python3
"""
Run slideshow with coverage analysis to identify unused code.
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))

def simulate_slideshow_usage():
    """Simulate typical slideshow usage to capture code coverage."""
    
    print("🎬 Simulating slideshow usage for coverage analysis...")
    
    try:
        from config import SlideshowConfig
        from photo_manager import PhotoManager
        from pygame_display_manager import PygameDisplayManager
        from slideshow_controller import SlideshowController, TriggerType, Direction
        from path_config import PathConfig
        
        # Initialize components
        path_config = PathConfig.create_from_env()
        config = SlideshowConfig(path_config)
        config.load_config()
        
        photo_manager = PhotoManager(config, path_config)
        photos = photo_manager.load_photos()
        
        if not photos:
            print("No photos found for coverage test")
            return
        
        # Create display manager (but don't actually display)
        display_manager = PygameDisplayManager(config)
        
        # Create controller
        controller = SlideshowController(config, photo_manager, display_manager)
        
        # Simulate various operations
        print("📸 Simulating photo operations...")
        
        # Test slide creation
        try:
            slide = controller._create_slide()
            if slide:
                print(f"✅ Created slide: {slide.get('type', 'unknown')}")
        except Exception as e:
            print(f"⚠️ Slide creation error: {e}")
        
        # Test key handling
        print("⌨️ Simulating key events...")
        class MockEvent:
            def __init__(self, keysym):
                self.keysym = keysym
        
        for key in ['space', 'left', 'right']:
            try:
                controller._handle_key_event(MockEvent(key))
                print(f"✅ Handled key: {key}")
            except Exception as e:
                print(f"⚠️ Key handling error for {key}: {e}")
        
        # Test navigation methods
        print("🧭 Simulating navigation...")
        try:
            controller.next_photo()
            controller.previous_photo()
            controller.toggle_pause()
            print("✅ Navigation methods executed")
        except Exception as e:
            print(f"⚠️ Navigation error: {e}")
        
        # Test video functionality
        print("🎥 Simulating video operations...")
        try:
            # Get videos from photo collection
            videos = [p for p in photos if p.get('media_type') == 'video']
            if videos:
                video = videos[0]
                # Test video overlay creation
                overlays = controller._create_video_overlays(video, 0, len(photos), "Test Location")
                print(f"✅ Created {len(overlays)} video overlays")
        except Exception as e:
            print(f"⚠️ Video operation error: {e}")
        
        # Cleanup
        display_manager.cleanup()
        print("✅ Coverage simulation completed")
        
    except Exception as e:
        print(f"❌ Coverage simulation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simulate_slideshow_usage()
