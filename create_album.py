#!/usr/bin/env python3
"""
Helper script to create the photoframe album in Photos.
"""

import subprocess
import sys

def create_photoframe_album():
    """Create photoframe album using AppleScript."""
    applescript = '''
    tell application "Photos"
        try
            make new album named "photoframe"
            return "Album 'photoframe' created successfully"
        on error
            return "Album 'photoframe' may already exist or there was an error"
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
    print("Creating 'photoframe' album in Photos...")
    create_photoframe_album()
    print("\nNow add some photos to the album in Photos app, then restart the slideshow.")
