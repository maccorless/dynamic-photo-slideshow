#!/usr/bin/env python3
"""
Specific video test - find and test the first video in the collection
"""

import sys
import os
sys.path.append('/Users/ken/CascadeProjects/photo-slideshow')

from photo_manager import PhotoManager
from slideshow_controller import SlideshowController
from display_manager import DisplayManager
from config import SlideshowConfig
from path_config import PathConfig
import tkinter as tk
import time

def test_first_video():
    """Find and test the first video in the collection."""
    config = SlideshowConfig.from_file('/Users/ken/.photo_slideshow_config.json')
    path_config = PathConfig()
    
    try:
        # Initialize components
        display_manager = DisplayManager(config)
        photo_manager = PhotoManager(config, path_config)
        controller = SlideshowController(config, photo_manager, display_manager, path_config)
        
        # Get the root window from display manager
        root = display_manager.root
        
        print("Loading photos and searching for first video...")
        photos = photo_manager.load_photos()
        
        # Find first video
        video_index = None
        video_photo = None
        for i, photo in enumerate(photos):
            if controller._is_video_content(photo):
                video_index = i
                video_photo = photo
                break
        
        if video_index is None:
            print("No videos found in collection!")
            return
            
        print(f"Found video at index {video_index}: {video_photo.get('filename')}")
        print(f"Media type: {video_photo.get('media_type')}")
        print(f"Path: {video_photo.get('path')}")
        print(f"Needs export: {video_photo.get('needs_export', False)}")
        
        # Set the current index and display
        controller.current_index = video_index
        controller.photos = photos
        
        # Display the video
        print("Attempting to display video...")
        controller._display_single_photo(video_photo, video_index, len(photos))
        
        # Add navigation instructions
        instructions = tk.Label(root, 
                              text=f"Testing Video {video_index+1}/{len(photos)}\n"
                                   f"Filename: {video_photo.get('filename')}\n"
                                   f"Media Type: {video_photo.get('media_type')}\n"
                                   f"Press 'n' for next, 'b' for back, 'q' to quit",
                              font=('Arial', 12),
                              bg='black', fg='white')
        instructions.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind keys for navigation
        def on_key(event):
            if event.char.lower() == 'n':
                controller.next_photo()
            elif event.char.lower() == 'b':
                controller.previous_photo()
            elif event.char.lower() == 'q':
                root.quit()
        
        root.bind('<Key>', on_key)
        root.focus_set()
        
        print(f"GUI started. Video should be playing. Press 'n' for next, 'b' for back, 'q' to quit")
        root.mainloop()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    test_first_video()
