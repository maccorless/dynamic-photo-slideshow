#!/usr/bin/env python3
"""
OpenCV + Pygame video test - alternative to pyvidplayer2 for flicker-free playback
"""

import pygame
import cv2
import numpy as np
import time
import sys
import os

class OpenCVVideoTest:
    def __init__(self):
        pygame.init()
        
        # Get screen dimensions
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        
        # Create display - try borderless windowed mode for best compatibility
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), 
            pygame.NOFRAME
        )
        pygame.display.set_caption("OpenCV Video Test")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        
        # Font for overlays
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
        # Video path
        self.test_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/short_test_video.mov"
        
        # State
        self.running = True
        self.clock = pygame.time.Clock()
        
        print("OpenCV Video Test initialized")
        print(f"Screen: {self.screen_width}x{self.screen_height}")
        
    def resize_frame_for_screen(self, frame):
        """Resize frame to fit screen while maintaining aspect ratio."""
        h, w = frame.shape[:2]
        
        # Calculate scale to fit screen
        scale = min(self.screen_width / w, self.screen_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize frame
        resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Calculate position to center
        x = (self.screen_width - new_w) // 2
        y = (self.screen_height - new_h) // 2
        
        return resized_frame, (x, y)
    
    def frame_to_pygame_surface(self, frame):
        """Convert OpenCV frame to pygame surface."""
        # OpenCV uses BGR, pygame uses RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Rotate 90 degrees to correct orientation
        frame_rgb = np.rot90(frame_rgb)
        # Convert to pygame surface
        return pygame.surfarray.make_surface(frame_rgb)
    
    def play_video_opencv(self, video_path, max_duration=8):
        """Play video using OpenCV for frame extraction and pygame for display."""
        try:
            print(f"Loading video: {os.path.basename(video_path)}")
            
            # Open video with OpenCV
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                print("Error: Could not open video")
                return False
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            print(f"Video FPS: {fps:.1f}, Duration: {duration:.1f}s, Frames: {frame_count}")
            
            start_time = time.time()
            frame_interval = 1.0 / fps if fps > 0 else 1.0 / 30
            
            # Pre-create surfaces to reduce allocations
            background_surface = pygame.Surface((self.screen_width, self.screen_height))
            
            while self.running and (time.time() - start_time) < max_duration:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        cap.release()
                        return False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                            cap.release()
                            return False
                        elif event.key == pygame.K_SPACE:
                            cap.release()
                            return True
                
                # Read frame from video
                ret, frame = cap.read()
                if not ret:
                    print("Video ended or error reading frame")
                    break
                
                # Resize frame for screen
                resized_frame, frame_pos = self.resize_frame_for_screen(frame)
                
                # Convert to pygame surface
                frame_surface = self.frame_to_pygame_surface(resized_frame)
                
                # Clear background
                background_surface.fill(self.BLACK)
                
                # Draw frame to background surface
                background_surface.blit(frame_surface, frame_pos)
                
                # Add overlays to background surface
                elapsed = time.time() - start_time
                remaining = max(0, max_duration - int(elapsed))
                
                countdown_text = self.font.render(f"OpenCV - {remaining}s", True, self.WHITE)
                background_surface.blit(countdown_text, (20, 20))
                
                fps_text = self.small_font.render(f"FPS: {fps:.1f}", True, self.WHITE)
                background_surface.blit(fps_text, (20, 70))
                
                # Single blit to screen
                self.screen.blit(background_surface, (0, 0))
                pygame.display.flip()
                
                # Frame timing - try to match video fps
                target_fps = min(30, fps) if fps > 0 else 30
                self.clock.tick(target_fps)
            
            cap.release()
            return True
            
        except Exception as e:
            print(f"Error playing video with OpenCV: {e}")
            return False
    
    def run_test(self):
        """Run the OpenCV video test."""
        try:
            print("\n=== OpenCV Video Test ===")
            print("Testing OpenCV frame extraction + pygame display...")
            
            # Show test info
            self.screen.fill(self.BLACK)
            info_text = self.font.render("OpenCV Video Test", True, self.WHITE)
            info_rect = info_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(info_text, info_rect)
            
            start_text = self.small_font.render("Starting in 2 seconds...", True, self.WHITE)
            start_rect = start_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
            self.screen.blit(start_text, start_rect)
            
            pygame.display.flip()
            time.sleep(2)
            
            # Run video test
            success = self.play_video_opencv(self.test_video)
            
            if success:
                print("✓ OpenCV video test completed")
                
                # Show completion message
                self.screen.fill(self.BLACK)
                complete_text = self.font.render("OpenCV Test Complete", True, self.WHITE)
                complete_rect = complete_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(complete_text, complete_rect)
                
                result_text = self.small_font.render("Did this reduce flickering?", True, self.WHITE)
                result_rect = result_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
                self.screen.blit(result_text, result_rect)
                
                pygame.display.flip()
                time.sleep(3)
            else:
                print("✗ OpenCV video test failed")
            
        except Exception as e:
            print(f"Test failed: {e}")
        finally:
            pygame.quit()

def main():
    print("=== OpenCV Video Test ===")
    print("This test uses OpenCV for video frame extraction instead of pyvidplayer2")
    print("Benefits:")
    print("- Direct control over frame timing")
    print("- No third-party video library interference")
    print("- Manual frame-by-frame rendering")
    print("- Consistent pygame surface operations")
    print()
    
    try:
        test = OpenCVVideoTest()
        test.run_test()
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main()
