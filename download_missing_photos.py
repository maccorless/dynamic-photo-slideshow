#!/usr/bin/env python3
"""
Script to download missing iCloud photos for the slideshow using osxphotos.

This script identifies photos that would be used by the slideshow but are missing
local files, then uses osxphotos export with --download-missing to download them.
"""

import os
import sys
import json
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project directory to Python path to import our modules
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from photo_manager import PhotoManager
from config import SlideshowConfig

class iCloudPhotoDownloader:
    """Downloads missing iCloud photos for the slideshow."""
    
    def __init__(self, config_path: str = "~/.photo_slideshow_config.json"):
        self.config_path = os.path.expanduser(config_path)
        self.config = SlideshowConfig()
        self.config.load_config()
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the downloader."""
        logger = logging.getLogger('icloud_downloader')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def identify_missing_photos(self) -> List[str]:
        """
        Identify photos that would be used by slideshow but have missing local files.
        Returns list of photo UUIDs.
        """
        self.logger.info("Identifying missing photos for slideshow...")
        
        # Create PhotoManager to analyze current photo availability
        photo_manager = PhotoManager(self.config)
        
        # Get all photos that match slideshow filters (including missing ones)
        all_filtered_photos = photo_manager._get_filtered_photos_including_missing()
        
        # Identify which ones are missing local files
        missing_uuids = []
        missing_count = 0
        
        for photo in all_filtered_photos:
            if not photo.path or photo.path == '':
                missing_uuids.append(photo.uuid)
                missing_count += 1
                
        self.logger.info(f"Found {missing_count} photos missing local files out of {len(all_filtered_photos)} total filtered photos")
        return missing_uuids
    
    def download_photos_by_uuid(self, uuids: List[str], batch_size: int = 100) -> bool:
        """
        Download photos by UUID using osxphotos export --download-missing.
        
        Args:
            uuids: List of photo UUIDs to download
            batch_size: Number of photos to process in each batch
            
        Returns:
            True if successful, False otherwise
        """
        if not uuids:
            self.logger.info("No photos to download")
            return True
            
        self.logger.info(f"Starting download of {len(uuids)} missing photos...")
        
        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            self.logger.info(f"Using temporary export directory: {temp_dir}")
            
            # Process photos in batches to avoid command line length limits
            total_batches = (len(uuids) + batch_size - 1) // batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(uuids))
                batch_uuids = uuids[start_idx:end_idx]
                
                self.logger.info(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_uuids)} photos)")
                
                # Create UUID file for this batch
                uuid_file = os.path.join(temp_dir, f"batch_{batch_num}_uuids.txt")
                with open(uuid_file, 'w') as f:
                    for uuid in batch_uuids:
                        f.write(f"{uuid}\n")
                
                # Build osxphotos export command
                cmd = [
                    'osxphotos', 'export',
                    '--download-missing',
                    '--use-photokit',  # Required with --download-missing
                    '--uuid-from-file', uuid_file,
                    '--verbose',
                    temp_dir
                ]
                
                try:
                    self.logger.info(f"Running: {' '.join(cmd)}")
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=1800  # 30 minute timeout per batch
                    )
                    
                    if result.returncode == 0:
                        self.logger.info(f"Batch {batch_num + 1} completed successfully")
                        if result.stdout:
                            self.logger.debug(f"osxphotos output: {result.stdout}")
                    else:
                        self.logger.error(f"Batch {batch_num + 1} failed with return code {result.returncode}")
                        if result.stderr:
                            self.logger.error(f"Error output: {result.stderr}")
                        return False
                        
                except subprocess.TimeoutExpired:
                    self.logger.error(f"Batch {batch_num + 1} timed out after 30 minutes")
                    return False
                except Exception as e:
                    self.logger.error(f"Error processing batch {batch_num + 1}: {e}")
                    return False
        
        self.logger.info("Photo download completed successfully!")
        return True
    
    def verify_download_success(self, original_missing_count: int) -> bool:
        """
        Verify that photos were successfully downloaded by checking current missing count.
        
        Args:
            original_missing_count: Number of missing photos before download
            
        Returns:
            True if fewer photos are missing now
        """
        self.logger.info("Verifying download success...")
        
        # Re-check missing photos
        current_missing_uuids = self.identify_missing_photos()
        current_missing_count = len(current_missing_uuids)
        
        improvement = original_missing_count - current_missing_count
        
        if improvement > 0:
            self.logger.info(f"Success! Downloaded {improvement} photos. "
                           f"Missing photos reduced from {original_missing_count} to {current_missing_count}")
            return True
        else:
            self.logger.warning(f"No improvement detected. Still {current_missing_count} missing photos")
            return False
    
    def run(self) -> bool:
        """
        Main method to identify and download missing photos.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if osxphotos is available
            try:
                subprocess.run(['osxphotos', '--version'], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.error("osxphotos not found. Please install it first: pip install osxphotos")
                return False
            
            # Identify missing photos
            missing_uuids = self.identify_missing_photos()
            original_missing_count = len(missing_uuids)
            
            if original_missing_count == 0:
                self.logger.info("No missing photos found. All slideshow photos are already available locally.")
                return True
            
            # Ask user for confirmation
            print(f"\nFound {original_missing_count} photos that need to be downloaded from iCloud.")
            print("This process may take a while depending on photo sizes and internet speed.")
            response = input("Do you want to proceed? (y/N): ").strip().lower()
            
            if response not in ['y', 'yes']:
                self.logger.info("Download cancelled by user")
                return False
            
            # Download the photos
            success = self.download_photos_by_uuid(missing_uuids)
            
            if success:
                # Verify the download worked
                return self.verify_download_success(original_missing_count)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download missing iCloud photos for the slideshow"
    )
    parser.add_argument(
        '--config', 
        default="~/.photo_slideshow_config.json",
        help="Path to slideshow config file"
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help="Number of photos to process in each batch (default: 100)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Only identify missing photos, don't download them"
    )
    
    args = parser.parse_args()
    
    downloader = iCloudPhotoDownloader(args.config)
    
    if args.dry_run:
        missing_uuids = downloader.identify_missing_photos()
        print(f"Dry run: Found {len(missing_uuids)} missing photos")
        return
    
    success = downloader.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
