#!/usr/bin/env python3
"""
Helper script to create a Smart Album named 'photoframe' in Photos.
"""

import subprocess
import sys

def create_smart_album():
    """Create a Smart Album using AppleScript."""
    applescript = '''
    tell application "Photos"
        try
            -- Create a Smart Album with criteria for recent photos
            make new smart album named "photoframe" with properties {criteria:{{{class:condition, property:date, operator:is in the range, value:{date "2020-01-01", date "2030-12-31"}}}}
            return "Smart Album 'photoframe' created successfully"
        on error errMsg
            return "Error creating Smart Album: " & errMsg
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

def create_simple_smart_album():
    """Create a simpler Smart Album using GUI automation."""
    print("Creating Smart Album via GUI automation...")
    applescript = '''
    tell application "Photos"
        activate
    end tell
    
    tell application "System Events"
        tell process "Photos"
            -- Wait for Photos to be ready
            delay 2
            
            -- Try to create new Smart Album via menu
            try
                click menu item "New Smart Album" of menu "File" of menu bar 1
                delay 1
                
                -- Type the album name
                keystroke "photoframe"
                delay 0.5
                
                -- Press Enter to confirm
                key code 36
                
                return "Smart Album creation initiated via GUI"
            on error
                return "Could not create Smart Album via GUI - please create manually"
            end try
        end tell
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True)
        print(result.stdout.strip())
    except Exception as e:
        print(f"Error with GUI automation: {e}")

if __name__ == "__main__":
    print("Creating Smart Album 'photoframe' in Photos...")
    create_smart_album()
    print("\nIf that didn't work, trying GUI method...")
    create_simple_smart_album()
    print("\nSmart Album should now be available for the slideshow!")
    print("You can customize the Smart Album criteria in Photos app if needed.")
