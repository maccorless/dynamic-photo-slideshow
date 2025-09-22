#!/usr/bin/env python3
"""
Test 1: Minimal Rendering - Video only, no overlays
"""

import pygame
import time
from pyvidplayer2 import Video

pygame.init()

# Get screen dimensions
info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h

# Create fullscreen display
screen = pygame.display.set_mode(
    (screen_width, screen_height),
    pygame.FULLSCREEN | pygame.DOUBLEBUF
)
pygame.display.set_caption("Test 1: Minimal Rendering")

# Colors
BLACK = (0, 0, 0)

# Video setup
test_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/short_test_video.mov"
clock = pygame.time.Clock()

def resize_video_for_screen(video):
    vw, vh = video.original_size
    scale = min(screen_width / vw, screen_height / vh)
    new_w = int(vw * scale)
    new_h = int(vh * scale)
    video.resize((new_w, new_h))
    x = (screen_width - new_w) // 2
    y = (screen_height - new_h) // 2
    return (x, y)

print("=== Test 1: Minimal Rendering ===")
print("Video only, no overlays - watch for flickering")

try:
    video = Video(test_video)
    video.set_volume(0.3)
    video_pos = resize_video_for_screen(video)
    
    start_time = time.time()
    running = True
    
    while running and (time.time() - start_time) < 8 and video.active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
        
        # MINIMAL RENDERING - just video, no overlays
        screen.fill(BLACK)
        video.draw(screen, video_pos, force_draw=False)
        pygame.display.flip()
        clock.tick(30)
    
    video.close()
    print("Test 1 completed")
    
except Exception as e:
    print(f"Test 1 error: {e}")

pygame.quit()
