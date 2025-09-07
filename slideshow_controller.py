"""
Slideshow controller for Dynamic Photo Slideshow.
Handles timing, navigation, and coordination between components.
"""

import logging
import os
import random
import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from location_service import LocationService
from path_config import PathConfig
from slideshow_exceptions import NavigationError, DisplayError, SlideshowError
from voice_command_service import VoiceCommandService


class SlideshowController:
    """Controls slideshow timing, navigation, and photo sequencing."""
    
    def __init__(self, config, photo_manager, display_manager, path_config=None):
        self.config = config
        self.photo_manager = photo_manager
        self.display_manager = display_manager
        self.path_config = path_config
        self.location_service = LocationService(config, path_config)
        self.logger = logging.getLogger(__name__)
        
        # Initialize voice command service
        self.voice_service = VoiceCommandService(self, config)
        
        # Set controller reference in display manager for overlay state checking
        self.display_manager.set_controller_reference(self)
        
        # Slideshow state - using indexed selection instead of shuffled list
        self.is_playing = True
        self.is_running = False
        self.show_filename = False
        self.current_photo_pair = None
        
        # Timing
        self.interval = config.get('slideshow_interval', 10)
        self.timer_thread = None
        self.countdown_thread = None
        self.last_advance_time = 0
        self.last_cache_check = time.time()
        self.cache_refresh_interval = config.get('cache_refresh_check_interval', 3600)  # Default 1 hour
        
        # Navigation history for anti-repetition
        self.recent_photos = []
        self.max_recent = config.get('max_recent_photos')
        
        # Photo history cache for previous navigation
        self.photo_history = []
        self.history_position = -1
        self.max_history = config.get('photo_history_cache_size', 100)
        
        # Auto-advance flag for main thread processing
        self.auto_advance_requested = False
        
        # Voice command properties
        self.is_paused = False
    
    def start_slideshow(self) -> None:
        """Start the slideshow with automatic advancement."""
        try:
            # Check for new photos on startup
            self.photo_manager.check_and_load_new_photos()
            
            photo_count = self.photo_manager.get_photo_count()
            if photo_count == 0:
                self.logger.error("No photos available for slideshow")
                return
            
            self.logger.info(f"Starting slideshow with {photo_count} photos")
            self.is_running = True
            self.last_cache_check = time.time()
            
            # Start voice command service if available
            if self.voice_service.is_available():
                if self.voice_service.start_listening():
                    self.logger.info("Voice commands enabled: say 'next', 'back', 'stop', or 'go'")
                else:
                    self.logger.warning("Voice commands failed to start")
            
            # Display first photo(s)
            self._display_next_photo()
            
            # Start auto-advance timer
            self._start_timer()
            
            # Start main event loop
            self.display_manager.start_event_loop(self._handle_key_event)
            
        except Exception as e:
            self.logger.error(f"Error starting slideshow: {e}")
            raise
    
    
    
    def _check_cache_refresh(self) -> None:
        """Check if it's time to refresh the photo cache and do so if needed."""
        current_time = time.time()
        if current_time - self.last_cache_check >= self.cache_refresh_interval:
            self.logger.debug("Checking for new photos (periodic cache refresh)")
            if self.photo_manager.check_and_load_new_photos():
                self.logger.info("New photos detected and loaded during slideshow")
            self.last_cache_check = current_time
    
    def _display_next_photo(self) -> None:
        """Display the next photo or photo pair using indexed selection."""
        try:
            self._check_cache_refresh()
            
            photo_count = self.photo_manager.get_photo_count()
            if photo_count == 0:
                return
            
            # Check if we're navigating through history and have a photo pair
            if self.history_position >= 0 and self.history_position < len(self.photo_history):
                history_data = self.photo_history[self.history_position]
                
                # If it's a photo pair from history, handle it directly
                if isinstance(history_data, tuple) and len(history_data) == 2:
                    photo, photo_index = self._handle_history_photo_pair(history_data)
                    return  # Photo pair already displayed in _handle_history_photo_pair
            
            # Get photo from history or generate new one
            photo, photo_index = self._get_next_photo()
            if not photo:
                self.logger.warning("Could not find a valid image file to display")
                return
            
            # Handle photo display based on orientation and pairing settings
            self._handle_photo_display(photo, photo_index, photo_count)
            
        except (OSError, MemoryError) as e:
            self.logger.error(f"Error displaying photo: {e}")
        except Exception as e:
            raise DisplayError(f"Unexpected error displaying photo: {e}")
    
    def _get_next_photo(self) -> tuple[Optional[Dict[str, Any]], Optional[int]]:
        """Get the next photo to display from history or generate new random photo."""
        # Try to get photo from history first
        photo, photo_index = self._get_photo_from_history()
        if photo:
            return photo, photo_index
        
        # Generate new random photo if no valid photo from history
        return self._get_random_photo()
    
    def _get_photo_from_history(self) -> tuple[Optional[Dict[str, Any]], Optional[int]]:
        """Get photo from navigation history if available."""
        if not (self.history_position >= 0 and self.history_position < len(self.photo_history)):
            return None, None
        
        history_data = self.photo_history[self.history_position]
        
        # Handle photo pair from history
        if isinstance(history_data, tuple) and len(history_data) == 2:
            return self._handle_history_photo_pair(history_data)
        
        # Handle single photo from history
        elif isinstance(history_data, int):
            photo_index = history_data
            photo = self.photo_manager.get_photo_by_index(photo_index)
            return (photo, photo_index) if photo else (None, None)
        
        return None, None
    
    def _handle_history_photo_pair(self, history_data: tuple) -> tuple[Optional[Dict[str, Any]], Optional[int]]:
        """Handle photo pair from history."""
        photo_index, second_photo_index = history_data
        photo = self.photo_manager.get_photo_by_index(photo_index)
        second_photo = self.photo_manager.get_photo_by_index(second_photo_index)
        
        if photo and second_photo:
            photo_count = self.photo_manager.get_photo_count()
            photo_pair = [photo, second_photo]
            self.current_photo_pair = photo_pair
            
            self.logger.info(f"Displaying photo pair from history: {photo['filename']}, {second_photo['filename']} ({photo_index+1}, {second_photo_index+1} of {photo_count})")
            
            location_string = self._get_location_string(photo)
            self.display_manager.display_photo(photo_pair, location_string)
            self._update_recent_photos([photo, second_photo])
            
            if self.history_position == -1:
                self._add_to_history((photo_index, second_photo_index))
            
            return photo, photo_index  # Return first photo for consistency
        
        return None, None
    
    def _get_random_photo(self) -> tuple[Optional[Dict[str, Any]], Optional[int]]:
        """Generate a new random photo."""
        attempts = 0
        while attempts < 10:
            photo_index = self.photo_manager.get_random_photo_index()
            candidate_photo = self.photo_manager.get_photo_by_index(photo_index)
            
            if candidate_photo:
                return candidate_photo, photo_index
            attempts += 1
        
        return None, None
    
    def _handle_photo_display(self, photo: Dict[str, Any], photo_index: int, photo_count: int) -> None:
        """Handle the display of a photo, including pairing logic."""
        # Check if portrait pairing is enabled and this is a portrait photo
        if (self.config.get('portrait_pairing', True) and photo.get('orientation') == 'portrait'):
            self._handle_portrait_photo_display(photo, photo_index, photo_count)
        else:
            self._display_single_photo(photo, photo_index, photo_count)
    
    def _handle_portrait_photo_display(self, photo: Dict[str, Any], photo_index: int, photo_count: int) -> None:
        """Handle display of portrait photos with pairing logic."""
        second_photo, second_photo_index = self._find_pairing_partner(photo, photo_index)
        
        if second_photo:
            self._display_photo_pair(photo, photo_index, second_photo, second_photo_index, photo_count)
        else:
            self._display_single_photo(photo, photo_index, photo_count)
    
    def _display_photo_pair(self, photo: Dict[str, Any], photo_index: int, 
                           second_photo: Dict[str, Any], second_photo_index: int, photo_count: int) -> None:
        """Display a pair of photos."""
        photo_pair = [photo, second_photo]
        self.current_photo_pair = photo_pair
        
        self.logger.info(f"Displaying photo pair: {photo['filename']}, {second_photo['filename']} ({photo_index+1}, {second_photo_index+1} of {photo_count})")
        
        location_string = self._get_location_string(photo)
        self.display_manager.display_photo(photo_pair, location_string)
        self._update_recent_photos([photo, second_photo])
        
        if self.history_position == -1:
            self._add_to_history((photo_index, second_photo_index))
    
    def _display_single_photo(self, photo: Dict[str, Any], photo_index: int, photo_count: int) -> None:
        """Display a single photo."""
        self.current_photo_pair = photo
        self.logger.info(f"Displaying photo: {photo['filename']} ({photo_index+1}/{photo_count})")
        
        location_string = self._get_location_string(photo)
        
        # Set interval based on media type
        if photo['media_type'] in ['video', 'live_photo'] and self.config.get('video_playback_enabled'):
            self.display_manager.display_video(photo['path'], self.config.get('video_audio_enabled'))
            self.interval = self.config.get('video_max_duration', 10)
        else:
            self.display_manager.display_photo(photo, location_string)
            self.interval = self.config.get('slideshow_interval', 10)
        
        # Update recent photos and history
        self._update_recent_photos(self.current_photo_pair)
        if self.history_position == -1:
            self._add_to_history(photo_index)
    
    def _get_location_string(self, photo: Dict[str, Any]) -> Optional[str]:
        """Get location string from photo GPS coordinates if available."""
        if 'gps_coordinates' not in photo:
            return None
        
        coords = photo['gps_coordinates']
        return self.location_service.get_location_string(
            coords['latitude'], coords['longitude']
        )

    def _find_pairing_partner(self, first_photo: Dict[str, Any], first_photo_index: int) -> (Optional[Dict[str, Any]], Optional[int]):
        """Find a suitable partner for a portrait photo. Only pairs image files since video playback was removed."""
        first_media_type = first_photo.get('media_type', 'image')
        
        # Only pair image files - skip video files since display manager can't handle them
        if first_media_type not in ['image']:
            return None, None
        
        partner_photo = None
        partner_index = None

        # Try to find an image partner for 10 attempts
        for _ in range(10):
            partner_index = self.photo_manager.get_random_portrait_image_index()
            if partner_index is not None and partner_index != first_photo_index:
                partner_photo = self.photo_manager.get_photo_by_index(partner_index)
                # Ensure partner is also an image file
                if partner_photo and partner_photo.get('media_type') == 'image':
                    return partner_photo, partner_index

        return None, None
    
    def _update_recent_photos(self, photos) -> None:
        """Update the list of recently displayed photos to avoid repetition."""
        if isinstance(photos, list):
            for photo in photos:
                if photo and 'uuid' in photo:
                    self.recent_photos.append(photo['uuid'])
        elif photos and 'uuid' in photos:
            self.recent_photos.append(photos['uuid'])
        
        # Keep only the most recent photos
        if len(self.recent_photos) > self.max_recent:
            self.recent_photos = self.recent_photos[-self.max_recent:]
    
    def _add_to_history(self, photo_data) -> None:
        """Add photo data to the history cache. Can be single index or pair of indexes."""
        # If we're not at the end of history, truncate everything after current position
        if self.history_position >= 0 and self.history_position < len(self.photo_history) - 1:
            self.photo_history = self.photo_history[:self.history_position + 1]
        
        # Add new photo data to history (can be int for single photo or tuple for pair)
        self.photo_history.append(photo_data)
        
        # Keep history within size limit
        if len(self.photo_history) > self.max_history:
            self.photo_history = self.photo_history[-self.max_history:]
        
        # Reset history position to indicate we're at the current photo
        self.history_position = -1
    
    def _navigate_previous(self) -> None:
        """Navigate to previous photo in history."""
        if not self.photo_history:
            return
        
        # If we're at the current photo, start from the one before the last item in history
        if self.history_position == -1:
            # Need at least two photos in history to go back
            if len(self.photo_history) < 2:
                return
            self.history_position = len(self.photo_history) - 2
        # Otherwise, move back in history
        elif self.history_position > 0:
            self.history_position -= 1
        else:
            # Already at the oldest photo in history
            return
        
        # Display the photo from history
        self._display_next_photo()
    
    def _navigate_next(self) -> None:
        """Navigate to next photo (forward in history or new random photo)."""
        if self.history_position >= 0:
            # We're in history navigation mode
            if self.history_position < len(self.photo_history) - 1:
                # Move forward in history
                self.history_position += 1
                self._display_next_photo()
            else:
                # At the end of history, generate new photo
                self.history_position = -1
                self._display_next_photo()
        else:
            # Normal mode, generate new photo
            self._display_next_photo()
    
    def _handle_key_event(self, event) -> None:
        """Handle keyboard input."""
        try:
            key = event.keysym.lower()
            
            if key == 'escape':
                self._stop_slideshow()
            elif key == 'space':
                self.toggle_pause()  # Use same method as voice commands
            elif key == 'left':
                self.previous_photo()  # Use same method as voice commands
            elif key == 'right':
                self.next_photo()  # Use same method as voice commands
            elif key == 'shift_l' or key == 'shift_r':
                self._toggle_filename_display()
            
        except Exception as e:
            self.logger.error(f"Error handling key event: {e}")
    
    def _handle_mouse_event(self, event_type: str) -> None:
        """Handle mouse input."""
        try:
            if event_type == 'single_click':
                self._previous_photo()
            elif event_type == 'double_click':
                self._next_photo()
        except Exception as e:
            self.logger.error(f"Error handling mouse event: {e}")
    
    def _toggle_play_pause(self) -> None:
        """Toggle slideshow play/pause state."""
        self.is_playing = not self.is_playing
        self.is_paused = not self.is_playing
        if self.is_playing:
            self.logger.info("Slideshow resumed")
            # Clear STOPPED overlay when resuming
            if hasattr(self, 'display_manager') and self.display_manager:
                self.display_manager.clear_stopped_overlay()
            # Restart timer
            self._restart_timer()
        else:
            self.logger.info("Slideshow paused")
            # Show STOPPED overlay when pausing
            if hasattr(self, 'display_manager') and self.display_manager:
                self.display_manager.show_stopped_overlay()
            # Stop timer
            self._stop_timer()
    
    def _advance_to_next_photo(self) -> None:
        """Advance to the next photo in the sequence."""
        self._navigate_next()
        
        # Reset timer
        if self.is_playing:
            self._restart_timer()
    
    def _toggle_filename_display(self) -> None:
        """Toggle filename overlay display."""
        self.show_filename = not self.show_filename
        # Re-display current photo with updated filename setting
        if self.current_photo_pair:
            self._display_next_photo()
    
    def _start_timer(self) -> None:
        """Start auto-advance timer."""
        if not self.is_playing:
            return
        
        self._stop_timer()  # Stop any existing timer
        self.last_advance_time = time.time()
        self.timer_thread = threading.Timer(self.interval, self._auto_advance)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        # Start countdown timer display
        self._start_countdown_timer()
    
    def _start_main_timer_only(self) -> None:
        """Start only the main auto-advance timer without resetting countdown."""
        if not self.is_playing:
            return
        
        # Only stop and restart the main timer, leave countdown running
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.cancel()
            self.timer_thread = None
        
        self.last_advance_time = time.time()
        self.timer_thread = threading.Timer(self.interval, self._auto_advance)
        self.timer_thread.daemon = True
        self.timer_thread.start()
    
    def _stop_timer(self) -> None:
        """Stop auto-advance timer."""
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.cancel()
            self.timer_thread = None
        self._stop_countdown_timer()
    
    def _restart_timer(self) -> None:
        """Restart auto-advance timer."""
        self._stop_timer()
        self._start_timer()
    
    def _auto_advance(self) -> None:
        """Auto-advance to next photo."""
        if self.is_playing and self.is_running:
            self.logger.debug(f"Auto-advancing after {self.interval} seconds")
            # Use tkinter's after method to safely call from timer thread
            if self.display_manager.root:
                self.display_manager.root.after(0, self._navigate_next)
                self.display_manager.root.after(0, self._start_timer)
    
    
    def next_photo(self) -> None:
        """Public method for both voice commands and keyboard navigation."""
        was_paused = self.is_paused
        self._navigate_next()
        if not was_paused:
            # Reset countdown timer AFTER photo change
            self._restart_timer()
        if was_paused:
            self.is_playing = False
            self.is_paused = True
    
    def previous_photo(self) -> None:
        """Public method for both voice commands and keyboard navigation."""
        was_paused = self.is_paused
        self._navigate_previous()
        if not was_paused:
            # Reset countdown timer AFTER photo change
            self._restart_timer()
        if was_paused:
            self.is_playing = False
            self.is_paused = True
    
    def pause_for_voice_command(self) -> None:
        """Pause both timers for voice command processing without changing play state."""
        # Stop main timer
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.cancel()
            self.timer_thread = None
        
        # Also stop countdown timer to freeze the display
        self._stop_countdown_timer()

    def resume_after_voice_command(self) -> None:
        """Resume the timer after voice command processing if slideshow is playing."""
        if self.is_playing:
            self._restart_timer()

    def toggle_pause(self) -> None:
        """Public method for voice commands to toggle pause/resume."""
        # Use same logic as spacebar
        self._toggle_play_pause()
    
    def _start_countdown_timer(self) -> None:
        """Start countdown timer display thread."""
        if not self.config.get('show_countdown_timer', False):
            return
        
        self._stop_countdown_timer()  # Stop any existing countdown timer
        
        def countdown_loop():
            while self.is_playing and self.is_running and self.timer_thread and self.timer_thread.is_alive():
                try:
                    elapsed = time.time() - self.last_advance_time
                    remaining = max(0, int(self.interval - elapsed))
                    
                    # Update countdown display on main thread
                    if self.display_manager.root:
                        self.display_manager.root.after(0, lambda r=remaining: self.display_manager.update_countdown_timer(r))
                    
                    if remaining <= 0:
                        break
                    
                    time.sleep(1)  # Update every second
                except Exception as e:
                    self.logger.error(f"Error in countdown timer: {e}")
                    break
        
        self.countdown_thread = threading.Thread(target=countdown_loop, daemon=True)
        self.countdown_thread.start()
    
    def _stop_countdown_timer(self) -> None:
        """Stop countdown timer display."""
        if self.countdown_thread and self.countdown_thread.is_alive():
            self.countdown_thread = None
        
        # Clear countdown display
        if self.display_manager:
            self.display_manager.clear_countdown_timer()
    
    def _stop_slideshow(self) -> None:
        """Stop the slideshow and exit."""
        self.logger.info("Stopping slideshow")
        self.is_running = False
        self.is_playing = False
        self._stop_timer()
        
        # Stop voice command service
        if hasattr(self, 'voice_service'):
            self.voice_service.stop_listening_service()
        
        self.display_manager.destroy()
    
    def _run_event_loop(self) -> None:
        """Run the main event loop."""
        try:
            while self.is_running:
                # Check for auto-advance request from timer thread
                if self.auto_advance_requested:
                    self.auto_advance_requested = False
                    self._advance_photo_on_main_thread()
                
                self.display_manager.update()
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
        except Exception as e:
            self.logger.error(f"Error in event loop: {e}")
        finally:
            self._stop_timer()
