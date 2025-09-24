#!/usr/bin/env python3
"""
Quick prototype to test video frame extraction performance.
Tests how fast we can extract the first frame from various video formats.
"""

import time
import cv2
import os
import sys
from pathlib import Path

def test_frame_extraction_opencv(video_path):
    """Test frame extraction using OpenCV."""
    start_time = time.time()
    
    try:
        # Open video file
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return None, f"Could not open video: {video_path}"
        
        # Read first frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None, "Could not read first frame"
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        return {
            'success': True,
            'duration_ms': duration_ms,
            'frame_shape': frame.shape,
            'method': 'opencv'
        }, None
        
    except Exception as e:
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        return None, f"OpenCV error after {duration_ms:.1f}ms: {e}"

def test_frame_extraction_moviepy(video_path):
    """Test frame extraction using MoviePy."""
    start_time = time.time()
    
    try:
        from moviepy.editor import VideoFileClip
        
        # Open video file
        clip = VideoFileClip(str(video_path))
        
        # Get first frame (at t=0)
        frame = clip.get_frame(0)
        clip.close()
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        return {
            'success': True,
            'duration_ms': duration_ms,
            'frame_shape': frame.shape,
            'method': 'moviepy'
        }, None
        
    except Exception as e:
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        return None, f"MoviePy error after {duration_ms:.1f}ms: {e}"

def find_test_videos():
    """Find video files to test with."""
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.m4v'}
    test_videos = []
    
    # First check for our generated test video
    test_video_path = Path("test_video.mp4")
    if test_video_path.exists():
        test_videos.append(test_video_path)
    
    # Look in common video directories
    search_paths = [
        Path.home() / "Movies",
        Path.home() / "Desktop", 
        Path.home() / "Downloads",
        Path("/System/Library/CoreServices/Applications/DVD Player.app/Contents/Resources"),  # macOS sample videos
        Path("/usr/share/pixmaps"),  # Linux sample videos
    ]
    
    for search_path in search_paths:
        if search_path.exists():
            for file_path in search_path.rglob("*"):
                if file_path.suffix.lower() in video_extensions and file_path.is_file():
                    # Limit file size to reasonable test videos (< 100MB)
                    try:
                        if file_path.stat().st_size < 100 * 1024 * 1024:
                            test_videos.append(file_path)
                            if len(test_videos) >= 5:  # Limit to 5 test videos
                                break
                    except:
                        continue
        if len(test_videos) >= 5:
            break
    
    return test_videos

def main():
    print("🎬 Video Frame Extraction Performance Test")
    print("=" * 50)
    
    # Find test videos
    test_videos = find_test_videos()
    
    if not test_videos:
        print("❌ No test videos found!")
        print("Please place a video file in ~/Movies, ~/Desktop, or ~/Downloads")
        return
    
    print(f"📹 Found {len(test_videos)} test videos:")
    for i, video in enumerate(test_videos, 1):
        size_mb = video.stat().st_size / (1024 * 1024)
        print(f"  {i}. {video.name} ({size_mb:.1f} MB)")
    
    print("\n🧪 Testing frame extraction methods...")
    print("-" * 50)
    
    results = []
    
    for video_path in test_videos:
        print(f"\n📹 Testing: {video_path.name}")
        
        # Test OpenCV
        print("  🔍 OpenCV method...")
        result, error = test_frame_extraction_opencv(video_path)
        if result:
            print(f"    ✅ Success: {result['duration_ms']:.1f}ms, frame: {result['frame_shape']}")
            results.append(result)
        else:
            print(f"    ❌ Failed: {error}")
        
        # Test MoviePy
        print("  🔍 MoviePy method...")
        result, error = test_frame_extraction_moviepy(video_path)
        if result:
            print(f"    ✅ Success: {result['duration_ms']:.1f}ms, frame: {result['frame_shape']}")
            results.append(result)
        else:
            print(f"    ❌ Failed: {error}")
    
    # Summary
    print("\n📊 PERFORMANCE SUMMARY")
    print("=" * 50)
    
    if results:
        opencv_results = [r for r in results if r['method'] == 'opencv']
        moviepy_results = [r for r in results if r['method'] == 'moviepy']
        
        if opencv_results:
            avg_opencv = sum(r['duration_ms'] for r in opencv_results) / len(opencv_results)
            min_opencv = min(r['duration_ms'] for r in opencv_results)
            max_opencv = max(r['duration_ms'] for r in opencv_results)
            print(f"🔍 OpenCV: {len(opencv_results)} tests")
            print(f"   Average: {avg_opencv:.1f}ms")
            print(f"   Range: {min_opencv:.1f}ms - {max_opencv:.1f}ms")
        
        if moviepy_results:
            avg_moviepy = sum(r['duration_ms'] for r in moviepy_results) / len(moviepy_results)
            min_moviepy = min(r['duration_ms'] for r in moviepy_results)
            max_moviepy = max(r['duration_ms'] for r in moviepy_results)
            print(f"🎬 MoviePy: {len(moviepy_results)} tests")
            print(f"   Average: {avg_moviepy:.1f}ms")
            print(f"   Range: {min_moviepy:.1f}ms - {max_moviepy:.1f}ms")
        
        # Recommendation
        all_times = [r['duration_ms'] for r in results]
        avg_time = sum(all_times) / len(all_times)
        
        print(f"\n💡 RECOMMENDATION:")
        if avg_time < 100:
            print(f"   ✅ Frame extraction is FAST ({avg_time:.1f}ms avg)")
            print(f"   👍 Option 1 (show first frame) is viable!")
        elif avg_time < 500:
            print(f"   ⚠️  Frame extraction is MODERATE ({avg_time:.1f}ms avg)")
            print(f"   🤔 Option 5 (hybrid with timeout) recommended")
        else:
            print(f"   ❌ Frame extraction is SLOW ({avg_time:.1f}ms avg)")
            print(f"   👎 Option 2/3 (metadata overlay) recommended")
    
    else:
        print("❌ No successful extractions - recommend metadata overlay approach")

if __name__ == "__main__":
    main()
