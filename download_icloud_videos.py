#!/usr/bin/env python3
"""
Helper script to download videos from iCloud to local storage.

This script uses osxphotos to identify videos that are in iCloud but not
downloaded locally, then uses the osxphotos CLI --download-missing feature
to download them.

Usage:
    python download_icloud_videos.py [--album ALBUM_NAME] [--person PERSON_NAME]
"""

import argparse
import sys
import subprocess
from pathlib import Path

try:
    import osxphotos
except ImportError:
    print("Error: osxphotos not installed. Install with: pip install osxphotos")
    sys.exit(1)


def find_missing_videos(album_name=None, person_name=None):
    """Find videos that are in iCloud but not downloaded locally."""
    print("🔍 Scanning Photos library for iCloud videos...")
    
    photosdb = osxphotos.PhotosDB()
    
    # Build query
    photos = photosdb.photos()
    
    # Filter for videos only
    videos = [p for p in photos if p.ismovie]
    print(f"📹 Found {len(videos)} total videos in library")
    
    # Filter by album if specified
    if album_name:
        videos = [v for v in videos if any(album_name.lower() in a.title.lower() for a in v.albums)]
        print(f"📁 Filtered to {len(videos)} videos in album '{album_name}'")
    
    # Filter by person if specified
    if person_name:
        videos = [v for v in videos if any(person_name.lower() in p.name.lower() for p in v.persons)]
        print(f"👤 Filtered to {len(videos)} videos with person '{person_name}'")
    
    # Find missing videos (in iCloud but not local)
    missing_videos = [v for v in videos if v.ismissing]
    
    print(f"\n☁️  Found {len(missing_videos)} videos in iCloud (not downloaded)")
    
    if missing_videos:
        print("\nMissing videos:")
        for i, video in enumerate(missing_videos[:10], 1):  # Show first 10
            print(f"  {i}. {video.filename} ({video.date.strftime('%Y-%m-%d') if video.date else 'no date'})")
        
        if len(missing_videos) > 10:
            print(f"  ... and {len(missing_videos) - 10} more")
    
    return missing_videos


def download_videos_cli(missing_videos):
    """Use osxphotos CLI to download missing videos."""
    if not missing_videos:
        print("\n✅ All videos are already downloaded!")
        return True
    
    print(f"\n📥 Preparing to download {len(missing_videos)} videos from iCloud...")
    print("\n⚠️  IMPORTANT NOTES:")
    print("  - This will use osxphotos CLI with --download-missing")
    print("  - Photos.app will be controlled via AppleScript")
    print("  - This may take a while depending on video sizes")
    print("  - Keep Photos.app open during the process")
    print("  - The AppleScript interface can be buggy")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Download cancelled")
        return False
    
    # Create temporary directory for export
    import tempfile
    temp_dir = Path(tempfile.mkdtemp(prefix="osxphotos_download_"))
    print(f"\n📂 Using temporary directory: {temp_dir}")
    
    # Create UUID file for osxphotos
    uuid_file = temp_dir / "video_uuids.txt"
    with open(uuid_file, 'w') as f:
        for video in missing_videos:
            f.write(f"{video.uuid}\n")
    
    print(f"📝 Created UUID file with {len(missing_videos)} videos")
    
    # Build osxphotos command
    cmd = [
        'osxphotos', 'export',
        str(temp_dir),
        '--uuid-from-file', str(uuid_file),
        '--download-missing',
        '--verbose'
    ]
    
    print(f"\n🚀 Running: {' '.join(cmd)}")
    print("\nThis may take several minutes...\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print("\n✅ Download complete!")
        print(f"\n🗑️  You can delete the temporary directory: {temp_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during download: {e}")
        print(f"\n🗑️  Temporary directory: {temp_dir}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        print(f"🗑️  Temporary directory: {temp_dir}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download videos from iCloud to local storage using osxphotos"
    )
    parser.add_argument(
        '--album',
        help='Filter videos by album name (case-insensitive substring match)'
    )
    parser.add_argument(
        '--person',
        help='Filter videos by person name (case-insensitive substring match)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only show what would be downloaded, do not actually download'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("iCloud Video Downloader for Photo Slideshow")
    print("=" * 70)
    
    # Find missing videos
    missing_videos = find_missing_videos(args.album, args.person)
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No downloads will be performed")
        return 0
    
    # Download videos
    if missing_videos:
        success = download_videos_cli(missing_videos)
        return 0 if success else 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())
