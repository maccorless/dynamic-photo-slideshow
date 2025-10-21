"""
Slideshow controller for Dynamic Photo Slideshow.
Handles timing, navigation, and coordination between components.
"""

import json
import logging
import os
import subprocess
import sys
import time
import random
import threading
from queue import Queue
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from enum import Enum
from slideshow_exceptions import DisplayError, NavigationError, SlideshowError
from slide_timer_manager import SlideTimerManager

class TriggerType(Enum):
    """Types of triggers that can cause slideshow advancement."""
    TIMER = "timer"
    KEY_NEXT = "key_next"
    KEY_PREVIOUS = "key_previous"
    VOICE_NEXT = "voice_next"
    VOICE_PREVIOUS = "voice_previous"
    MOUSE = "mouse"
    STARTUP = "startup"

class Direction(Enum):
    """Direction of slideshow advancement."""
    NEXT = "next"
    PREVIOUS = "previous"

from location_service import LocationService
from path_config import PathConfig
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
        try:
            self.logger.debug(f"Creating VoiceCommandService...")
            self.voice_service = VoiceCommandService(self, config)
            self.logger.debug(f"VoiceCommandService created successfully, is_enabled={self.voice_service.is_enabled}")
        except Exception as e:
            self.logger.error(f"[VOICE-INIT] Failed to create VoiceCommandService: {e}")
            import traceback
            traceback.print_exc()
            # Create a dummy service that's always unavailable
            class DummyVoiceService:
                is_enabled = False
                is_listening = False
                def is_available(self): return False
                def start_listening(self): return False
                def stop_listening_service(self): pass
            self.voice_service = DummyVoiceService()
        
        # Set controller reference in display manager for overlay state checking
        self.display_manager.set_controller_reference(self)
        
        # Initialize state
        self.current_photo_pair = None
        self.current_index = 0
        self.is_playing = False
        self.is_running = False
        self.is_paused = False
        
        # Timer management - NEW: Use SlideTimerManager for clean abstraction
        self.current_timer_manager: Optional[SlideTimerManager] = None
        self.paused_remaining_time: Optional[float] = None
        
        # REMOVED: Legacy timer variables - replaced by SlideTimerManager
        # self.timer_thread = None  # REMOVED
        # self.slideshow_timer = None  # REMOVED
        
        self.current_slide_id = 0  # Track current slide to prevent duplicate timers
        self.last_cache_check = time.time()
        self.cache_refresh_interval = config.get('cache_refresh_check_interval', 3600)  # Default 1 hour
        self.show_filename = False  # Initialize filename display state
        
        # Navigation history for anti-repetition
        self.recent_photos = []
        self.max_recent = config.get('max_recent_photos')
        
        # Slide history cache for previous navigation
        self.slide_history = []
        self.history_position = -1
        self.max_history = config.get('NAV_HISTORY_SIZE', 100)
        
        # Timer advancement flag for main thread processing (macOS compatibility)
        self.timer_advance_requested = False
        
        # Voice command queue for thread-safe main thread processing (macOS/pygame compatibility)
        self.voice_command_queue = Queue()  # Thread-safe FIFO queue for voice commands
        
        # Pause state tracking
        self.pause_start_time = None  # Track when pause started
        self.paused_remaining_time = None  # Track remaining time when paused
        
        # Current slide being displayed
        self.current_slide = None
        
        # Statistics tracking
        self.stats_total_slides = 0
        self.stats_photos_displayed = 0
        self.stats_videos_displayed = 0
    
    # ========================================
    # SINGLE ENTRY POINT - All advancement goes through here
    # ========================================
    
    def advance_slideshow(self, trigger: TriggerType, direction: Direction = Direction.NEXT) -> bool:
        """Advance the slideshow in the specified direction."""
        if not self.is_running:
            return False
        
        # Block input during slide transition to prevent rapid navigation
        if hasattr(self, 'block_input'):
            self.block_input(f"slide navigation ({trigger.value}, {direction.value})")
        
        self.logger.debug(f"Advancing slideshow: {trigger.value} -> {direction.value}")
        
        # Check conditions for advancing
        if not self.is_running:
            return False
        
        # NOTE: Timer cleanup is handled by _display_slide_with_timer() -> _cleanup_previous_slide_timers()
        # DO NOT call _stop_current_timer() here as it causes duplicate cleanup and orphaned threads
        
        # Don't advance if paused (except for navigation keys/voice)
        if (self.is_paused and 
            trigger not in [TriggerType.KEY_NEXT, TriggerType.KEY_PREVIOUS, 
                           TriggerType.VOICE_NEXT, TriggerType.VOICE_PREVIOUS]):
            self.logger.debug(f"Slideshow paused, ignoring {trigger.value}")
            return False
        
        # Determine next slide (create new or get from history)
        slide = self._determine_next_slide(direction)
        if not slide:
            self.logger.error("Failed to determine next slide")
            return False
        
        # 3. Display slide with timer setup (single responsibility)
        success = self._display_slide_with_timer(slide)
        
        if not success:
            self.logger.error("Failed to display slide")
        
        # Unblock input after slide transition completes
        if hasattr(self, 'unblock_input'):
            self.unblock_input()
        
        return success
    
    # ========================================
    # SLIDE DETERMINATION - Single responsibility
    # ========================================
    
    def _determine_next_slide(self, direction: Direction) -> Optional[Dict[str, Any]]:
        """
        Determine what the next slide should be.
        
        This method handles ALL slide determination logic:
        - Navigation state updates
        - History retrieval vs new slide creation
        - Video test mode logic
        
        Args:
            direction: Direction to advance (NEXT or PREVIOUS)
            
        Returns:
            Dict: The slide to display, or None if failed
        """
        if direction == Direction.NEXT:
            return self._determine_next_slide_forward()
        elif direction == Direction.PREVIOUS:
            return self._determine_next_slide_backward()
        else:
            self.logger.error(f"Unknown direction: {direction}")
            return None
    
    def _determine_next_slide_forward(self) -> Optional[Dict[str, Any]]:
        """Determine next slide when going forward."""
        # Update navigation state
        self._navigate_next()
        
        # Get slide based on current navigation state
        if self.history_position >= 0:
            # We're in history mode - get from history
            if self.history_position < len(self.slide_history):
                slide = self.slide_history[self.history_position]
                if self._validate_slide(slide):
                    self.logger.debug(f"Retrieved slide from history position {self.history_position}")
                    return slide
                else:
                    self.logger.warning(f"Invalid slide in history, creating new one")
        
        # Create new slide (includes video test mode logic)
        return self._create_new_slide()
    
    def _determine_next_slide_backward(self) -> Optional[Dict[str, Any]]:
        """Determine next slide when going backward."""
        # Update navigation state
        success = self._navigate_previous()
        if not success:
            self.logger.debug("Cannot go back further in history")
            return None
        
        # Get slide from history
        if self.history_position >= 0 and self.history_position < len(self.slide_history):
            slide = self.slide_history[self.history_position]
            if self._validate_slide(slide):
                self.logger.debug(f"Retrieved slide from history position {self.history_position}")
                return slide
        
        self.logger.error("Failed to retrieve slide from history")
        return None
    
    def _stop_current_timer(self) -> None:
        """Stop the current timer if running."""
        # Use new timer manager to stop timers
        if self.current_timer_manager:
            self.logger.debug("[TIMER] Stopping current timer manager")
            self.current_timer_manager.cancel_all_timers()
            self.current_timer_manager = None
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds using ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                '-show_format', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
                self.logger.debug(f"Video duration for {os.path.basename(video_path)}: {duration}s")
                return duration
            else:
                self.logger.warning(f"Could not get duration for {video_path}: {result.stderr}")
                return self.config.get('VIDEO_MAX_TIMER', 15)  # Fallback to config
                
        except Exception as e:
            self.logger.error(f"Error getting video duration for {video_path}: {e}")
            return self.config.get('VIDEO_MAX_DURATION', 15)  # Fallback to config
    
    def _calculate_slideshow_timer(self, photo_data) -> int:
        """Calculate slideshow timer duration for current slide composition."""
        try:
            # Check if this is a video
            if isinstance(photo_data, dict) and photo_data.get('path'):
                file_path = photo_data['path']
                if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.m4v')):
                    # Get actual video duration
                    video_duration = self._get_video_duration(file_path)
                    config_max = self.config.get('VIDEO_MAX_TIMER', 15)
                    
                    # Use minimum of video duration and config max
                    calculated_duration = min(int(video_duration), config_max)
                    self.logger.debug(f"Video slideshow timer: {calculated_duration}s (video: {video_duration}s, config: {config_max}s)")
                    return calculated_duration
            
            elif isinstance(photo_data, list):
                # Photo pair or list - check if any are videos
                for item in photo_data:
                    if isinstance(item, dict) and item.get('path'):
                        file_path = item['path']
                        if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.m4v')):
                            # If any item in pair is video, treat as video
                            video_duration = self._get_video_duration(file_path)
                            config_max = self.config.get('VIDEO_MAX_TIMER', 15)
                            calculated_duration = min(int(video_duration), config_max)
                            self.logger.debug(f"Mixed content slideshow timer: {calculated_duration}s")
                            return calculated_duration
            
            # Default to photo slideshow interval for photos
            photo_duration = self.config.get('PHOTO_TIMER', 10)
            self.logger.debug(f"Photo slideshow timer: {photo_duration}s")
            return photo_duration
            
        except Exception as e:
            self.logger.error(f"Error calculating slideshow timer: {e}")
            return self.config.get('PHOTO_TIMER', 10)  # Safe fallback
    
    
    def start_slideshow(self) -> None:
        """Start the slideshow with automatic advancement."""
        try:
            # Check for new photos on startup
            self.photo_manager.check_and_load_new_photos()
            
            photo_count = self.photo_manager.get_photo_count()
            if photo_count == 0:
                self.logger.error("No photos available for slideshow")
                return
            
            self.logger.debug(f"Slideshow ready - {photo_count} photos loaded")
            self.is_running = True
            self.is_playing = True  # Set playing state to True when slideshow starts
            self.last_cache_check = time.time()
            
            # Start voice command service if available
            if self.voice_service.is_available():
                if self.voice_service.start_listening():
                    self.logger.debug("Voice commands enabled: say 'next', 'back', 'stop', or 'go'")
                else:
                    self.logger.warning("Voice commands failed to start")
            else:
                self.logger.debug("Voice service not available")
            
            # Display first slide using single entry point
            self.advance_slideshow(TriggerType.STARTUP, Direction.NEXT)
            
            # Start main event loop
            self.display_manager.start_event_loop(self._handle_key_event)
            
        except Exception as e:
            self.logger.error(f"Error starting slideshow: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the slideshow and cleanup resources."""
        self.logger.info("Stopping slideshow...")
        
        # Log statistics summary
        self.logger.info(f"Session Summary: {self.stats_total_slides} slides displayed ({self.stats_photos_displayed} photos, {self.stats_videos_displayed} videos)")
        
        self.is_running = False
        self.is_playing = False
        
        # Stop voice commands FIRST to prevent new callbacks
        if hasattr(self, 'voice_service') and self.voice_service:
            self.voice_service.stop_listening_service()
        
        # Stop timers using new timer manager (fast shutdown - don't wait for threads)
        if self.current_timer_manager:
            self.current_timer_manager.cancel_all_timers(wait_for_threads=False)
            self.current_timer_manager = None
        
        # Stop display manager
        if hasattr(self.display_manager, 'stop'):
            self.display_manager.stop()
    
    
    
    def _check_cache_refresh(self) -> None:
        """Check if it's time to refresh the photo cache and do so if needed."""
        current_time = time.time()
        if current_time - self.last_cache_check >= self.cache_refresh_interval:
            self.logger.debug("Checking for new photos (periodic cache refresh)")
            if self.photo_manager.check_and_load_new_photos():
                self.logger.debug("New photos detected and loaded during slideshow")
            self.last_cache_check = current_time
    
    def _get_current_slide(self) -> Optional[Dict[str, Any]]:
        """Get the current slide based on navigation state."""
        self._check_cache_refresh()
        
        photo_count = self.photo_manager.get_photo_count()
        if photo_count == 0:
            return None
        
        # Check if we're navigating through slide history
        if self.history_position >= 0 and self.history_position < len(self.slide_history):
            slide = self.slide_history[self.history_position]
            
            # Validate that the slide's photos still exist
            if self._validate_slide(slide):
                self.logger.debug(f"Retrieved slide from history position {self.history_position}, type: {slide['type']}")
                return slide
            else:
                self.logger.error(f"Slide at position {self.history_position} contains invalid photos, skipping")
                # Skip this invalid slide and try to move to next valid one
                return None
        
        # Generate new slide if no valid slide from history
        return self._create_new_slide()
    
    def _validate_slide(self, slide: Dict[str, Any]) -> bool:
        """Validate that a slide's photos still exist and are accessible."""
        try:
            for photo_index in slide.get('photo_indices', []):
                photo = self.photo_manager.get_photo_by_index(photo_index)
                if not photo:
                    return False
            return True
        except Exception as e:
            self.logger.error(f"[SLIDE-VALIDATION] Error validating slide: {e}")
            return False
    
    def _create_new_slide(self) -> Optional[Dict[str, Any]]:
        """Create a new slide from a random photo or video."""
        self.logger.debug(f"Creating new slide, video_test_mode: {self.config.get('video_test_mode', False)}")
        
        # Check if video test mode is enabled first to avoid photo flash
        if self.config.get('video_test_mode', False):
            test_video = self._get_test_video_if_applicable()
            if test_video:
                self.logger.debug(f"Using test video: {test_video.get('filename', 'unknown')}")
                return self._create_slide_from_video(test_video, 0)
        
        # Normal slide creation logic
        photo, photo_index = self._get_random_photo()
        if not photo:
            return None
        
        # Determine if this is a video or photo and create appropriate slide
        if self._is_video_content(photo):
            self.logger.debug(f"Random selection was video: {photo.get('filename', 'unknown')}")
            # Use the cached video directly (respects same filter as photos)
            return self._create_slide_from_video(photo, photo_index)
        else:
            return self._create_slide_from_photo(photo, photo_index)
    
    # ========================================
    # SLIDE DISPLAY - Single responsibility
    # ========================================
    
    def _display_slide_with_timer(self, slide: Dict[str, Any]) -> bool:
        """
        Display a slide and set up its timer.
        
        This method handles ALL display responsibilities:
        - Slide display (photos, videos, pairs)
        - Timer setup and starting
        - History management
        - State updates
        
        Args:
            slide: The slide dictionary to display
            
        Returns:
            bool: True if display was successful
        """
        try:
            if not slide:
                self.logger.error("[DISPLAY] No slide provided")
                return False
            
            # CRITICAL: Clean up ALL previous timers BEFORE displaying new slide
            # This ensures no residual timer state from pause/resume cycles
            self._cleanup_previous_slide_timers()
            
            # Capture the slide ID BEFORE updating current_slide (for race condition check later)
            incoming_slide_id = slide.get('slide_id')
            
            # Update current slide state
            self.current_slide = slide
            self.slideshow_timer = slide['slide_timer']
            
            # Display the slide content (photos/videos)
            result = self._display_slide_content(slide)
            self.logger.debug(f"Displayed {slide.get('type')} slide: success={result}")
            
            # Add to history if it's a new slide (not from history navigation)
            if self.history_position == -1:
                self._add_slide_to_history(slide)
            
            # Track statistics
            self.stats_total_slides += 1
            
            # Timer creation - Check we're still on this slide (prevents race condition with async video display)
            # Use the captured incoming_slide_id from before current_slide was updated
            current_slide_id = self.current_slide.get('slide_id') if self.current_slide else None
            
            if incoming_slide_id and current_slide_id and incoming_slide_id != current_slide_id:
                self.logger.debug(f"Skipping timer creation - slide changed")
                return True
            
            # Timer creation - NEW: Always create timer manager regardless of pause state
            slide_type = slide.get('type', 'unknown')
            self._create_slide_timer_manager(slide)
            
            # Start timer only if playing and not video (videos start their own timers)
            if self.is_playing and slide_type != 'video':
                # Photos display immediately, start timer now
                self._start_timer_manager()
            elif slide_type == 'video':
                # Video will start timer when ready (handled by video display manager)
                self.logger.debug(f"Video slide - timer will start when ready")
            else:
                # Slideshow is paused - timer manager created but not started
                self.logger.debug(f"Timer manager created but not started - paused")
            return True
            
        except (OSError, MemoryError) as e:
            self.logger.error(f"[DISPLAY] Error displaying slide: {e}")
            return False
        except Exception as e:
            self.logger.error(f"[DISPLAY] Unexpected error displaying slide: {e}")
            return False
    
    def _display_slide_content(self, slide: Dict[str, Any]) -> bool:
        """Display the actual slide content (photos/videos)."""
        slide_type = slide['type']
        
        try:
            if slide_type == 'portrait_pair':
                return self._display_portrait_pair_content(slide)
            elif slide_type == 'video':
                return self._display_video_content(slide)
            elif slide_type in ['landscape', 'single_portrait']:
                return self._display_single_photo_content(slide)
            else:
                self.logger.error(f"[DISPLAY] Unknown slide type: {slide_type}")
                return False
        except Exception as e:
            self.logger.error(f"[DISPLAY] Error displaying {slide_type} content: {e}")
            return False
    
    # REMOVED: _start_slide_timer - replaced by _start_slide_timer_new (SlideTimerManager)
    # This legacy method was causing double timers and timing conflicts
    
    # NEW TIMER MANAGER METHODS
    # ========================================
    
    def _cleanup_previous_slide_timers(self) -> None:
        """Clean up all timers from previous slide before starting new one."""
        self.logger.debug("Cleaning up previous slide timers")
        
        if self.current_timer_manager:
            # Cancel all timers (this includes join() which will wait)
            self.current_timer_manager.cancel_all_timers()
            self.current_timer_manager = None
        
        # Clear any advancement flags
        self.timer_advance_requested = False
        
        # Clear any paused timing state to ensure clean slate
        self.paused_remaining_time = None
    
    def _create_slide_timer_manager(self, slide: Dict[str, Any]) -> None:
        """Create timer manager for slide (always called regardless of pause state)."""
        # Create new timer manager for this slide (cleanup already done in _display_slide_with_timer)
        self.current_timer_manager = SlideTimerManager(self, self.logger)
        
        slide_timer = slide.get('slide_timer', 10)  # Default 10 seconds
        slide_type = slide.get('type', 'unknown')
        
        self.logger.debug(f"Created timer manager for {slide_type} slide ({slide_timer}s)")
        
        # Store slide info for potential timer start
        self._pending_slide_timer = slide_timer
        self._pending_slide_type = slide_type
    
    def _start_timer_manager(self) -> None:
        """Start the timer manager (only called when slideshow is playing)."""
        if self.current_timer_manager and hasattr(self, '_pending_slide_timer'):
            slide_timer = self._pending_slide_timer
            slide_type = self._pending_slide_type
            
            self.current_timer_manager.start_slide_timing(slide_timer, slide_type)
            
            # Clean up pending info
            delattr(self, '_pending_slide_timer')
            delattr(self, '_pending_slide_type')
        else:
            self.logger.warning(f"Cannot start timer - no manager or pending info")
    
    def _start_slide_timer_new(self, slide: Dict[str, Any]) -> None:
        """Legacy method - now routes to split create/start approach."""
        self._create_slide_timer_manager(slide)
        if self.is_playing:
            self._start_timer_manager()
    
    def _pause_timer_new(self) -> None:
        """Pause timer using new SlideTimerManager (replaces _pause_timer)."""
        if self.current_timer_manager:
            remaining_time = self.current_timer_manager.pause_timing()
            self.paused_remaining_time = remaining_time
            self.logger.debug(f"Timer paused with {remaining_time:.1f}s remaining")
        else:
            self.logger.warning(f"No timer manager to pause")
            self.paused_remaining_time = 5.0  # Fallback
    
    def _resume_timer_new(self) -> None:
        """Resume timer using new SlideTimerManager (replaces _resume_timer)."""
        if self.current_timer_manager and self.paused_remaining_time is not None:
            # Resume existing paused timer
            slide_type = self.current_slide.get('type', 'unknown') if self.current_slide else 'unknown'
            self.logger.debug(f"Resuming timer with {self.paused_remaining_time:.1f}s remaining")
            self.current_timer_manager.resume_timing(self.paused_remaining_time, slide_type)
            self.paused_remaining_time = None
        elif self.current_timer_manager and hasattr(self, '_pending_slide_timer'):
            # Timer manager exists but was never started (created during pause) - start it now
            # Use current slide info, not stale pending info
            if self.current_slide:
                current_slide_type = self.current_slide.get('type', 'unknown')
                current_slide_timer = self.current_slide.get('slide_timer', 10)
                self.logger.debug(f"Starting timer for current slide: {current_slide_type} ({current_slide_timer}s)")
                self.current_timer_manager.start_slide_timing(current_slide_timer, current_slide_type)
                # Clean up pending info
                if hasattr(self, '_pending_slide_timer'):
                    delattr(self, '_pending_slide_timer')
                if hasattr(self, '_pending_slide_type'):
                    delattr(self, '_pending_slide_type')
            else:
                self.logger.warning(f"No current slide available for resume")
                self._start_timer_manager()
        else:
            self.logger.warning(f"Cannot resume timer - missing manager or timing info")
    
    def start_video_timer(self, slide: Dict[str, Any]) -> None:
        """Video timer start - NOT NEEDED since video completion callback handles advancement."""
        if not self.is_playing or not slide:
            self.logger.warning(f"Video not playing or no slide data")
    
    def _schedule_advancement_on_main_thread(self) -> None:
        """Schedule slideshow advancement on the main thread to avoid macOS threading issues."""
        try:
            # Pygame version - set flag for main event loop to check
            # This avoids calling pygame operations from background threads
            self.timer_advance_requested = True
            self.logger.debug("[TIMER] Set timer_advance_requested flag for main thread processing")
        except Exception as e:
            self.logger.error(f"[TIMER] Error scheduling advancement: {e}")
            # Fallback: set flag
            self.timer_advance_requested = True
    
    # Legacy method for compatibility during transition
    def _display_slide(self, slide: Optional[Dict[str, Any]]) -> None:
        """Legacy method - now routes to unified display method."""
        if slide:
            self._display_slide_with_timer(slide)
    
    def _display_portrait_pair_content(self, slide: Dict[str, Any]) -> bool:
        """Display portrait pair content only (no timer logic)."""
        try:
            photos = slide['photos']
            location_string = slide['location_string']
            slideshow_timer = slide['slide_timer']
            
            self.current_photo_pair = photos
            self.logger.debug(f"Displaying portrait pair: {photos[0].get('filename', 'Unknown')}, {photos[1].get('filename', 'Unknown')}")
            
            # Slide ID already assigned during slide creation
            
            # Display the photo pair
            self.display_manager.display_photo(photos, location_string, slideshow_timer)
            
            # Track statistics - portrait pair counts as 2 photos
            self.stats_photos_displayed += 2
            return True
            
        except Exception as e:
            self.logger.error(f"Error displaying portrait pair: {e}")
            return False
    
    # REMOVED: _display_slide_portrait_pair - dead code, replaced by _display_slide_with_timer()
    
    def _display_single_photo_content(self, slide: Dict[str, Any]) -> bool:
        """Display single photo content only (no timer logic)."""
        try:
            photo = slide['photos'][0]
            location_string = slide['location_string']
            slideshow_timer = slide['slide_timer']
            
            self.current_photo_pair = photo
            self.logger.debug(f"Displaying single photo: {photo.get('filename', 'Unknown')}")
            
            # Slide ID already assigned during slide creation
            
            # Display the photo
            self.display_manager.display_photo(photo, location_string, slideshow_timer)
            
            # Track statistics - single photo
            self.stats_photos_displayed += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Error displaying single photo: {e}")
            return False
    
    # REMOVED: _display_slide_single_photo - dead code, replaced by _display_slide_with_timer()
    
    def _display_video_content(self, slide: Dict[str, Any]) -> bool:
        """Display video content only (no timer logic)."""
        try:
            video = slide['photos'][0]  # Videos are stored in photos array for consistency
            location_string = slide['location_string']
            slideshow_timer = slide['slide_timer']
            
            self.current_photo_pair = video
            self.logger.debug(f"Displaying video: {video.get('filename', 'Unknown')}")
            
            # Slide ID already assigned during slide creation
            slide_id = slide.get('slide_id', 'UNKNOWN')
            
            # Display the video using existing video display logic
            video_path = video.get('path')
            
            # Handle videos that need to be exported from Apple Photos
            if not video_path and video.get('needs_export'):
                self.logger.debug(f"Video needs export, calling photo_manager._export_video_temporarily")
                video_path = self.photo_manager._export_video_temporarily(video)
                if video_path:
                    self.logger.debug(f"Successfully exported video to: {video_path}")
                    # Update the video data with the exported path
                    video['path'] = video_path
                    video['needs_export'] = False
                else:
                    self.logger.error(f"Failed to export video: {video.get('filename', 'unknown')}")
                    self.logger.error(f"Video data for debugging: {video}")
                    return False
            
            if video_path:
                video_index = slide.get('photo_indices', [0])[0]
                total_count = self.photo_manager.get_photo_count()
                overlays = self._create_video_overlays(video, video_index, total_count, location_string)
                display_duration = slideshow_timer
                
                # Create completion callback to handle video completion
                def video_completion_callback():
                    self.logger.debug(f"Video completed - advancing to next slide")
                    # Videos don't use timer managers - advance directly
                    self._schedule_advancement_on_main_thread()
                
                success = self.display_manager.display_video(video_path, overlays, display_duration, video_completion_callback, video)
                
                if success:
                    self.logger.debug(f"Successfully displayed video: {video_path}")
                    # Track statistics - video displayed
                    self.stats_videos_displayed += 1
                    return True
                else:
                    self.logger.error(f"Failed to display video: {video_path}")
                    return False
            else:
                self.logger.error("Video path not found in slide")
                return False
                
        except Exception as e:
            self.logger.error(f"Error displaying video: {e}")
            return False
    
    # REMOVED: _display_slide_video - dead code, replaced by _display_slide_with_timer()
    
    
    # REMOVED: _display_current_photo - dead code, replaced by _display_slide_with_timer()
    
    # REMOVED: _display_next_photo - dead code, replaced by advance_slideshow()
    
    # REMOVED: _get_next_photo - dead code, replaced by _determine_next_slide()
    
    # REMOVED: _get_photo_from_history - dead code, replaced by slide-based history in _determine_next_slide()
    
    # REMOVED: _handle_history_photo_pair - dead code, replaced by slide-based history
    
    def _get_random_photo(self) -> tuple[Optional[Dict[str, Any]], Optional[int]]:
        """Generate a new random photo."""
        # Video test mode logic moved to _create_new_slide() to avoid photo flash
        
        attempts = 0
        while attempts < 10:
            photo_index = self.photo_manager.get_random_photo_index()
            candidate_photo = self.photo_manager.get_photo_by_index(photo_index)
            
            if candidate_photo:
                return candidate_photo, photo_index
            attempts += 1
        
        return None, None
    
    def _get_random_photo_only(self) -> tuple[Optional[Dict[str, Any]], Optional[int]]:
        """Generate a random photo (excluding videos)."""
        attempts = 0
        while attempts < 20:  # More attempts since we're filtering out videos
            photo_index = self.photo_manager.get_random_photo_index()
            candidate_photo = self.photo_manager.get_photo_by_index(photo_index)
            
            if candidate_photo and not self._is_video_content(candidate_photo):
                return candidate_photo, photo_index
            attempts += 1
        
        return None, None
    
    def _get_filtered_video(self) -> Optional[Dict[str, Any]]:
        """Get a filtered video based on configuration (person, local availability)."""
        try:
            # Get video filtering configuration
            person_filter = self.config.get('video_person_filter')
            local_only = self.config.get('video_local_only', True)
            
            self.logger.debug(f"Filtering videos - person: '{person_filter}', local_only: {local_only}")
            
            # Get videos from photo manager's photo database
            if not hasattr(self.photo_manager, 'photos_db') or not self.photo_manager.photos_db:
                self.logger.error(f"No photos database available")
                return None
            
            # Start with all videos or filter by person
            if person_filter:
                self.logger.debug(f"Searching for videos with person '{person_filter}'")
                try:
                    all_photos = self.photo_manager.photos_db.photos(persons=[person_filter])
                    candidate_videos = [p for p in all_photos if p.ismovie]
                    self.logger.debug(f"Found {len(candidate_videos)} videos with person '{person_filter}'")
                except Exception as e:
                    self.logger.error(f"Error searching for person '{person_filter}': {e}")
                    return None
            else:
                # No person filter - get all videos
                all_photos = self.photo_manager.photos_db.photos()
                candidate_videos = [p for p in all_photos if p.ismovie]
                self.logger.debug(f"Found {len(candidate_videos)} total videos (no person filter)")
            
            if not candidate_videos:
                self.logger.warning(f"No videos found matching criteria")
                return None
            
            # Filter for local availability if required
            if local_only:
                locally_available = []
                for video in candidate_videos:
                    is_missing = getattr(video, 'ismissing', False)
                    has_path = getattr(video, 'path', None) and os.path.exists(video.path)
                    
                    if not is_missing and has_path:
                        locally_available.append(video)
                
                self.logger.debug(f"{len(locally_available)} of {len(candidate_videos)} videos are locally available")
                candidate_videos = locally_available
            
            if not candidate_videos:
                self.logger.warning(f"No locally available videos found")
                return None
            
            # Select random video from filtered candidates
            import random
            selected_video = random.choice(candidate_videos)
            
            # Extract metadata using existing photo pipeline
            video_data = self.photo_manager._extract_photo_metadata(selected_video)
            if video_data:
                self.logger.debug(f"Selected video: {video_data.get('filename', 'unknown')}")
                return video_data
            else:
                self.logger.error(f"Failed to extract metadata for selected video")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting filtered video: {e}")
            return None
    
    def _get_test_video_if_applicable(self) -> Optional[Dict[str, Any]]:
        """Get real video from Apple Photos for video test mode if applicable."""
        if not self.config.get('video_test_mode', False):
            return None
        
        # Initialize slide count if not set
        if not hasattr(self, 'slide_count'):
            self.slide_count = 0
        
        # Increment slide count for this new slide
        self.slide_count += 1
        
        self.logger.debug(f"Checking slide {self.slide_count} for real video from Apple Photos")
        
        if self.slide_count == 2 or self.slide_count == 5:
            # Get filtered video for slides 2 and 5 using unified method
            self.logger.debug(f"Getting filtered video for slide {self.slide_count}")
            return self._get_filtered_video()
        
        self.logger.debug(f"No test video for slide {self.slide_count}")
        return None
    
    # REMOVED: _get_real_video_for_test - replaced by unified _get_filtered_video method
    
    # REMOVED: _create_test_video_dict - replaced by _get_filtered_video using Apple Photos
    
    # REMOVED: _handle_photo_display - dead code, replaced by _create_slide_from_photo()
    
    # REMOVED: _handle_portrait_photo_display - dead code, replaced by _create_slide_from_photo()
    
    def _display_photo_pair(self, photo: Dict[str, Any], photo_index: int, 
                           second_photo: Dict[str, Any], second_photo_index: int, photo_count: int) -> None:
        """Display a pair of photos/videos with mixed content support."""
        photo_pair = [photo, second_photo]
        
        self.logger.info(f"Displaying photo pair: {photo.get('filename', 'Unknown')}, {second_photo.get('filename', 'Unknown')} ({photo_index+1}, {second_photo_index+1} of {photo_count})")
        self.current_photo_pair = photo_pair
        
        # Calculate slideshow timer for this composition
        self.slideshow_timer = self._calculate_slideshow_timer(photo_pair)
        self.logger.info(f"Photo pair slideshow_timer calculated: {self.slideshow_timer}s")
        
        # Only assign new slide ID if not navigating through history
        if self.history_position == -1:
            self.current_slide_id += 1
            slide_id = self.current_slide_id
        else:
            # When navigating history, use a unique slide ID but don't increment counter
            slide_id = self.current_slide_id + 1000 + self.history_position
        
        # Clear countdown immediately when slide changes to prevent stale display
        if hasattr(self.display_manager, 'clear_countdown_timer'):
            self.display_manager.clear_countdown_timer()
        
        # Check for mixed content (photo + video)
        photo_is_video = self._is_video_content(photo)
        second_is_video = self._is_video_content(second_photo)
        
        if photo_is_video or second_is_video:
            # Handle mixed content - display video first, then photo
            self.logger.info(f"[TRACE-MIXED] Mixed content detected - photo_is_video: {photo_is_video}, second_is_video: {second_is_video}")
            if photo_is_video:
                location_string = self._get_location_string(photo)
                self.logger.info(f"[TRACE-MIXED] About to call _display_video_content with WRONG parameters: photo, {photo_index}, {photo_count}, '{location_string}'")
                self._display_video_content(photo, photo_index, photo_count, location_string)
                self.logger.info(f"[TRACE-MIXED] _display_video_content call completed (or failed)")
            else:
                location_string = self._get_location_string(second_photo)
                self.logger.info(f"[TRACE-MIXED] About to call _display_video_content with WRONG parameters: second_photo, {second_photo_index}, {photo_count}, '{location_string}'")
                self._display_video_content(second_photo, second_photo_index, photo_count, location_string)
                self.logger.info(f"[TRACE-MIXED] _display_video_content call completed (or failed)")
        else:
            # Both are images, display as pair
            location_string = self._get_location_string(photo)
            self.logger.info(f"Calling display_photo with slideshow_timer: {self.slideshow_timer}")
            self.display_manager.display_photo(photo_pair, location_string, self.slideshow_timer)
            
            # Start timer immediately after display
            self.logger.info(f"[PHOTO-PAIR] Starting timer after photo pair display, slide_id: {slide_id}")
            self._start_timer()
        
        self._update_recent_photos([photo, second_photo])
        
        if self.history_position == -1:
            self._add_to_history((photo_index, second_photo_index))
    
    # REMOVED: _display_single_photo - dead code, replaced by _display_single_photo_content()
    
    def _is_video_content(self, content: Dict[str, Any]) -> bool:
        """Check if content is a video file."""
        if not self.display_manager.is_video_supported():
            return False
        
        # Check media_type first (most reliable for Apple Photos)
        if content.get('media_type') == 'video':
            return True
        
        # Fallback to file extension check
        file_path = content.get('path') or content.get('filename', '')
        if file_path:
            return self.photo_manager.video_manager and self.photo_manager.video_manager.is_video_file(file_path)
        
        return False
    
    # Old duplicate method removed - using new unified _display_video_content method above
    
    def _display_photo_content(self, photo: Dict[str, Any], photo_index: int, photo_count: int, location_string: str) -> None:
        """Display photo content (original behavior)."""
        self.current_interval = self.slideshow_timer
        
        self.display_manager.display_photo(photo, location_string, self.slideshow_timer)
        
        # Start timer immediately after display
        self.logger.info(f"[PHOTO-CONTENT] Starting timer after photo content display, slide_id: {self.current_slide_id}")
        self._start_timer()
        
        # Update recent photos and history
        self._update_recent_photos([photo])
        if self.history_position == -1:
            self._add_to_history(photo_index)
    
    def _create_video_overlays(self, video: Dict[str, Any], video_index: int, total_count: int, location_string: str) -> List[Dict[str, Any]]:
        """Create overlay information for video display (matching photo overlay format)."""
        overlays = []
        self.logger.debug(f"[VIDEO-OVERLAY-CREATE] Creating overlays for video: {video.get('filename', 'unknown')}")
        self.logger.debug(f"[VIDEO-OVERLAY-CREATE] Video date_taken: {video.get('date_taken')}")
        self.logger.debug(f"[VIDEO-OVERLAY-CREATE] Location string: {location_string}")
        
        # Add date overlay if available and enabled (same as photos)
        if self.config.get('show_date_overlay', True) and video.get('date_taken'):
            date_str = video['date_taken'].strftime('%B %d, %Y')
            overlays.append({
                'type': 'date',
                'text': date_str,
                'position': 'left_margin'  # Match photo overlay positioning
            })
            self.logger.debug(f"[VIDEO-OVERLAY-CREATE] Added date overlay: {date_str}")
        else:
            self.logger.debug(f"[VIDEO-OVERLAY-CREATE] Date overlay disabled or no date_taken available")
        
        # Add location overlay if available and enabled (same as photos)
        if self.config.get('show_location_overlay', True) and location_string:
            overlays.append({
                'type': 'location',
                'text': location_string,
                'position': 'right_margin'  # Match photo overlay positioning
            })
            self.logger.debug(f"[VIDEO-OVERLAY-CREATE] Added location overlay: {location_string}")
        else:
            self.logger.debug(f"[VIDEO-OVERLAY-CREATE] Location overlay disabled or no location available")
        
        # Add filename overlay if enabled
        if self.show_filename:
            overlays.append({
                'type': 'filename',
                'text': video.get('filename', 'Unknown Video'),
                'position': 'bottom_left'
            })
        
        # Add video info overlay
        overlays.append({
            'type': 'video_info',
            'text': f"Video {video_index+1}/{total_count}",
            'position': 'top_left'
        })
        
        self.logger.debug(f"[VIDEO-OVERLAY-CREATE] Created {len(overlays)} total overlays: {[o['type'] for o in overlays]}")
        return overlays
    
    def pause_video(self) -> None:
        """Pause video playback if currently playing."""
        if self.display_manager.is_video_playing():
            self.display_manager.pause_video()
            self.logger.info("Video paused")
    
    def resume_video(self) -> None:
        """Resume video playback if paused."""
        if self.display_manager.is_video_supported():
            self.display_manager.resume_video()
            self.logger.info("Video resumed")
    
    def stop_video(self) -> None:
        """Stop video playback."""
        if self.display_manager.is_video_supported():
            self.display_manager.stop_video()
            self.logger.info("Video stopped")
    
    def _get_location_string(self, photo: Dict[str, Any]) -> Optional[str]:
        """Get location string from photo GPS coordinates if available."""
        if 'gps_coordinates' not in photo:
            return None
        
        coords = photo['gps_coordinates']
        return self.location_service.get_location_string(
            coords['latitude'], coords['longitude']
        )

    def _find_pairing_partner(self, first_photo: Dict[str, Any], first_photo_index: int) -> (Optional[Dict[str, Any]], Optional[int]):
        """Find a suitable partner for a portrait photo. Supports mixed photo/video pairing."""
        first_media_type = first_photo.get('media_type', 'image')
        
        # Allow pairing for both images and videos
        if first_media_type not in ['image', 'video']:
            return None, None
        
        partner_photo = None
        partner_index = None

        # Try to find a partner (image or video) for 10 attempts
        for _ in range(10):
            partner_index = self.photo_manager.get_random_portrait_image_index()
            if partner_index is not None and partner_index != first_photo_index:
                partner_photo = self.photo_manager.get_photo_by_index(partner_index)
                # Accept both image and video partners
                if partner_photo and partner_photo.get('media_type') in ['image', 'video']:
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
    
    def _create_slide_from_photo(self, photo: Dict[str, Any], photo_index: int) -> Dict[str, Any]:
        """Create a slide from a photo, handling portrait pairing."""
        photo_count = self.photo_manager.get_photo_count()
        
        # Generate slide ID
        self.current_slide_id += 1
        slide_id = self.current_slide_id
        
        # Check if portrait pairing is enabled and this is a portrait photo
        if (self.config.get('PORTRAIT_PHOTO_PAIRING', True) and photo.get('orientation') == 'portrait'):
            second_photo, second_photo_index = self._find_pairing_partner(photo, photo_index)
            
            if second_photo:
                # Create portrait pair slide
                photo_pair = [photo, second_photo]
                slideshow_timer = self._calculate_slideshow_timer(photo_pair)
                location_string = self._get_location_string(photo)
                
                slide = {
                    'type': 'portrait_pair',
                    'photos': photo_pair,
                    'slide_timer': slideshow_timer,
                    'location_string': location_string,
                    'photo_indices': [photo_index, second_photo_index],
                    'slide_id': slide_id
                }
                
                self.logger.debug(f"Created portrait pair slide: {photo.get('filename', 'Unknown')}, {second_photo.get('filename', 'Unknown')} ({photo_index+1}, {second_photo_index+1} of {photo_count})")
                return slide
        
        # Create single photo slide (landscape or single portrait)
        slideshow_timer = self._calculate_slideshow_timer([photo])
        location_string = self._get_location_string(photo)
        
        slide = {
            'type': 'landscape' if photo.get('orientation') != 'portrait' else 'single_portrait',
            'photos': [photo],
            'slide_timer': slideshow_timer,
            'location_string': location_string,
            'photo_indices': [photo_index],
            'slide_id': slide_id
        }
        
        self.logger.debug(f"Created single photo slide: {photo.get('filename', 'Unknown')} ({photo_index+1} of {photo_count})")
        return slide
    
    def _create_slide_from_video(self, video: Dict[str, Any], video_index: int) -> Dict[str, Any]:
        """Create a slide from a video."""
        video_count = self.photo_manager.get_photo_count()
        
        # Generate slide ID
        self.current_slide_id += 1
        slide_id = self.current_slide_id
        
        # Calculate video duration and timer
        slideshow_timer = self._calculate_slideshow_timer([video])
        location_string = self._get_location_string(video)
        
        slide = {
            'type': 'video',
            'photos': [video],  # Keep consistent naming even for videos
            'slide_timer': slideshow_timer,
            'location_string': location_string,
            'photo_indices': [video_index],
            'slide_id': slide_id
        }
        
        self.logger.debug(f"Created video slide: {video.get('filename', 'Unknown')} ({video_index+1} of {video_count})")
        return slide
    
    def _add_slide_to_history(self, slide: Dict[str, Any]) -> None:
        """Add slide to the history cache."""
        # If we're not at the end of history, truncate everything after current position
        if self.history_position >= 0 and self.history_position < len(self.slide_history) - 1:
            self.slide_history = self.slide_history[:self.history_position + 1]
        
        # Add new slide to history
        self.slide_history.append(slide)
        
        # Keep history within size limit
        if len(self.slide_history) > self.max_history:
            self.slide_history = self.slide_history[-self.max_history:]
        
        # Reset history position to indicate we're at the current slide
        self.history_position = -1
        
        self.logger.debug(f"Added slide to history. History length: {len(self.slide_history)}, type: {slide['type']}")
    
    def _add_to_history(self, photo_data) -> None:
        """Legacy method - kept for compatibility during transition."""
        # This method is deprecated but kept to avoid breaking existing code
        # New code should use _add_slide_to_history instead
        pass
    
    def _navigate_to_random(self) -> None:
        """Navigate to a new random slide (exit history mode)."""
        self.history_position = -1
        self.logger.debug("Navigating to new random slide")
    
    def _navigate_previous(self) -> bool:
        """Navigate to previous slide in history. Returns True if navigation was successful."""
        if not self.slide_history:
            self.logger.debug("No slide history available - cannot go back")
            return False
        
        # If we're at the current slide, start from the one before the last item in history
        if self.history_position == -1:
            # Need at least two slides in history to go back
            if len(self.slide_history) < 2:
                self.logger.debug("Need at least 2 slides in history to go back")
                return False
            self.history_position = len(self.slide_history) - 2
            self.logger.debug(f"Moving to slide history position {self.history_position}")
        # Otherwise, move back in history
        elif self.history_position > 0:
            self.history_position -= 1
            self.logger.debug(f"Moving back to slide history position {self.history_position}")
        else:
            # Already at the oldest slide in history
            self.logger.debug("Already at oldest slide in history")
            return False
        
        self.logger.debug(f"Successfully navigated to slide history position {self.history_position}")
        return True
    
    def _navigate_next(self) -> None:
        """Navigate to next slide (forward in history or new random slide)."""
        if self.history_position >= 0:
            # We're in history navigation mode
            if self.history_position < len(self.slide_history) - 1:
                # Move forward in history
                self.history_position += 1
                self.logger.debug(f"Moving forward to slide history position {self.history_position}")
            else:
                # At the end of history, generate new slide
                self.history_position = -1
                self.logger.debug("At end of slide history, will generate new slide")
        else:
            # Normal mode, generate new slide (history_position stays at -1)
            pass
    
    def _handle_key_event(self, event) -> None:
        """Handle keyboard input."""
        try:
            key = event.keysym.lower()
            current_time = time.time()
            
            self.logger.debug(f"Key pressed: {key}")
            
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
    
    # REMOVED: _handle_mouse_event - dead code, not called anywhere
    
    def _toggle_play_pause(self) -> None:
        """Toggle slideshow play/pause state."""
        # Block input during state transition to prevent GPU crashes
        if hasattr(self, 'block_input'):
            action = "resume" if not self.is_playing else "pause"
            self.block_input(f"pause/resume transition ({action})")
        
        self.is_playing = not self.is_playing
        self.is_paused = not self.is_playing
        if self.is_playing:
            self.logger.debug("Slideshow resumed")
            # IMPORTANT: Resume the current slide, don't advance to next
            
            # Clear STOPPED overlay when resuming
            if hasattr(self, 'display_manager') and self.display_manager:
                self.display_manager.clear_stopped_overlay()
            
            # Re-display current slide after clearing overlay
            if self.current_slide:
                # Use self.current_slide directly - DON'T call _get_current_slide() as it may create new slides
                slide = self.current_slide
                # Re-display the current slide without creating a new one
                slide_type = slide.get('type', 'unknown')
                if slide_type in ['portrait_pair', 'single_portrait', 'single_landscape']:
                    # For photos, re-display using display manager
                    photo_data = slide.get('photo_data') or slide.get('photos') or slide.get('images')
                    location_string = slide.get('location_string', '')
                    slideshow_timer = slide.get('slide_timer', 10)
                    
                    if photo_data and hasattr(self, 'display_manager'):
                        try:
                            self.display_manager.display_photo(photo_data, location_string, slideshow_timer)
                        except Exception as e:
                            self.logger.error(f"Error re-displaying photo after resume: {e}")
                    else:
                        self.logger.warning(f"Cannot re-display photo - missing data or display manager")
                    # For videos, let the video loop handle re-display
            
            # Restart timer with preserved remaining time for CURRENT slide
            self._resume_timer_new()  # NEW: Use timer manager
            
            # Unblock input after resume completes
            if hasattr(self, 'unblock_input'):
                self.unblock_input()
        else:
            self.logger.debug("Slideshow paused")
            # Show STOPPED overlay when pausing
            if hasattr(self, 'display_manager') and self.display_manager:
                self.display_manager.show_stopped_overlay()
            # Pause timer and preserve remaining time
            self._pause_timer_new()  # NEW: Use timer manager
            
            # Unblock input after pause completes
            if hasattr(self, 'unblock_input'):
                self.unblock_input()
    
    # REMOVED: _advance_to_next_photo - dead code, replaced by advance_slideshow()
    
    def _toggle_filename_display(self) -> None:
        """Toggle filename overlay display."""
        self.show_filename = not self.show_filename
        # Re-display current slide with updated filename setting
        if self.current_slide:
            slide = self._get_current_slide()
            self._display_slide(slide)
    
    def _start_timer(self) -> None:
        """Start unified timer for both countdown display and auto-advance."""
        if not self.is_playing:
            return
        
        self.timer_id_counter += 1
        timer_id = self.timer_id_counter
        self.logger.info(f"[TIMER-{timer_id}] Starting unified timer - slideshow_timer: {self.slideshow_timer}s, active_threads: {self.active_countdown_threads}")
        
        # Stop any existing timer using new timer manager
        if self.current_timer_manager:
            self.current_timer_manager.cancel_all_timers()
        
        # Clear any existing countdown display before starting new timer
        if hasattr(self.display_manager, 'clear_countdown_timer'):
            self.display_manager.clear_countdown_timer()
        elif hasattr(self.display_manager, 'show_countdown'):
            self.display_manager.show_countdown(0)
        
        # Capture start time once for unified timing
        start_time = time.time()
        self.last_advance_time = start_time
        self.logger.info(f"[TIMER-{timer_id}] Set last_advance_time: {start_time}")
        
        # Determine slide_id based on navigation state
        if self.history_position == -1:
            slide_id = self.current_slide_id
        else:
            slide_id = self.current_slide_id + 1000 + self.history_position
        
        # Store which slide this timer belongs to
        setattr(self, f'_timer_{timer_id}_slide_id', slide_id)
        self.logger.info(f"[TIMER-{timer_id}] Associated with slide {slide_id}")
        
        # Start unified countdown timer that handles both display and auto-advance
        self._start_countdown_timer(timer_id)
    
    # REMOVED: _start_main_timer_only - dead code, replaced by _start_slide_timer()
    
    # REMOVED: _stop_timer - replaced by SlideTimerManager
    
    # REMOVED: _pause_timer - replaced by _pause_timer_new (SlideTimerManager)
    
    # REMOVED: _resume_timer - replaced by _resume_timer_new (SlideTimerManager)
    
    # REMOVED: _restart_timer - replaced by _resume_timer_new (SlideTimerManager)
    
    # REMOVED: _auto_advance and _auto_advance_helper - dead code, replaced by _start_slide_timer()
    
    
    # ========================================
    # PUBLIC API - All route to single entry point
    # ========================================
    
    def next_photo(self) -> None:
        """Public API for next navigation."""
        self.advance_slideshow(TriggerType.KEY_NEXT, Direction.NEXT)
    
    def previous_photo(self) -> None:
        """Public API for previous navigation."""
        self.advance_slideshow(TriggerType.KEY_PREVIOUS, Direction.PREVIOUS)
    
    def voice_next(self) -> None:
        """Public API for voice next command."""
        # Add to queue for thread-safe main thread processing (pygame/macOS compatibility)
        self.voice_command_queue.put('next')
        self.logger.debug("[VOICE] Added 'next' to voice command queue")
    
    def voice_previous(self) -> None:
        """Public API for voice previous command."""
        # Add to queue for thread-safe main thread processing (pygame/macOS compatibility)
        self.voice_command_queue.put('back')
        self.logger.debug("[VOICE] Added 'back' to voice command queue")
    
    def pause_for_voice_command(self) -> None:
        """Pause the timer temporarily for voice command processing."""
        # Store the remaining time and the timer manager ID to avoid race condition
        if self.current_timer_manager and self.current_timer_manager.is_active:
            remaining_time = self.current_timer_manager.pause_timing()
            self.paused_remaining_time = remaining_time
            self.paused_timer_manager_id = id(self.current_timer_manager)
            self.logger.debug(f"[VOICE] Paused timer, saved {remaining_time:.1f}s remaining")

    def resume_after_voice_command(self) -> None:
        """Resume the timer after voice command processing if slideshow is playing."""
        # Only resume if:
        # 1. We actually paused a timer
        # 2. Slideshow is still playing
        # 3. We're still on the SAME slide (timer manager hasn't changed)
        # If navigation happened (next/back), a NEW timer was already created, don't resume old one
        if (self.is_playing and 
            self.paused_remaining_time is not None and
            self.current_timer_manager and
            id(self.current_timer_manager) == getattr(self, 'paused_timer_manager_id', None)):
            # Still on same slide, resume the timer with saved remaining time
            slide_type = self.current_slide.get('type', 'unknown') if self.current_slide else 'unknown'
            self.current_timer_manager.resume_timing(self.paused_remaining_time, slide_type)
            self.logger.debug(f"[VOICE] Resumed timer with {self.paused_remaining_time:.1f}s remaining")
        else:
            if self.paused_remaining_time is not None:
                self.logger.debug(f"[VOICE] Skipping resume - slide changed or no longer playing")
        
        # Clear saved state
        self.paused_remaining_time = None
        self.paused_timer_manager_id = None

    def toggle_pause(self) -> None:
        """Public method for voice commands to toggle pause/resume."""
        # Use same logic as spacebar
        self._toggle_play_pause()
    
    # REMOVED: _start_countdown_timer and _stop_countdown_timer - dead code, replaced by _start_slide_timer()
    
    def _stop_slideshow(self) -> None:
        """Stop the slideshow and exit."""
        self.logger.info("Stopping slideshow")
        self.is_running = False
        self.is_playing = False
        
        # Stop timers using new timer manager
        if self.current_timer_manager:
            self.current_timer_manager.cancel_all_timers()
            self.current_timer_manager = None
        
        # Stop voice command service
        if hasattr(self, 'voice_service'):
            self.voice_service.stop_listening_service()
        
        self.display_manager.destroy()
    
    # REMOVED: _run_event_loop - dead code, replaced by display_manager.start_event_loop()
