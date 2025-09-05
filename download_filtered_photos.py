#!/usr/bin/env python3
"""
Script to download missing iCloud photos with enhanced filtering options.

This script allows you to specify additional filters to reduce the number of photos
downloaded while still improving temporal diversity.
"""

import os
import sys
import json
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Add the project directory to Python path to import our modules
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from photo_manager import PhotoManager
from config import SlideshowConfig
from cache_manager import CacheManager

class FilteredPhotoDownloader:
    """Downloads missing iCloud photos with enhanced filtering."""
    
    def __init__(self, config_path: str = "~/.photo_slideshow_config.json"):
        self.config_path = os.path.expanduser(config_path)
        self.config = SlideshowConfig()
        self.config.load_config()
        self.logger = self._setup_logging()
        self.cache_manager = CacheManager(self.config)
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the downloader."""
        logger = logging.getLogger('filtered_downloader')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def identify_missing_photos_with_filters(self, 
                                           people_names: List[str] = None,
                                           date_range_years: int = None,
                                           max_photos: int = None) -> List[str]:
        """
        Identify missing photos with additional filtering options.
        
        Args:
            people_names: List of people names to filter by
            date_range_years: Only include photos from last N years
            max_photos: Maximum number of photos to download
            
        Returns:
            List of photo UUIDs to download
        """
        self.logger.info("Identifying missing photos with enhanced filters...")
        
        # Create PhotoManager to analyze current photo availability
        photo_manager = PhotoManager(self.config)
        
        # Temporarily modify config for filtering
        original_people = self.config.get('filter_people_names', [])
        if people_names:
            # Create a temporary config dict with the people filter
            temp_config = SlideshowConfig()
            temp_config.load_config()
            temp_config.config['filter_people_names'] = people_names
            photo_manager = PhotoManager(temp_config)
            self.logger.info(f"Filtering by people: {people_names}")
        
        # Get all photos that match filters (including missing ones)
        all_filtered_photos = photo_manager._get_filtered_photos_including_missing()
        
        # Apply date range filter if specified
        if date_range_years:
            cutoff_date = datetime.now() - timedelta(days=365 * date_range_years)
            filtered_by_date = []
            for photo in all_filtered_photos:
                try:
                    if hasattr(photo, 'date') and photo.date and photo.date >= cutoff_date:
                        filtered_by_date.append(photo)
                except:
                    # Include photos with unknown dates
                    filtered_by_date.append(photo)
            all_filtered_photos = filtered_by_date
            self.logger.info(f"Filtered to photos from last {date_range_years} years: {len(all_filtered_photos)} photos")
        
        # Identify which ones are missing local files
        missing_photos = []
        missing_count = 0
        
        for photo in all_filtered_photos:
            if not photo.path or photo.path == '':
                missing_photos.append(photo)
                missing_count += 1
        
        # Apply max photos limit
        if max_photos and len(missing_photos) > max_photos:
            self.logger.info(f"Limiting to {max_photos} photos from {len(missing_photos)} missing photos")
            missing_photos = missing_photos[:max_photos]
            missing_count = len(missing_photos)
        
        missing_uuids = [photo.uuid for photo in missing_photos]
        
        self.logger.info(f"Found {missing_count} photos to download out of {len(all_filtered_photos)} total filtered photos")
        return missing_uuids
    
    
    def download_photos_by_uuid(self, uuids: List[str], batch_size: int = None) -> bool:
        """Download photos by UUID using osxphotos export --download-missing."""
        if not uuids:
            self.logger.info("No photos to download")
            return True
            
        if batch_size is None:
            batch_size = self.config.get('download_batch_size')
            
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
                        timeout=900  # 15 minute timeout per batch
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
                    self.logger.error(f"Batch {batch_num + 1} timed out after 15 minutes")
                    return False
                except Exception as e:
                    self.logger.error(f"Error processing batch {batch_num + 1}: {e}")
                    return False
        
        self.logger.info("Photo download completed successfully!")
        
        # Write signal file to indicate new photos are available
        try:
            self.cache_manager.write_download_signal(len(uuids))
            self.logger.info(f"Updated download signal file with {len(uuids)} new photos")
        except Exception as e:
            self.logger.warning(f"Failed to write download signal file: {e}")
        
        return True
    
    def run_interactive(self) -> bool:
        """Interactive mode to select filtering options."""
        try:
            # Check if osxphotos is available
            try:
                subprocess.run(['osxphotos', '--version'], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.error("osxphotos not found. Please install it first: pip install osxphotos")
                return False
            
            print("\n=== Filtered iCloud Photo Downloader ===")
            print("This tool helps you download only specific photos from iCloud to improve slideshow diversity.")
            print()
            
            # Get filtering preferences
            print("Filtering Options:")
            print("1. People filter (download photos of specific people)")
            print("2. Date range filter (download photos from recent years)")
            print("3. Maximum photos limit (limit total downloads)")
            print()
            
            # People filter
            people_names = []
            use_people = input("Filter by specific people? (y/N): ").strip().lower()
            if use_people in ['y', 'yes']:
                people_input = input("Enter people names (comma-separated): ").strip()
                if people_input:
                    people_names = [name.strip() for name in people_input.split(',')]
                    print(f"Will filter by people: {people_names}")
            
            # Date range filter
            date_range_years = None
            use_date = input("Filter by date range? (y/N): ").strip().lower()
            if use_date in ['y', 'yes']:
                try:
                    years = int(input("Download photos from last N years (e.g., 5): ").strip())
                    if years > 0:
                        date_range_years = years
                        print(f"Will download photos from last {years} years")
                except ValueError:
                    print("Invalid input, skipping date filter")
            
            # Max photos limit
            max_photos = None
            use_limit = input("Limit maximum photos to download? (y/N): ").strip().lower()
            if use_limit in ['y', 'yes']:
                try:
                    limit = int(input("Maximum photos to download (e.g., 1000): ").strip())
                    if limit > 0:
                        max_photos = limit
                        print(f"Will download maximum {limit} photos")
                except ValueError:
                    print("Invalid input, skipping photo limit")
            
            print("\n--- Analyzing photo library ---")
            
            # Identify missing photos with filters
            missing_uuids = self.identify_missing_photos_with_filters(
                people_names=people_names,
                date_range_years=date_range_years,
                max_photos=max_photos
            )
            
            if not missing_uuids:
                print("No missing photos found with the specified filters.")
                return True
            
            print(f"\nFound {len(missing_uuids)} photos to download with your filters.")
            print("This is much more manageable than downloading all 13,846 missing photos!")
            
            # Confirm download
            response = input(f"\nProceed with downloading {len(missing_uuids)} photos? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Download cancelled.")
                return False
            
            # Download the photos
            success = self.download_photos_by_uuid(missing_uuids)
            
            if success:
                print(f"\n✅ Successfully downloaded {len(missing_uuids)} photos!")
                print("You can now run your slideshow with the downloaded photos.")
                return True
            else:
                print("\n❌ Download failed. Check the logs for details.")
                return False
                
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download missing iCloud photos with filtering options"
    )
    parser.add_argument(
        '--config', 
        default="~/.photo_slideshow_config.json",
        help="Path to slideshow config file"
    )
    parser.add_argument(
        '--people',
        nargs='+',
        help="Filter by specific people names"
    )
    parser.add_argument(
        '--years',
        type=int,
        help="Download photos from last N years"
    )
    parser.add_argument(
        '--max-photos',
        type=int,
        help="Maximum number of photos to download"
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help="Run in interactive mode (default)"
    )
    
    args = parser.parse_args()
    
    downloader = FilteredPhotoDownloader(args.config)
    
    # If no command line args provided, run interactive mode
    if not any([args.people, args.years, args.max_photos]) or args.interactive:
        success = downloader.run_interactive()
    else:
        # Command line mode
        missing_uuids = downloader.identify_missing_photos_with_filters(
            people_names=args.people,
            date_range_years=args.years,
            max_photos=args.max_photos
        )
        
        if missing_uuids:
            print(f"Found {len(missing_uuids)} photos to download")
            response = input("Proceed? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                success = downloader.download_photos_by_uuid(missing_uuids)
            else:
                success = False
        else:
            print("No photos found matching criteria")
            success = True
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
