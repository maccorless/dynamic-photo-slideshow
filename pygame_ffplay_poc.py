#!/usr/bin/env python3
"""
Pygame + FFplay PoC for seamless video playback without stretching.
Uses ffplay subprocess for video, pygame for photos and overlays.
"""

import pygame
import subprocess
import time
import sys
import os
import threading

class PygameFFplayPoC:
    def __init__(self):
        pygame.init()
        
        # Get screen dimensions
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        
        # Create fullscreen display
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("Pygame + FFplay PoC")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (50, 100, 150)
        
        # Font for overlays
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
        # Video paths
        self.short_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/short_test_video.mov"
        self.long_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/long_test_video.mov"
        
        # State
        self.running = True
        self.clock = pygame.time.Clock()
        self.video_process = None
        
        print("Pygame + FFplay PoC initialized")
        print(f"Screen: {self.screen_width}x{self.screen_height}")
        
    def create_test_photo(self):
        """Create a test photo surface with some content."""
        photo_surface = pygame.Surface((800, 600))
        photo_surface.fill(self.BLUE)
        
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
            "SPACE: Skip",
            "Using pygame + ffplay"
        ]
        
        y_offset = self.screen_height - 100
        for instruction in instructions:
            text = self.small_font.render(instruction, True, self.WHITE)
            self.screen.blit(text, (20, y_offset))
            y_offset += 25
            
    def play_video(self, video_path, max_duration=15):
        """Play video using ffplay subprocess while maintaining pygame control."""
        try:
            print(f"Playing video: {os.path.basename(video_path)}")
            
            # Hide pygame window temporarily
            pygame.display.iconify()
            
            # ffplay command with proper aspect ratio handling
            ffplay_cmd = [
                'ffplay',
                '-i', video_path,
                '-fs',  # Fullscreen
                '-autoexit',
                '-loglevel', 'quiet'
            ]
            
            print(f"Running: {' '.join(ffplay_cmd)}")
            
            # Start ffplay process
            self.video_process = subprocess.Popen(
                ffplay_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            start_time = time.time()
            
            # Monitor video playback
            while self.running:
                # Handle pygame events even during video
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        if self.video_process and self.video_process.poll() is None:
                            self.video_process.terminate()
                        return False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                            if self.video_process and self.video_process.poll() is None:
                                self.video_process.terminate()
                            return False
                        elif event.key == pygame.K_SPACE:
                            if self.video_process and self.video_process.poll() is None:
                                self.video_process.terminate()
                            return True  # Skip to next
                            
                # Check if video process is still running
                if self.video_process.poll() is not None:
                    print("Video ended naturally")
                    break
                    
                # Check duration limit
                elapsed = time.time() - start_time
                if elapsed > max_duration:
                    print(f"Video duration limit reached ({max_duration}s)")
                    if self.video_process and self.video_process.poll() is None:
                        self.video_process.terminate()
                    break
                    
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            # Restore pygame window
            pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
            
            return True
            
        except Exception as e:
            print(f"Error playing video: {e}")
            # Restore pygame window on error
            pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
            return False
            
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
            self.show_message("Pygame + FFplay PoC Starting...", 2)
            
            if not self.running:
                return
                
            # Play short video
            self.show_message("1/3: Playing Short Video (8.5s)", 1)
            if not self.play_video(self.short_video, max_duration=10):
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
            if not self.play_video(self.long_video, max_duration=15):
                return
                
            # Final message
            self.show_message("Pygame + FFplay transition complete!", 3)
            
        except Exception as e:
            print(f"Error in PoC: {e}")
            self.show_message(f"Error: {e}", 3)
            
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources."""
        if self.video_process and self.video_process.poll() is None:
            self.video_process.terminate()
        pygame.quit()
        print("Pygame + FFplay PoC cleanup complete")

def main():
    print("=== Pygame + FFplay PoC ===")
    print("This PoC uses ffplay for video (no stretching) and pygame for photos/UI")
    print("Controls: ESC (exit), SPACE (skip)")
    
    try:
        poc = PygameFFplayPoC()
        poc.run()
    except KeyboardInterrupt:
        print("\nPoC interrupted by user")
    except Exception as e:
        print(f"PoC failed: {e}")

if __name__ == "__main__":
    main()
