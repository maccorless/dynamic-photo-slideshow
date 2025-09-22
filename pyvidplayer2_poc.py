#!/usr/bin/env python3
"""
PyVidPlayer2 PoC for seamless video playback with audio and rotation fixes.
Tests the pyvidplayer2 library for video->photo->video transitions.
"""

import pygame
from pyvidplayer2 import Video
import time
import sys
import os

class PyVidPlayer2PoC:
    def __init__(self):
        pygame.init()
        
        # Get screen dimensions
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        
        # Create fullscreen display with double buffering
        flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            flags
        )
        pygame.display.set_caption("PyVidPlayer2 PoC")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (50, 100, 150)
        
        # Font for overlays
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
        # Pre-render instruction surfaces to reduce per-frame work
        self.instructions_surfaces = [
            self.small_font.render("ESC: Exit", True, self.WHITE),
            self.small_font.render("SPACE: Skip", True, self.WHITE),
            self.small_font.render("Using pyvidplayer2 library", True, self.WHITE),
        ]
        
        # Video paths
        self.short_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/short_test_video.mov"
        self.long_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/long_test_video.mov"
        
        # State
        self.running = True
        self.clock = pygame.time.Clock()
        
        print("PyVidPlayer2 PoC initialized")
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
        # Only update countdown text when it actually changes (not every frame)
        if countdown is not None and (not hasattr(self, '_last_countdown') or self._last_countdown != countdown):
            self._countdown_text = self.font.render(f"Next: {countdown}s", True, self.WHITE)
            self._countdown_rect = self._countdown_text.get_rect(topright=(self.screen_width - 20, 20))
            self._last_countdown = countdown
        
        # Draw cached countdown text
        if countdown is not None and hasattr(self, '_countdown_text'):
            self.screen.blit(self._countdown_text, self._countdown_rect)
            
        # Pre-rendered instruction surfaces
        y_offset = self.screen_height - 100
        for surf in self.instructions_surfaces:
            self.screen.blit(surf, (20, y_offset))
            y_offset += 25
            
    def rotate_surface_90_clockwise(self, surface):
        """Rotate a pygame surface 90 degrees clockwise."""
        return pygame.transform.rotate(surface, -90)
        
    def resize_video_for_screen(self, video):
        """Aspect-correct fit with letterboxing (no stretching)."""
        vw, vh = video.original_size  # actual decoded frame size

        scale = min(self.screen_width / vw, self.screen_height / vh)
        new_w = int(vw * scale)
        new_h = int(vh * scale)

        video.resize((new_w, new_h))

        x = (self.screen_width - new_w) // 2
        y = (self.screen_height - new_h) // 2
        return (x, y)
            
            
    def play_video(self, video_path, max_duration=15):
        """Play video using pyvidplayer2 library with rotation fix."""
        try:
            print(f"Loading video: {os.path.basename(video_path)}")
            
            # Load video
            video = Video(video_path)
            video.set_volume(1.0)  # Ensure audio is enabled
            
            print(f"Playing: {os.path.basename(video_path)}")
            print(f"Video properties: {video.original_size}, duration: {video.duration:.1f}s")
            
            # Resize and position video for correct display
            video_pos = self.resize_video_for_screen(video)
            
            start_time = time.time()
            
            while self.running:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        video.close()
                        return False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                            video.close()
                            return False
                        elif event.key == pygame.K_SPACE:
                            video.close()
                            return True  # Skip to next
                            
                # Check if video is still playing
                if not video.active:
                    print("Video ended naturally")
                    break
                    
                # Check duration limit
                elapsed = time.time() - start_time
                if elapsed > max_duration:
                    print(f"Video duration limit reached ({max_duration}s)")
                    video.close()
                    break
                    
                # Clear screen
                self.screen.fill(self.BLACK)
                
                # Use library's draw method for proper video playback timing
                video.draw(self.screen, video_pos, force_draw=False)
                
                # Draw overlays
                remaining = max(0, max_duration - int(elapsed))
                self.draw_overlays(countdown=remaining)
                
                # Update display
                pygame.display.flip()
                # Use video fps if available, otherwise 30Hz
                fps = min(30, int(getattr(video, "fps", 30)) or 30)
                self.clock.tick(fps)
                
            video.close()
            return True
            
        except Exception as e:
            print(f"Error playing video: {e}")
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
            self.show_message("PyVidPlayer2 PoC Starting...", 2)
            
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
            self.show_message("PyVidPlayer2 transition complete!", 3)
            
        except Exception as e:
            print(f"Error in PoC: {e}")
            self.show_message(f"Error: {e}", 3)
            
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources."""
        pygame.quit()
        print("PyVidPlayer2 PoC cleanup complete")

def main():
    print("=== PyVidPlayer2 PoC ===")
    print("This PoC tests video playback with audio and rotation fixes")
    print("Controls: ESC (exit), SPACE (skip)")
    
    try:
        poc = PyVidPlayer2PoC()
        poc.run()
    except KeyboardInterrupt:
        print("\nPoC interrupted by user")
    except Exception as e:
        print(f"PoC failed: {e}")

if __name__ == "__main__":
    main()
