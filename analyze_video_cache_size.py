#!/usr/bin/env python3
"""
Quick script to analyze OSX Photos videos with person "ally" 
and calculate total storage needed for pre-caching.
"""

import os
import sys
import logging
from typing import List, Dict, Any

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import osxphotos
except ImportError:
    print("Error: osxphotos library not found. Please install it first.")
    sys.exit(1)

def analyze_ally_videos():
    """Analyze videos with person 'ally' and calculate cache storage requirements."""
    
    print("🔍 Analyzing OSX Photos videos with person 'ally'...")
    print("=" * 60)
    
    try:
        # Initialize Photos database
        print("📱 Connecting to Photos library...")
        photosdb = osxphotos.PhotosDB()
        
        # First, let's see what person names are available
        print("👥 Available person names in your Photos library:")
        try:
            all_persons = photosdb.persons
            # Handle both string and object formats
            if all_persons and len(all_persons) > 0:
                if hasattr(all_persons[0], 'name'):
                    person_names = [person.name for person in all_persons if person.name]
                else:
                    person_names = [str(person) for person in all_persons if person]
            else:
                person_names = []
            print(f"Found {len(person_names)} named persons: {person_names[:10]}{'...' if len(person_names) > 10 else ''}")
        except Exception as e:
            print(f"Could not retrieve person names: {e}")
            person_names = []
        print()
        
        # Also check total videos
        all_videos = [p for p in photosdb.photos() if p.ismovie]
        print(f"📊 Total videos in library: {len(all_videos)}")
        print()
        
        # Get all videos with person "ally" (case insensitive)
        print("🎬 Searching for videos with person 'ally' (case insensitive)...")
        ally_videos = []
        
        # Try different variations of "ally"
        search_names = ["ally", "Ally", "ALLY"]
        for search_name in search_names:
            try:
                photos_with_name = photosdb.photos(persons=[search_name])
                for photo in photos_with_name:
                    if photo.ismovie and photo not in ally_videos:
                        ally_videos.append(photo)
                if len(photos_with_name) > 0:
                    print(f"  Found {len([p for p in photos_with_name if p.ismovie])} videos with '{search_name}'")
            except:
                pass
        
        print(f"✅ Found {len(ally_videos)} total videos with person 'ally' (any case)")
        print()
        
        if len(ally_videos) == 0:
            print("❌ No videos found with person 'ally'")
            print("💡 Try running with a different person name from the list above")
            
            # Show a sample of videos with people for reference
            print("\n📝 Sample videos with people (first 5):")
            videos_with_people = [v for v in all_videos[:20] if v.persons]
            for i, video in enumerate(videos_with_people[:5]):
                person_names = [p.name for p in video.persons if p.name]
                print(f"  {i+1}. {video.filename} - People: {person_names}")
            return
        
        # Analyze each video
        total_size_bytes = 0
        locally_available = 0
        needs_download = 0
        missing_size = 0
        
        print("📊 Video Analysis:")
        print("-" * 60)
        print(f"{'Filename':<40} {'Size (MB)':<10} {'Status':<15} {'Date'}")
        print("-" * 60)
        
        for i, video in enumerate(ally_videos):
            try:
                # Get video info
                filename = video.filename or f"video_{i+1}.mov"
                date_str = video.date.strftime("%Y-%m-%d") if video.date else "Unknown"
                
                # Check availability
                is_missing = getattr(video, 'ismissing', False)
                local_available = getattr(video, 'path', None) and os.path.exists(video.path)
                
                # Get file size
                if local_available and video.path:
                    try:
                        file_size = os.path.getsize(video.path)
                        size_mb = file_size / (1024 * 1024)
                        status = "Local"
                        locally_available += 1
                        total_size_bytes += file_size
                    except (OSError, AttributeError):
                        # Try to get original filesize from metadata
                        file_size = getattr(video, 'original_filesize', 0) or 0
                        size_mb = file_size / (1024 * 1024) if file_size else 0
                        status = "iCloud" if is_missing else "Unknown"
                        needs_download += 1
                        missing_size += file_size
                else:
                    # Try to get original filesize from metadata
                    file_size = getattr(video, 'original_filesize', 0) or 0
                    size_mb = file_size / (1024 * 1024) if file_size else 0
                    status = "iCloud" if is_missing else "Unknown"
                    needs_download += 1
                    missing_size += file_size
                
                print(f"{filename:<40} {size_mb:>8.1f}  {status:<15} {date_str}")
                
            except Exception as e:
                print(f"{filename:<40} {'ERROR':<10} {'Failed':<15} {date_str}")
                print(f"  Error: {e}")
        
        print("-" * 60)
        
        # Calculate totals
        total_gb = total_size_bytes / (1024 * 1024 * 1024)
        missing_gb = missing_size / (1024 * 1024 * 1024)
        estimated_total_gb = (total_size_bytes + missing_size) / (1024 * 1024 * 1024)
        
        print()
        print("📈 CACHE STORAGE ANALYSIS:")
        print("=" * 40)
        print(f"Total videos found:           {len(ally_videos)}")
        print(f"Locally available:            {locally_available}")
        print(f"Need download from iCloud:    {needs_download}")
        print()
        print(f"Current local storage:        {total_gb:.2f} GB")
        print(f"iCloud storage (estimated):   {missing_gb:.2f} GB")
        print(f"TOTAL CACHE SIZE NEEDED:      {estimated_total_gb:.2f} GB")
        print()
        
        if estimated_total_gb > 10:
            print("⚠️  WARNING: Cache size would exceed 10 GB!")
        elif estimated_total_gb > 5:
            print("⚠️  CAUTION: Cache size would exceed 5 GB")
        else:
            print("✅ Cache size is reasonable")
        
        print()
        print("💡 RECOMMENDATIONS:")
        if needs_download > locally_available:
            print(f"- {needs_download} videos need to be downloaded from iCloud first")
            print("- Consider downloading videos manually before caching")
        
        if estimated_total_gb > 20:
            print("- Consider filtering videos by date range to reduce cache size")
            print("- Implement cache size limits and LRU eviction")
        
        print(f"- Cache directory: ~/.photo_slideshow_cache/videos/")
        print(f"- Each video will be cached permanently until manually deleted")
        
    except Exception as e:
        print(f"❌ Error analyzing videos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_ally_videos()
