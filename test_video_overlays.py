#!/usr/bin/env python3
"""
Test script to verify video overlays and countdown timer functionality.
"""

import sys
import os
import time
import tkinter as tk
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from photo_manager import PhotoManager
from display_manager import DisplayManager
from slideshow_controller import SlideshowController
from config import SlideshowConfig

def test_video_overlays():
    """Test video overlays and countdown timer display."""
    print("Testing video overlays and countdown timer...")
    
    try:
        # Initialize components
        config = SlideshowConfig()
        photo_manager = PhotoManager(config)
        
        # Load photos to find videos
        print("Loading photos...")
        photos = photo_manager.load_photos()
        print(f"Loaded {len(photos)} photos")
        
        # Find first video
        video_photo = None
        video_index = -1
        
        for i, photo in enumerate(photos):
            if photo.get('media_type') == 'video':
                video_photo = photo
                video_index = i
                print(f"Found video at index {i}: {photo.get('filename', 'Unknown')}")
                print(f"Media type: {photo.get('media_type')}")
                print(f"Path: {photo.get('path')}")
                print(f"Date taken: {photo.get('date_taken')}")
                print(f"Location: {photo.get('location')}")
                break
        
        if not video_photo:
            print("No videos found in collection!")
            return
        
        # Initialize display manager (it creates its own root)
        display_manager = DisplayManager(config)
        display_manager.photo_manager = photo_manager
        
        # Test video with overlays
        print("\nTesting video display with overlays...")
        video_path = video_photo.get('path')
        
        # If video needs export, do it now
        if not video_path:
            print("Video needs export from Apple Photos...")
            video_path = photo_manager._export_video_temporarily(video_photo)
            if video_path:
                print(f"Video exported to: {video_path}")
                video_photo['path'] = video_path
            else:
                print("Failed to export video")
                return
        
        location_string = "Test Location • Sample Video"
        
        # Add some test metadata for overlays
        metadata = photo_manager.get_video_metadata(video_photo)
        if metadata:
            video_photo['duration'] = metadata.get('duration', 8.0)
        else:
            video_photo['duration'] = 8.0
        
        success = display_manager.display_video_with_overlays(video_path, video_photo, location_string)
        
        if success:
            print("✅ Video display started successfully")
            print("✅ Check for overlays: filename, date, location, duration")
            print("✅ Check for countdown timer in top-right corner")
        else:
            print("❌ Video display failed")
        
        # Instructions
        print("\nGUI started. Video should be playing with:")
        print("- Video overlays at bottom (date, location, duration)")
        print("- Countdown timer in top-right corner")
        print("- Audio playback")
        print("Press 'q' to quit, 'n' for next, 'b' for back")
        
        def on_key_press(event):
            key = event.keysym.lower()
            if key == 'q':
                display_manager.stop_video()
                display_manager.root.quit()
            elif key == 'n':
                print("Next pressed - video should advance")
            elif key == 'b':
                print("Back pressed - video should go back")
        
        display_manager.root.bind('<KeyPress>', on_key_press)
        display_manager.root.focus_set()
        
        # Start the GUI
        display_manager.root.mainloop()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_video_overlays()
