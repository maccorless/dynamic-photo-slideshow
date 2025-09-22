#!/usr/bin/env python3
"""
Debug test to trace the video flash issue.
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
        self.displayed_slides = []
        self.controller = None
    
    def set_controller_reference(self, controller):
        self.controller = controller
    
    def display_photo(self, photo_data, location_string, slideshow_timer=None):
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

def test_video_flash_debug():
    """Debug the video flash issue with detailed logging."""
    print("🐛 Debugging Video Flash Issue")
    print("=" * 40)
    
    # Setup detailed logging
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    
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
        
        print("\n🔍 Testing Slide Creation Sequence")
        print("-" * 35)
        
        # Simulate the exact sequence that causes the flash
        print("\n1️⃣ Creating slide 1 (should be photo):")
        slide1 = controller._create_new_slide()
        if slide1:
            print(f"   Created: {slide1['type']} slide")
            controller._display_slide(slide1)
        
        print("\n2️⃣ Creating slide 2 (should be video in test mode):")
        slide2 = controller._create_new_slide()
        if slide2:
            print(f"   Created: {slide2['type']} slide")
            controller._display_slide(slide2)
        
        print("\n3️⃣ Creating slide 3 (should be photo):")
        slide3 = controller._create_new_slide()
        if slide3:
            print(f"   Created: {slide3['type']} slide")
            controller._display_slide(slide3)
        
        print("\n📊 Results:")
        print(f"   Total displays: {len(display_manager.displayed_slides)}")
        for i, display in enumerate(display_manager.displayed_slides, 1):
            print(f"   Slide {i}: {display}")
        
        # Check if slide 2 is a video
        if len(display_manager.displayed_slides) >= 2:
            slide2_display = display_manager.displayed_slides[1]
            if slide2_display.startswith("VIDEO:"):
                print("   ✅ SUCCESS: Slide 2 is a video (no photo flash)")
                return True
            else:
                print("   ❌ FAILED: Slide 2 is not a video (photo flash detected)")
                return False
        else:
            print("   ❌ FAILED: Not enough slides created")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_video_flash_debug()
    if success:
        print("\n🎉 Video flash debug test PASSED!")
    else:
        print("\n💥 Video flash debug test FAILED!")
    
    sys.exit(0 if success else 1)
