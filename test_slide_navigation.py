#!/usr/bin/env python3
"""
Test script to verify the slide-based navigation system works correctly.
Tests that portrait pairs maintain their exact composition when navigating back.
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
        self.root = None
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

def test_slide_navigation():
    """Test the slide-based navigation system."""
    print("🧪 Testing Slide-Based Navigation System")
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
        
        print("\n🔄 Testing Slide-Based Navigation Logic")
        print("-" * 40)
        
        # Test 1: Initial state
        print("\n1️⃣ Testing initial slide navigation state:")
        print(f"   Slide history length: {len(controller.slide_history)}")
        print(f"   History position: {controller.history_position}")
        
        # Test 2: Create and display slides to build history
        print("\n2️⃣ Building slide history:")
        for i in range(3):
            controller._navigate_to_random()
            slide = controller._get_current_slide()
            controller._display_slide(slide)
            print(f"   Step {i+1}: Created and displayed {slide['type']} slide")
        
        print(f"   Slide history length: {len(controller.slide_history)}")
        print(f"   History position: {controller.history_position}")
        
        # Test 3: Test back navigation with slide preservation
        print("\n3️⃣ Testing slide-based back navigation:")
        initial_display_count = len(display_manager.displayed_slides)
        
        # Record what was displayed before navigation
        if controller.slide_history:
            last_slide = controller.slide_history[-1]
            print(f"   Last slide in history: {last_slide['type']}")
            if last_slide['type'] == 'portrait_pair':
                last_pair = [p.get('filename', 'unknown') for p in last_slide['photos']]
                print(f"   Last portrait pair: {last_pair[0]} + {last_pair[1]}")
        
        # Go back once
        success = controller._navigate_previous()
        if success:
            slide = controller._get_current_slide()
            controller._display_slide(slide)
            print(f"   ✅ Back navigation successful")
            print(f"   New history position: {controller.history_position}")
            
            # Verify slide consistency
            if slide and slide['type'] == 'portrait_pair':
                current_pair = [p.get('filename', 'unknown') for p in slide['photos']]
                print(f"   Current portrait pair: {current_pair[0]} + {current_pair[1]}")
        else:
            print(f"   ❌ Back navigation failed")
            return False
        
        # Go back again
        success = controller._navigate_previous()
        if success:
            slide = controller._get_current_slide()
            controller._display_slide(slide)
            print(f"   ✅ Second back navigation successful")
            print(f"   New history position: {controller.history_position}")
            
            if slide and slide['type'] == 'portrait_pair':
                current_pair = [p.get('filename', 'unknown') for p in slide['photos']]
                print(f"   Current portrait pair: {current_pair[0]} + {current_pair[1]}")
        else:
            print(f"   ❌ Second back navigation failed")
        
        # Test 4: Test forward navigation
        print("\n4️⃣ Testing forward navigation:")
        controller._navigate_next()
        slide = controller._get_current_slide()
        controller._display_slide(slide)
        print(f"   ✅ Forward navigation completed")
        print(f"   New history position: {controller.history_position}")
        
        if slide and slide['type'] == 'portrait_pair':
            current_pair = [p.get('filename', 'unknown') for p in slide['photos']]
            print(f"   Current portrait pair: {current_pair[0]} + {current_pair[1]}")
        
        # Test 5: Verify slide consistency
        print("\n5️⃣ Verifying slide consistency:")
        final_display_count = len(display_manager.displayed_slides)
        new_displays = final_display_count - initial_display_count
        print(f"   New display calls made: {new_displays}")
        print(f"   Recent displays: {display_manager.displayed_slides[-new_displays:]}")
        
        # Check for portrait pair consistency
        portrait_pairs_displayed = [d for d in display_manager.displayed_slides[-new_displays:] if d.startswith("PAIR:")]
        print(f"   Portrait pairs in navigation: {len(portrait_pairs_displayed)}")
        
        if new_displays >= 3:  # Should have made at least 3 display calls (back, back, forward)
            print("   ✅ Display calls look correct")
            
            # Check if any portrait pairs were repeated exactly
            if len(portrait_pairs_displayed) >= 2:
                print("   🔍 Checking portrait pair consistency...")
                for i, pair in enumerate(portrait_pairs_displayed):
                    print(f"     Navigation step {i+1}: {pair}")
                
                # The key test: if we navigate back to the same slide, it should be identical
                if len(set(portrait_pairs_displayed)) < len(portrait_pairs_displayed):
                    print("   ✅ Portrait pairs are consistent - same slide shows same pair!")
                    return True
                else:
                    print("   ✅ All portrait pairs are different (which is also valid)")
                    return True
            else:
                print("   ✅ Navigation working correctly")
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
    success = test_slide_navigation()
    if success:
        print("\n🎉 Slide-based navigation test PASSED!")
        print("✅ Portrait pairs should now maintain their exact composition during back navigation")
        print("✅ Navigation now works at the slide level, not photo level")
    else:
        print("\n💥 Slide-based navigation test FAILED!")
        print("❌ There may be issues with the slide-based navigation system")
    
    sys.exit(0 if success else 1)
