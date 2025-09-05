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
from voice_command_service import VoiceCommandService


class SlideshowController:
    """Controls slideshow timing, navigation, and photo sequencing."""
    
    def __init__(self, config, photo_manager, display_manager):
        self.config = config
        self.photo_manager = photo_manager
        self.display_manager = display_manager
        self.location_service = LocationService(config)
        self.logger = logging.getLogger(__name__)
        
        # Initialize voice command service
        self.voice_service = VoiceCommandService(self, config)
        
        # Slideshow state - using indexed selection instead of shuffled list
        self.is_playing = True
        self.is_running = False
        self.show_filename = False
        self.current_photo_pair = None
        
        # Timing
        self.interval = config.get('slideshow_interval', config.get('SLIDESHOW_INTERVAL_SECONDS', 10))
        self.timer_thread = None
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
            if self.voice_service.is_voice_available():
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
    
    def _process_portrait_pairing(self, photos: List[Dict[str, Any]]) -> List[Any]:
        """Process photos to pair portrait photos side by side."""
        try:
            portrait_photos = []
            landscape_photos = []
            
            # Separate portrait and landscape photos
            for photo in photos:
                if self._is_portrait_photo(photo):
                    portrait_photos.append(photo)
                else:
                    landscape_photos.append(photo)
            
            self.logger.info(f"Found {len(portrait_photos)} portrait and {len(landscape_photos)} landscape photos")
            
            # Create pairs from portrait photos
            paired_photos = []
            i = 0
            while i < len(portrait_photos) - 1:
                # Create a pair of two portrait photos
                pair = [portrait_photos[i], portrait_photos[i + 1]]
                paired_photos.append(pair)
                i += 2
            
            # Add any remaining single portrait photo
            if i < len(portrait_photos):
                paired_photos.append(portrait_photos[i])
            
            # Combine paired portraits with landscape photos
            result = paired_photos + landscape_photos
            
            self.logger.info(f"Created {len(paired_photos)} portrait pairs/singles and {len(landscape_photos)} landscape photos")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing portrait pairing: {e}")
            return photos
    
    def _is_portrait_photo(self, photo: Dict[str, Any]) -> bool:
        """Determine if a photo is portrait orientation."""
        try:
            width = photo.get('width', 0)
            height = photo.get('height', 0)
            
            if width > 0 and height > 0:
                return height > width
            
            # Fallback: check orientation from EXIF if available
            orientation = photo.get('exif_orientation', 1)
            # EXIF orientations 6 and 8 are typically portrait after rotation
            return orientation in [6, 8]
            
        except Exception as e:
            self.logger.debug(f"Error determining photo orientation: {e}")
            return False
    
    def _is_image_file(self, filename: str) -> bool:
        """Check if the file is a supported image format."""
        if not filename:
            return False
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.heic', '.heif', '.webp'}
        file_ext = os.path.splitext(filename.lower())[1]
        return file_ext in image_extensions
    
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
            # Check for new photos periodically (at configured interval)
            self._check_cache_refresh()
            
            photo_count = self.photo_manager.get_photo_count()
            if photo_count == 0:
                return
            
            # Get photo from history or generate new random index
            photo = None
            photo_index = None
            
            # If we're navigating through history, use history position
            if self.history_position >= 0 and self.history_position < len(self.photo_history):
                history_data = self.photo_history[self.history_position]
                
                # Check if history data is a pair (tuple) or single index (int)
                if isinstance(history_data, tuple) and len(history_data) == 2:
                    # Photo pair from history
                    photo_index, second_photo_index = history_data
                    photo = self.photo_manager.get_photo_by_index(photo_index)
                    second_photo = self.photo_manager.get_photo_by_index(second_photo_index)
                    
                    if (photo and self._is_image_file(photo.get('filename', '')) and
                        second_photo and self._is_image_file(second_photo.get('filename', ''))):
                        # Valid photo pair from history - display immediately
                        photo_pair = [photo, second_photo]
                        self.current_photo_pair = photo_pair
                        self.logger.info(f"Displaying photo pair from history: {photo['filename']}, {second_photo['filename']} ({photo_index+1}, {second_photo_index+1} of {photo_count})")
                        
                        # Get location string from first photo if GPS coordinates available
                        location_string = None
                        if 'gps_coordinates' in photo:
                            coords = photo['gps_coordinates']
                            location_string = self.location_service.get_location_string(
                                coords['latitude'], coords['longitude']
                            )
                        
                        self.display_manager.display_photo(photo_pair, location_string)
                        self._update_recent_photos([photo, second_photo])
                        
                        # Add photo pair to history if this is a new photo (not from history navigation)
                        if self.history_position == -1:
                            self._add_to_history((photo_index, second_portrait_index))
                        return
                    else:
                        # Invalid photo pair in history, generate new one
                        photo = None
                        photo_index = None
                elif isinstance(history_data, int):
                    # Single photo from history
                    photo_index = history_data
                    photo = self.photo_manager.get_photo_by_index(photo_index)
                    if photo and self._is_image_file(photo.get('filename', '')):
                        # Valid photo from history
                        pass
                    else:
                        # Invalid photo in history, generate new one
                        photo = None
                        photo_index = None
                else:
                    # Invalid history data format
                    photo = None
                    photo_index = None
            
            # If no valid photo from history, generate new random photo
            if not photo:
                attempts = 0
                while attempts < 10 and not photo:
                    photo_index = self.photo_manager.get_random_photo_index()
                    candidate_photo = self.photo_manager.get_photo_by_index(photo_index)
                    
                    if candidate_photo and self._is_image_file(candidate_photo.get('filename', '')):
                        photo = candidate_photo
                        break
                    attempts += 1
            
            if not photo:
                self.logger.warning("Could not find a valid image file to display")
                return
            
            # Check if portrait pairing is enabled and this is a portrait photo
            if (self.config.get('portrait_pairing', True) and 
                photo.get('orientation') == 'portrait'):
                
                # Try to find another portrait photo for pairing
                second_photo = None
                pairing_attempts = 0
                
                while pairing_attempts < 10 and not second_photo:
                    second_portrait_index = self.photo_manager.get_random_portrait_index()
                    
                    if (second_portrait_index is not None and 
                        second_portrait_index != photo_index):
                        candidate_second = self.photo_manager.get_photo_by_index(second_portrait_index)
                        
                        if (candidate_second and 
                            self._is_image_file(candidate_second.get('filename', ''))):
                            second_photo = candidate_second
                            break
                    
                    pairing_attempts += 1
                
                if second_photo:
                    # Display photo pair
                    photo_pair = [photo, second_photo]
                    self.current_photo_pair = photo_pair
                    self.logger.info(f"Displaying photo pair: {photo['filename']}, {second_photo['filename']} ({photo_index+1}, {second_portrait_index+1} of {photo_count})")
                    
                    # Get location string from first photo if GPS coordinates available
                    location_string = None
                    if 'gps_coordinates' in photo:
                        coords = photo['gps_coordinates']
                        location_string = self.location_service.get_location_string(
                            coords['latitude'], coords['longitude']
                        )
                    
                    self.display_manager.display_photo(photo_pair, location_string)
                    self._update_recent_photos([photo, second_photo])
                    
                    # Add photo pair to history if this is a new photo (not from history navigation)
                    if self.history_position == -1:
                        self._add_to_history((photo_index, second_portrait_index))
                else:
                    # Display single portrait photo
                    self.current_photo_pair = photo
                    self.logger.info(f"Displaying photo: {photo['filename']} ({photo_index+1}/{photo_count})")
                    
                    # Get location string if GPS coordinates available
                    location_string = None
                    if 'gps_coordinates' in photo:
                        coords = photo['gps_coordinates']
                        location_string = self.location_service.get_location_string(
                            coords['latitude'], coords['longitude']
                        )
                    
                    self.display_manager.display_photo(photo, location_string)
                    
                    # Add single photo to history if this is a new photo (not from history navigation)
                    if self.history_position == -1:
                        self._add_to_history(photo_index)
            else:
                # Display single photo (landscape or portrait pairing disabled)
                self.current_photo_pair = photo
                self.logger.info(f"Displaying photo: {photo['filename']} ({photo_index+1}/{photo_count})")
                
                # Get location string if GPS coordinates available
                location_string = None
                if 'gps_coordinates' in photo:
                    coords = photo['gps_coordinates']
                    location_string = self.location_service.get_location_string(
                        coords['latitude'], coords['longitude']
                    )
                
                self.display_manager.display_photo(photo, location_string)
                
                # Add single photo to history if this is a new photo (not from history navigation)
                if self.history_position == -1:
                    self._add_to_history(photo_index)
            
            # Update recent photos for anti-repetition
            self._update_recent_photos(self.current_photo_pair)
            
        except Exception as e:
            self.logger.error(f"Error displaying photo: {e}")
    
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
        
        # If we're at current photo, start from the last item in history
        if self.history_position == -1:
            self.history_position = len(self.photo_history) - 1
        # Otherwise, move back in history
        elif self.history_position > 0:
            self.history_position -= 1
        else:
            # Already at the oldest photo in history
            return
        
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
                self._toggle_play_pause()
            elif key == 'left':
                self._navigate_previous()
            elif key == 'right':
                self._navigate_next()
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
        else:
            self.logger.info("Slideshow paused")
    
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
    
    def _stop_timer(self) -> None:
        """Stop auto-advance timer."""
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.cancel()
            self.timer_thread = None
    
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
    
    def _advance_photo_on_main_thread(self) -> None:
        """Advance photo on main thread to avoid GUI threading issues."""
        if self.is_playing and self.is_running:
            self.current_index = (self.current_index + 1) % len(self.photos)
            self._display_current_photo()
            # Restart timer for continuous auto-advance
            self._start_timer()
    
    def next_photo(self) -> None:
        """Public method for voice commands to advance to next photo."""
        self._navigate_next()
    
    def previous_photo(self) -> None:
        """Public method for voice commands to go to previous photo."""
        self._navigate_previous()
    
    def toggle_pause(self) -> None:
        """Public method for voice commands to toggle pause/resume."""
        self._toggle_play_pause()
    
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
