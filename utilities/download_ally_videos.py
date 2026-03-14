#!/Users/ken/CascadeProjects/photo-slideshow/slideshow_env/bin/python
"""
Automated script to download all "Ally" videos from iCloud to local storage.
Designed to run daily via cron/launchd to keep videos synchronized.

Usage:
    python download_ally_videos.py [--person NAME] [--dry-run] [--verbose]

Examples:
    python download_ally_videos.py                    # Download all Ally videos
    python download_ally_videos.py --person "John"    # Download videos for different person
    python download_ally_videos.py --dry-run          # Show what would be downloaded without downloading
    python download_ally_videos.py --verbose          # Show detailed progress
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import osxphotos
except ImportError:
    print("ERROR: osxphotos is required. Install with: pip install osxphotos")
    sys.exit(1)


class AllyVideoDownloader:
    """Downloads videos for a specific person from iCloud to local storage."""
    
    def __init__(self, person_name="Ally", dry_run=False, verbose=False):
        self.person_name = person_name
        self.dry_run = dry_run
        self.verbose = verbose
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup log file
        log_dir = Path.home() / '.photo_slideshow_cache' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_dir / f'video_download_{datetime.now().strftime("%Y%m%d")}.log'
        
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        self.photos_db = None
        self.stats = {
            'total_videos': 0,
            'already_local': 0,
            'needs_download': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def connect_to_photos(self):
        """Connect to Photos library."""
        try:
            self.logger.info("Connecting to Photos library...")
            self.photos_db = osxphotos.PhotosDB()
            self.logger.info("Successfully connected to Photos library")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Photos library: {e}")
            return False
    
    def find_videos(self):
        """Find all videos for the specified person."""
        try:
            self.logger.info(f"Searching for videos with person '{self.person_name}'...")
            
            # Get all photos for this person
            all_photos = self.photos_db.photos(persons=[self.person_name])
            
            # Filter to only videos
            videos = [p for p in all_photos if p.ismovie]
            
            self.stats['total_videos'] = len(videos)
            self.logger.info(f"Found {len(videos)} videos with person '{self.person_name}'")
            
            return videos
            
        except Exception as e:
            self.logger.error(f"Error searching for videos: {e}")
            return []
    
    def check_video_status(self, video):
        """
        Check if a video is available locally.
        
        Returns:
            tuple: (is_local, status_message)
        """
        try:
            # Check if video is missing from local storage
            is_missing = getattr(video, 'ismissing', False)
            
            # Check if video has a valid local path
            video_path = getattr(video, 'path', None)
            has_local_file = video_path and os.path.exists(video_path)
            
            # Check iCloud status
            in_cloud = getattr(video, 'incloud', False)
            
            if is_missing:
                return False, "Missing from local storage (in iCloud only)"
            elif not has_local_file:
                return False, "No local file path"
            elif in_cloud and not has_local_file:
                return False, "In iCloud, not downloaded"
            else:
                return True, "Available locally"
                
        except Exception as e:
            self.logger.debug(f"Error checking video status: {e}")
            return False, f"Error: {e}"
    
    def download_video(self, video, export_dir):
        """
        Download a video from iCloud to local storage.
        
        Args:
            video: osxphotos PhotoInfo object
            export_dir: Directory to export video to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            filename = video.filename
            
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would download: {filename}")
                self.stats['skipped'] += 1
                return True
            
            self.logger.info(f"Downloading: {filename} ({self._format_size(video.original_filesize)})")
            
            # Export video (this triggers download from iCloud if needed)
            export_paths = video.export(
                export_dir,
                filename=f"{video.uuid}.mov",
                overwrite=False,  # Don't re-download if already exists
                download_missing=True  # Download from iCloud if needed
            )
            
            if export_paths:
                exported_path = export_paths[0]
                if os.path.exists(exported_path):
                    file_size = os.path.getsize(exported_path)
                    self.logger.info(f"✓ Successfully downloaded: {filename} ({self._format_size(file_size)})")
                    self.stats['downloaded'] += 1
                    return True
                else:
                    self.logger.warning(f"✗ Export reported success but file not found: {filename}")
                    self.stats['failed'] += 1
                    return False
            else:
                self.logger.warning(f"✗ Export failed (empty result): {filename}")
                self.stats['failed'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"✗ Error downloading {video.filename}: {e}")
            self.stats['failed'] += 1
            return False
    
    def _format_size(self, size_bytes):
        """Format file size in human-readable format."""
        if size_bytes is None:
            return "unknown size"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def run(self):
        """Main execution flow."""
        start_time = datetime.now()
        
        self.logger.info("=" * 70)
        self.logger.info(f"Ally Video Downloader - Started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Person: {self.person_name}")
        self.logger.info(f"Dry run: {self.dry_run}")
        self.logger.info("=" * 70)
        
        # Connect to Photos
        if not self.connect_to_photos():
            self.logger.error("Failed to connect to Photos library. Exiting.")
            return 1
        
        # Find videos
        videos = self.find_videos()
        if not videos:
            self.logger.info("No videos found. Nothing to do.")
            return 0
        
        # Setup export directory
        export_dir = Path.home() / '.photo_slideshow_cache' / 'videos'
        export_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Export directory: {export_dir}")
        
        # Check and download videos
        self.logger.info("\nChecking video availability...")
        self.logger.info("-" * 70)
        
        videos_to_download = []
        
        for i, video in enumerate(videos, 1):
            is_local, status = self.check_video_status(video)
            
            if is_local:
                self.stats['already_local'] += 1
                if self.verbose:
                    self.logger.debug(f"[{i}/{len(videos)}] ✓ {video.filename} - {status}")
            else:
                self.stats['needs_download'] += 1
                videos_to_download.append(video)
                self.logger.info(f"[{i}/{len(videos)}] ⬇ {video.filename} - {status}")
        
        # Summary before download
        self.logger.info("-" * 70)
        self.logger.info(f"Summary: {self.stats['already_local']} already local, {self.stats['needs_download']} need download")
        
        # Download videos that need it
        if videos_to_download:
            self.logger.info("\nDownloading videos...")
            self.logger.info("-" * 70)
            
            for i, video in enumerate(videos_to_download, 1):
                self.logger.info(f"[{i}/{len(videos_to_download)}] Processing: {video.filename}")
                self.download_video(video, export_dir)
        else:
            self.logger.info("\nAll videos are already available locally. Nothing to download.")
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.logger.info("=" * 70)
        self.logger.info("FINAL SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Total videos found:      {self.stats['total_videos']}")
        self.logger.info(f"Already local:           {self.stats['already_local']}")
        self.logger.info(f"Needed download:         {self.stats['needs_download']}")
        self.logger.info(f"Successfully downloaded: {self.stats['downloaded']}")
        self.logger.info(f"Failed:                  {self.stats['failed']}")
        if self.dry_run:
            self.logger.info(f"Skipped (dry run):       {self.stats['skipped']}")
        self.logger.info(f"Duration:                {duration:.1f} seconds")
        self.logger.info(f"Log file:                {self.log_file}")
        self.logger.info("=" * 70)
        
        # Return exit code
        if self.stats['failed'] > 0:
            return 1  # Some failures
        else:
            return 0  # Success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download videos for a specific person from iCloud to local storage.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Download all Ally videos
  %(prog)s --person "John"          Download videos for different person
  %(prog)s --dry-run                Show what would be downloaded
  %(prog)s --verbose                Show detailed progress
  %(prog)s --dry-run --verbose      Detailed dry run

The script will:
  1. Find all videos tagged with the specified person
  2. Check which videos are already available locally
  3. Download only the videos that are missing or in iCloud
  4. Save videos to: ~/.photo_slideshow_cache/videos/
  5. Log results to: ~/.photo_slideshow_cache/logs/
        """
    )
    
    parser.add_argument(
        '--person',
        default='Ally',
        help='Name of person to filter videos (default: Ally)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be downloaded without actually downloading'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress and debug information'
    )
    
    args = parser.parse_args()
    
    # Create and run downloader
    downloader = AllyVideoDownloader(
        person_name=args.person,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    exit_code = downloader.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
