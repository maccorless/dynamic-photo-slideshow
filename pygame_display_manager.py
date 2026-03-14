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
from settings_manager import SettingsManager
from settings_window import SettingsWindow

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
        
        # Voice command overlay state
        self._voice_command_text = None
        self._voice_command_timer = None
        self._voice_command_lock = threading.Lock()
        
        # Surface rendering lock for thread safety
        self._surface_lock = threading.Lock()
        
        # Test mode for simulating video failures
        self._test_video_failure_mode = False
        self._test_failure_type = None  # 'load', 'codec', 'playback'
        
        # Settings window (will be initialized with settings_manager later)
        self.settings_manager = None
        self.settings_window = None
        
        self.logger.debug(f"Pygame Display Manager initialized: {self.screen_width}x{self.screen_height}")

    def show_loading_screen(self, message: str = "Loading...") -> None:
        """Display a centered loading message on a black background."""
        self.screen.fill(self.BLACK)
        text_surface = self.font.render(message, True, self.WHITE)
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text_surface, text_rect)
        pygame.display.flip()

    def set_controller(self, controller, settings_manager):
        """
        Set the controller reference and settings manager for live settings updates.
        
        Args:
            controller: Slideshow controller instance
            settings_manager: Shared SettingsManager instance
        """
        self.settings_manager = settings_manager
        self.settings_window = SettingsWindow(self.screen, settings_manager, controller)
        self.logger.debug("Settings window initialized with shared settings manager and controller")
    
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
            
            # Handle photos that need to be exported from iCloud
            if (not photo_path or not os.path.exists(photo_path)) and photo_data.get('needs_export'):
                self.logger.info(f"[SINGLE-DISPLAY] Photo needs export from iCloud, attempting download...")
                if hasattr(self, 'controller') and self.controller and hasattr(self.controller, 'photo_manager'):
                    exported_path = self.controller.photo_manager._export_photo_temporarily(photo_data)
                    if exported_path:
                        self.logger.info(f"[SINGLE-DISPLAY] Successfully exported photo from iCloud: {exported_path}")
                        photo_path = exported_path
                        photo_data['path'] = exported_path
                    else:
                        self.logger.error(f"[SINGLE-DISPLAY] Failed to export photo from iCloud (filename: {photo_data.get('filename', 'unknown')}, uuid: {photo_data.get('uuid', 'unknown')})")
                        self._display_error_message(f"Cannot download from iCloud: {os.path.basename(photo_data.get('filename', 'Unknown'))}")
                        return
                else:
                    self.logger.error(f"[SINGLE-DISPLAY] Cannot export photo - no photo_manager available")
                    self._display_error_message(f"Cannot download from iCloud: {os.path.basename(photo_data.get('filename', 'Unknown'))}")
                    return
            
            # Final check - if still no valid path, show error
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
            
            # Debug logging for paired photo display
            self.logger.debug(f"[PAIRED-DISPLAY] Starting paired photo display")
            self.logger.debug(f"[PAIRED-DISPLAY] Photo 1: {photo_data_list[0].get('path')} (filename: {photo_data_list[0].get('filename', 'unknown')}, uuid: {photo_data_list[0].get('uuid', 'unknown')})")
            self.logger.debug(f"[PAIRED-DISPLAY] Photo 2: {photo_data_list[1].get('path')} (filename: {photo_data_list[1].get('filename', 'unknown')}, uuid: {photo_data_list[1].get('uuid', 'unknown')})")
            
            # Clear screen
            self.screen.fill(self.BLACK)
            
            # Calculate available space for each photo (split screen)
            available_width = self.screen_width // 2
            available_height = self.screen_height
            
            for i, photo_data in enumerate(photo_data_list):
                photo_path = photo_data.get('path')
                
                # Handle photos that need to be exported from iCloud
                if (not photo_path or not os.path.exists(photo_path)) and photo_data.get('needs_export'):
                    self.logger.info(f"[PAIRED-DISPLAY] Photo {i+1} needs export from iCloud, attempting download...")
                    if hasattr(self, 'controller') and self.controller and hasattr(self.controller, 'photo_manager'):
                        exported_path = self.controller.photo_manager._export_photo_temporarily(photo_data)
                        if exported_path:
                            self.logger.info(f"[PAIRED-DISPLAY] Successfully exported photo {i+1} from iCloud: {exported_path}")
                            photo_path = exported_path
                            photo_data['path'] = exported_path
                        else:
                            self.logger.error(f"[PAIRED-DISPLAY] Failed to export photo {i+1} from iCloud (filename: {photo_data.get('filename', 'unknown')}, uuid: {photo_data.get('uuid', 'unknown')})")
                            continue
                    else:
                        self.logger.error(f"[PAIRED-DISPLAY] Cannot export photo {i+1} - no photo_manager available")
                        continue
                
                # Final check - if still no valid path, skip this photo
                if not photo_path or not os.path.exists(photo_path):
                    self.logger.error(f"[PAIRED-DISPLAY] Photo {i+1} path not found or doesn't exist: {photo_path} (filename: {photo_data.get('filename', 'unknown')}, uuid: {photo_data.get('uuid', 'unknown')})")
                    continue
                
                # Load and process image with HEIC support
                try:
                    pil_image = Image.open(photo_path)
                    self.logger.debug(f"[PAIRED-DISPLAY] Successfully loaded photo {i+1}: {os.path.basename(photo_path)}")
                    self.logger.debug(f"[PAIRED-DISPLAY] PIL image {i+1} mode={pil_image.mode}, size={pil_image.size}")
                except Exception as e:
                    if photo_path.lower().endswith('.heic') and not HEIC_SUPPORTED:
                        self.logger.error(f"[PAIRED-DISPLAY] HEIC support not available for photo {i+1}: {os.path.basename(photo_path)}")
                        continue
                    else:
                        self.logger.error(f"[PAIRED-DISPLAY] Failed to load photo {i+1}: {e}")
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
                self.logger.debug(f"[PAIRED-DISPLAY] Pygame surface {i+1} created: {pygame_image.get_size()}")
                
                # Calculate position (left or right half)
                if i == 0:  # Left photo
                    x = (available_width - new_w) // 2
                else:  # Right photo
                    x = available_width + (available_width - new_w) // 2
                
                y = (self.screen_height - new_h) // 2
                
                # Display image
                self.screen.blit(pygame_image, (x, y))
                self.logger.debug(f"[PAIRED-DISPLAY] Blitted photo {i+1} at position ({x}, {y})")
            
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
            self.logger.debug(f"[PAIRED-DISPLAY] Completed paired photo display")
            
        except Exception as e:
            self.logger.error(f"Error displaying paired photos: {e}")
            self._display_error_message("Cannot load paired images")
    
    def _display_video_error_message(self, message: str, duration_seconds: int = None) -> None:
        """Display video-specific error message on screen with countdown timer.
        
        Args:
            message: Error message to display
            duration_seconds: Duration to show error (defaults to slideshow interval from config)
        """
        try:
            # Use slideshow interval from config if duration not specified
            if duration_seconds is None:
                duration_seconds = self.config.get('SLIDESHOW_INTERVAL_SECONDS', 10)
            
            # Ensure screen is valid
            if not self.screen or not pygame.display.get_surface():
                self.logger.error(f"[VIDEO-ERROR-DISPLAY] Cannot show error - screen not initialized")
                return
            
            self.logger.info(f"[VIDEO-ERROR-DISPLAY] Showing error with {duration_seconds}s countdown: {message}")
            
            start_time = time.time()
            last_countdown = -1
            
            # Display loop with countdown
            while True:
                elapsed = time.time() - start_time
                remaining = int(duration_seconds - elapsed)
                
                # Check if time expired
                if remaining <= 0:
                    self.logger.info(f"[VIDEO-ERROR-DISPLAY] Countdown complete - triggering auto-advance")
                    # Trigger next slide via controller
                    if hasattr(self, 'controller') and self.controller:
                        self.logger.info(f"[VIDEO-ERROR-DISPLAY] Calling controller.next_photo()")
                        self.controller.next_photo()
                    break
                
                # Only redraw when countdown changes
                if remaining != last_countdown:
                    with self._surface_lock:
                        self.screen.fill(self.BLACK)
                        
                        # Main error message
                        error_text = self.font.render("⚠ VIDEO ERROR", True, (255, 100, 100))  # Red color
                        error_rect = error_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 50))
                        
                        # Detail message
                        detail_text = self.small_font.render(message, True, self.WHITE)
                        detail_rect = detail_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 10))
                        
                        # Skip instruction with auto-advance info
                        skip_msg = f"Press RIGHT ARROW to skip or auto-advancing in {remaining}s"
                        skip_text = self.small_font.render(skip_msg, True, (200, 200, 200))
                        skip_rect = skip_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 60))
                        
                        # Countdown timer (top-right corner, same as photo countdown)
                        countdown_text = self.font.render(f"{remaining}s", True, self.WHITE)
                        countdown_rect = countdown_text.get_rect(topright=(self.screen_width - 50, 50))
                        
                        # Draw messages
                        self.screen.blit(error_text, error_rect)
                        self.screen.blit(detail_text, detail_rect)
                        self.screen.blit(skip_text, skip_rect)
                        self.screen.blit(countdown_text, countdown_rect)
                        
                        pygame.display.flip()
                        last_countdown = remaining
                        self.logger.debug(f"[VIDEO-ERROR-DISPLAY] Countdown: {remaining}s")
                
                # Check for user input to skip
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key in [pygame.K_RIGHT, pygame.K_n, pygame.K_ESCAPE]:
                            self.logger.info(f"[VIDEO-ERROR-DISPLAY] User skipped error message")
                            # Trigger next slide
                            if hasattr(self, 'controller') and self.controller:
                                self.controller.next_photo()
                            return  # User skipped
                    elif event.type == pygame.QUIT:
                        self.logger.info(f"[VIDEO-ERROR-DISPLAY] Quit event received")
                        return
                
                # Small delay to prevent busy loop
                pygame.time.wait(100)
                    
        except Exception as e:
            self.logger.error(f"[VIDEO-ERROR-DISPLAY] Failed to display error message: {e}")
            import traceback
            self.logger.error(f"[VIDEO-ERROR-DISPLAY] Traceback: {traceback.format_exc()}")
    
    def play_video(self, video_path: str, max_duration: int = 15, completion_callback=None, overlays: List[Dict[str, Any]] = None, video_metadata: Dict[str, Any] = None) -> bool:
        """Play video using pyvidplayer2 with overlay support."""
        try:
            self.logger.debug(f"Playing video: {os.path.basename(video_path)}")
            
            # Store overlays for use during video playback
            self.current_video_overlays = overlays or []
            self.logger.debug(f"[VIDEO-OVERLAY-STORE] Stored {len(self.current_video_overlays)} overlays for video playback")
            if self.current_video_overlays:
                for i, overlay in enumerate(self.current_video_overlays):
                    self.logger.debug(f"[VIDEO-OVERLAY-STORE] Overlay {i+1}: {overlay.get('type')} = '{overlay.get('text')}' at {overlay.get('position')}")
            
            # Reset countdown state for new slide
            self._reset_countdown_state()
            
            # Clean up any existing video first
            if self.current_video:
                self.current_video.close()
                self.current_video = None
            self.video_playing = False
            
            # TEST MODE: Simulate video loading failure if enabled
            if self._test_video_failure_mode and self._test_failure_type == 'load':
                self.logger.warning(f"[VIDEO-TEST-MODE] Simulating video load failure")
                raise FileNotFoundError(f"Test mode: Simulated video load failure")
            elif self._test_video_failure_mode and self._test_failure_type == 'codec':
                self.logger.warning(f"[VIDEO-TEST-MODE] Simulating codec error")
                raise ValueError(f"Test mode: Unsupported video codec")
            
            # Load video with detailed error handling
            try:
                video = Video(video_path)
                self.logger.debug(f"[VIDEO-LOAD] Successfully loaded video: {os.path.basename(video_path)}")
                video.set_volume(self.config.get('AUDIO_ENABLED', True))
            except FileNotFoundError:
                self.logger.error(f"[VIDEO-LOAD-ERROR] Video file not found: {video_path}")
                self._display_video_error_message(f"Video not found: {os.path.basename(video_path)}")
                return False
            except Exception as e:
                # Log detailed error information
                self.logger.error(f"[VIDEO-LOAD-ERROR] Failed to load video: {os.path.basename(video_path)}")
                self.logger.error(f"[VIDEO-LOAD-ERROR] Video path: {video_path}")
                self.logger.error(f"[VIDEO-LOAD-ERROR] Error type: {type(e).__name__}")
                self.logger.error(f"[VIDEO-LOAD-ERROR] Error message: {str(e)}")
                
                # Show visual error to user
                error_msg = f"Cannot play video: {os.path.basename(video_path)}"
                if "codec" in str(e).lower():
                    error_msg += " (unsupported codec)"
                elif "format" in str(e).lower():
                    error_msg += " (unsupported format)"
                
                self._display_video_error_message(error_msg)
                return False
            
            # Store video metadata for overlay positioning
            if video_metadata:
                self.current_video_metadata = {
                    'width': video_metadata.get('width', self.screen_width),
                    'height': video_metadata.get('height', self.screen_height),
                    'path': video_path
                }
                self.logger.debug(f"[VIDEO-METADATA] Stored video dimensions from metadata: {self.current_video_metadata['width']}x{self.current_video_metadata['height']}")
            else:
                # Fallback if no metadata provided
                self.current_video_metadata = {
                    'width': self.screen_width,
                    'height': self.screen_height,
                    'path': video_path
                }
                self.logger.warning(f"[VIDEO-METADATA] No video metadata provided, using screen dimensions as fallback")
            
            # Resize video for screen
            video_pos = self._resize_video_for_screen(video)
            
            start_time = time.time()
            self.video_playing = True
            self.current_video = video
            
            # Calculate actual video duration for countdown
            # pyvidplayer2 Video object has duration property
            try:
                video_duration = video.duration if hasattr(video, 'duration') and video.duration else max_duration
                # Use minimum of actual video duration and max_duration cap
                slide_timer = min(int(video_duration), max_duration)
                self.logger.debug(f"[VIDEO-COUNTDOWN] Video duration: {video_duration:.1f}s, max_duration: {max_duration}s, using slide_timer: {slide_timer}s")
            except Exception as e:
                self.logger.warning(f"[VIDEO-COUNTDOWN] Could not get video duration: {e}, using max_duration: {max_duration}s")
                slide_timer = max_duration
            
            # Video is now ready - notify controller to start timer
            if hasattr(self, 'controller') and self.controller and hasattr(self.controller, 'current_slide'):
                if hasattr(self.controller, 'start_video_timer'):
                    self.logger.debug(f"[VIDEO-READY] Video setup complete - notifying controller to start timer")
                    self.controller.start_video_timer(self.controller.current_slide)
                else:
                    self.logger.warning(f"[VIDEO-READY] Controller has no start_video_timer method")
            else:
                self.logger.warning(f"[VIDEO-READY] No controller available to start timer")
            
            # Normal video playback loop
            while self.running and self.video_playing and (time.time() - start_time) < max_duration:
                # Check if slideshow is paused
                if hasattr(self, 'controller') and self.controller and self.controller.is_paused:
                    self.logger.debug(f"[VIDEO-PAUSE] Video paused by slideshow controller")
                    
                    # Pause the video
                    pause_success = self.pause_video()
                    if pause_success:
                        self.logger.debug(f"[VIDEO-PAUSE] Video successfully paused")
                    else:
                        self.logger.warning(f"[VIDEO-PAUSE] Failed to pause video")
                    
                    # Show pause overlay
                    self.show_stopped_overlay()
                    
                    # Wait while paused
                    paused_start_time = time.time()
                    while (self.running and self.video_playing and 
                           hasattr(self, 'controller') and self.controller and self.controller.is_paused):
                        pygame.time.wait(50)
                        
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
                                    # Explicitly toggle pause so controller state updates
                                    if hasattr(self, 'controller') and self.controller:
                                        self.controller.toggle_pause()
                                    # Break inner event processing; loop condition will re-check is_paused
                                    break
                                elif event.key in [pygame.K_RIGHT, pygame.K_n]:
                                    # Navigate while paused
                                    self.video_playing = False
                                    video.close()
                                    if hasattr(self, 'controller') and self.controller:
                                        self.controller.next_photo()
                                    return True
                                elif event.key in [pygame.K_LEFT, pygame.K_b]:
                                    # Navigate while paused
                                    self.video_playing = False
                                    video.close()
                                    if hasattr(self, 'controller') and self.controller:
                                        self.controller.previous_photo()
                                    return True
                    
                    # Resume video when unpaused
                    resume_success = self.resume_video()
                    if resume_success:
                        self.logger.debug(f"[VIDEO-RESUME] Video successfully resumed")
                    else:
                        self.logger.warning(f"[VIDEO-RESUME] Failed to resume video")
                    
                    # Adjust timing for pause duration
                    paused_duration = time.time() - paused_start_time
                    start_time += paused_duration
                    self.logger.debug(f"[VIDEO-RESUME] Adjusted timing after {paused_duration:.1f}s pause")
                    continue
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
                    self.logger.debug("Video ended naturally")
                    break
                
                # Clear screen and draw video frame
                self.screen.fill(self.BLACK)
                video.draw(self.screen, video_pos)
                
                # Add video overlays with accurate slide timer countdown
                elapsed_time = time.time() - start_time
                remaining_time = max(0, int(slide_timer - elapsed_time))
                self._add_video_overlays(video_path, remaining_time, self.current_video_overlays)
                
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
            self.logger.error(f"[VIDEO-PLAYBACK-ERROR] Error during video playback")
            self.logger.error(f"[VIDEO-PLAYBACK-ERROR] Video: {os.path.basename(video_path)}")
            self.logger.error(f"[VIDEO-PLAYBACK-ERROR] Error: {str(e)}")
            import traceback
            self.logger.error(f"[VIDEO-PLAYBACK-ERROR] Traceback: {traceback.format_exc()}")
            
            # Clean up state properly
            self.video_playing = False
            if self.current_video:
                try:
                    self.current_video.close()
                except:
                    pass
            self.current_video = None
            
            # Reset countdown state to prevent surface errors
            self._reset_countdown_state()
            
            # Show error message
            self._display_video_error_message(f"Video playback failed: {os.path.basename(video_path)}")
            
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
            
            # Format date if available and enabled (EXACT v2.0 logic)
            if self.config.get('show_date_overlay', True) and photo_data.get('date_taken'):
                date_str = photo_data['date_taken'].strftime('%B %d, %Y')
                overlay_texts.append(date_str)
            
            # Add location if available and enabled
            if self.config.get('show_location_overlay', True) and location_string:
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
    
    def _render_margin_overlay(self, text: str, position: str) -> None:
        """Render overlay text in screen margins using photo overlay styling.
        
        Args:
            text: Text to display
            position: 'left_margin' or 'right_margin'
        """
        try:
            # Use same font and styling as photos
            font_size = 36
            try:
                overlay_font = pygame.font.SysFont('Arial', font_size)
            except:
                overlay_font = pygame.font.Font(None, font_size)
            
            text_surface = overlay_font.render(text, True, (0, 0, 0))  # Black text
            text_width = text_surface.get_width()
            text_height = text_surface.get_height()
            
            # Create background sized exactly to text dimensions (matching photos)
            padding = 8
            bg_width = text_width + 2 * padding
            bg_height = text_height + 2 * padding
            
            # Calculate actual video display dimensions and border gaps
            # Get the current video dimensions if available
            video_display_width = self.screen_width  # Default to full screen
            
            # Try to get actual video dimensions from current video metadata
            if hasattr(self, 'current_video_metadata') and self.current_video_metadata:
                video_width = self.current_video_metadata.get('width', self.screen_width)
                video_height = self.current_video_metadata.get('height', self.screen_height)
                
                # Calculate how the video is scaled to fit screen while maintaining aspect ratio
                video_aspect = video_width / video_height if video_height > 0 else 1.0
                screen_aspect = self.screen_width / self.screen_height
                
                if video_aspect > screen_aspect:
                    # Video is wider - will have letterboxing (black bars top/bottom)
                    # Video uses full screen width
                    video_display_width = self.screen_width
                else:
                    # Video is taller - will have pillarboxing (black bars left/right)
                    # Video width is constrained by height
                    video_display_width = int(self.screen_height * video_aspect)
            
            # Calculate the actual border gap on each side
            total_gap = self.screen_width - video_display_width
            gap_per_side = total_gap // 2
            
            # Calculate center point of each gap and center overlay there
            if gap_per_side > bg_width:
                # Enough space to center overlay in gap
                if position == 'left_margin':
                    # Center overlay in left gap (0 to gap_per_side)
                    gap_center = gap_per_side // 2
                    bg_x = gap_center - bg_width // 2
                elif position == 'right_margin':
                    # Center overlay in right gap (screen_width - gap_per_side to screen_width)
                    right_gap_start = self.screen_width - gap_per_side
                    gap_center = right_gap_start + gap_per_side // 2
                    bg_x = gap_center - bg_width // 2
                else:
                    # Default to left gap
                    gap_center = gap_per_side // 2
                    bg_x = gap_center - bg_width // 2
            else:
                # Gap too small for overlay, fall back to minimal margins
                margin = 10
                if position == 'left_margin':
                    bg_x = margin
                elif position == 'right_margin':
                    bg_x = self.screen_width - bg_width - margin
                else:
                    bg_x = margin
            
            # Center vertically in screen
            bg_y = (self.screen_height - bg_height) // 2
            
            # Draw solid white background (same as photos)
            pygame.draw.rect(self.screen, (255, 255, 255), (bg_x, bg_y, bg_width, bg_height))
            
            # Position text at the center of the background
            text_x = bg_x + bg_width // 2 - text_width // 2
            text_y = bg_y + bg_height // 2 - text_height // 2
            
            # Draw text centered on the white background
            self.screen.blit(text_surface, (text_x, text_y))
            
        except Exception as e:
            self.logger.error(f"Error rendering margin overlay: {e}")
    
    def _add_video_overlays(self, video_path: str, remaining_time: int, overlays: List[Dict[str, Any]] = None) -> None:
        """Add overlays for video display using slideshow controller data (same format as photos)."""
        try:
            # Render date and location overlays from slideshow controller data
            if overlays:
                for overlay in overlays:
                    overlay_type = overlay.get('type')
                    text = overlay.get('text', '')
                    position = overlay.get('position', 'left_margin')
                    
                    if not text:
                        continue
                        
                    # Render date and location overlays using photo styling
                    if overlay_type in ['date', 'location'] and position in ['left_margin', 'right_margin']:
                        self._render_margin_overlay(text, position)
            
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
        events = pygame.event.get()
        
        # If settings window is open, let it handle events first
        if self.settings_window is not None and self.settings_window.is_open():
            filtered_events = []
            for event in events:
                if not self.settings_window.handle_event(event):
                    # Event not handled by settings window, pass it through
                    filtered_events.append(event)
            return filtered_events
        
        return events
    
    def update_display(self) -> None:
        """Update the display."""
        # Update settings window if open
        if self.settings_window is not None and self.settings_window.is_open():
            clock = pygame.time.Clock()
            time_delta = clock.tick(60) / 1000.0
            self.settings_window.update(time_delta)
            self.settings_window.draw()
        
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
    
    def display_video(self, video_path: str, overlays: List[Dict[str, Any]] = None, max_duration: int = None, completion_callback=None, video_metadata: Dict[str, Any] = None) -> bool:
        """Display video with overlays (compatibility method)."""
        if max_duration is None:
            max_duration = self.config.get('VIDEO_MAX_TIMER', 15)
        return self.play_video(video_path, max_duration, completion_callback, overlays, video_metadata)
    
    def pause_video(self) -> None:
        """Pause video playback."""
        if self.current_video and self.video_playing:
            self.current_video.pause()
            self.logger.debug("Video paused")
    
    def resume_video(self) -> None:
        """Resume video playback."""
        if self.current_video and self.video_playing:
            self.current_video.resume()
            self.logger.debug("Video resumed")
    
    def stop_video(self) -> None:
        """Stop video playback."""
        if self.current_video:
            self.current_video.close()
            self.current_video = None
        self.video_playing = False
        self.logger.debug("Video stopped")
    
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
                self.logger.debug("[VIDEO-PAUSE] Video paused successfully")
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
                self.logger.debug("[VIDEO-RESUME] Video resumed successfully")
                return True
            elif hasattr(self.current_video, 'unpause'):
                self.current_video.unpause()
                self.logger.debug("[VIDEO-RESUME] Video unpaused successfully")
                return True
            elif hasattr(self.current_video, 'play'):
                self.current_video.play()
                self.logger.debug("[VIDEO-RESUME] Video play() called successfully")
                return True
            else:
                self.logger.warning("[VIDEO-RESUME] Video object has no resume/unpause/play method")
                return False
        except Exception as e:
            self.logger.error(f"[VIDEO-RESUME] Failed to resume video: {e}")
            return False
    
    def _show_pause_overlay_no_flip(self) -> None:
        """Show pause overlay without calling pygame.display.flip() - for composite rendering."""
        try:
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
            # Note: No pygame.display.flip() - caller handles display update
            
        except Exception as e:
            self.logger.error(f"Error showing pause overlay: {e}")

    def show_stopped_overlay(self) -> None:
        """Show STOPPED overlay when slideshow is paused (centered message only, no black screen)."""
        self._show_pause_overlay_no_flip()
        pygame.display.flip()
    
    # REMOVED: show_video_pause_overlay() - now using unified show_stopped_overlay() for both photos and videos
    
    def clear_stopped_overlay(self) -> None:
        """Clear STOPPED overlay when resuming slideshow."""
        # For videos: The overlay will be cleared when video frames resume drawing
        # For photos: The overlay will be cleared by the next countdown update
        # This approach prevents black screen issues while ensuring overlay disappears
        pass
    
    def show_voice_command_overlay(self, command: str) -> None:
        """Show voice command feedback overlay in top-right corner (photos only).
        
        Args:
            command: The command to display (e.g., 'next', 'stop', 'resume')
        """
        try:
            # Only show for photos (not videos to avoid threading issues)
            if self.video_playing:
                self.logger.debug(f"[VOICE-OVERLAY] Skipping overlay for video (command: {command})")
                return
            
            with self._voice_command_lock:
                # Cancel any existing timer
                if self._voice_command_timer:
                    self._voice_command_timer.cancel()
                
                # Store command text
                self._voice_command_text = command.upper()
                self.logger.debug(f"[VOICE-OVERLAY] Showing command: {self._voice_command_text}")
                
                # Draw the overlay immediately
                self._draw_voice_command_overlay()
                pygame.display.flip()
                
                # Schedule auto-clear after 1.5 seconds
                self._voice_command_timer = threading.Timer(1.5, self._clear_voice_command_overlay)
                self._voice_command_timer.daemon = True
                self._voice_command_timer.start()
        
        except Exception as e:
            self.logger.error(f"Error showing voice command overlay: {e}")
    
    def _draw_voice_command_overlay(self) -> None:
        """Draw voice command overlay in top-right corner (above countdown)."""
        try:
            if not self._voice_command_text:
                return
            
            # Render command text (smaller font)
            command_text = self.small_font.render(self._voice_command_text, True, self.WHITE)
            
            # Position in top-right corner ABOVE countdown timer
            # Countdown is at y=50, so place this at y=10 with good separation
            margin_right = 50  # Same right margin as countdown
            margin_top = 10    # Higher than countdown
            text_rect = command_text.get_rect()
            text_rect.topright = (self.screen_width - margin_right, margin_top)
            
            # Draw background rectangle for better readability
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, (0, 100, 0, 200), bg_rect)  # Dark green background
            pygame.draw.rect(self.screen, self.WHITE, bg_rect, 2)  # White border
            
            # Draw text
            self.screen.blit(command_text, text_rect)
            
        except Exception as e:
            self.logger.error(f"Error drawing voice command overlay: {e}")
    
    def _clear_voice_command_overlay(self) -> None:
        """Clear voice command overlay (called by timer)."""
        try:
            with self._voice_command_lock:
                if self._voice_command_text:
                    self.logger.debug(f"[VOICE-OVERLAY] Auto-clearing command: {self._voice_command_text}")
                    self._voice_command_text = None
                    # Note: Overlay will be cleared on next display update (countdown or video frame)
        
        except Exception as e:
            self.logger.error(f"Error clearing voice command overlay: {e}")
    
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
    
    def show_countdown(self, remaining_seconds: int, manager_id: str = "UNKNOWN") -> None:
        """Show countdown timer overlay in top-right corner (thread-safe)."""
        try:
            if not self.config.get('show_countdown_timer', False):
                return
            
            # Validate pygame screen is initialized
            if not self.screen or not pygame.display.get_surface():
                return
            
            if remaining_seconds <= 0:
                return
            
            # Use thread lock to prevent concurrent surface operations
            with self._surface_lock:
                # Validate surface again inside lock
                if not self.screen or not pygame.display.get_surface():
                    return
                
                # Only update countdown text when value changes to prevent flicker
                if remaining_seconds != self._last_countdown:
                    # Clear the previous countdown area if it exists
                    if self._countdown_rect:
                        try:
                            # Create a slightly larger rectangle to ensure complete clearing
                            clear_rect = self._countdown_rect.inflate(10, 10)
                            pygame.draw.rect(self.screen, self.BLACK, clear_rect)
                        except pygame.error as e:
                            self.logger.debug(f"Error clearing countdown rect: {e}")
                            self._countdown_rect = None
                    
                    countdown_text = f"{remaining_seconds}s"
                    try:
                        self._countdown_text = self.font.render(countdown_text, True, self.WHITE)
                        self._countdown_rect = self._countdown_text.get_rect(topright=(self.screen_width - 50, 50))
                        self._last_countdown = remaining_seconds
                    except pygame.error as e:
                        self.logger.error(f"Error rendering countdown text: {e}")
                        self._reset_countdown_state()
                        return
                
                # Render countdown to screen buffer
                if self._countdown_text and self._countdown_rect:
                    try:
                        self.screen.blit(self._countdown_text, self._countdown_rect)
                        
                        # Also render voice command overlay if active (thread-safe)
                        with self._voice_command_lock:
                            if self._voice_command_text:
                                self._draw_voice_command_overlay()
                        
                        # Only call flip() for photos (videos handle their own display updates)
                        video_state = getattr(self, 'video_playing', False)
                        if not video_state:
                            pygame.display.flip()
                    except pygame.error as e:
                        self.logger.error(f"Error blitting countdown: {e}")
                        self._reset_countdown_state()
                
        except Exception as e:
            self.logger.error(f"Unexpected error showing countdown: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def clear_countdown_timer(self) -> None:
        """Clear countdown timer overlay and reset state (thread-safe)."""
        import threading
        thread_id = threading.current_thread().ident
        self.logger.info(f"[COUNTDOWN-CLEAR] Thread-{thread_id}: Clearing countdown state - last_countdown: {self._last_countdown}")
        
        with self._surface_lock:
            # Clear the countdown area if it exists
            if self._countdown_rect and self.screen and pygame.display.get_surface():
                try:
                    clear_rect = self._countdown_rect.inflate(10, 10)
                    pygame.draw.rect(self.screen, self.BLACK, clear_rect)
                    pygame.display.flip()
                except pygame.error as e:
                    self.logger.warning(f"[COUNTDOWN-CLEAR] Error clearing countdown: {e}")
            
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
    
    # Removed tkinter compatibility methods - using pure pygame approach
    
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
    
    # REMOVED: show_filename_overlay method (per requirements - no filename/hotkey overlays)
    
    # ========== SETTINGS WINDOW METHODS ==========
    
    def show_settings(self) -> None:
        """Show the settings window."""
        if self.settings_window is None:
            self.logger.error("Cannot show settings: settings_window not initialized")
            return
        self.logger.info("Showing settings window")
        self.settings_window.show()
    
    def hide_settings(self) -> None:
        """Hide the settings window."""
        if self.settings_window is None:
            self.logger.error("Cannot hide settings: settings_window not initialized")
            return
        self.logger.info("Hiding settings window")
        self.settings_window.hide()
    
    def is_settings_open(self) -> bool:
        """Check if settings window is currently open."""
        return self.settings_window is not None and self.settings_window.is_open()
    
    # ========== TEST HELPER METHODS ==========
    
    def enable_video_failure_test_mode(self, failure_type: str = 'load') -> None:
        """Enable test mode to simulate video failures.
        
        Args:
            failure_type: Type of failure to simulate: 'load', 'codec', or 'playback'
        """
        valid_types = ['load', 'codec', 'playback']
        if failure_type not in valid_types:
            self.logger.error(f"[TEST-MODE] Invalid failure type: {failure_type}. Must be one of {valid_types}")
            return
        
        self._test_video_failure_mode = True
        self._test_failure_type = failure_type
        self.logger.warning(f"[TEST-MODE] Video failure test mode ENABLED - simulating '{failure_type}' errors")
        self.logger.warning(f"[TEST-MODE] Next video playback will fail with simulated {failure_type} error")
    
    def disable_video_failure_test_mode(self) -> None:
        """Disable test mode and return to normal video playback."""
        self._test_video_failure_mode = False
        self._test_failure_type = None
        self.logger.info(f"[TEST-MODE] Video failure test mode DISABLED - normal playback resumed")
    
    def is_test_mode_enabled(self) -> bool:
        """Check if test mode is currently enabled."""
        return self._test_video_failure_mode
    
    def get_test_failure_type(self) -> str:
        """Get the current test failure type."""
        return self._test_failure_type if self._test_video_failure_mode else None
