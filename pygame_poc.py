#!/usr/bin/env python3
"""
Pygame Proof of Concept for video playback with overlays.
Tests video playback and basic UI elements without touching existing codebase.
"""

import pygame
import cv2
import numpy as np
import time
import sys
import os
from threading import Thread
import queue

class PygameVideoPoC:
    def __init__(self):
        pygame.init()
        
        # Get screen dimensions
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        
        # Create fullscreen display
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("Pygame Video PoC")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        
        # Font for overlays
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
        # Video paths
        self.short_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/short_test_video.mov"
        self.long_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/long_test_video.mov"
        
        # Sample photo path (we'll create a test image)
        self.test_photo = None
        
        # State
        self.running = True
        self.current_video = None
        self.video_cap = None
        self.clock = pygame.time.Clock()
        
        print("Pygame PoC initialized")
        print(f"Screen: {self.screen_width}x{self.screen_height}")
        
    def load_video(self, video_path):
        """Load video using OpenCV."""
        if self.video_cap:
            self.video_cap.release()
            
        self.video_cap = cv2.VideoCapture(video_path)
        if not self.video_cap.isOpened():
            print(f"Failed to open video: {video_path}")
            return False
            
        # Get video properties
        fps = self.video_cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        print(f"Loaded video: {os.path.basename(video_path)}")
        print(f"FPS: {fps}, Frames: {frame_count}, Duration: {duration:.1f}s")
        
        return True
        
    def get_next_frame(self):
        """Get next video frame as pygame surface."""
        if not self.video_cap:
            return None
            
        ret, frame = self.video_cap.read()
        if not ret:
            return None
            
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Rotate frame to handle iPhone rotation
        # Videos rotated 90 degrees to the left of vertical need 270 degrees clockwise to correct
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        
        # Scale to fit screen while maintaining aspect ratio
        h, w = frame.shape[:2]
        scale = min(self.screen_width / w, self.screen_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        frame = cv2.resize(frame, (new_w, new_h))
        
        # Convert to pygame surface
        frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        
        return frame_surface
        
    def create_test_photo(self):
        """Create a test photo surface with some content."""
        photo_surface = pygame.Surface((800, 600))
        photo_surface.fill((50, 100, 150))  # Blue background
        
        # Add some text to make it look like a photo
        title_text = self.font.render("Test Photo", True, self.WHITE)
        subtitle_text = self.small_font.render("This simulates a photo in the slideshow", True, self.WHITE)
        
        # Center the text
        title_rect = title_text.get_rect(center=(400, 250))
        subtitle_rect = subtitle_text.get_rect(center=(400, 300))
        
        photo_surface.blit(title_text, title_rect)
        photo_surface.blit(subtitle_text, subtitle_rect)
        
        # Add some decorative elements
        pygame.draw.circle(photo_surface, self.WHITE, (400, 400), 50, 3)
        pygame.draw.rect(photo_surface, self.GREEN, (350, 450, 100, 50), 2)
        
        return photo_surface
        
    def display_photo(self, duration=5):
        """Display a test photo for specified duration."""
        photo_surface = self.create_test_photo()
        start_time = time.time()
        
        print(f"Displaying photo for {duration}s")
        
        while time.time() - start_time < duration and self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return False
                    elif event.key == pygame.K_SPACE:
                        return True  # Skip to next item
                        
            # Clear screen
            self.screen.fill(self.BLACK)
            
            # Center and draw photo
            photo_rect = photo_surface.get_rect()
            photo_rect.center = (self.screen_width // 2, self.screen_height // 2)
            self.screen.blit(photo_surface, photo_rect)
            
            # Draw overlays
            elapsed = time.time() - start_time
            remaining = max(0, duration - int(elapsed))
            self.draw_overlays(countdown=remaining)
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)
            
        return True
        
    def draw_overlays(self, countdown=None):
        """Draw UI overlays on screen."""
        # Countdown timer
        if countdown is not None:
            countdown_text = self.font.render(f"Next: {countdown}s", True, self.WHITE)
            countdown_rect = countdown_text.get_rect()
            countdown_rect.topright = (self.screen_width - 20, 20)
            self.screen.blit(countdown_text, countdown_rect)
            
        # Instructions
        instructions = [
            "ESC: Exit",
            "SPACE: Next video",
            "Arrow keys: Navigate"
        ]
        
        y_offset = self.screen_height - 100
        for instruction in instructions:
            text = self.small_font.render(instruction, True, self.WHITE)
            self.screen.blit(text, (20, y_offset))
            y_offset += 25
            
    def play_video(self, video_path):
        """Play video with overlays."""
        if not self.load_video(video_path):
            return False
            
        print(f"Playing: {os.path.basename(video_path)}")
        
        # Get video FPS for timing
        fps = self.video_cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1000 / fps if fps > 0 else 33  # Default to ~30fps
        
        start_time = time.time()
        frame_count = 0
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return False
                    elif event.key == pygame.K_SPACE:
                        return True  # Skip to next video
                        
            # Get next frame
            frame_surface = self.get_next_frame()
            if frame_surface is None:
                print("Video ended")
                return True
                
            # Clear screen
            self.screen.fill(self.BLACK)
            
            # Center and draw video frame
            frame_rect = frame_surface.get_rect()
            frame_rect.center = (self.screen_width // 2, self.screen_height // 2)
            self.screen.blit(frame_surface, frame_rect)
            
            # Draw overlays
            elapsed = time.time() - start_time
            remaining = max(0, 15 - int(elapsed))  # 15 second max
            self.draw_overlays(countdown=remaining)
            
            # Update display
            pygame.display.flip()
            
            # Control frame rate
            self.clock.tick(fps if fps > 0 else 30)
            frame_count += 1
            
        return False
        
    def show_message(self, message, duration=2):
        """Show a text message for specified duration."""
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return
                        
            # Clear screen
            self.screen.fill(self.BLACK)
            
            # Draw message
            text = self.font.render(message, True, self.WHITE)
            text_rect = text.get_rect()
            text_rect.center = (self.screen_width // 2, self.screen_height // 2)
            self.screen.blit(text, text_rect)
            
            # Draw overlays
            self.draw_overlays()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)
            
    def run(self):
        """Run the PoC demonstration with video->photo->video sequence."""
        try:
            self.show_message("Pygame Transition PoC Starting...", 2)
            
            if not self.running:
                return
                
            # Play short video
            self.show_message("1/3: Playing Short Video (8.5s)", 1)
            if not self.play_video(self.short_video):
                return
                
            if not self.running:
                return
                
            # Show photo
            self.show_message("2/3: Displaying Photo (5s)", 1)
            if not self.display_photo(duration=5):
                return
            
            if not self.running:
                return
                
            # Play long video  
            self.show_message("3/3: Playing Long Video (12.1s)", 1)
            if not self.play_video(self.long_video):
                return
                
            # Final message
            self.show_message("Video->Photo->Video transition complete!", 3)
            
        except Exception as e:
            print(f"Error in PoC: {e}")
            self.show_message(f"Error: {e}", 3)
            
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources."""
        if self.video_cap:
            self.video_cap.release()
        pygame.quit()
        print("PoC cleanup complete")

def main():
    print("=== Pygame Video PoC ===")
    print("This PoC tests video playback with overlays using pygame")
    print("Controls: ESC (exit), SPACE (skip video)")
    
    try:
        poc = PygameVideoPoC()
        poc.run()
    except KeyboardInterrupt:
        print("\nPoC interrupted by user")
    except Exception as e:
        print(f"PoC failed: {e}")

if __name__ == "__main__":
    main()
