#!/usr/bin/env python3
"""
Test video export latency to measure performance impact
"""

import sys
import os
import time
sys.path.append('/Users/ken/CascadeProjects/photo-slideshow')

from photo_manager import PhotoManager
from config import SlideshowConfig
from path_config import PathConfig

def test_video_export_latency():
    """Test how long video exports take."""
    config = SlideshowConfig.from_file('/Users/ken/.photo_slideshow_config.json')
    path_config = PathConfig()
    
    try:
        photo_manager = PhotoManager(config, path_config)
        photos = photo_manager.load_photos()
        
        # Find videos that need export
        export_videos = []
        direct_videos = []
        
        for photo in photos:
            if photo.get('media_type') == 'video':
                if photo.get('needs_export'):
                    export_videos.append(photo)
                else:
                    direct_videos.append(photo)
        
        print(f"Found {len(export_videos)} videos needing export")
        print(f"Found {len(direct_videos)} videos with direct paths")
        
        if export_videos:
            print("\nTesting export latency for first 3 videos...")
            
            for i, video in enumerate(export_videos[:3]):
                print(f"\nVideo {i+1}: {video.get('filename')}")
                print(f"Original size: {video.get('original_filesize', 'unknown')} bytes")
                
                start_time = time.time()
                exported_path = photo_manager._export_video_temporarily(video)
                export_time = time.time() - start_time
                
                if exported_path:
                    file_size = os.path.getsize(exported_path)
                    print(f"Export time: {export_time:.2f} seconds")
                    print(f"Exported size: {file_size} bytes")
                    print(f"Export path: {exported_path}")
                else:
                    print(f"Export failed after {export_time:.2f} seconds")
        
        if direct_videos:
            print(f"\nDirect path videos (no export needed):")
            for i, video in enumerate(direct_videos[:3]):
                print(f"Video {i+1}: {video.get('filename')} - Path: {video.get('path')}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_video_export_latency()
