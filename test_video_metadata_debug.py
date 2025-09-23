#!/usr/bin/env python3
"""
Debug test for video metadata overlays - forces video slide and analyzes logs.
"""

import sys
import os
import time
import pygame

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SlideshowConfig
from path_config import PathConfig
from slideshow_controller import SlideshowController
from photo_manager import PhotoManager
from pygame_display_manager import PygameDisplayManager

def force_video_slide_test():
    """Force a video slide to test metadata overlays with debug logging."""
    print("🎬 DEBUGGING VIDEO METADATA OVERLAYS")
    print("=" * 50)
    
    try:
        # Initialize components
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        config.load_config()
        
        photo_manager = PhotoManager(config, path_config)
        display_manager = PygameDisplayManager(config)
        controller = SlideshowController(config, photo_manager, display_manager, path_config)
        
        print(f"✅ Components initialized")
        
        # Force slide count to get video (slide 2 or 5)
        controller.slide_count = 1  # Will be incremented to 2 for video
        
        print(f"🎯 Forcing video slide creation...")
        
        # Create a slide - should be video on slide 2
        slide = controller._create_new_slide()
        
        if slide and slide.get('type') == 'video':
            print(f"✅ Video slide created successfully!")
            print(f"   Type: {slide.get('type')}")
            print(f"   Video: {slide['photos'][0].get('filename', 'unknown')}")
            
            # Display the video slide
            print(f"\n🎬 Displaying video slide with debug logging...")
            print(f"📋 Watch for these log messages:")
            print(f"   [VIDEO-OVERLAY-CREATE] - Controller creating overlays")
            print(f"   [VIDEO-OVERLAY-STORE] - Display manager storing overlays")  
            print(f"   [VIDEO-OVERLAY-RENDER] - Display manager rendering overlays")
            print(f"\n" + "="*60)
            
            success = controller._display_video_content(slide)
            
            if success:
                print(f"\n" + "="*60)
                print(f"✅ Video display completed!")
                print(f"📋 Check the logs above for overlay debug messages")
                return True
            else:
                print(f"❌ Video display failed")
                return False
        else:
            print(f"❌ Failed to create video slide - got {slide.get('type') if slide else 'None'}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 Video Metadata Overlay Debug Test")
    print("=" * 40)
    
    success = force_video_slide_test()
    
    print(f"\n📋 Test Result:")
    if success:
        print(f"✅ Video slide displayed - check logs for overlay debug messages")
        print(f"🔍 Look for [VIDEO-OVERLAY-CREATE], [VIDEO-OVERLAY-STORE], [VIDEO-OVERLAY-RENDER]")
    else:
        print(f"❌ Video slide test failed")

if __name__ == "__main__":
    main()
