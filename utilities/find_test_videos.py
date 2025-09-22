#!/usr/bin/env python3
"""
Script to find and extract test videos from Apple Photos library.
Finds one short video (<10 seconds) and one long video (>15 seconds) for testing.
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from photo_manager import PhotoManager
from config import SlideshowConfig

def find_test_videos():
    """Find suitable test videos and copy them to test directory."""
    
    # Initialize photo manager
    config = SlideshowConfig()
    photo_manager = PhotoManager(config.config)
    
    # Connect to Photos database
    if not photo_manager._connect_to_photos():
        print("ERROR: Could not connect to Apple Photos library")
        return False
    
    # Get all photos (including videos)
    all_photos = photo_manager.photos_db.photos()
    
    short_video = None
    long_video = None
    
    print("Scanning Apple Photos library for test videos...")
    
    videos_found = []
    
    for photo in all_photos:
        if not photo.ismovie:
            continue
            
        # Get video duration (in seconds) - try multiple approaches
        duration = None
        
        # Try to get duration from metadata
        try:
            # Check if photo has duration attribute
            if hasattr(photo, 'duration') and photo.duration:
                duration = photo.duration
            # Try video_duration attribute
            elif hasattr(photo, 'video_duration') and photo.video_duration:
                duration = photo.video_duration
            # Try to extract from path using our video manager
            elif photo.path:
                from video_manager import VideoManager
                vm = VideoManager(None)
                metadata = vm.get_video_metadata(photo.path)
                if metadata and 'duration' in metadata:
                    duration = metadata['duration']
        except Exception as e:
            print(f"  Error getting duration for {photo.filename}: {e}")
            continue
            
        if duration is None or duration <= 0:
            print(f"Found video: {photo.filename} - Duration: Unknown")
            continue
            
        print(f"Found video: {photo.filename} - Duration: {duration:.1f}s")
        videos_found.append((photo, duration))
        
        # Look for short video (< 15 seconds, relaxed criteria)
        if short_video is None and duration < 15:
            short_video = photo
            print(f"  -> Selected as SHORT test video")
            
        # Look for long video (> 10 seconds, relaxed criteria)  
        if long_video is None and duration > 10 and photo != short_video:
            long_video = photo
            print(f"  -> Selected as LONG test video")
            
        # Stop when we have both
        if short_video and long_video:
            break
    
    print(f"\nFound {len(videos_found)} videos total")
    
    # If we couldn't find ideal videos, use what we have
    if not short_video and videos_found:
        short_video = videos_found[0][0]
        print(f"Using first available video as SHORT: {short_video.filename}")
        
    if not long_video and len(videos_found) > 1:
        long_video = videos_found[1][0]
        print(f"Using second available video as LONG: {long_video.filename}")
    elif not long_video and len(videos_found) == 1:
        # Use the same video for both if only one available
        long_video = videos_found[0][0]
        print(f"Using same video for both SHORT and LONG: {long_video.filename}")
    
    if not short_video:
        print("ERROR: Could not find a short video (< 10 seconds)")
        return False
        
    if not long_video:
        print("ERROR: Could not find a long video (> 15 seconds)")
        return False
    
    # Create test videos directory
    test_dir = Path(__file__).parent.parent / "test_videos"
    test_dir.mkdir(exist_ok=True)
    
    # Export and copy videos
    short_path = export_video(short_video, test_dir, "short_test_video")
    long_path = export_video(long_video, test_dir, "long_test_video")
    
    if not short_path or not long_path:
        return False
    
    # Update config file
    config_path = Path.home() / ".photo_slideshow_config.json"
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    config_data['video_test_short_path'] = str(short_path)
    config_data['video_test_long_path'] = str(long_path)
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"\nTest videos extracted successfully:")
    print(f"Short video: {short_path}")
    print(f"Long video: {long_path}")
    print(f"Config updated with test video paths")
    print(f"\nTo enable video test mode, set 'video_test_mode': true in config")
    
    return True

def export_video(photo, test_dir, prefix):
    """Export video from Apple Photos and copy to test directory."""
    try:
        print(f"Exporting {photo.filename}...")
        
        # Get original filename extension
        original_ext = Path(photo.filename).suffix
        target_filename = f"{prefix}{original_ext}"
        target_path = test_dir / target_filename
        
        # Export video (this handles Apple Photos export automatically)
        exported_path = photo.export(str(test_dir), filename=target_filename)[0]
        
        print(f"  -> Exported to: {exported_path}")
        return target_path
        
    except Exception as e:
        print(f"ERROR exporting {photo.filename}: {e}")
        return None

if __name__ == "__main__":
    success = find_test_videos()
    sys.exit(0 if success else 1)
