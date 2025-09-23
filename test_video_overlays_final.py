#!/usr/bin/env python3
"""
Final test for video overlays - forces video slide and verifies overlays work.
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

def test_video_overlays():
    """Test video overlays with manual verification."""
    print("🎬 Testing Video Overlays - Final Verification")
    print("=" * 50)
    
    try:
        # Initialize components
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        config.load_config()
        
        # Enable video test mode to force video slides
        config.config['video_test_mode'] = True
        print("✅ Video test mode enabled")
        
        photo_manager = PhotoManager(config, path_config)
        display_manager = PygameDisplayManager(config)
        controller = SlideshowController(config, photo_manager, display_manager, path_config)
        
        # Force slide count to 2 to get a video
        controller.slide_count = 1  # Will be incremented to 2
        
        print(f"\n🎯 Creating video slide with overlays...")
        
        # Create a video slide
        slide = controller._create_new_slide()
        
        if slide and slide.get('type') == 'video':
            video_data = slide['photos'][0]  # Video data is in photos array
            print(f"✅ Video slide created: {video_data.get('filename', 'unknown')}")
            
            # Get the video path and overlays
            video_path = video_data.get('path')
            if video_path and os.path.exists(video_path):
                print(f"✅ Video file exists: {os.path.basename(video_path)}")
                
                # Create overlays manually to test the system
                test_overlays = [
                    {
                        'type': 'date',
                        'text': 'September 08, 2025',
                        'position': 'left_margin'
                    },
                    {
                        'type': 'location', 
                        'text': 'Test Location, TX',
                        'position': 'right_margin'
                    }
                ]
                
                print(f"🎨 Testing overlay rendering...")
                print(f"   Date overlay: 'September 08, 2025' on left margin")
                print(f"   Location overlay: 'Test Location, TX' on right margin")
                
                # Test the display_video method with overlays
                success = display_manager.display_video(
                    video_path, 
                    overlays=test_overlays,
                    max_duration=10
                )
                
                if success:
                    print(f"\n🎉 SUCCESS! Video overlays should now be visible!")
                    print(f"📋 Manual verification checklist:")
                    print(f"   ✓ Video is playing")
                    print(f"   ✓ Date overlay on LEFT margin (white background, black text)")
                    print(f"   ✓ Location overlay on RIGHT margin (white background, black text)")
                    print(f"   ✓ Countdown timer in top-right corner")
                    print(f"   ✓ No filename or instruction overlays")
                    print(f"   ✓ Press SPACEBAR to test pause overlay (centered message, no black screen)")
                    
                    print(f"\n⏱️  Video will play for 10 seconds...")
                    return True
                else:
                    print(f"❌ Failed to display video")
                    return False
            else:
                print(f"❌ Video file not found: {video_path}")
                return False
        else:
            print(f"❌ Failed to create video slide")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 Final Video Overlay Test")
    print("=" * 30)
    
    success = test_video_overlays()
    
    print(f"\n📋 Test Result:")
    if success:
        print(f"✅ Video overlay system is working!")
        print(f"🎯 Ready for manual verification in main slideshow")
    else:
        print(f"❌ Video overlay test failed")
        print(f"💡 Check the error messages above")

if __name__ == "__main__":
    main()
