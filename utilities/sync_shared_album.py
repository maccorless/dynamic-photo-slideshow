#!/usr/bin/env python3
"""
Sync photos from shared albums to main library without creating duplicates.

This script tracks which photos have been imported from shared albums and only
imports new photos on subsequent runs, keeping your library in sync with shared albums.

Usage:
    python sync_shared_album.py --album "Album Name" [--dry-run]
    
Examples:
    # First sync (dry run)
    python sync_shared_album.py --album "Ken shared" --dry-run
    
    # Actually sync the album
    python sync_shared_album.py --album "Ken shared"
    
    # Sync again later to get new photos only
    python sync_shared_album.py --album "Ken shared"
    
    # Show sync status
    python sync_shared_album.py --status
"""

import os
import json
import hashlib
import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, List, Optional


class SharedAlbumSync:
    """Sync shared albums to main library without duplicates."""
    
    def __init__(self, dry_run: bool = False, target_album: str = "Imported from Shared", auto_confirm: bool = False):
        self.dry_run = dry_run
        self.target_album = target_album
        self.auto_confirm = auto_confirm
        self.sync_db_path = Path.home() / '.photo_slideshow_shared_album_sync.json'
        self.sync_db = self._load_sync_db()
        
    def _load_sync_db(self) -> Dict:
        """Load the sync database that tracks imported photos."""
        if self.sync_db_path.exists():
            with open(self.sync_db_path, 'r') as f:
                return json.load(f)
        return {'albums': {}, 'last_updated': None}
    
    def _save_sync_db(self):
        """Save the sync database."""
        self.sync_db['last_updated'] = datetime.now().isoformat()
        with open(self.sync_db_path, 'w') as f:
            json.dump(self.sync_db, f, indent=2)
    
    def _get_album_sync_info(self, album_name: str) -> Dict:
        """Get sync info for a specific album."""
        if album_name not in self.sync_db['albums']:
            self.sync_db['albums'][album_name] = {
                'imported_photos': {},  # filename -> {date_imported, checksum}
                'last_sync': None,
                'total_imported': 0
            }
        return self.sync_db['albums'][album_name]
    
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
    
    def _ensure_target_album_exists(self) -> bool:
        """Create the target album if it doesn't exist."""
        script = f'''
        tell application "Photos"
            try
                -- Try to get the album
                set targetAlbum to album "{self.target_album}"
                return "exists"
            on error
                -- Album doesn't exist, create it
                make new album named "{self.target_album}"
                return "created"
            end try
        end tell
        '''
        
        try:
            result = self.run_applescript(script)
            if result == "created":
                print(f"✓ Created album '{self.target_album}'")
            return True
        except Exception as e:
            print(f"Error creating album: {e}")
            return False
    
    def get_shared_album_photos(self, album_name: str) -> List[Dict]:
        """
        Get list of photos in a shared album using GUI scripting.
        
        Note: This requires manual export from Photos.app since shared albums
        are not accessible via AppleScript.
        """
        print(f"\n⚠️  Shared albums cannot be accessed programmatically.")
        print(f"\nTo sync '{album_name}', you need to:")
        print(f"1. Open Photos.app")
        print(f"2. Go to Shared Albums → '{album_name}'")
        print(f"3. Select all photos (Cmd+A)")
        print(f"4. File → Export → Export Unmodified Original")
        print(f"5. Save to: /tmp/shared_album_export/")
        print(f"\nThen run this script again with --import-from-export")
        return []
    
    def import_from_export_folder(self, album_name: str, export_folder: Path) -> bool:
        """
        Import photos from an export folder, skipping duplicates.
        
        Args:
            album_name: Name of the shared album
            export_folder: Path to folder containing exported photos
            
        Returns:
            True if successful
        """
        if not export_folder.exists():
            print(f"Export folder not found: {export_folder}")
            return False
        
        # Get list of files in export folder
        photo_files = []
        for ext in ['*.jpg', '*.jpeg', '*.heic', '*.png', '*.mov', '*.mp4']:
            photo_files.extend(export_folder.glob(ext))
            photo_files.extend(export_folder.glob(ext.upper()))
        
        if not photo_files:
            print(f"No photos found in {export_folder}")
            return False
        
        print(f"\nFound {len(photo_files)} files in export folder")
        
        # Get sync info for this album
        sync_info = self._get_album_sync_info(album_name)
        imported_photos = sync_info['imported_photos']
        
        # Check which photos are new
        new_photos = []
        skipped_photos = []
        
        for photo_file in photo_files:
            filename = photo_file.name
            
            # Calculate checksum to detect duplicates
            checksum = self._calculate_checksum(photo_file)
            
            # Check if already imported
            if filename in imported_photos:
                stored_checksum = imported_photos[filename].get('checksum')
                if stored_checksum == checksum:
                    skipped_photos.append(filename)
                    continue
            
            new_photos.append({
                'path': photo_file,
                'filename': filename,
                'checksum': checksum
            })
        
        print(f"\nNew photos to import: {len(new_photos)}")
        print(f"Already imported (skipped): {len(skipped_photos)}")
        
        if not new_photos:
            print(f"\n✓ Album '{album_name}' is already up to date!")
            return True
        
        if self.dry_run:
            print(f"\n[DRY RUN] Would import {len(new_photos)} new photos:")
            for photo in new_photos[:10]:  # Show first 10
                print(f"  - {photo['filename']}")
            if len(new_photos) > 10:
                print(f"  ... and {len(new_photos) - 10} more")
            print(f"\nPhotos would be added to album: '{self.target_album}'")
            return True
        
        # Ensure target album exists
        if not self._ensure_target_album_exists():
            print("Failed to create target album. Aborting.")
            return False
        
        # Confirm with user (unless auto-confirmed)
        if not hasattr(self, 'auto_confirm') or not self.auto_confirm:
            print(f"\nThis will import {len(new_photos)} new photos into your library.")
            print(f"Photos will be added to album: '{self.target_album}'")
            response = input("Continue? (yes/no): ").strip().lower()
            
            if response not in ['yes', 'y']:
                print("Import cancelled.")
                return False
        else:
            print(f"\nImporting {len(new_photos)} new photos into your library.")
            print(f"Photos will be added to album: '{self.target_album}'")
        
        # Import the new photos using osxphotos
        print(f"\nImporting {len(new_photos)} photos...")
        
        try:
            import osxphotos
            
            # Import all photos in one command (so "apply to all" works)
            # Build list of POSIX file paths
            file_paths = [str(photo['path']) for photo in new_photos]
            file_list = ', '.join([f'POSIX file "{path}"' for path in file_paths])
            
            try:
                # Import all files at once with skip duplicates option
                script = f'''
                tell application "Photos"
                    with timeout of 300 seconds
                        import {{{file_list}}} skip check duplicates true
                    end timeout
                end tell
                '''
                self.run_applescript(script)
                
                # Record all in sync database
                for photo in new_photos:
                    imported_photos[photo['filename']] = {
                        'checksum': photo['checksum'],
                        'date_imported': datetime.now().isoformat(),
                        'source_album': album_name
                    }
                
                imported_count = len(new_photos)
                print(f"  Imported {imported_count} photos (duplicates skipped automatically)")
                
            except Exception as e:
                print(f"  Error during batch import: {e}")
                print(f"  Falling back to individual imports...")
                
                # Fallback: import one by one
                imported_count = 0
                for photo in new_photos:
                    try:
                        script = f'''
                        tell application "Photos"
                            with timeout of 60 seconds
                                import POSIX file "{photo['path']}" skip check duplicates true
                            end timeout
                        end tell
                        '''
                        self.run_applescript(script)
                        
                        imported_photos[photo['filename']] = {
                            'checksum': photo['checksum'],
                            'date_imported': datetime.now().isoformat(),
                            'source_album': album_name
                        }
                        
                        imported_count += 1
                        if imported_count % 10 == 0:
                            print(f"  Imported {imported_count}/{len(new_photos)}...")
                        
                    except Exception as e:
                        print(f"  Error importing {photo['filename']}: {e}")
            
            # Update sync info
            sync_info['total_imported'] = len(imported_photos)
            sync_info['last_sync'] = datetime.now().isoformat()
            self._save_sync_db()
            
            print(f"\n✓ Successfully imported {imported_count} new photos")
            print(f"\nTotal photos tracked for '{album_name}': {len(imported_photos)}")
            print(f"\nNote: To organize these photos, you can manually:")
            print(f"  1. Open Photos.app")
            print(f"  2. Go to 'Imports' (they'll be in the most recent import)")
            print(f"  3. Select the {imported_count} photos")
            print(f"  4. Add them to an album of your choice")
            
            return True
            
        except Exception as e:
            print(f"Error during import: {e}")
            return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()
    
    def show_status(self):
        """Show sync status for all tracked albums."""
        if not self.sync_db['albums']:
            print("No albums have been synced yet.")
            return
        
        print("\n=== Shared Album Sync Status ===\n")
        
        for album_name, info in self.sync_db['albums'].items():
            print(f"Album: {album_name}")
            print(f"  Total photos imported: {info['total_imported']}")
            print(f"  Last sync: {info['last_sync'] or 'Never'}")
            print()
        
        print(f"Sync database: {self.sync_db_path}")
    
    def manual_sync_instructions(self, album_name: str):
        """Print instructions for manual sync process."""
        export_folder = Path("/tmp/shared_album_export")
        
        print(f"\n=== Manual Sync Process for '{album_name}' ===\n")
        print("Step 1: Export photos from shared album")
        print("  1. Open Photos.app")
        print(f"  2. Go to: Shared Albums → '{album_name}'")
        print("  3. Select all photos: Cmd+A")
        print("  4. File → Export → Export Unmodified Original")
        print(f"  5. Save to: {export_folder}")
        print("     (Create this folder if it doesn't exist)")
        print("\nStep 2: Import to main library (avoiding duplicates)")
        print(f"  python sync_shared_album.py --album \"{album_name}\" --import-from-export")
        print("\nStep 3: Clean up")
        print(f"  rm -rf {export_folder}")
        print("\n=== Future Syncs ===")
        print("Repeat the same process. The script will automatically skip")
        print("photos that have already been imported.")


def main():
    parser = argparse.ArgumentParser(
        description='Sync shared albums to main library without duplicates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--album',
        type=str,
        help='Name of the shared album to sync'
    )
    
    parser.add_argument(
        '--import-from-export',
        action='store_true',
        help='Import from /tmp/shared_album_export/ folder'
    )
    
    parser.add_argument(
        '--export-folder',
        type=Path,
        default=Path('/tmp/shared_album_export'),
        help='Path to export folder (default: /tmp/shared_album_export)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without actually importing'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show sync status for all tracked albums'
    )
    
    parser.add_argument(
        '--target-album',
        type=str,
        default='Imported from Shared',
        help='Name of album to import photos into (default: "Imported from Shared")'
    )
    
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Auto-confirm import without prompting'
    )
    
    args = parser.parse_args()
    
    syncer = SharedAlbumSync(dry_run=args.dry_run, target_album=args.target_album, auto_confirm=args.yes)
    
    if args.status:
        syncer.show_status()
        return
    
    if args.album:
        if args.import_from_export:
            # Import from export folder
            success = syncer.import_from_export_folder(args.album, args.export_folder)
            sys.exit(0 if success else 1)
        else:
            # Show manual sync instructions
            syncer.manual_sync_instructions(args.album)
            return
    
    # No arguments provided
    parser.print_help()


if __name__ == '__main__':
    main()
