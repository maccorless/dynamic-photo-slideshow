"""
Pygame Display Manager for Dynamic Photo Slideshow v3.0.
Handles pygame-based fullscreen display with video playback support.
"""

import pygame
import logging
import os
import time
import threading
from typing import Dict, Any, Optional, List, Union
from PIL import Image
import numpy as np
from pyvidplayer2 import Video

from slideshow_exceptions import VideoProcessingError, DisplayError

# Enable HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

class PygameDisplayManager:
    """Manages pygame-based fullscreen display with video playback."""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.screen = None
        self.screen_width = 0
        self.screen_height = 0
        self.running = False
        self.pending_callbacks = []
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        
        # Create fullscreen display with anti-flicker configuration
        flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            flags
        )
        pygame.display.set_caption("Dynamic Photo Slideshow")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        
        # Fonts for overlays
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
        # Removed: Pre-rendered instruction surfaces (no longer used in video overlays)
        
        # State management
        self.running = True
        self.clock = pygame.time.Clock()
        
        # Video state
        self.current_video = None
        self.video_playing = False
        
        # Overlay caching for flicker-free rendering
        self._last_countdown = None
        self._countdown_text = None
        self._countdown_rect = None
        
        self.logger.info(f"Pygame Display Manager initialized: {self.screen_width}x{self.screen_height}")
    
    def display_photo(self, photo_data, location_string: Optional[str] = None, slideshow_timer: Optional[int] = None) -> None:
        """Display a photo using pygame."""
        # Handle None location_string for compatibility
        if location_string is None:
            location_string = ""
        
        # Reset countdown state for new slide
        self._reset_countdown_state()
            
        try:
            if isinstance(photo_data, list) and len(photo_data) == 2:
                self._display_paired_photos(photo_data, location_string, slideshow_timer)
            else:
                self._display_single_photo(photo_data, location_string, slideshow_timer)
        except Exception as e:
            self.logger.error(f"Error in display_photo: {e}")
            self._display_error_message(f"Cannot load image: {os.path.basename(photo_data.get('path', 'Unknown'))}")
    
    def _display_single_photo(self, photo_data: Dict[str, Any], location_string: Optional[str], slideshow_timer: Optional[int] = None) -> None:
        """Display a single photo with overlays."""
        try:
            photo_path = photo_data.get('path')
            if not photo_path or not os.path.exists(photo_path):
                self.logger.error(f"Photo path not found: {photo_path}")
                return
            
            # Load and process image with HEIC support
            try:
                pil_image = Image.open(photo_path)
            except Exception as e:
                if photo_path.lower().endswith('.heic') and not HEIC_SUPPORTED:
                    self.logger.error(f"HEIC support not available for: {os.path.basename(photo_path)}")
                    self._display_error_message(f"HEIC not supported: {os.path.basename(photo_path)}")
                    return
                else:
                    raise e
            
            # Handle rotation based on EXIF
            if hasattr(pil_image, '_getexif') and pil_image._getexif() is not None:
                exif = pil_image._getexif()
                orientation = exif.get(274)  # Orientation tag
                if orientation == 3:
                    pil_image = pil_image.rotate(180, expand=True)
                elif orientation == 6:
                    pil_image = pil_image.rotate(270, expand=True)
                elif orientation == 8:
                    pil_image = pil_image.rotate(90, expand=True)
            
            # Resize image to fit screen while maintaining aspect ratio
            img_w, img_h = pil_image.size
            scale = min(self.screen_width / img_w, self.screen_height / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            pil_image = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Convert PIL image to pygame surface
            image_string = pil_image.tobytes()
            pygame_image = pygame.image.fromstring(image_string, pil_image.size, pil_image.mode)
            
            # Calculate position to center image
            x = (self.screen_width - new_w) // 2
            y = (self.screen_height - new_h) // 2
            
            # Clear screen and display image
            self.screen.fill(self.BLACK)
            self.screen.blit(pygame_image, (x, y))
            
            # Add overlays
            self._add_photo_overlays(photo_data, location_string, x, y, new_w, new_h)
            
            # Check if we need to show stopped overlay after photo display
            self._refresh_stopped_overlay()
            
            # Add countdown timer if slideshow_timer is provided (render AFTER stopped overlay)
            if slideshow_timer and slideshow_timer > 0:
                # Reset countdown start time for new photo
                self._countdown_start_time = time.time()
                # Don't render here - let main loop handle it for consistency
            
            # Update display
            pygame.display.flip()
            
        except Exception as e:
            self.logger.error(f"Error displaying single photo: {e}")
            self._display_error_message(f"Cannot load image: {os.path.basename(photo_data.get('path', 'Unknown'))}")
    
    def _display_paired_photos(self, photo_data_list: List[Dict[str, Any]], location_string: Optional[str], slideshow_timer: Optional[int] = None) -> None:
        """Display two photos side by side."""
        try:
            if len(photo_data_list) != 2:
                self.logger.error("Paired photos must contain exactly 2 photos")
                return
            
            # Clear screen
            self.screen.fill(self.BLACK)
            
            # Calculate available space for each photo (split screen)
            available_width = self.screen_width // 2
            available_height = self.screen_height
            
            for i, photo_data in enumerate(photo_data_list):
                photo_path = photo_data.get('path')
                if not photo_path or not os.path.exists(photo_path):
                    continue
                
                # Load and process image with HEIC support
                try:
                    pil_image = Image.open(photo_path)
                except Exception as e:
                    if photo_path.lower().endswith('.heic') and not HEIC_SUPPORTED:
                        self.logger.error(f"HEIC support not available for: {os.path.basename(photo_path)}")
                        continue
                    else:
                        raise e
                
                # Handle rotation
                if hasattr(pil_image, '_getexif') and pil_image._getexif() is not None:
                    exif = pil_image._getexif()
                    orientation = exif.get(274)
                    if orientation == 3:
                        pil_image = pil_image.rotate(180, expand=True)
                    elif orientation == 6:
                        pil_image = pil_image.rotate(270, expand=True)
                    elif orientation == 8:
                        pil_image = pil_image.rotate(90, expand=True)
                
                # Resize to fit half screen
                img_w, img_h = pil_image.size
                scale = min(available_width / img_w, available_height / img_h)
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                
                # Store original dimensions for overlay calculations
                photo_data['pil_size'] = (img_w, img_h)
                
                pil_image = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Convert to pygame surface
                image_string = pil_image.tobytes()
                pygame_image = pygame.image.fromstring(image_string, pil_image.size, pil_image.mode)
                
                # Calculate position (left or right half)
                if i == 0:  # Left photo
                    x = (available_width - new_w) // 2
                else:  # Right photo
                    x = available_width + (available_width - new_w) // 2
                
                y = (self.screen_height - new_h) // 2
                
                # Display image
                self.screen.blit(pygame_image, (x, y))
            
            # Add overlays for each photo individually with proper positioning
            for i, photo_data in enumerate(photo_data_list):
                # Use the exact same calculations as the image display above
                img_w, img_h = photo_data.get('pil_size', (photo_data.get('width', 1), photo_data.get('height', 1)))
                
                scale = min(available_width / img_w, available_height / img_h)
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                
                # Calculate position (left or right half) - exact same logic as image display
                if i == 0:  # Left photo
                    x = (available_width - new_w) // 2
                else:  # Right photo
                    x = available_width + (available_width - new_w) // 2
                
                y = (self.screen_height - new_h) // 2
                
                # Get individual location for this specific photo
                # First try photo's own location_string, then fall back to shared location
                individual_location = photo_data.get('location_string')
                if not individual_location and hasattr(self, 'controller') and self.controller:
                    # Get location string specifically for this photo
                    try:
                        individual_location = self.controller._get_location_string(photo_data)
                    except:
                        individual_location = location_string
                else:
                    individual_location = individual_location or location_string
                
                # Add overlay for this specific photo
                self._add_photo_overlays(photo_data, individual_location, x, y, new_w, new_h)
            
            # Check if we need to show stopped overlay after photo display
            self._refresh_stopped_overlay()
            
            # Add countdown timer if slideshow_timer is provided (render AFTER stopped overlay)
            if slideshow_timer and slideshow_timer > 0:
                # Reset countdown start time for new photo
                self._countdown_start_time = time.time()
                # Don't render here - let main loop handle it for consistency
            
            # Update display
            pygame.display.flip()
            
        except Exception as e:
            self.logger.error(f"Error displaying paired photos: {e}")
            self._display_error_message("Cannot load paired images")
    
    def play_video(self, video_path: str, max_duration: int = 15, completion_callback=None) -> bool:
        """Play video using pyvidplayer2."""
        try:
            self.logger.info(f"Playing video: {os.path.basename(video_path)}")
            
            # Reset countdown state for new slide
            self._reset_countdown_state()
            
            # Clean up any existing video first
            if self.current_video:
                self.current_video.close()
                self.current_video = None
            self.video_playing = False
            
            # Load video
            video = Video(video_path)
            video.set_volume(self.config.get('VIDEO_AUDIO_ENABLED', True))
            
            # Resize video for screen
            video_pos = self._resize_video_for_screen(video)
            
            start_time = time.time()
            self.video_playing = True
            self.current_video = video
            
            # Use max_duration as slide timer (this is the correct slideshow timer passed from controller)
            slide_timer = max_duration
            self.logger.info(f"[VIDEO-COUNTDOWN] Using slide_timer: {slide_timer}s for video countdown (from max_duration parameter)")
            
            # Video is now ready - notify controller to start timer
            if hasattr(self, 'controller') and self.controller and hasattr(self.controller, 'current_slide'):
                if hasattr(self.controller, 'start_video_timer'):
                    self.logger.info(f"[VIDEO-READY] Video setup complete - notifying controller to start timer")
                    self.controller.start_video_timer(self.controller.current_slide)
                else:
                    self.logger.warning(f"[VIDEO-READY] Controller has no start_video_timer method")
            else:
                self.logger.warning(f"[VIDEO-READY] No controller available to start timer")
            
            while self.running and self.video_playing and (time.time() - start_time) < max_duration:
                # Check if slideshow is paused
                if hasattr(self, 'controller') and self.controller and self.controller.is_paused:
                    self.logger.info(f"[VIDEO-PAUSE] Video paused by slideshow controller")
                    
                    # Use synchronous pause method
                    pause_success = self.pause_video()
                    if pause_success:
                        self.logger.info(f"[VIDEO-PAUSE] Video successfully paused, showing overlay")
                        # Now show the overlay after video is paused
                        self.show_stopped_overlay()
                    else:
                        self.logger.warning(f"[VIDEO-PAUSE] Failed to pause video, showing overlay anyway")
                        self.show_stopped_overlay()
                    
                    paused_start_time = time.time()
                    
                    # Wait while paused - overlay is already shown above
                    while (self.running and self.video_playing and 
                           hasattr(self, 'controller') and self.controller and self.controller.is_paused):
                        pygame.time.wait(50)  # Small delay to prevent busy waiting
                        # Overlay remains visible from the single call above
                        
                        # Handle events while paused
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                self.running = False
                                self.video_playing = False
                                video.close()
                                return False
                            elif event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_ESCAPE:
                                    self.running = False
                                    self.video_playing = False
                                    video.close()
                                    return False
                                elif event.key == pygame.K_SPACE:
                                    # Resume video - let controller handle this
                                    if hasattr(self, 'controller') and self.controller:
                                        self.controller.toggle_pause()
                                    break
                    
                    # Resume video when unpaused using synchronous method
                    resume_success = self.resume_video()
                    if resume_success:
                        self.logger.info(f"[VIDEO-RESUME] Video successfully resumed")
                    else:
                        self.logger.warning(f"[VIDEO-RESUME] Failed to resume video")
                    
                    # Calculate how much time was spent paused
                    paused_duration = time.time() - paused_start_time
                    self.logger.info(f"[VIDEO-RESUME] Video resumed after {paused_duration:.1f}s pause")
                    
                    # Adjust start_time to account for pause duration
                    # This ensures the video timing is correct
                    start_time += paused_duration
                    
                    continue  # Continue video playback from where we left off
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        self.video_playing = False
                        video.close()
                        return False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                            self.video_playing = False
                            video.close()
                            return False
                        elif event.key == pygame.K_SPACE:
                            # Pause/Resume video - let controller handle this
                            if hasattr(self, 'controller') and self.controller:
                                self.controller.toggle_pause()
                            # Continue playing video if not paused
                            continue
                        elif event.key in [pygame.K_RIGHT, pygame.K_n]:
                            # Next/Skip video
                            self.video_playing = False
                            video.close()
                            # Trigger navigation via controller if available
                            if hasattr(self, 'controller') and self.controller:
                                self.controller.next_photo()
                            return True
                        elif event.key in [pygame.K_LEFT, pygame.K_b]:
                            # Previous
                            self.video_playing = False
                            video.close()
                            # Trigger navigation via controller if available
                            if hasattr(self, 'controller') and self.controller:
                                self.controller.previous_photo()
                            return True
                        elif event.key == pygame.K_p:
                            # Pause/Resume
                            if hasattr(self, 'controller') and self.controller:
                                self.controller.toggle_pause()
                            # Continue playing video if not paused
                            continue
                
                # Check if video is still playing
                if not video.active:
                    self.logger.info("Video ended naturally")
                    break
                
                # Clear screen and draw video frame
                self.screen.fill(self.BLACK)
                video.draw(self.screen, video_pos)
                
                # Add video overlays with accurate slide timer countdown
                elapsed_time = time.time() - start_time
                remaining_time = max(0, int(slide_timer - elapsed_time))
                self._add_video_overlays(video_path, remaining_time)
                
                # Update countdown display for videos
                if self.config.get('show_countdown_timer', False):
                    self.show_countdown(remaining_time)
                
                # Update display to show video frame
                pygame.display.flip()
                self.clock.tick(30)
            
            # Clean up after video playback
            self.video_playing = False
            if self.current_video:
                self.current_video.close()
            self.current_video = None
            
            # Call completion callback if provided
            if completion_callback:
                completion_callback()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error playing video: {e}")
            self.video_playing = False
            self.current_video = None
            return False
    
    def _resize_video_for_screen(self, video):
        """Resize video to fit screen while maintaining aspect ratio."""
        vw, vh = video.original_size
        scale = min(self.screen_width / vw, self.screen_height / vh)
        new_w = int(vw * scale)
        new_h = int(vh * scale)
        video.resize((new_w, new_h))
        x = (self.screen_width - new_w) // 2
        y = (self.screen_height - new_h) // 2
        return (x, y)
    
    def _add_photo_overlays(self, photo_data: Dict[str, Any], location_string: Optional[str], 
                           x: int, y: int, width: int, height: int) -> None:
        """Add date and location overlays to the displayed image (v2.0 compliant)."""
        try:
            overlay_texts = []
            
            # Format date if available (EXACT v2.0 logic)
            if photo_data.get('date_taken'):
                date_str = photo_data['date_taken'].strftime('%B %d, %Y')
                overlay_texts.append(date_str)
            
            # Add location if available
            if location_string:
                overlay_texts.append(location_string)
            
            if not overlay_texts:
                return
            
            # Combine texts (EXACT v2.0 logic)
            overlay_text = ' • '.join(overlay_texts)
            
            # Calculate overlay position based on config (v2.0 style)
            placement = self.config.get('OVERLAY_PLACEMENT', 'TOP')
            alignment = self.config.get('OVERLAY_ALIGNMENT', 'CENTER')
            
            # Font size from requirements (36px) - will be adjusted if text is too wide
            font_size = 36
            
            # Calculate optimal font size to fit within image width
            font_size = self._calculate_optimal_font_size(overlay_text, font_size, width)
            
            # Create font and get text dimensions (using Arial to match v2.0)
            try:
                # Try to use Arial font to match v2.0 exactly
                overlay_font = pygame.font.SysFont('Arial', font_size)
            except:
                # Fallback to default font if Arial not available
                overlay_font = pygame.font.Font(None, font_size)
            
            text_surface = overlay_font.render(overlay_text, True, (0, 0, 0))  # Black text
            text_width = text_surface.get_width()
            text_height = text_surface.get_height()
            
            # Create background sized exactly to text dimensions (matching v2.0)
            padding = 8  # Same as v2.0
            
            # Calculate background dimensions first (matching v2.0 logic)
            bg_width = text_width + 2 * padding
            bg_height = text_height + 2 * padding
            
            # Determine background position based on overlay type and alignment (matching v2.0 exactly)
            if placement == 'TOP':
                bg_y = y + 20
            else:  # BOTTOM
                bg_y = y + height - bg_height - 20
            
            if alignment == 'LEFT':
                bg_x = x + 20
            elif alignment == 'RIGHT':
                bg_x = x + width - bg_width - 20
            else:  # CENTER
                bg_x = x + (width - bg_width) // 2
            
            # Draw solid white background
            pygame.draw.rect(self.screen, (255, 255, 255), (bg_x, bg_y, bg_width, bg_height))
            
            # Position text at the center of the background (matching v2.0 exactly)
            text_x = bg_x + bg_width // 2 - text_width // 2
            text_y = bg_y + bg_height // 2 - text_height // 2
            
            # Draw text centered on the white background
            self.screen.blit(text_surface, (text_x, text_y))
                
        except Exception as e:
            self.logger.error(f"Error adding photo overlays: {e}")
    
    def _add_video_overlays(self, video_path: str, remaining_time: int) -> None:
        """Add overlays for video display with flicker-free countdown."""
        try:
            # Video filename
            filename = os.path.basename(video_path)
            filename_text = self.small_font.render(filename, True, self.WHITE)
            self.screen.blit(filename_text, (20, 20))
            
            # Countdown timer - use consistent styling with photos
            if remaining_time != self._last_countdown:
                countdown_text = f"{remaining_time}s"
                self._countdown_text = self.font.render(countdown_text, True, self.WHITE)
                self._countdown_rect = self._countdown_text.get_rect(topright=(self.screen_width - 50, 50))
                self._last_countdown = remaining_time
            
            # Draw countdown with consistent background styling
            if self._countdown_text and self._countdown_rect:
                # Create a semi-transparent background rectangle for better visibility
                bg_rect = self._countdown_rect.copy()
                bg_rect.inflate_ip(10, 5)
                
                # Create a surface for the semi-transparent background
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
                bg_surface.set_alpha(128)
                bg_surface.fill((0, 0, 0))
                
                # Draw background and text
                self.screen.blit(bg_surface, bg_rect.topleft)
                self.screen.blit(self._countdown_text, self._countdown_rect)
            
            # Removed: Instruction overlays (per requirements)
                
        except Exception as e:
            self.logger.error(f"Error adding video overlays: {e}")
    
    def _display_error_message(self, message: str) -> None:
        """Display an error message."""
        try:
            self.screen.fill(self.BLACK)
            
            error_text = self.font.render(f"Error: {message}", True, self.WHITE)
            error_rect = error_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(error_text, error_rect)
            
            pygame.display.flip()
            
        except Exception as e:
            self.logger.error(f"Error displaying error message: {e}")
    
    def show_message(self, message: str, duration: float = 2.0) -> None:
        """Display a temporary message."""
        try:
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
                
                # Clear screen and show message
                self.screen.fill(self.BLACK)
                
                message_text = self.font.render(message, True, self.WHITE)
                message_rect = message_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(message_text, message_rect)
                
                pygame.display.flip()
                self.clock.tick(60)
                
        except Exception as e:
            self.logger.error(f"Error showing message: {e}")
    
    def handle_events(self) -> List[pygame.event.Event]:
        """Handle pygame events and return them for processing."""
        return pygame.event.get()
    
    def update_display(self) -> None:
        """Update the display."""
        pygame.display.flip()
    
    def cleanup(self) -> None:
        """Clean up pygame resources."""
        try:
            if self.current_video:
                self.current_video.close()
            pygame.quit()
            self.logger.info("Pygame Display Manager cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def is_running(self) -> bool:
        """Check if the display manager is still running."""
        return self.running
    
    def stop(self) -> None:
        """Stop the display manager immediately."""
        self.running = False
        self.video_playing = False
        
        # Immediately stop any current video
        if self.current_video:
            try:
                self.current_video.close()
                self.current_video = None
            except Exception as e:
                self.logger.error(f"Error closing video on stop: {e}")
        
        # Clear any pending callbacks to prevent delays
        self.pending_callbacks.clear()
    
    # Methods required by SlideshowController
    
    def set_controller_reference(self, controller) -> None:
        """Set reference to slideshow controller for compatibility."""
        self.controller = controller
    
    def _refresh_stopped_overlay(self) -> None:
        """Show STOPPED overlay if slideshow is paused - called after image display."""
        try:
            # Check if we should show stopped overlay by checking controller state
            if hasattr(self, 'controller') and self.controller:
                if hasattr(self.controller, 'is_paused') and self.controller.is_paused:
                    self.show_stopped_overlay()
        except Exception as e:
            self.logger.error(f"Error refreshing stopped overlay: {e}")
    
    def is_video_supported(self) -> bool:
        """Check if video playback is supported."""
        return True  # pygame display manager supports video via pyvidplayer2
    
    def is_video_playing(self) -> bool:
        """Check if video is currently playing."""
        return self.video_playing
    
    def display_video(self, video_path: str, overlays: dict = None, max_duration: int = None, completion_callback=None) -> bool:
        """Display video with overlays (compatibility method)."""
        if max_duration is None:
            max_duration = self.config.get('video_max_duration', 15)
        return self.play_video(video_path, max_duration, completion_callback)
    
    def pause_video(self) -> None:
        """Pause video playback."""
        if self.current_video and self.video_playing:
            self.current_video.pause()
            self.logger.info("Video paused")
    
    def resume_video(self) -> None:
        """Resume video playback."""
        if self.current_video and self.video_playing:
            self.current_video.resume()
            self.logger.info("Video resumed")
    
    def stop_video(self) -> None:
        """Stop video playback."""
        if self.current_video:
            self.current_video.close()
            self.current_video = None
        self.video_playing = False
        self.logger.info("Video stopped")
    
    def pause_video(self) -> bool:
        """Synchronously pause the currently playing video.
        
        Returns:
            bool: True if video was successfully paused, False otherwise
        """
        if not self.video_playing or not self.current_video:
            self.logger.debug("[VIDEO-PAUSE] No video playing to pause")
            return False
            
        try:
            if hasattr(self.current_video, 'pause'):
                self.current_video.pause()
                self.logger.info("[VIDEO-PAUSE] Video paused successfully")
                return True
            else:
                self.logger.warning("[VIDEO-PAUSE] Video object has no pause method")
                return False
        except Exception as e:
            self.logger.error(f"[VIDEO-PAUSE] Failed to pause video: {e}")
            return False
    
    def resume_video(self) -> bool:
        """Synchronously resume the currently paused video.
        
        Returns:
            bool: True if video was successfully resumed, False otherwise
        """
        if not self.video_playing or not self.current_video:
            self.logger.debug("[VIDEO-RESUME] No video playing to resume")
            return False
            
        try:
            if hasattr(self.current_video, 'resume'):
                self.current_video.resume()
                self.logger.info("[VIDEO-RESUME] Video resumed successfully")
                return True
            elif hasattr(self.current_video, 'unpause'):
                self.current_video.unpause()
                self.logger.info("[VIDEO-RESUME] Video unpaused successfully")
                return True
            elif hasattr(self.current_video, 'play'):
                self.current_video.play()
                self.logger.info("[VIDEO-RESUME] Video play() called successfully")
                return True
            else:
                self.logger.warning("[VIDEO-RESUME] Video object has no resume/unpause/play method")
                return False
        except Exception as e:
            self.logger.error(f"[VIDEO-RESUME] Failed to resume video: {e}")
            return False
    
    def show_stopped_overlay(self) -> None:
        """Show STOPPED overlay when slideshow is paused (centered message only, no black screen)."""
        try:
            # DON'T create full-screen black overlay - just show pause message
            # The video/photo content should remain visible underneath
            
            # Create pause message with background
            stopped_text = self.font.render("SLIDESHOW PAUSED", True, self.WHITE)
            stopped_rect = stopped_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            
            # Draw background rectangle for better readability
            bg_rect = stopped_rect.inflate(40, 20)
            pygame.draw.rect(self.screen, (0, 0, 0, 200), bg_rect)
            pygame.draw.rect(self.screen, self.WHITE, bg_rect, 2)
            
            self.screen.blit(stopped_text, stopped_rect)
            
            # Add instruction text
            instruction_text = self.small_font.render("Press SPACE to resume", True, self.WHITE)
            instruction_rect = instruction_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
            
            # Background for instruction text
            inst_bg_rect = instruction_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, (0, 0, 0, 200), inst_bg_rect)
            pygame.draw.rect(self.screen, self.WHITE, inst_bg_rect, 1)
            
            self.screen.blit(instruction_text, instruction_rect)
            
            pygame.display.flip()
            
        except Exception as e:
            self.logger.error(f"Error showing stopped overlay: {e}")
    
    # REMOVED: show_video_pause_overlay() - now using unified show_stopped_overlay() for both photos and videos
    
    def clear_stopped_overlay(self) -> None:
        """Clear STOPPED overlay when resuming slideshow."""
        try:
            self.logger.info(f"[OVERLAY-CLEAR] Clearing overlay - letting natural display updates handle it")
            
            # For videos: The overlay will be cleared when video frames resume drawing
            # For photos: The overlay will be cleared by the next countdown update
            # This approach prevents black screen issues while ensuring overlay disappears
            
            self.logger.info(f"[OVERLAY-CLEAR] Overlay will be cleared by next display update")
                
        except Exception as e:
            self.logger.error(f"Error clearing stopped overlay: {e}")
    
    def _redisplay_current_photo(self, slide: dict) -> None:
        """Re-display the current photo to clear overlays."""
        try:
            self.logger.info(f"[REDISPLAY] Attempting to re-display slide: {slide.get('type', 'unknown')}")
            
            if slide.get('type') in ['portrait_pair', 'single_portrait', 'single_landscape']:
                photo_data = slide.get('photo_data')
                location_string = slide.get('location_string', '')
                slideshow_timer = slide.get('slide_timer', 10)
                
                self.logger.info(f"[REDISPLAY] Photo data available: {photo_data is not None}")
                self.logger.info(f"[REDISPLAY] Location: {location_string}")
                self.logger.info(f"[REDISPLAY] Timer: {slideshow_timer}")
                
                if photo_data:
                    self.logger.info(f"[REDISPLAY] Calling display_photo()")
                    self.display_photo(photo_data, location_string, slideshow_timer)
                    self.logger.info(f"[REDISPLAY] display_photo() completed")
                else:
                    self.logger.error(f"[REDISPLAY] No photo_data in slide: {list(slide.keys())}")
            else:
                self.logger.warning(f"[REDISPLAY] Unsupported slide type: {slide.get('type')}")
                
        except Exception as e:
            self.logger.error(f"Error re-displaying current photo: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def show_countdown(self, remaining_seconds: int) -> None:
        """Show countdown timer overlay in top-right corner."""
        try:
            if not self.config.get('show_countdown_timer', False):
                return
            
            # Add detailed debugging for countdown display calls
            import threading
            thread_id = threading.current_thread().ident
            self.logger.info(f"[COUNTDOWN-DISPLAY] Thread-{thread_id}: show_countdown({remaining_seconds}s) called, last_countdown: {self._last_countdown}")
            
            if remaining_seconds <= 0:
                self.logger.info(f"[COUNTDOWN-DISPLAY] Thread-{thread_id}: Skipping display - remaining_seconds <= 0")
                return
            
            # Only update countdown text when value changes to prevent flicker
            if remaining_seconds != self._last_countdown:
                # Clear the previous countdown area if it exists
                if self._countdown_rect:
                    # Create a slightly larger rectangle to ensure complete clearing
                    clear_rect = self._countdown_rect.inflate(10, 10)
                    pygame.draw.rect(self.screen, self.BLACK, clear_rect)
                
                countdown_text = f"{remaining_seconds}s"
                self._countdown_text = self.font.render(countdown_text, True, self.WHITE)
                self._countdown_rect = self._countdown_text.get_rect(topright=(self.screen_width - 50, 50))
                self._last_countdown = remaining_seconds
            
            # Render countdown immediately to screen and update display
            if self._countdown_text and self._countdown_rect:
                self.screen.blit(self._countdown_text, self._countdown_rect)
                pygame.display.flip()
                
        except Exception as e:
            self.logger.error(f"Error showing countdown: {e}")
    
    def clear_countdown_timer(self) -> None:
        """Clear countdown timer overlay and reset state."""
        import threading
        thread_id = threading.current_thread().ident
        self.logger.info(f"[COUNTDOWN-CLEAR] Thread-{thread_id}: Clearing countdown state - last_countdown: {self._last_countdown}")
        
        # Clear the countdown area if it exists
        if self._countdown_rect:
            clear_rect = self._countdown_rect.inflate(10, 10)
            pygame.draw.rect(self.screen, self.BLACK, clear_rect)
            pygame.display.flip()
        
        self._last_countdown = None
        self._countdown_text = None
        self._countdown_rect = None
    
    def _reset_countdown_state(self) -> None:
        """Reset countdown state when starting a new slide."""
        self.logger.debug(f"[COUNTDOWN-RESET] Resetting countdown state - was: {self._last_countdown}")
        self._last_countdown = None
        self._countdown_text = None
        self._countdown_rect = None
    
    # REMOVED: Duplicate _add_video_overlays method that overrides the proper one above
    
    def _render_slideshow_countdown(self, slideshow_timer: int) -> None:
        """Render slideshow countdown timer using the calculated slideshow_timer value."""
        try:
            countdown_enabled = self.config.get('show_countdown_timer', False)
            if not countdown_enabled:
                return
            
            if slideshow_timer <= 0:
                return
            
            # Calculate elapsed time from controller's last_advance_time
            current_time = time.time()
            if hasattr(self, 'controller') and self.controller and hasattr(self.controller, 'last_advance_time'):
                elapsed = current_time - self.controller.last_advance_time
                remaining = max(0, int(slideshow_timer - elapsed))
            else:
                # Fallback: use current time if controller reference not available
                if not hasattr(self, '_countdown_start_time'):
                    self._countdown_start_time = current_time
                elapsed = current_time - self._countdown_start_time
                remaining = max(0, int(slideshow_timer - elapsed))
            
            if remaining <= 0:
                self.logger.debug(f"Countdown remaining time <= 0: {remaining}")
                return
            
            # Only update countdown text when value changes to prevent flicker
            if remaining != self._last_countdown:
                countdown_text = f"{remaining}s"
                self._countdown_text = self.font.render(countdown_text, True, self.WHITE)
                self._countdown_rect = self._countdown_text.get_rect(topright=(self.screen_width - 50, 50))
                self._last_countdown = remaining
            
            # Draw countdown with background
            if self._countdown_text and self._countdown_rect:
                # Create a semi-transparent background rectangle for better visibility
                bg_rect = self._countdown_rect.copy()
                bg_rect.inflate_ip(10, 5)
                
                # Create a surface for the semi-transparent background
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
                bg_surface.set_alpha(128)
                bg_surface.fill((0, 0, 0))
                
                # Draw background and text
                self.screen.blit(bg_surface, bg_rect.topleft)
                self.screen.blit(self._countdown_text, self._countdown_rect)
                
        except Exception as e:
            self.logger.error(f"Error rendering slideshow countdown: {e}")
    
    def update(self) -> None:
        """Update display (compatibility method)."""
        pygame.display.flip()
    
    def destroy(self) -> None:
        """Destroy display manager (compatibility method)."""
        self.cleanup()
    
    @property
    def root(self):
        """Compatibility property for tkinter root access."""
        return self  # Return self to allow method calls
    
    def after(self, delay_ms: int, callback):
        """Compatibility method for tkinter's after method."""
        # For pygame, we'll handle timing differently in the main loop
        # Schedule callback to be executed in the main event loop
        if callable(callback):
            # Store callback for execution in main loop
            if not hasattr(self, '_pending_callbacks'):
                self._pending_callbacks = []
            self._pending_callbacks.append((pygame.time.get_ticks() + delay_ms, callback))
    
    def process_pending_callbacks(self):
        """Process any pending callbacks scheduled via after method."""
        if not hasattr(self, '_pending_callbacks'):
            self._pending_callbacks = []
            return
        
        current_time = pygame.time.get_ticks()
        remaining_callbacks = []
        
        for scheduled_time, callback in self._pending_callbacks:
            if current_time >= scheduled_time:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Error executing scheduled callback: {e}")
            else:
                remaining_callbacks.append((scheduled_time, callback))
        
        self._pending_callbacks = remaining_callbacks
    
    def _calculate_optimal_font_size(self, text: str, initial_font_size: int, max_width: int) -> int:
        """Calculate optimal font size to fit text within given width (v2.0 compliant)."""
        try:
            # Reserve some padding (40px total - 20px on each side) - matching v2.0 exactly
            available_width = max_width - 40
            
            font_size = initial_font_size
            min_font_size = 12  # Don't go below 12px - matching v2.0
            
            while font_size >= min_font_size:
                # Test current font size using Arial font to match v2.0
                try:
                    test_font = pygame.font.SysFont('Arial', font_size)
                except:
                    test_font = pygame.font.Font(None, font_size)
                text_surface = test_font.render(text, True, (0, 0, 0))
                text_width = text_surface.get_width()
                
                if text_width <= available_width:
                    return font_size
                
                # Reduce font size by 2 and try again - matching v2.0 behavior
                font_size -= 2
            
            return min_font_size
            
        except Exception as e:
            self.logger.debug(f"Error calculating optimal font size: {e}")
            return initial_font_size
    
    def show_filename_overlay(self, filename: str) -> None:
        """Show filename overlay (activated by Shift key)."""
        try:
            # Position filename at top-center
            font_size = 24
            font = pygame.font.Font(None, font_size)
            text_surface = font.render(filename, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.centerx = self.screen_width // 2
            text_rect.y = 20
            
            # Add semi-transparent background
            bg_rect = text_rect.inflate(20, 10)
            bg_surface = pygame.Surface(bg_rect.size)
            bg_surface.set_alpha(128)
            bg_surface.fill((0, 0, 0))
            
            # Draw to screen
            self.screen.blit(bg_surface, bg_rect)
            self.screen.blit(text_surface, text_rect)
            pygame.display.flip()
            
        except Exception as e:
            self.logger.error(f"Error showing filename overlay: {e}")
