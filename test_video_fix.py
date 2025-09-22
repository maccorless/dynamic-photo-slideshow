#!/usr/bin/env python3
"""
Test comprehensive video flickering fixes with multiple approaches
"""

import pygame
import time
import sys
import os
from pyvidplayer2 import Video

class VideoFlickerFix:
    def __init__(self):
        pygame.init()
        
        # Get screen dimensions
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        
        # Try multiple display configurations to eliminate flickering
        self.screen = self.setup_anti_flicker_display()
        pygame.display.set_caption("Video Flicker Fix Test")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        
        # Font for overlays
        self.font = pygame.font.Font(None, 48)
        
        # Video path
        self.test_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/short_test_video.mov"
        
        # State
        self.running = True
        self.clock = pygame.time.Clock()
        
        print("Video Flicker Fix Test initialized")
        print(f"Screen: {self.screen_width}x{self.screen_height}")
        
    def setup_anti_flicker_display(self):
        """Setup display with most aggressive anti-flicker configuration."""
        # Try different approaches in order of preference
        
        try:
            # Approach 1: Windowed borderless (most compatible with macOS)
            print("Trying windowed borderless mode...")
            return pygame.display.set_mode((self.screen_width, self.screen_height), pygame.NOFRAME)
        except Exception as e:
            print(f"Borderless failed: {e}")
            
        try:
            # Approach 2: Basic fullscreen without any flags
            print("Trying basic fullscreen...")
            return pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        except Exception as e:
            print(f"Basic fullscreen failed: {e}")
            
        # Fallback: Regular window
        print("Using windowed mode as fallback...")
        return pygame.display.set_mode((1280, 720))
    
    def resize_video_for_screen(self, video):
        """Aspect-correct fit with letterboxing."""
        vw, vh = video.original_size
        
        scale = min(self.screen_width / vw, self.screen_height / vh)
        new_w = int(vw * scale)
        new_h = int(vh * scale)
        
        video.resize((new_w, new_h))
        
        x = (self.screen_width - new_w) // 2
        y = (self.screen_height - new_h) // 2
        return (x, y)
    
    def play_video_method_1(self, video_path, duration=6):
        """Method 1: Persistent surface + single blit."""
        print("Testing Method 1: Persistent surface rendering...")
        
        try:
            video = Video(video_path)
            video.set_volume(0.3)
            video_pos = self.resize_video_for_screen(video)
            
            start_time = time.time()
            # Create persistent surface to reduce allocations
            video_surface = pygame.Surface((self.screen_width, self.screen_height))
            
            while self.running and (time.time() - start_time) < duration and video.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        video.close()
                        return False
                
                # Render to persistent surface first
                video_surface.fill(self.BLACK)
                video.draw(video_surface, video_pos, force_draw=True)
                
                # Add overlay
                elapsed = time.time() - start_time
                remaining = max(0, duration - int(elapsed))
                text = self.font.render(f"Method 1 - {remaining}s", True, self.WHITE)
                video_surface.blit(text, (20, 20))
                
                # Single blit to screen
                self.screen.blit(video_surface, (0, 0))
                pygame.display.flip()
                self.clock.tick(15)  # Very conservative
            
            video.close()
            return True
            
        except Exception as e:
            print(f"Method 1 error: {e}")
            return False
    
    def play_video_method_2(self, video_path, duration=6):
        """Method 2: Direct rendering with pygame.display.update()."""
        print("Testing Method 2: Direct rendering with update()...")
        
        try:
            video = Video(video_path)
            video.set_volume(0.3)
            video_pos = self.resize_video_for_screen(video)
            
            start_time = time.time()
            
            while self.running and (time.time() - start_time) < duration and video.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        video.close()
                        return False
                
                # Direct rendering
                self.screen.fill(self.BLACK)
                video.draw(self.screen, video_pos, force_draw=True)
                
                # Add overlay
                elapsed = time.time() - start_time
                remaining = max(0, duration - int(elapsed))
                text = self.font.render(f"Method 2 - {remaining}s", True, self.WHITE)
                self.screen.blit(text, (20, 20))
                
                # Use update() instead of flip()
                pygame.display.update()
                self.clock.tick(12)  # Even more conservative
            
            video.close()
            return True
            
        except Exception as e:
            print(f"Method 2 error: {e}")
            return False
    
    def play_video_method_3(self, video_path, duration=6):
        """Method 3: Manual frame extraction and display."""
        print("Testing Method 3: Manual frame control...")
        
        try:
            video = Video(video_path)
            video.set_volume(0.3)
            video_pos = self.resize_video_for_screen(video)
            
            start_time = time.time()
            frame_count = 0
            
            while self.running and (time.time() - start_time) < duration and video.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        video.close()
                        return False
                
                # Manual timing control
                current_time = time.time() - start_time
                target_frame = int(current_time * 10)  # 10fps target
                
                if frame_count <= target_frame:
                    self.screen.fill(self.BLACK)
                    video.draw(self.screen, video_pos, force_draw=True)
                    
                    # Add overlay
                    remaining = max(0, duration - int(current_time))
                    text = self.font.render(f"Method 3 - {remaining}s", True, self.WHITE)
                    self.screen.blit(text, (20, 20))
                    
                    pygame.display.flip()
                    frame_count += 1
                
                time.sleep(0.01)  # Small sleep to prevent busy waiting
            
            video.close()
            return True
            
        except Exception as e:
            print(f"Method 3 error: {e}")
            return False
    
    def run_test(self):
        """Run all anti-flicker methods."""
        try:
            print("\n=== Video Flicker Fix Test Suite ===")
            
            methods = [
                ("Persistent Surface", self.play_video_method_1),
                ("Direct + Update", self.play_video_method_2),
                ("Manual Timing", self.play_video_method_3)
            ]
            
            for i, (name, method) in enumerate(methods, 1):
                print(f"\n--- Test {i}/3: {name} ---")
                
                # Show method info
                self.screen.fill(self.BLACK)
                info_text = self.font.render(f"Testing: {name}", True, self.WHITE)
                info_rect = info_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(info_text, info_rect)
                
                start_text = pygame.font.Font(None, 24).render("Starting in 2 seconds...", True, self.WHITE)
                start_rect = start_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
                self.screen.blit(start_text, start_rect)
                
                pygame.display.flip()
                time.sleep(2)
                
                # Run method
                success = method(self.test_video)
                
                if success:
                    print(f"✓ {name} completed")
                else:
                    print(f"✗ {name} failed")
                
                if i < len(methods):
                    time.sleep(1)  # Brief pause between methods
            
            print("\n=== All Methods Tested ===")
            print("Which method showed the least flickering?")
            
        except Exception as e:
            print(f"Test suite failed: {e}")
        finally:
            pygame.quit()

def main():
    print("=== Video Flicker Fix Test Suite ===")
    print("This will test 3 different anti-flickering approaches:")
    print("1. Persistent Surface: Render to intermediate surface first")
    print("2. Direct + Update: Direct rendering with pygame.display.update()")
    print("3. Manual Timing: Manual frame rate control at 10fps")
    print()
    print("Watch each method carefully for flickering differences.")
    print()
    
    try:
        test = VideoFlickerFix()
        test.run_test()
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main()
