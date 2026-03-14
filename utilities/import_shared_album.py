#!/usr/bin/env python3
"""
Import photos from a shared album into the main Photos library.

This script uses AppleScript to interact with Photos.app and import photos
from shared albums (that others have shared with you) into your main library,
making them accessible to osxphotos and the slideshow application.

Usage:
    python import_shared_album.py --album "Album Name" [--dry-run]
    
Examples:
    # List all shared albums
    python import_shared_album.py --list
    
    # Import from a specific shared album (dry run first)
    python import_shared_album.py --album "Emma & Gene's Wedding" --dry-run
    
    # Actually import the photos
    python import_shared_album.py --album "Emma & Gene's Wedding"
"""

import subprocess
import sys
import argparse
import json
from typing import List, Dict, Optional


class SharedAlbumImporter:
    """Import photos from shared albums using AppleScript."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        
    def run_applescript(self, script: str) -> str:
        """Execute AppleScript and return the result."""
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"AppleScript error: {e.stderr}")
            raise
    
    def list_shared_albums(self) -> List[Dict[str, any]]:
        """List all shared albums visible in Photos.app."""
        script = '''
        tell application "Photos"
            set sharedAlbumsList to {}
            repeat with anAlbum in albums
                try
                    -- Check if this is a shared album
                    set albumClass to class of anAlbum as string
                    set albumName to name of anAlbum
                    set photoCount to count of media items of anAlbum
                    
                    -- Add to list (we'll filter for shared albums)
                    set end of sharedAlbumsList to {albumName:albumName, photoCount:photoCount}
                end try
            end repeat
            return sharedAlbumsList
        end tell
        '''
        
        try:
            result = self.run_applescript(script)
            print(f"\nFound albums in Photos.app:")
            print(f"(Note: AppleScript cannot distinguish shared vs regular albums)")
            print(f"Please verify in Photos.app which albums are shared)\n")
            
            # Parse the result - it will be in AppleScript record format
            # For now, we'll just return the raw result
            return result
        except Exception as e:
            print(f"Error listing albums: {e}")
            return []
    
    def get_album_photo_count(self, album_name: str) -> int:
        """Get the number of photos in a specific album."""
        script = f'''
        tell application "Photos"
            try
                set targetAlbum to album "{album_name}"
                return count of media items of targetAlbum
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
        '''
        
        try:
            result = self.run_applescript(script)
            if result.startswith("ERROR:"):
                print(f"Error: {result}")
                return 0
            return int(result)
        except Exception as e:
            print(f"Error getting photo count: {e}")
            return 0
    
    def import_shared_album(self, album_name: str) -> bool:
        """
        Import all photos from a shared album into the main library.
        
        Args:
            album_name: Name of the shared album to import
            
        Returns:
            True if successful, False otherwise
        """
        # First, check if the album exists
        photo_count = self.get_album_photo_count(album_name)
        
        if photo_count == 0:
            print(f"Album '{album_name}' not found or has no photos.")
            return False
        
        print(f"\nFound album '{album_name}' with {photo_count} photos")
        
        if self.dry_run:
            print(f"\n[DRY RUN] Would import {photo_count} photos from '{album_name}'")
            print("Run without --dry-run to actually import the photos")
            return True
        
        # Confirm with user
        print(f"\nThis will import {photo_count} photos into your main library.")
        print("The photos will be duplicated if they already exist in your library.")
        response = input("Continue? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("Import cancelled.")
            return False
        
        # Import the photos
        print(f"\nImporting photos from '{album_name}'...")
        print("This may take a while depending on the number of photos...")
        
        script = f'''
        tell application "Photos"
            try
                set targetAlbum to album "{album_name}"
                set albumPhotos to media items of targetAlbum
                set photoCount to count of albumPhotos
                
                -- Import each photo
                set importedCount to 0
                repeat with aPhoto in albumPhotos
                    try
                        -- Import the photo (this creates a copy in the main library)
                        import aPhoto
                        set importedCount to importedCount + 1
                    end try
                end repeat
                
                return "Imported " & importedCount & " of " & photoCount & " photos"
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
        '''
        
        try:
            result = self.run_applescript(script)
            print(f"\nResult: {result}")
            
            if result.startswith("ERROR:"):
                print("\nImport failed. The album might not support direct import.")
                print("\nAlternative method:")
                print("1. Open Photos.app")
                print(f"2. Navigate to the shared album '{album_name}'")
                print("3. Select all photos (Cmd+A)")
                print("4. Right-click and choose 'Import'")
                print("5. The photos will be added to your main library")
                return False
            
            print(f"\n✓ Successfully imported photos from '{album_name}'")
            print("\nNote: It may take a few moments for Photos to process the imported photos.")
            print("You may need to restart your slideshow for the new photos to appear.")
            return True
            
        except Exception as e:
            print(f"Error during import: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Import photos from shared albums into main Photos library',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all albums in Photos.app'
    )
    
    parser.add_argument(
        '--album',
        type=str,
        help='Name of the shared album to import'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without actually importing'
    )
    
    args = parser.parse_args()
    
    importer = SharedAlbumImporter(dry_run=args.dry_run)
    
    if args.list:
        print("Listing albums in Photos.app...")
        result = importer.list_shared_albums()
        print(f"\n{result}")
        print("\nTo import a specific album, use:")
        print('  python import_shared_album.py --album "Album Name"')
        return
    
    if args.album:
        success = importer.import_shared_album(args.album)
        sys.exit(0 if success else 1)
    
    # No arguments provided
    parser.print_help()
    print("\nTip: Use --list to see all available albums")


if __name__ == '__main__':
    main()
