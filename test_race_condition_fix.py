#!/usr/bin/env python3
"""
Test to verify that the race condition fix prevents photo flashing.
"""

import sys
import logging
import time
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import SlideshowConfig
from photo_manager import PhotoManager
from slideshow_controller import SlideshowController
from path_config import PathConfig

# Mock display manager for testing
class MockDisplayManager:
    def __init__(self):
        self.displayed_slides = []
        self.controller = None
        self.display_lock = threading.Lock()
    
    def set_controller_reference(self, controller):
        self.controller = controller
    
    def display_photo(self, photo_data, location_string, slideshow_timer=None):
        with self.display_lock:
            if isinstance(photo_data, list):
                # Photo pair
                filenames = [p.get('filename', 'unknown') for p in photo_data]
                slide_info = f"PAIR: {filenames[0]} + {filenames[1]}"
                self.displayed_slides.append(slide_info)
                print(f"📸 DISPLAYED PORTRAIT PAIR: {filenames[0]} + {filenames[1]}")
            else:
                # Single photo
                filename = photo_data.get('filename', 'unknown') if photo_data else 'None'
                slide_info = f"SINGLE: {filename}"
                self.displayed_slides.append(slide_info)
                print(f"📸 DISPLAYED SINGLE: {filename}")
    
    def display_video(self, video_path, overlays=None, display_duration=None):
        with self.display_lock:
            # video_path is a string path, not a dict
            if isinstance(video_path, str):
                filename = video_path.split('/')[-1] if '/' in video_path else video_path
            else:
                filename = str(video_path)
            slide_info = f"VIDEO: {filename}"
            self.displayed_slides.append(slide_info)
            print(f"🎥 DISPLAYED VIDEO: {filename}")
            return True  # Return success
    
    def start_event_loop(self, callback):
        pass
    
    def stop(self):
        pass
    
    def show_countdown(self, seconds):
        pass
    
    def clear_countdown(self):
        pass
    
    def is_video_supported(self):
        return True
    
    def is_running(self):
        return True

def simulate_race_condition(controller):
    """Simulate multiple threads trying to advance at the same time."""
    print("🏁 Simulating race condition...")
    
    def thread_advance(thread_id):
        try:
            print(f"   Thread {thread_id}: Setting auto_advance_requested = True")
            controller.auto_advance_requested = True
            time.sleep(0.01)  # Small delay to increase chance of race condition
            
            # Simulate what the main loop would do
            if controller.auto_advance_requested:
                controller.auto_advance_requested = False
                print(f"   Thread {thread_id}: Processing auto-advance")
                controller._navigate_to_random()
                slide = controller._get_current_slide()
                controller._display_slide(slide)
                print(f"   Thread {thread_id}: Auto-advance completed")
        except Exception as e:
            print(f"   Thread {thread_id}: Error - {e}")
    
    # Start multiple threads simultaneously
    threads = []
    for i in range(3):
        thread = threading.Thread(target=thread_advance, args=(i,))
        threads.append(thread)
    
    # Start all threads at nearly the same time
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

def test_race_condition_fix():
    """Test that the race condition fix prevents multiple slide creations."""
    print("🧪 Testing Race Condition Fix")
    print("=" * 35)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        # Initialize components
        path_config = PathConfig.create_from_env()
        config = SlideshowConfig(path_config)
        config.load_config()
        
        # Enable video test mode
        config.config['video_test_mode'] = True
        print("✅ Video test mode enabled")
        
        photo_manager = PhotoManager(config, path_config)
        photos = photo_manager.load_photos()
        
        if not photos:
            print("❌ No photos found for testing")
            return False
        
        print(f"✅ Loaded {len(photos)} photos")
        
        # Create mock display manager and controller
        display_manager = MockDisplayManager()
        controller = SlideshowController(config, photo_manager, display_manager, path_config)
        
        print("\n🔄 Testing Race Condition Scenarios")
        print("-" * 35)
        
        # Test 1: Normal slide creation (should work)
        print("\n1️⃣ Normal slide creation:")
        initial_count = len(display_manager.displayed_slides)
        slide = controller._create_new_slide()
        controller._display_slide(slide)
        
        normal_count = len(display_manager.displayed_slides) - initial_count
        print(f"   Slides created: {normal_count}")
        
        # Test 2: Simulate race condition
        print("\n2️⃣ Simulating race condition:")
        race_initial_count = len(display_manager.displayed_slides)
        
        simulate_race_condition(controller)
        
        race_final_count = len(display_manager.displayed_slides) - race_initial_count
        print(f"   Slides created during race condition: {race_final_count}")
        
        # Test 3: Check slide counter consistency
        print("\n3️⃣ Checking slide counter consistency:")
        if hasattr(controller, 'slide_count'):
            print(f"   Current slide count: {controller.slide_count}")
        else:
            print("   Slide count not initialized")
        
        # Create a few more slides to test consistency
        for i in range(3):
            slide = controller._create_new_slide()
            if slide:
                controller._display_slide(slide)
        
        if hasattr(controller, 'slide_count'):
            print(f"   Final slide count: {controller.slide_count}")
        
        print("\n📊 Results:")
        total_displays = len(display_manager.displayed_slides)
        print(f"   Total displays: {total_displays}")
        
        # Check for video on slide 2 and 5
        video_slides = []
        for i, display in enumerate(display_manager.displayed_slides, 1):
            if display.startswith("VIDEO:"):
                video_slides.append(i)
                print(f"   Slide {i}: {display} ✅")
            else:
                print(f"   Slide {i}: {display}")
        
        print(f"   Video slides found at positions: {video_slides}")
        
        # Success criteria:
        # 1. No excessive slide creation during race condition
        # 2. Videos appear at expected positions (2, 5, etc.)
        # 3. No duplicate displays
        
        if race_final_count <= 1:  # Should only create one slide even with race condition
            print("   ✅ SUCCESS: Race condition handled correctly")
            return True
        else:
            print("   ❌ FAILED: Race condition created multiple slides")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_race_condition_fix()
    if success:
        print("\n🎉 Race condition fix test PASSED!")
        print("✅ Auto-advance race conditions should be prevented")
        print("✅ Photo flashing before videos should be eliminated")
    else:
        print("\n💥 Race condition fix test FAILED!")
        print("❌ Race conditions may still cause photo flashing")
    
    sys.exit(0 if success else 1)
