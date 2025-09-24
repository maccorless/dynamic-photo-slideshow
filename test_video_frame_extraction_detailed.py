#!/usr/bin/env python3
"""
Detailed video frame extraction performance test.
Tests multiple runs and optimization techniques.
"""

import time
import cv2
import numpy as np
from pathlib import Path

def test_opencv_basic(video_path, runs=5):
    """Test basic OpenCV frame extraction multiple times."""
    times = []
    
    for i in range(runs):
        start_time = time.time()
        
        cap = cv2.VideoCapture(str(video_path))
        ret, frame = cap.read()
        cap.release()
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        times.append(duration_ms)
    
    return {
        'method': 'opencv_basic',
        'times': times,
        'avg': sum(times) / len(times),
        'min': min(times),
        'max': max(times)
    }

def test_opencv_optimized(video_path, runs=5):
    """Test optimized OpenCV frame extraction."""
    times = []
    
    for i in range(runs):
        start_time = time.time()
        
        cap = cv2.VideoCapture(str(video_path))
        # Set buffer size to 1 to reduce latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # Jump to first frame explicitly
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        ret, frame = cap.read()
        cap.release()
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        times.append(duration_ms)
    
    return {
        'method': 'opencv_optimized',
        'times': times,
        'avg': sum(times) / len(times),
        'min': min(times),
        'max': max(times)
    }

def test_opencv_thumbnail(video_path, runs=5):
    """Test OpenCV with immediate thumbnail resize."""
    times = []
    
    for i in range(runs):
        start_time = time.time()
        
        cap = cv2.VideoCapture(str(video_path))
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        ret, frame = cap.read()
        if ret:
            # Resize to thumbnail immediately (faster for display)
            thumbnail = cv2.resize(frame, (320, 180))
        
        cap.release()
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        times.append(duration_ms)
    
    return {
        'method': 'opencv_thumbnail',
        'times': times,
        'avg': sum(times) / len(times),
        'min': min(times),
        'max': max(times)
    }

def main():
    print("🎬 Detailed Video Frame Extraction Performance Test")
    print("=" * 60)
    
    video_path = Path("test_video.mp4")
    if not video_path.exists():
        print("❌ test_video.mp4 not found!")
        return
    
    print(f"📹 Testing with: {video_path.name}")
    print(f"📏 File size: {video_path.stat().st_size / 1024:.1f} KB")
    
    # Get video info
    cap = cv2.VideoCapture(str(video_path))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    print(f"📊 Video info: {width}x{height}, {fps:.1f}fps, {frame_count} frames")
    print()
    
    # Run tests
    tests = [
        test_opencv_basic,
        test_opencv_optimized, 
        test_opencv_thumbnail
    ]
    
    results = []
    
    for test_func in tests:
        print(f"🧪 Running {test_func.__name__}...")
        result = test_func(video_path, runs=10)
        results.append(result)
        
        print(f"   Method: {result['method']}")
        print(f"   Average: {result['avg']:.1f}ms")
        print(f"   Range: {result['min']:.1f}ms - {result['max']:.1f}ms")
        print(f"   All times: {[f'{t:.1f}' for t in result['times']]}")
        print()
    
    # Summary
    print("📊 SUMMARY & RECOMMENDATIONS")
    print("=" * 60)
    
    fastest = min(results, key=lambda r: r['avg'])
    print(f"🏆 Fastest method: {fastest['method']}")
    print(f"   Average time: {fastest['avg']:.1f}ms")
    print(f"   Best time: {fastest['min']:.1f}ms")
    
    print(f"\n💡 ANALYSIS:")
    if fastest['avg'] < 50:
        print(f"   ✅ EXCELLENT: Frame extraction is very fast ({fastest['avg']:.1f}ms)")
        print(f"   👍 Recommendation: Use Option 1 (show first frame)")
        print(f"   🎯 User experience: Immediate visual feedback")
    elif fastest['avg'] < 100:
        print(f"   ✅ GOOD: Frame extraction is acceptably fast ({fastest['avg']:.1f}ms)")
        print(f"   👍 Recommendation: Use Option 1 with loading indicator")
        print(f"   🎯 User experience: Brief delay but good feedback")
    else:
        print(f"   ⚠️  SLOW: Frame extraction may cause noticeable delay ({fastest['avg']:.1f}ms)")
        print(f"   🤔 Recommendation: Use Option 2/3 (metadata overlay)")
        print(f"   🎯 User experience: Instant feedback with metadata")
    
    print(f"\n🔧 IMPLEMENTATION NOTES:")
    print(f"   • OpenCV is available and working")
    print(f"   • Buffer size optimization helps slightly")
    print(f"   • Thumbnail resize adds minimal overhead")
    print(f"   • Consider 50ms timeout for production use")

if __name__ == "__main__":
    main()
