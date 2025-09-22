#!/usr/bin/env python3
"""
Quick automated flicker test - runs all display modes automatically
"""

import pygame
import time
import sys
import os
from pyvidplayer2 import Video

def test_display_mode(mode_name, setup_func, video_path, duration=5):
    """Test a single display mode and return timing metrics."""
    try:
        pygame.init()
        
        # Get screen dimensions
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        
        # Setup display with the specified configuration
        screen = setup_func(screen_width, screen_height)
        pygame.display.set_caption(f"Flicker Test: {mode_name}")
        
        # Load and setup video
        video = Video(video_path)
        video.set_volume(0.0)  # Mute for testing
        
        # Resize video
        vw, vh = video.original_size
        scale = min(screen_width / vw, screen_height / vh)
        new_w = int(vw * scale)
        new_h = int(vh * scale)
        video.resize((new_w, new_h))
        
        video_pos = ((screen_width - new_w) // 2, (screen_height - new_h) // 2)
        
        # Test playback and measure frame timing
        start_time = time.time()
        frame_times = []
        last_frame_time = start_time
        clock = pygame.time.Clock()
        
        print(f"Testing {mode_name}...")
        
        while (time.time() - start_time) < duration and video.active:
            current_time = time.time()
            frame_delta = current_time - last_frame_time
            if frame_delta > 0:  # Avoid division by zero
                frame_times.append(frame_delta)
            last_frame_time = current_time
            
            # Handle quit events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    break
            
            # Render frame
            screen.fill((0, 0, 0))
            video.draw(screen, video_pos, force_draw=False)
            pygame.display.flip()
            clock.tick(30)
        
        video.close()
        pygame.quit()
        
        # Calculate metrics
        if frame_times:
            avg_frame_time = sum(frame_times) / len(frame_times)
            frame_variance = sum((t - avg_frame_time) ** 2 for t in frame_times) / len(frame_times)
            max_frame_time = max(frame_times)
            min_frame_time = min(frame_times)
            
            return {
                'mode': mode_name,
                'avg_fps': 1 / avg_frame_time if avg_frame_time > 0 else 0,
                'variance': frame_variance,
                'max_frame_time': max_frame_time,
                'min_frame_time': min_frame_time,
                'consistency_score': 1 / (1 + frame_variance * 1000),  # Higher is better
                'success': True
            }
        else:
            return {'mode': mode_name, 'success': False, 'error': 'No frame data'}
            
    except Exception as e:
        try:
            pygame.quit()
        except:
            pass
        return {'mode': mode_name, 'success': False, 'error': str(e)}

def setup_default(width, height):
    """Original configuration with all flags."""
    flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
    return pygame.display.set_mode((width, height), flags, vsync=1)

def setup_no_hwsurface(width, height):
    """Remove HWSURFACE flag."""
    flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
    return pygame.display.set_mode((width, height), flags, vsync=1)

def setup_no_vsync(width, height):
    """Remove vsync."""
    flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
    return pygame.display.set_mode((width, height), flags)

def setup_software_only(width, height):
    """Software rendering only."""
    flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
    return pygame.display.set_mode((width, height), flags)

def setup_scaled_window(width, height):
    """Scaled window instead of fullscreen."""
    flags = pygame.SCALED | pygame.DOUBLEBUF
    return pygame.display.set_mode((width, height), flags, vsync=1)

def setup_basic_fullscreen(width, height):
    """Minimal flags."""
    return pygame.display.set_mode((width, height), pygame.FULLSCREEN)

def main():
    video_path = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/short_test_video.mov"
    
    if not os.path.exists(video_path):
        print(f"Error: Test video not found at {video_path}")
        return
    
    test_configs = [
        ("default", setup_default),
        ("no_hwsurface", setup_no_hwsurface),
        ("no_vsync", setup_no_vsync),
        ("software_only", setup_software_only),
        ("scaled_window", setup_scaled_window),
        ("basic_fullscreen", setup_basic_fullscreen),
    ]
    
    print("=== Quick Flicker Test ===")
    print("Testing display configurations automatically...\n")
    
    results = []
    
    for mode_name, setup_func in test_configs:
        result = test_display_mode(mode_name, setup_func, video_path, duration=3)
        results.append(result)
        
        if result['success']:
            print(f"✓ {mode_name}: {result['avg_fps']:.1f} FPS, consistency: {result['consistency_score']:.3f}")
        else:
            print(f"✗ {mode_name}: FAILED - {result.get('error', 'Unknown error')}")
        
        time.sleep(0.5)  # Brief pause between tests
    
    print("\n=== Results Summary ===")
    
    # Sort by consistency score (higher is better)
    successful_results = [r for r in results if r['success']]
    if successful_results:
        successful_results.sort(key=lambda x: x['consistency_score'], reverse=True)
        
        print("Ranked by frame timing consistency (best first):")
        for i, result in enumerate(successful_results, 1):
            variance_ms = result['variance'] * 1000
            print(f"{i}. {result['mode']}: {result['avg_fps']:.1f} FPS, "
                  f"variance: {variance_ms:.2f}ms², consistency: {result['consistency_score']:.3f}")
        
        best_mode = successful_results[0]
        print(f"\n🏆 RECOMMENDED: {best_mode['mode']}")
        print(f"   - Most consistent frame timing")
        print(f"   - Average FPS: {best_mode['avg_fps']:.1f}")
        print(f"   - Frame variance: {best_mode['variance']*1000:.2f}ms²")
        
        if best_mode['variance'] < 0.001:
            print("   - ✓ Low flickering risk")
        else:
            print("   - ⚠️  May still have some flickering")
    else:
        print("❌ All display modes failed!")
    
    print(f"\nTested {len(results)} configurations.")

if __name__ == "__main__":
    main()
