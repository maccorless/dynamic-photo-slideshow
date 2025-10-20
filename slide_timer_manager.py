"""
Slide Timer Manager - Provides clean abstraction for slide timing with proper isolation.

This module manages all timing for individual slides, ensuring:
- Only two timers active per slide (advancement + display)
- Complete state isolation between slides
- Proper cleanup when transitioning between slides
- No timer proliferation or orphaned callbacks
"""

import threading
import time
import logging
from typing import Optional, Callable


class SlideTimerManager:
    """Manages all timing for a single slide with proper isolation."""
    
    def __init__(self, controller, logger: Optional[logging.Logger] = None):
        """Initialize timer manager for a slide.
        
        Args:
            controller: The slideshow controller instance
            logger: Optional logger instance
        """
        self.controller = controller
        self.logger = logger or logging.getLogger(__name__)
        
        # Timer state
        self.advancement_timer: Optional[threading.Timer] = None
        self.countdown_thread: Optional[threading.Thread] = None
        self.is_active = False
        
        # Timing information
        self.start_time: Optional[float] = None
        self.duration: Optional[float] = None
        
        # Generate unique ID for this timer manager instance
        import random
        self.manager_id = f"MGR-{random.randint(1000, 9999)}"
        self.logger.debug(f"Timer manager {self.manager_id} created")
        
    def start_slide_timing(self, duration: float, slide_type: str) -> None:
        """Start timing for a slide.
        
        Args:
            duration: Duration in seconds
            slide_type: Type of slide for countdown display
        """
        self.logger.debug(f"Starting {duration}s timer for {slide_type}")
        
        # Cancel any existing timers first
        self.cancel_all_timers()
        
        # Set up timing info
        self.start_time = time.time()
        self.duration = duration
        self.is_active = True
        
        # Start advancement timer
        def advance_callback():
            if self.is_active:  # Only advance if this timer is still active
                self.logger.debug(f"Timer expired after {duration}s - advancing")
                self.controller._schedule_advancement_on_main_thread()
            else:
                self.logger.debug(f"Timer expired but manager inactive - ignoring")
        
        self.advancement_timer = threading.Timer(duration, advance_callback)
        self.advancement_timer.start()
        
        # Start countdown display for photos (videos handle their own countdown)
        if slide_type != 'video' and self.controller.config.get('show_countdown_timer', False):
            self._start_countdown_display(duration)
    
    def cancel_all_timers(self, wait_for_threads: bool = True) -> None:
        """Cancel all timers and mark as inactive.
        
        Args:
            wait_for_threads: If True, wait for threads to finish. If False (shutdown), don't wait.
        """
        self.logger.debug("Canceling timers")
        self.is_active = False
        
        # Cancel advancement timer
        if self.advancement_timer:
            self.advancement_timer.cancel()
            self.advancement_timer = None
            
        # Stop countdown thread
        if self.countdown_thread and self.countdown_thread.is_alive():
            if wait_for_threads:
                # Thread will check is_active and stop itself
                # Wait up to 1.5 seconds for thread to finish (countdown updates every 1s)
                self.countdown_thread.join(timeout=1.5)
                if self.countdown_thread.is_alive():
                    self.logger.warning(f"Countdown thread did not stop in time")
            self.countdown_thread = None
        
        # Clear timing info
        self.start_time = None
        self.duration = None
    
    def advance_immediately(self) -> None:
        """Advance immediately (for video completion or other early advancement)."""
        if self.is_active:
            self.logger.debug("Advancing immediately")
            self.cancel_all_timers()
            self.controller._schedule_advancement_on_main_thread()
        else:
            # For video completion after pause/resume, we should still advance
            # This handles the case where video completes before timer manager is fully resumed
            if hasattr(self.controller, 'current_slide') and self.controller.current_slide:
                slide_type = self.controller.current_slide.get('type', 'unknown')
                if slide_type == 'video':
                    self.logger.debug("Video completion - advancing")
                    self.controller._schedule_advancement_on_main_thread()
    
    def get_remaining_time(self) -> float:
        """Get remaining time on current timer.
        
        Returns:
            Remaining seconds, or 0 if no active timer
        """
        if not self.is_active or not self.start_time or not self.duration:
            return 0.0
        
        elapsed = time.time() - self.start_time
        remaining = max(0.0, self.duration - elapsed)
        return remaining
    
    def pause_timing(self) -> float:
        """Pause timing and return remaining time.
        
        Returns:
            Remaining seconds when paused
        """
        remaining = self.get_remaining_time()
        self.logger.debug(f"Pausing timer with {remaining:.1f}s remaining")
        
        # Set inactive - this is important for pause state
        self.is_active = False
        
        # Cancel timers but keep timing info for resume
        if self.advancement_timer:
            if self.advancement_timer.is_alive():
                self.advancement_timer.cancel()
            self.advancement_timer = None
        
        # Stop countdown but don't clear timing info
        if self.countdown_thread and self.countdown_thread.is_alive():
            # Wait for thread to notice is_active=False and stop
            self.countdown_thread.join(timeout=1.5)
            self.countdown_thread = None
        
        return remaining
    
    def resume_timing(self, remaining_seconds: float, slide_type: str) -> None:
        """Resume timing with specified remaining time.
        
        Args:
            remaining_seconds: Time remaining for the slide
            slide_type: Type of slide for countdown display
        """
        self.logger.debug(f"Resuming timer with {remaining_seconds:.1f}s remaining")
        
        if remaining_seconds <= 0:
            self.logger.debug("No time remaining - advancing immediately")
            self.advance_immediately()
            return
        
        # Set active - resume the timer
        self.is_active = True
        
        # Update timing info
        self.start_time = time.time()
        self.duration = remaining_seconds
        
        # Start new advancement timer with remaining time
        def advance_callback():
            if self.is_active:
                self.logger.debug(f"Resumed timer expired")
                self.controller._schedule_advancement_on_main_thread()
        
        self.advancement_timer = threading.Timer(remaining_seconds, advance_callback)
        self.advancement_timer.start()
        
        # Resume countdown display for photos
        if slide_type != 'video' and self.controller.config.get('show_countdown_timer', False):
            self._start_countdown_display(remaining_seconds)
    
    def _start_countdown_display(self, duration_seconds: float) -> None:
        """Start countdown display thread.
        
        Args:
            duration_seconds: Duration for countdown display
        """
        def countdown_worker():
            """Worker function for countdown display thread."""
            try:
                while self.is_active and duration_seconds > 0:
                    remaining = self.get_remaining_time()
                    
                    if remaining <= 0 or not self.is_active:
                        break
                    
                    # Show countdown via display manager
                    if (hasattr(self.controller, 'display_manager') and 
                        hasattr(self.controller.display_manager, 'show_countdown')):
                        self.controller.display_manager.show_countdown(int(remaining), self.manager_id)
                    
                    # Sleep in small intervals to allow faster shutdown response
                    # Check is_active every 100ms instead of sleeping for full second
                    for _ in range(10):
                        if not self.is_active:
                            break
                        time.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"Error in countdown display: {e}")
        
        self.countdown_thread = threading.Thread(target=countdown_worker, daemon=True)
        self.countdown_thread.start()
    
    def is_timer_active(self) -> bool:
        """Check if timer manager is currently active.
        
        Returns:
            True if timer is active and managing a slide
        """
        return self.is_active
    
    def __str__(self) -> str:
        """String representation for debugging."""
        status = "active" if self.is_active else "inactive"
        remaining = self.get_remaining_time() if self.is_active else 0
        return f"SlideTimerManager({status}, {remaining:.1f}s remaining)"
