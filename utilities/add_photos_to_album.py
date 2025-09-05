#!/usr/bin/env python3
"""
Helper script to add photos to the photoframe album.
"""

import subprocess
import sys

def add_photos_to_album():
    """Add photos to photoframe album using AppleScript."""
    applescript = '''
    tell application "Photos"
        try
            set photoframeAlbum to album "photoframe"
            
            -- Get some recent photos (last 10)
            set recentPhotos to media items 1 thru 10
            
            repeat with aPhoto in recentPhotos
                try
                    add aPhoto to photoframeAlbum
                end try
            end repeat
            
            return "Added recent photos to photoframe album"
        on error errMsg
            return "Error: " & errMsg
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True)
        print(result.stdout.strip())
        if result.stderr:
            print(f"Error: {result.stderr.strip()}")
    except Exception as e:
        print(f"Error running AppleScript: {e}")

if __name__ == "__main__":
    print("Adding recent photos to 'photoframe' album...")
    add_photos_to_album()
    print("\nPhotos added! You can now restart the slideshow to use the photoframe album.")
