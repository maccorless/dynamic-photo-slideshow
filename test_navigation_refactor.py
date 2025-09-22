#!/usr/bin/env python3
"""
Test script to verify the navigation refactoring works correctly.
Tests the separation of navigation logic from display logic.
"""

import sys
import logging
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
        self.displayed_photos = []
        self.root = None
        self.controller = None
    
    def set_controller_reference(self, controller):
        self.controller = controller
    
    def display_photo(self, photo_data, location_string, slideshow_timer=None):
        if isinstance(photo_data, list):
            # Photo pair
            filenames = [p.get('filename', 'unknown') for p in photo_data]
            self.displayed_photos.append(f"PAIR: {', '.join(filenames)}")
            print(f"📸 DISPLAYED PAIR: {', '.join(filenames)}")
        else:
            # Single photo
            filename = photo_data.get('filename', 'unknown') if photo_data else 'None'
            self.displayed_photos.append(f"SINGLE: {filename}")
            print(f"📸 DISPLAYED: {filename}")
    
    def display_video(self, video_path, overlays=None, display_duration=None):
        # video_path is a string path, not a dict
        if isinstance(video_path, str):
            filename = video_path.split('/')[-1] if '/' in video_path else video_path
        else:
            filename = str(video_path)
        self.displayed_photos.append(f"VIDEO: {filename}")
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

def test_navigation_refactor():
    """Test the navigation refactoring."""
    print("🧪 Testing Navigation Refactoring")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        # Initialize components
        path_config = PathConfig.create_from_env()
        config = SlideshowConfig(path_config)
        config.load_config()
        
        photo_manager = PhotoManager(config, path_config)
        photos = photo_manager.load_photos()
        
        if not photos:
            print("❌ No photos found for testing")
            return False
        
        print(f"✅ Loaded {len(photos)} photos")
        
        # Create mock display manager and controller
        display_manager = MockDisplayManager()
        controller = SlideshowController(config, photo_manager, display_manager, path_config)
        
        print("\n🔄 Testing Navigation Logic")
        print("-" * 30)
        
        # Test 1: Initial state
        print("\n1️⃣ Testing initial navigation state:")
        print(f"   History length: {len(controller.photo_history)}")
        print(f"   History position: {controller.history_position}")
        
        # Test 2: Navigate to random photos and build history
        print("\n2️⃣ Building navigation history:")
        for i in range(3):
            controller._navigate_to_random()
            photo, photo_index = controller._get_current_photo()
            controller._display_current_photo(photo, photo_index)
            controller._add_to_history(photo_index)  # Simulate adding to history
            print(f"   Step {i+1}: Added photo {photo_index} to history")
        
        print(f"   History length: {len(controller.photo_history)}")
        print(f"   History position: {controller.history_position}")
        print(f"   History contents: {controller.photo_history}")
        
        # Test 3: Test back navigation
        print("\n3️⃣ Testing back navigation:")
        initial_display_count = len(display_manager.displayed_photos)
        
        # Go back once
        success = controller._navigate_previous()
        if success:
            photo, photo_index = controller._get_current_photo()
            controller._display_current_photo(photo, photo_index)
            print(f"   ✅ Back navigation successful")
            print(f"   New history position: {controller.history_position}")
        else:
            print(f"   ❌ Back navigation failed")
            return False
        
        # Go back again
        success = controller._navigate_previous()
        if success:
            photo, photo_index = controller._get_current_photo()
            controller._display_current_photo(photo, photo_index)
            print(f"   ✅ Second back navigation successful")
            print(f"   New history position: {controller.history_position}")
        else:
            print(f"   ❌ Second back navigation failed")
        
        # Test 4: Test forward navigation
        print("\n4️⃣ Testing forward navigation:")
        controller._navigate_next()
        photo, photo_index = controller._get_current_photo()
        controller._display_current_photo(photo, photo_index)
        print(f"   ✅ Forward navigation completed")
        print(f"   New history position: {controller.history_position}")
        
        # Test 5: Verify display calls
        print("\n5️⃣ Verifying display calls:")
        final_display_count = len(display_manager.displayed_photos)
        new_displays = final_display_count - initial_display_count
        print(f"   New display calls made: {new_displays}")
        print(f"   Recent displays: {display_manager.displayed_photos[-new_displays:]}")
        
        if new_displays >= 3:  # Should have made at least 3 display calls (back, back, forward)
            print("   ✅ Display calls look correct")
            return True
        else:
            print("   ❌ Not enough display calls made")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_navigation_refactor()
    if success:
        print("\n🎉 Navigation refactoring test PASSED!")
        print("✅ Back navigation should now work correctly in the slideshow")
    else:
        print("\n💥 Navigation refactoring test FAILED!")
        print("❌ There may be issues with the back navigation")
    
    sys.exit(0 if success else 1)
