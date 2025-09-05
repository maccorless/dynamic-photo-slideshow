#!/usr/bin/env python3
"""
Automated photo sync script for maintaining local cache in sync with iCloud.

This script can be run hourly to download new photos that match the slideshow
criteria without re-downloading existing photos.
"""

import os
import sys
import json
import tempfile
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Set

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from photo_manager import PhotoManager

class PhotoSyncManager:
    """Manages incremental photo synchronization from iCloud."""
    
    def __init__(self, config_path: str = "~/.photo_slideshow_config.json"):
        self.config_path = os.path.expanduser(config_path)
        self.logger = self._setup_logging()
        self.sync_log_file = project_dir / "sync_log.json"
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the sync manager."""
        logger = logging.getLogger('photo_sync')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler for sync history
            log_file = project_dir / "sync.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
            
        return logger
    
    def load_sync_state(self) -> dict:
        """Load the last sync state from file."""
        if self.sync_log_file.exists():
            try:
                with open(self.sync_log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load sync state: {e}")
        
        return {
            "last_sync": None,
            "synced_photos": [],
            "total_synced": 0
        }
    
    def save_sync_state(self, state: dict):
        """Save the current sync state to file."""
        try:
            with open(self.sync_log_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Could not save sync state: {e}")
    
    def get_photos_needing_sync(self) -> List[str]:
        """Identify photos that need to be downloaded."""
        self.logger.info("Identifying photos that need synchronization...")
        
        # Load config
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # Get all photos matching criteria (including missing ones)
        photo_manager = PhotoManager(config)
        all_filtered_photos = photo_manager._get_filtered_photos_including_missing()
        
        # Get currently missing photos (not downloaded locally)
        missing_photos = []
        for photo in all_filtered_photos:
            if not photo.path or photo.path == '':
                missing_photos.append(photo.uuid)
        
        self.logger.info(f"Found {len(missing_photos)} photos missing locally")
        return missing_photos
    
    def sync_photos(self, max_photos: int = 100, dry_run: bool = False) -> bool:
        """
        Sync photos incrementally.
        
        Args:
            max_photos: Maximum number of photos to download in this sync
            dry_run: If True, only show what would be downloaded
        """
        sync_state = self.load_sync_state()
        
        # Get photos that need syncing
        missing_uuids = self.get_photos_needing_sync()
        
        if not missing_uuids:
            self.logger.info("No photos need syncing - all up to date!")
            return True
        
        # Limit the number of photos to sync in this run
        photos_to_sync = missing_uuids[:max_photos]
        
        self.logger.info(f"Syncing {len(photos_to_sync)} photos (max {max_photos})")
        
        if dry_run:
            self.logger.info("DRY RUN - Would sync the following photos:")
            for uuid in photos_to_sync[:10]:  # Show first 10
                self.logger.info(f"  - {uuid}")
            if len(photos_to_sync) > 10:
                self.logger.info(f"  ... and {len(photos_to_sync) - 10} more")
            return True
        
        # Perform the sync using osxphotos
        success = self._download_photos_by_uuid(photos_to_sync)
        
        if success:
            # Update sync state
            sync_state["last_sync"] = datetime.now().isoformat()
            sync_state["synced_photos"].extend(photos_to_sync)
            sync_state["total_synced"] = len(sync_state["synced_photos"])
            self.save_sync_state(sync_state)
            
            self.logger.info(f"Successfully synced {len(photos_to_sync)} photos")
            return True
        else:
            self.logger.error("Sync failed")
            return False
    
    def _download_photos_by_uuid(self, uuids: List[str]) -> bool:
        """Download specific photos by UUID using osxphotos."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                self.logger.info(f"Using temporary directory: {temp_dir}")
                
                # Build osxphotos command with UUID filtering
                cmd = [
                    'osxphotos', 'export',
                    '--download-missing',  # Download from iCloud if missing
                    '--not-hidden',        # Exclude hidden photos
                    '--verbose',
                    temp_dir
                ]
                
                # Add UUID filters
                for uuid in uuids:
                    cmd.extend(['--uuid', uuid])
                
                self.logger.info(f"Running sync command for {len(uuids)} photos...")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minute timeout
                )
                
                if result.returncode == 0:
                    self.logger.info("Sync completed successfully!")
                    
                    # Log some output details
                    if result.stdout:
                        lines = result.stdout.split('\n')
                        for line in lines[-10:]:  # Show last 10 lines
                            if line.strip() and ('exported' in line.lower() or 'processed' in line.lower()):
                                self.logger.info(line.strip())
                    
                    return True
                else:
                    self.logger.error(f"Sync failed with return code {result.returncode}")
                    if result.stderr:
                        self.logger.error(f"Error: {result.stderr}")
                    return False
                    
        except subprocess.TimeoutExpired:
            self.logger.error("Sync timed out after 30 minutes")
            return False
        except Exception as e:
            self.logger.error(f"Error during sync: {e}")
            return False
    
    def get_sync_status(self) -> dict:
        """Get current sync status and statistics."""
        sync_state = self.load_sync_state()
        missing_count = len(self.get_photos_needing_sync())
        
        return {
            "last_sync": sync_state.get("last_sync"),
            "total_synced": sync_state.get("total_synced", 0),
            "photos_needing_sync": missing_count,
            "sync_up_to_date": missing_count == 0
        }

def main():
    """Main entry point for the sync script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync photos from iCloud incrementally")
    parser.add_argument('--max-photos', type=int, default=100,
                       help='Maximum photos to sync in this run (default: 100)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be synced without downloading')
    parser.add_argument('--status', action='store_true',
                       help='Show sync status and exit')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce logging output')
    
    args = parser.parse_args()
    
    sync_manager = PhotoSyncManager()
    
    if args.quiet:
        sync_manager.logger.setLevel(logging.WARNING)
    
    if args.status:
        status = sync_manager.get_sync_status()
        print(f"Last sync: {status['last_sync']}")
        print(f"Total synced: {status['total_synced']}")
        print(f"Photos needing sync: {status['photos_needing_sync']}")
        print(f"Up to date: {status['sync_up_to_date']}")
        return
    
    print(f"Starting incremental photo sync (max {args.max_photos} photos)...")
    
    success = sync_manager.sync_photos(
        max_photos=args.max_photos,
        dry_run=args.dry_run
    )
    
    if success:
        print("✅ Sync completed successfully!")
    else:
        print("❌ Sync failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
