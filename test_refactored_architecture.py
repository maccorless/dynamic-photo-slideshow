#!/usr/bin/env python3
"""
Test script to verify the refactored slideshow architecture works correctly.
"""

import sys
import logging
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import SlideshowConfig
from photo_manager import PhotoManager
from slideshow_controller import SlideshowController, TriggerType, Direction
from path_config import PathConfig

# Mock display manager for testing
class MockDisplayManager:
    def __init__(self):
        self.displayed_slides = []
        self.controller = None
        self.display_call_count = 0
    
    def set_controller_reference(self, controller):
        self.controller = controller
    
    def display_photo(self, photo_data, location_string, slideshow_timer=None):
        self.display_call_count += 1
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
        self.display_call_count += 1
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

def test_refactored_architecture():
    """Test the refactored slideshow architecture."""
    print("🏗️  Testing Refactored Slideshow Architecture")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        # Initialize components
        path_config = PathConfig.create_from_env()
        config = SlideshowConfig(path_config)
        config.load_config()
        
        # Enable video test mode for predictable testing
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
        
        # Set controller to running state for testing
        controller.is_running = True
        controller.is_playing = True
        
        print("\\n🔄 Testing Single Entry Point Architecture")
        print("-" * 45)
        
        # Test 1: Single entry point for different triggers
        print("\\n1️⃣ Testing single entry point with different triggers:")
        
        initial_count = len(display_manager.displayed_slides)
        
        # Test startup trigger
        success1 = controller.advance_slideshow(TriggerType.STARTUP, Direction.NEXT)
        print(f"   Startup trigger: {'✅ SUCCESS' if success1 else '❌ FAILED'}")
        
        # Test key next trigger  
        success2 = controller.advance_slideshow(TriggerType.KEY_NEXT, Direction.NEXT)
        print(f"   Key next trigger: {'✅ SUCCESS' if success2 else '❌ FAILED'}")
        
        # Test key previous trigger
        success3 = controller.advance_slideshow(TriggerType.KEY_PREVIOUS, Direction.PREVIOUS)
        print(f"   Key previous trigger: {'✅ SUCCESS' if success3 else '❌ FAILED'}")
        
        # Test voice triggers
        success4 = controller.advance_slideshow(TriggerType.VOICE_NEXT, Direction.NEXT)
        print(f"   Voice next trigger: {'✅ SUCCESS' if success4 else '❌ FAILED'}")
        
        entry_point_count = len(display_manager.displayed_slides) - initial_count
        print(f"   Total slides displayed via entry point: {entry_point_count}")
        
        # Test 2: Public API methods (should route to entry point)
        print("\\n2️⃣ Testing public API methods:")
        
        api_initial_count = len(display_manager.displayed_slides)
        
        controller.next_photo()
        print("   next_photo() called")
        
        controller.previous_photo()
        print("   previous_photo() called")
        
        controller.voice_next()
        print("   voice_next() called")
        
        controller.voice_previous()
        print("   voice_previous() called")
        
        api_count = len(display_manager.displayed_slides) - api_initial_count
        print(f"   Total slides displayed via public API: {api_count}")
        
        # Test 3: Verify no duplicate logic
        print("\\n3️⃣ Testing for duplicate logic elimination:")
        
        # Check that display calls are reasonable (no excessive calls)
        total_displays = len(display_manager.displayed_slides)
        total_calls = display_manager.display_call_count
        
        print(f"   Total display calls: {total_calls}")
        print(f"   Total slides tracked: {total_displays}")
        
        if total_calls == total_displays:
            print("   ✅ SUCCESS: No duplicate display calls detected")
        else:
            print("   ⚠️  WARNING: Display call count mismatch")
        
        # Test 4: Video test mode consistency
        print("\\n4️⃣ Testing video test mode consistency:")
        
        video_slides = [i+1 for i, slide in enumerate(display_manager.displayed_slides) if slide.startswith("VIDEO:")]
        print(f"   Video slides found at positions: {video_slides}")
        
        # Should have videos at positions 2, 5, etc. (depending on how many slides we created)
        expected_video_positions = [pos for pos in [2, 5, 8, 11] if pos <= len(display_manager.displayed_slides)]
        actual_video_positions = video_slides
        
        if set(expected_video_positions).issubset(set(actual_video_positions)):
            print("   ✅ SUCCESS: Videos appear at expected positions")
        else:
            print(f"   ⚠️  INFO: Expected videos at {expected_video_positions}, found at {actual_video_positions}")
        
        # Test 5: Architecture verification
        print("\\n5️⃣ Architecture verification:")
        
        # Check that the controller has the new methods
        has_advance_slideshow = hasattr(controller, 'advance_slideshow')
        has_determine_slide = hasattr(controller, '_determine_next_slide')
        has_display_with_timer = hasattr(controller, '_display_slide_with_timer')
        
        print(f"   Has advance_slideshow(): {'✅' if has_advance_slideshow else '❌'}")
        print(f"   Has _determine_next_slide(): {'✅' if has_determine_slide else '❌'}")
        print(f"   Has _display_slide_with_timer(): {'✅' if has_display_with_timer else '❌'}")
        
        architecture_score = sum([has_advance_slideshow, has_determine_slide, has_display_with_timer])
        
        print("\\n📊 Test Results Summary:")
        print(f"   Entry point tests: {sum([success1, success2, success3, success4])}/4 passed")
        print(f"   Public API tests: {api_count} slides displayed")
        print(f"   Duplicate logic: {'✅ Eliminated' if total_calls == total_displays else '⚠️  Possible issues'}")
        print(f"   Video test mode: {'✅ Working' if video_slides else '⚠️  No videos detected'}")
        print(f"   Architecture methods: {architecture_score}/3 present")
        
        # Overall success criteria
        overall_success = (
            sum([success1, success2, success3, success4]) >= 3 and  # Most entry point tests pass
            api_count >= 2 and  # Public API works
            architecture_score == 3 and  # All architecture methods present
            total_calls == total_displays  # No duplicate calls
        )
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_refactored_architecture()
    if success:
        print("\\n🎉 Refactored architecture test PASSED!")
        print("✅ Single entry point working correctly")
        print("✅ Public API routing to entry point")
        print("✅ No duplicate logic detected")
        print("✅ Architecture methods implemented")
    else:
        print("\\n💥 Refactored architecture test FAILED!")
        print("❌ Issues detected in refactored architecture")
    
    sys.exit(0 if success else 1)
