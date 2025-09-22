#!/usr/bin/env python3
"""
Direct video test - navigate to a known video position to test playback
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

def test_video_at_index(target_index):
    """Test video playback at a specific index."""
    config = SlideshowConfig.from_file('/Users/ken/.photo_slideshow_config.json')
    path_config = PathConfig()
    
    try:
        # Initialize components
        display_manager = DisplayManager(config)
        photo_manager = PhotoManager(config, path_config)
        controller = SlideshowController(config, photo_manager, display_manager, path_config)
        
        # Get the root window from display manager
        root = display_manager.root
        
        print(f"Loading photos and navigating to index {target_index}...")
        photos = photo_manager.load_photos()
        
        if target_index >= len(photos):
            print(f"Error: Index {target_index} out of range (max: {len(photos)-1})")
            return
            
        target_photo = photos[target_index]
        print(f"Target photo: {target_photo.get('filename')}")
        print(f"Media type: {target_photo.get('media_type')}")
        print(f"Is video: {controller._is_video_content(target_photo)}")
        
        # Set the current index and display
        controller.current_index = target_index
        controller.photos = photos
        
        # Display the target photo/video
        controller._display_single_photo(target_photo, target_index, len(photos))
        
        # Add navigation instructions
        instructions = tk.Label(root, 
                              text=f"Showing item {target_index+1}/{len(photos)}\n"
                                   f"Filename: {target_photo.get('filename')}\n"
                                   f"Media Type: {target_photo.get('media_type')}\n"
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
        
        print(f"GUI started. Press 'n' for next, 'b' for back, 'q' to quit")
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
    # Test video at index 2 (found video in collection)
    test_video_at_index(2)
