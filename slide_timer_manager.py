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
        self.logger.info(f"[TIMER-{self.manager_id}] Timer manager instance created")
        
    def start_slide_timing(self, duration: float, slide_type: str) -> None:
        """Start timing for a slide.
        
        Args:
            duration: Duration in seconds
            slide_type: Type of slide for countdown display
        """
        current_time = time.time()
        self.logger.info(f"[TIMER-DEBUG] ===== STARTING TIMER ======")
        self.logger.info(f"[TIMER-DEBUG] Slide type: {slide_type}")
        self.logger.info(f"[TIMER-DEBUG] Duration: {duration}s")
        self.logger.info(f"[TIMER-DEBUG] Start time: {current_time:.3f}")
        self.logger.info(f"[TIMER-DEBUG] Expected end time: {current_time + duration:.3f}")
        
        # Cancel any existing timers first
        self.cancel_all_timers()
        
        # Set up timing info
        self.start_time = current_time
        self.duration = duration
        self.is_active = True
        
        # Start advancement timer
        def advance_callback():
            if self.is_active:  # Only advance if this timer is still active
                actual_duration = time.time() - self.start_time if self.start_time else 0
                self.logger.info(f"[TIMER-DEBUG] ===== TIMER EXPIRED ======")
                self.logger.info(f"[TIMER-DEBUG] Expected duration: {duration}s")
                self.logger.info(f"[TIMER-DEBUG] Actual duration: {actual_duration:.3f}s")
                self.logger.info(f"[TIMER-DEBUG] Timer still active: {self.is_active}")
                self.logger.info(f"[TIMER-DEBUG] Advancing slideshow now")
                self.controller._schedule_advancement_on_main_thread()
            else:
                self.logger.warning(f"[TIMER-DEBUG] Timer expired but manager inactive - ignoring")
        
        self.advancement_timer = threading.Timer(duration, advance_callback)
        self.advancement_timer.start()
        self.logger.info(f"[TIMER-MGR] Started advancement timer for {duration}s")
        
        # Start countdown display for photos (videos handle their own countdown)
        if slide_type != 'video' and self.controller.config.get('show_countdown_timer', False):
            self._start_countdown_display(duration)
    
    def cancel_all_timers(self, wait_for_threads: bool = True) -> None:
        """Cancel all timers and mark as inactive.
        
        Args:
            wait_for_threads: If True, wait for threads to finish. If False (shutdown), don't wait.
        """
        current_time = time.time()
        elapsed = current_time - self.start_time if self.start_time else 0
        remaining = self.duration - elapsed if self.duration else 0
        
        self.logger.info(f"[TIMER-DEBUG] ===== CANCELING TIMERS ======")
        self.logger.info(f"[TIMER-DEBUG] Was active: {self.is_active}")
        self.logger.info(f"[TIMER-DEBUG] Elapsed time: {elapsed:.3f}s")
        self.logger.info(f"[TIMER-DEBUG] Remaining time: {remaining:.3f}s")
        
        self.is_active = False
        
        # Cancel advancement timer
        if self.advancement_timer:
            self.advancement_timer.cancel()
            if self.advancement_timer.is_alive():
                self.logger.info(f"[TIMER-MGR] Canceled advancement timer")
            self.advancement_timer = None
            
        # Stop countdown thread
        if self.countdown_thread and self.countdown_thread.is_alive():
            if wait_for_threads:
                self.logger.info(f"[TIMER-MGR] Stopping countdown thread, waiting for it to finish...")
                # Thread will check is_active and stop itself
                # Wait up to 1.5 seconds for thread to finish (countdown updates every 1s)
                self.countdown_thread.join(timeout=1.5)
                if self.countdown_thread.is_alive():
                    self.logger.warning(f"[TIMER-MGR] Countdown thread did not stop in time (still alive after 1.5s)")
                else:
                    self.logger.info(f"[TIMER-MGR] Countdown thread stopped successfully")
            else:
                # On shutdown, don't wait - daemon thread will be cleaned up by Python
                self.logger.info(f"[TIMER-MGR] Shutdown mode - not waiting for countdown thread (daemon will exit)")
            self.countdown_thread = None
        
        # Clear timing info
        self.start_time = None
        self.duration = None
    
    def advance_immediately(self) -> None:
        """Advance immediately (for video completion or other early advancement)."""
        current_time = time.time()
        elapsed = current_time - self.start_time if self.start_time else 0
        
        self.logger.info(f"[TIMER-DEBUG] ===== ADVANCE IMMEDIATELY CALLED ======")
        self.logger.info(f"[TIMER-DEBUG] Timer active: {self.is_active}")
        self.logger.info(f"[TIMER-DEBUG] Elapsed time: {elapsed:.3f}s")
        
        if self.is_active:
            self.logger.info(f"[TIMER-DEBUG] Canceling timers and advancing")
            self.cancel_all_timers()
            self.controller._schedule_advancement_on_main_thread()
        else:
            self.logger.warning(f"[TIMER-DEBUG] Timer manager not active - checking for video completion")
            # For video completion after pause/resume, we should still advance
            # This handles the case where video completes before timer manager is fully resumed
            if hasattr(self.controller, 'current_slide') and self.controller.current_slide:
                slide_type = self.controller.current_slide.get('type', 'unknown')
                if slide_type == 'video':
                    self.logger.info(f"[TIMER-DEBUG] Video completion detected - advancing anyway")
                    self.controller._schedule_advancement_on_main_thread()
                else:
                    self.logger.warning(f"[TIMER-DEBUG] Not a video slide - ignoring advance request")
    
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
        self.logger.info(f"[TIMER-MGR] Pausing timing with {remaining:.1f}s remaining")
        
        # Set inactive - this is important for pause state
        self.is_active = False
        
        # Cancel timers but keep timing info for resume
        if self.advancement_timer:
            if self.advancement_timer.is_alive():
                self.advancement_timer.cancel()
            self.advancement_timer = None
        
        # Stop countdown but don't clear timing info
        if self.countdown_thread and self.countdown_thread.is_alive():
            self.logger.info(f"[TIMER-MGR] Pausing countdown thread, waiting for it to finish...")
            # Wait for thread to notice is_active=False and stop
            self.countdown_thread.join(timeout=1.5)
            if self.countdown_thread.is_alive():
                self.logger.warning(f"[TIMER-MGR] Countdown thread did not stop during pause")
            self.countdown_thread = None
        
        return remaining
    
    def resume_timing(self, remaining_seconds: float, slide_type: str) -> None:
        """Resume timing with specified remaining time.
        
        Args:
            remaining_seconds: Time remaining for the slide
            slide_type: Type of slide for countdown display
        """
        self.logger.info(f"[TIMER-MGR] Resuming timing with {remaining_seconds:.1f}s remaining")
        
        if remaining_seconds <= 0:
            self.logger.warning(f"[TIMER-MGR] No time remaining - advancing immediately")
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
                self.logger.info(f"[TIMER-MGR] Resumed timer expired after {remaining_seconds:.1f}s")
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
            thread_id = threading.current_thread().ident
            self.logger.info(f"[TIMER-{self.manager_id}] Countdown worker started, thread_id={thread_id}")
            try:
                iteration = 0
                while self.is_active and duration_seconds > 0:
                    remaining = self.get_remaining_time()
                    iteration += 1
                    self.logger.info(f"[TIMER-{self.manager_id}] Countdown iteration {iteration}, remaining={remaining:.1f}s, is_active={self.is_active}, thread_id={thread_id}")
                    
                    if remaining <= 0 or not self.is_active:
                        self.logger.info(f"[TIMER-{self.manager_id}] Countdown worker exiting: remaining={remaining:.1f}s, is_active={self.is_active}")
                        break
                    
                    # Show countdown via display manager
                    if (hasattr(self.controller, 'display_manager') and 
                        hasattr(self.controller.display_manager, 'show_countdown')):
                        self.controller.display_manager.show_countdown(int(remaining), self.manager_id)
                    
                    time.sleep(1.0)  # Update every second
                    
            except Exception as e:
                self.logger.error(f"[TIMER-{self.manager_id}] Error in countdown display: {e}")
            finally:
                self.logger.info(f"[TIMER-{self.manager_id}] Countdown worker finished, thread_id={thread_id}")
        
        self.countdown_thread = threading.Thread(target=countdown_worker, daemon=True)
        self.countdown_thread.start()
        self.logger.info(f"[TIMER-{self.manager_id}] Started countdown display thread: {self.countdown_thread.name}, id={self.countdown_thread.ident}")
    
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
