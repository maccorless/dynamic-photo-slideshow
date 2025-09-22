#!/usr/bin/env python3
"""
PyVidPlayer2 Anti-Flicker Test - Multiple display configurations to eliminate flickering
"""

import pygame
import time
import sys
import os
from pyvidplayer2 import Video

class AntiFlickerTest:
    def __init__(self, display_mode="default"):
        pygame.init()
        
        # Get screen dimensions
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        
        self.display_mode = display_mode
        self.screen = self.setup_display(display_mode)
        pygame.display.set_caption(f"Anti-Flicker Test - Mode: {display_mode}")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        
        # Font for overlays
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
        # Pre-render instruction surfaces
        self.instructions_surfaces = [
            self.small_font.render("ESC: Exit", True, self.WHITE),
            self.small_font.render("SPACE: Skip", True, self.WHITE),
            self.small_font.render(f"Mode: {display_mode}", True, self.WHITE),
        ]
        
        # Video path
        self.test_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/short_test_video.mov"
        
        # State
        self.running = True
        self.clock = pygame.time.Clock()
        
        print(f"Anti-Flicker Test initialized - Mode: {display_mode}")
        print(f"Screen: {self.screen_width}x{self.screen_height}")
        
    def setup_display(self, mode):
        """Setup display with different anti-flicker configurations."""
        if mode == "default":
            # Original configuration with all flags
            flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            return pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                flags,
                vsync=1
            )
            
        elif mode == "no_hwsurface":
            # Remove HWSURFACE flag (software rendering)
            flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
            return pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                flags,
                vsync=1
            )
            
        elif mode == "no_vsync":
            # Remove vsync
            flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            return pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                flags
            )
            
        elif mode == "software_only":
            # Software rendering, no hardware acceleration
            flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
            return pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                flags
            )
            
        elif mode == "scaled_window":
            # Use pygame.SCALED instead of true fullscreen
            flags = pygame.SCALED | pygame.DOUBLEBUF
            return pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                flags,
                vsync=1
            )
            
        elif mode == "basic_fullscreen":
            # Minimal flags
            return pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                pygame.FULLSCREEN
            )
            
        else:
            raise ValueError(f"Unknown display mode: {mode}")
    
    def resize_video_for_screen(self, video):
        """Aspect-correct fit with letterboxing (no stretching)."""
        vw, vh = video.original_size
        
        scale = min(self.screen_width / vw, self.screen_height / vh)
        new_w = int(vw * scale)
        new_h = int(vh * scale)
        
        video.resize((new_w, new_h))
        
        x = (self.screen_width - new_w) // 2
        y = (self.screen_height - new_h) // 2
        return (x, y)
    
    def draw_overlays(self, countdown=None, fps_actual=None):
        """Draw UI overlays on screen."""
        # Countdown timer
        if countdown is not None:
            countdown_text = self.font.render(f"Next: {countdown}s", True, self.WHITE)
            countdown_rect = countdown_text.get_rect(topright=(self.screen_width - 20, 20))
            self.screen.blit(countdown_text, countdown_rect)
            
        # FPS display
        if fps_actual is not None:
            fps_text = self.small_font.render(f"FPS: {fps_actual:.1f}", True, self.WHITE)
            fps_rect = fps_text.get_rect(topleft=(20, 20))
            self.screen.blit(fps_text, fps_rect)
        
        # Pre-rendered instruction surfaces
        y_offset = self.screen_height - 100
        for surf in self.instructions_surfaces:
            self.screen.blit(surf, (20, y_offset))
            y_offset += 25
    
    def play_video_with_timing_analysis(self, video_path, duration=10):
        """Play video with frame timing analysis to detect flickering patterns."""
        try:
            print(f"Loading video: {os.path.basename(video_path)}")
            
            video = Video(video_path)
            video.set_volume(0.5)  # Reduce volume for testing
            
            print(f"Video properties: {video.original_size}, duration: {video.duration:.1f}s")
            
            video_pos = self.resize_video_for_screen(video)
            
            start_time = time.time()
            frame_times = []
            last_frame_time = start_time
            
            while self.running and (time.time() - start_time) < duration:
                current_time = time.time()
                frame_delta = current_time - last_frame_time
                frame_times.append(frame_delta)
                last_frame_time = current_time
                
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
                            return True
                
                # Check if video is still playing
                if not video.active:
                    print("Video ended naturally")
                    break
                
                # Clear screen with specific method based on display mode
                if self.display_mode in ["software_only", "no_hwsurface"]:
                    # For software rendering, use fill
                    self.screen.fill(self.BLACK)
                else:
                    # For hardware rendering, try lock/unlock pattern
                    self.screen.fill(self.BLACK)
                
                # Draw video
                video.draw(self.screen, video_pos, force_draw=False)
                
                # Draw overlays with FPS info
                elapsed = time.time() - start_time
                remaining = max(0, duration - int(elapsed))
                current_fps = 1.0 / frame_delta if frame_delta > 0 else 0
                self.draw_overlays(countdown=remaining, fps_actual=current_fps)
                
                # Update display with mode-specific method
                if self.display_mode == "scaled_window":
                    pygame.display.update()
                else:
                    pygame.display.flip()
                
                # Timing strategy based on mode
                if self.display_mode in ["no_vsync", "basic_fullscreen"]:
                    # Manual frame rate limiting
                    target_fps = min(30, int(getattr(video, "fps", 30)) or 30)
                    self.clock.tick(target_fps)
                elif self.display_mode == "software_only":
                    # Slower frame rate for software rendering
                    self.clock.tick(24)
                else:
                    # Use video fps with vsync
                    fps = min(60, int(getattr(video, "fps", 60)) or 60)
                    self.clock.tick(fps)
            
            video.close()
            
            # Analyze frame timing
            if frame_times:
                avg_frame_time = sum(frame_times) / len(frame_times)
                max_frame_time = max(frame_times)
                min_frame_time = min(frame_times)
                frame_variance = sum((t - avg_frame_time) ** 2 for t in frame_times) / len(frame_times)
                
                print(f"\n=== Frame Timing Analysis ===")
                print(f"Average frame time: {avg_frame_time*1000:.2f}ms ({1/avg_frame_time:.1f} FPS)")
                print(f"Min frame time: {min_frame_time*1000:.2f}ms")
                print(f"Max frame time: {max_frame_time*1000:.2f}ms")
                print(f"Frame variance: {frame_variance*1000:.2f}ms²")
                print(f"Timing consistency: {'GOOD' if frame_variance < 0.001 else 'POOR - LIKELY FLICKERING'}")
            
            return True
            
        except Exception as e:
            print(f"Error playing video: {e}")
            return False
    
    def run_test(self):
        """Run the anti-flicker test."""
        try:
            print(f"\n=== Testing Display Mode: {self.display_mode} ===")
            
            # Show test info
            self.screen.fill(self.BLACK)
            info_text = self.font.render(f"Testing Mode: {self.display_mode}", True, self.WHITE)
            info_rect = info_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(info_text, info_rect)
            
            start_text = self.small_font.render("Starting video test in 2 seconds...", True, self.WHITE)
            start_rect = start_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
            self.screen.blit(start_text, start_rect)
            
            pygame.display.flip()
            time.sleep(2)
            
            # Run video test
            self.play_video_with_timing_analysis(self.test_video, duration=8)
            
        except Exception as e:
            print(f"Test failed: {e}")
        finally:
            pygame.quit()

def main():
    """Test multiple display modes to find the best anti-flicker configuration."""
    test_modes = [
        "default",           # Original with all flags
        "no_hwsurface",      # Remove hardware surface
        "no_vsync",          # Remove vsync
        "software_only",     # Software rendering only
        "scaled_window",     # Scaled window instead of fullscreen
        "basic_fullscreen"   # Minimal flags
    ]
    
    print("=== PyVidPlayer2 Anti-Flicker Test Suite ===")
    print("This will test different display configurations to eliminate flickering")
    print("Watch for visual flickering and check the frame timing analysis")
    print()
    
    for i, mode in enumerate(test_modes):
        print(f"\nTest {i+1}/{len(test_modes)}: {mode}")
        input("Press Enter to start this test...")
        
        try:
            test = AntiFlickerTest(mode)
            test.run_test()
            
            print(f"Test {mode} completed.")
            if i < len(test_modes) - 1:
                input("Press Enter to continue to next test...")
                
        except Exception as e:
            print(f"Test {mode} failed: {e}")
            continue
    
    print("\n=== All Tests Complete ===")
    print("Review the frame timing analysis for each mode.")
    print("The mode with the most consistent timing and no visual flickering is optimal.")

if __name__ == "__main__":
    main()
