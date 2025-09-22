#!/usr/bin/env python3
"""
PyVidPlayer2 Flicker Debug - Systematic approach to identify and fix flickering
"""

import pygame
import time
import sys
import os
from pyvidplayer2 import Video

class FlickerDebugger:
    def __init__(self):
        pygame.init()
        
        # Get screen dimensions
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        
        # Start with basic fullscreen configuration
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.FULLSCREEN | pygame.DOUBLEBUF
        )
        pygame.display.set_caption("PyVidPlayer2 Flicker Debug")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        
        # Font
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
        # Video path
        self.test_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/short_test_video.mov"
        
        # State
        self.running = True
        self.clock = pygame.time.Clock()
        
        print("Flicker Debugger initialized")
        print(f"Screen: {self.screen_width}x{self.screen_height}")
        
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
    
    def test_minimal_rendering(self, video_path, duration=5):
        """Test 1: Minimal rendering - video only, no overlays."""
        print("Test 1: Minimal rendering (video only)")
        
        try:
            video = Video(video_path)
            video.set_volume(0.2)
            video_pos = self.resize_video_for_screen(video)
            
            start_time = time.time()
            
            while self.running and (time.time() - start_time) < duration and video.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        video.close()
                        return False
                
                # Minimal rendering - just video, no overlays
                self.screen.fill(self.BLACK)
                video.draw(self.screen, video_pos, force_draw=False)
                pygame.display.flip()
                self.clock.tick(30)
            
            video.close()
            return True
            
        except Exception as e:
            print(f"Test 1 error: {e}")
            return False
    
    def test_no_clear_screen(self, video_path, duration=5):
        """Test 2: No screen clearing between frames."""
        print("Test 2: No screen clearing")
        
        try:
            video = Video(video_path)
            video.set_volume(0.2)
            video_pos = self.resize_video_for_screen(video)
            
            start_time = time.time()
            
            # Clear screen once at start
            self.screen.fill(self.BLACK)
            
            while self.running and (time.time() - start_time) < duration and video.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        video.close()
                        return False
                
                # Don't clear screen - just draw video over existing content
                video.draw(self.screen, video_pos, force_draw=False)
                pygame.display.flip()
                self.clock.tick(30)
            
            video.close()
            return True
            
        except Exception as e:
            print(f"Test 2 error: {e}")
            return False
    
    def test_different_fps(self, video_path, duration=5):
        """Test 3: Different frame rates to isolate timing issues."""
        print("Test 3: Lower frame rate (15fps)")
        
        try:
            video = Video(video_path)
            video.set_volume(0.2)
            video_pos = self.resize_video_for_screen(video)
            
            start_time = time.time()
            
            while self.running and (time.time() - start_time) < duration and video.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        video.close()
                        return False
                
                self.screen.fill(self.BLACK)
                video.draw(self.screen, video_pos, force_draw=False)
                
                # Add simple overlay to test if overlays cause flickering
                elapsed = time.time() - start_time
                remaining = max(0, duration - int(elapsed))
                text = self.font.render(f"15fps - {remaining}s", True, self.WHITE)
                self.screen.blit(text, (20, 20))
                
                pygame.display.flip()
                self.clock.tick(15)  # Much lower frame rate
            
            video.close()
            return True
            
        except Exception as e:
            print(f"Test 3 error: {e}")
            return False
    
    def test_force_draw_true(self, video_path, duration=5):
        """Test 4: Force draw = True to ensure consistent frame updates."""
        print("Test 4: force_draw=True")
        
        try:
            video = Video(video_path)
            video.set_volume(0.2)
            video_pos = self.resize_video_for_screen(video)
            
            start_time = time.time()
            
            while self.running and (time.time() - start_time) < duration and video.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        video.close()
                        return False
                
                self.screen.fill(self.BLACK)
                video.draw(self.screen, video_pos, force_draw=True)  # Force every frame
                
                elapsed = time.time() - start_time
                remaining = max(0, duration - int(elapsed))
                text = self.font.render(f"Force - {remaining}s", True, self.WHITE)
                self.screen.blit(text, (20, 20))
                
                pygame.display.flip()
                self.clock.tick(30)
            
            video.close()
            return True
            
        except Exception as e:
            print(f"Test 4 error: {e}")
            return False
    
    def test_display_update_instead_flip(self, video_path, duration=5):
        """Test 5: Use pygame.display.update() instead of flip()."""
        print("Test 5: display.update() instead of flip()")
        
        try:
            video = Video(video_path)
            video.set_volume(0.2)
            video_pos = self.resize_video_for_screen(video)
            
            start_time = time.time()
            
            while self.running and (time.time() - start_time) < duration and video.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        video.close()
                        return False
                
                self.screen.fill(self.BLACK)
                video.draw(self.screen, video_pos, force_draw=False)
                
                elapsed = time.time() - start_time
                remaining = max(0, duration - int(elapsed))
                text = self.font.render(f"Update - {remaining}s", True, self.WHITE)
                self.screen.blit(text, (20, 20))
                
                pygame.display.update()  # Use update() instead of flip()
                self.clock.tick(30)
            
            video.close()
            return True
            
        except Exception as e:
            print(f"Test 5 error: {e}")
            return False
    
    def run_debug_tests(self):
        """Run all flicker debug tests."""
        tests = [
            ("Minimal Rendering", self.test_minimal_rendering),
            ("No Screen Clear", self.test_no_clear_screen),
            ("Lower FPS (15)", self.test_different_fps),
            ("Force Draw True", self.test_force_draw_true),
            ("Update vs Flip", self.test_display_update_instead_flip)
        ]
        
        print("\n=== PyVidPlayer2 Flicker Debug Tests ===")
        print("Watch each test carefully for flickering patterns")
        print("Note which tests show more or less flickering\n")
        
        for i, (name, test_func) in enumerate(tests, 1):
            print(f"--- Test {i}/5: {name} ---")
            
            # Show test info
            self.screen.fill(self.BLACK)
            info_text = self.font.render(f"Test {i}: {name}", True, self.WHITE)
            info_rect = info_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(info_text, info_rect)
            
            start_text = self.small_font.render("Starting in 2 seconds...", True, self.WHITE)
            start_rect = start_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
            self.screen.blit(start_text, start_rect)
            
            pygame.display.flip()
            time.sleep(2)
            
            # Run test
            success = test_func(self.test_video)
            
            if success:
                print(f"✓ {name} completed")
            else:
                print(f"✗ {name} failed")
            
            if i < len(tests):
                time.sleep(1)
        
        print("\n=== Debug Tests Complete ===")
        print("Which test showed the least flickering?")
        print("This will help identify the specific cause.")
        
        pygame.quit()

def main():
    print("=== PyVidPlayer2 Flicker Debug ===")
    print("This will run 5 systematic tests to isolate the flickering cause:")
    print("1. Minimal rendering (video only)")
    print("2. No screen clearing")
    print("3. Lower frame rate (15fps)")
    print("4. Force draw every frame")
    print("5. display.update() vs flip()")
    print()
    
    try:
        debugger = FlickerDebugger()
        debugger.run_debug_tests()
    except Exception as e:
        print(f"Debug failed: {e}")

if __name__ == "__main__":
    main()
