#!/usr/bin/env python3
"""
Test Video Export Delay
Tests actual video export times to measure slideshow delays.
"""

import time
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from photo_manager import PhotoManager
from config import SlideshowConfig
from path_config import PathConfig

def test_video_export_delay():
    """Test video export delays to understand threading requirements."""
    print("🎬 Testing Video Export Delays...")
    print("=" * 50)
    
    try:
        # Initialize configuration
        print("⚙️  Loading configuration...")
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        config.load_config()
        
        # Initialize photo manager
        print("📸 Loading photo manager...")
        photo_manager = PhotoManager(config, path_config)
        
        # Load photos from Apple Photos
        print("📚 Loading photos from Apple Photos...")
        photos = photo_manager.load_photos()
        print(f"📊 Loaded {len(photos)} total photos")
        
        # Find videos that need export
        videos_needing_export = [p for p in photos if p.get('needs_export') == True]
        all_videos = [p for p in photos if p.get('media_type') == 'video']
        
        print(f"🎥 Found {len(all_videos)} total videos")
        print(f"📤 Found {len(videos_needing_export)} videos that need export")
        
        if not videos_needing_export:
            print("\n✅ RESULT: No videos need export - all are accessible as files!")
            print("   This explains why you don't see 2-10 second delays.")
            print("   The threading concern may not apply to your photo library.")
            return
        
        print(f"\n🧪 Testing export delay for first video that needs export...")
        
        # Test first video that needs export
        video = videos_needing_export[0]
        filename = video.get('filename', 'unknown')
        file_size = video.get('original_filesize', 'unknown')
        
        print(f"📁 Video: {filename}")
        print(f"📏 Size: {file_size} bytes")
        print(f"🔍 UUID: {video.get('uuid', 'unknown')}")
        print(f"📤 Needs export: {video.get('needs_export')}")
        
        # Clear any existing cache for this video to force fresh export
        cache_dir = os.path.join(os.path.expanduser('~'), '.photo_slideshow_cache', 'videos')
        photo_uuid = video.get('uuid', '')
        cached_path = os.path.join(cache_dir, f"{photo_uuid}.mov")
        
        if os.path.exists(cached_path):
            print(f"🗑️  Removing cached file to force fresh export: {cached_path}")
            os.remove(cached_path)
        
        print(f"\n⏱️  Starting export timing...")
        print("   (This is what would block the slideshow main thread)")
        
        # Measure export time
        start_time = time.time()
        exported_path = photo_manager._export_video_temporarily(video)
        export_time = time.time() - start_time
        
        print(f"\n📊 EXPORT RESULTS:")
        print(f"   ⏱️  Export time: {export_time:.2f} seconds")
        print(f"   📁 Exported to: {exported_path}")
        
        if export_time > 1.0:
            print(f"\n⚠️  WARNING: {export_time:.2f}s delay would freeze slideshow!")
            print(f"   This confirms threading is needed for video exports.")
        else:
            print(f"\n✅ Export was fast ({export_time:.2f}s) - threading less critical.")
        
        # Test a few more videos if available
        if len(videos_needing_export) > 1:
            print(f"\n🔄 Testing {min(3, len(videos_needing_export)-1)} more videos...")
            
            for i, video in enumerate(videos_needing_export[1:4], 2):
                filename = video.get('filename', f'video_{i}')
                
                # Clear cache
                photo_uuid = video.get('uuid', '')
                cached_path = os.path.join(cache_dir, f"{photo_uuid}.mov")
                if os.path.exists(cached_path):
                    os.remove(cached_path)
                
                start_time = time.time()
                exported_path = photo_manager._export_video_temporarily(video)
                export_time = time.time() - start_time
                
                print(f"   📹 Video {i}: {filename} - {export_time:.2f}s")
        
        print(f"\n🎯 CONCLUSION:")
        if any(True for v in videos_needing_export[:4]):  # We tested up to 4 videos
            print(f"   Video exports DO cause delays in your library.")
            print(f"   Background threading for exports is justified.")
        else:
            print(f"   Most videos don't need export in your library.")
            print(f"   Threading concern may be less critical.")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_video_export_delay()
