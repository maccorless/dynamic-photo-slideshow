#!/usr/bin/env python3
"""
Proposed refactored architecture for slideshow advancement.
This shows the ideal single-responsibility pattern.
"""

from typing import Optional, Dict, Any
from enum import Enum

class TriggerType(Enum):
    TIMER = "timer"
    KEY_NEXT = "key_next"
    KEY_PREVIOUS = "key_previous"
    VOICE_NEXT = "voice_next"
    VOICE_PREVIOUS = "voice_previous"

class Direction(Enum):
    NEXT = "next"
    PREVIOUS = "previous"

class RefactoredSlideshowController:
    """
    Proposed refactored slideshow controller with single-responsibility methods.
    """
    
    def __init__(self):
        self.slide_history = []
        self.history_position = -1
        self.current_slide = None
        self.is_playing = True
        self.timer_thread = None
    
    # ========================================
    # SINGLE ENTRY POINT - This is the key!
    # ========================================
    
    def advance_slideshow(self, trigger: TriggerType, direction: Direction = Direction.NEXT) -> bool:
        """
        SINGLE ENTRY POINT for all slide advancement.
        
        This is the ONLY method that should be called to change slides.
        All other advancement should go through this method.
        
        Args:
            trigger: What triggered the advancement (timer, key, voice)
            direction: Which direction to advance
            
        Returns:
            bool: True if advancement was successful
        """
        try:
            self.logger.info(f"[ADVANCE] Slideshow advancement triggered by {trigger.value}, direction: {direction.value}")
            
            # 1. Stop current timer (if any)
            self._stop_current_timer()
            
            # 2. Determine next slide (create new or get from history)
            slide = self._determine_next_slide(direction)
            if not slide:
                self.logger.error("[ADVANCE] Failed to determine next slide")
                return False
            
            # 3. Display slide with timer setup (single responsibility)
            success = self._display_slide_with_timer(slide)
            
            if success:
                self.logger.info(f"[ADVANCE] Successfully advanced to {slide['type']} slide")
            else:
                self.logger.error("[ADVANCE] Failed to display slide")
            
            return success
            
        except Exception as e:
            self.logger.error(f"[ADVANCE] Error in slideshow advancement: {e}")
            return False
    
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
        
        Returns:
            Dict: The slide to display, or None if failed
        """
        if direction == Direction.NEXT:
            return self._determine_next_slide_forward()
        elif direction == Direction.PREVIOUS:
            return self._determine_next_slide_backward()
        else:
            self.logger.error(f"[DETERMINE] Unknown direction: {direction}")
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
                    self.logger.info(f"[DETERMINE] Retrieved slide from history position {self.history_position}")
                    return slide
                else:
                    self.logger.warning(f"[DETERMINE] Invalid slide in history, creating new one")
        
        # Create new slide (includes video test mode logic)
        return self._create_new_slide()
    
    def _determine_next_slide_backward(self) -> Optional[Dict[str, Any]]:
        """Determine next slide when going backward."""
        # Update navigation state
        success = self._navigate_previous()
        if not success:
            self.logger.info("[DETERMINE] Cannot go back further in history")
            return None
        
        # Get slide from history
        if self.history_position >= 0 and self.history_position < len(self.slide_history):
            slide = self.slide_history[self.history_position]
            if self._validate_slide(slide):
                self.logger.info(f"[DETERMINE] Retrieved slide from history position {self.history_position}")
                return slide
        
        self.logger.error("[DETERMINE] Failed to retrieve slide from history")
        return None
    
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
            
            # Update current slide state
            self.current_slide = slide
            
            # Display the slide based on its type
            display_success = self._display_slide_content(slide)
            if not display_success:
                return False
            
            # Add to history if it's a new slide (not from history navigation)
            if self.history_position == -1:
                self._add_slide_to_history(slide)
            
            # Start timer for this slide
            self._start_slide_timer(slide)
            
            self.logger.info(f"[DISPLAY] Successfully displayed {slide['type']} slide with timer")
            return True
            
        except Exception as e:
            self.logger.error(f"[DISPLAY] Error displaying slide: {e}")
            return False
    
    def _display_slide_content(self, slide: Dict[str, Any]) -> bool:
        """Display the actual slide content (photos/videos)."""
        slide_type = slide['type']
        
        if slide_type == 'portrait_pair':
            return self._display_portrait_pair_content(slide)
        elif slide_type == 'video':
            return self._display_video_content(slide)
        elif slide_type in ['landscape', 'single_portrait']:
            return self._display_single_photo_content(slide)
        else:
            self.logger.error(f"[DISPLAY] Unknown slide type: {slide_type}")
            return False
    
    def _start_slide_timer(self, slide: Dict[str, Any]) -> None:
        """Start the timer for the given slide."""
        if not self.is_playing:
            return
        
        slide_timer = slide.get('slide_timer', 10)  # Default 10 seconds
        
        # Stop any existing timer
        self._stop_current_timer()
        
        # Start new timer that will call advance_slideshow when it expires
        self.timer_thread = threading.Timer(
            slide_timer, 
            lambda: self.advance_slideshow(TriggerType.TIMER, Direction.NEXT)
        )
        self.timer_thread.start()
        
        self.logger.info(f"[TIMER] Started {slide_timer}s timer for {slide['type']} slide")
    
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
        self.advance_slideshow(TriggerType.VOICE_NEXT, Direction.NEXT)
    
    def voice_previous(self) -> None:
        """Public API for voice previous command."""
        self.advance_slideshow(TriggerType.VOICE_PREVIOUS, Direction.PREVIOUS)
    
    # Timer callback would call:
    # self.advance_slideshow(TriggerType.TIMER, Direction.NEXT)
    
    # ========================================
    # HELPER METHODS - Single responsibility each
    # ========================================
    
    def _navigate_next(self) -> None:
        """Update navigation state for forward movement."""
        # Implementation here...
        pass
    
    def _navigate_previous(self) -> bool:
        """Update navigation state for backward movement."""
        # Implementation here...
        return True
    
    def _create_new_slide(self) -> Optional[Dict[str, Any]]:
        """Create a new slide (includes video test mode logic)."""
        # Implementation here...
        return {}
    
    def _validate_slide(self, slide: Dict[str, Any]) -> bool:
        """Validate that a slide is still valid."""
        # Implementation here...
        return True
    
    def _add_slide_to_history(self, slide: Dict[str, Any]) -> None:
        """Add slide to history."""
        # Implementation here...
        pass
    
    def _stop_current_timer(self) -> None:
        """Stop the current timer if running."""
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.cancel()
            self.timer_thread = None
    
    def _display_portrait_pair_content(self, slide: Dict[str, Any]) -> bool:
        """Display portrait pair content only."""
        # Implementation here...
        return True
    
    def _display_video_content(self, slide: Dict[str, Any]) -> bool:
        """Display video content only."""
        # Implementation here...
        return True
    
    def _display_single_photo_content(self, slide: Dict[str, Any]) -> bool:
        """Display single photo content only."""
        # Implementation here...
        return True

# ========================================
# USAGE EXAMPLES
# ========================================

def example_usage():
    """Show how the refactored architecture would be used."""
    controller = RefactoredSlideshowController()
    
    # All advancement goes through single entry point:
    
    # Timer expires:
    controller.advance_slideshow(TriggerType.TIMER, Direction.NEXT)
    
    # User presses right arrow:
    controller.advance_slideshow(TriggerType.KEY_NEXT, Direction.NEXT)
    
    # User presses left arrow:
    controller.advance_slideshow(TriggerType.KEY_PREVIOUS, Direction.PREVIOUS)
    
    # Voice command "next":
    controller.advance_slideshow(TriggerType.VOICE_NEXT, Direction.NEXT)
    
    # Public APIs still work but route to single entry point:
    controller.next_photo()  # Calls advance_slideshow internally
    controller.previous_photo()  # Calls advance_slideshow internally

if __name__ == "__main__":
    print("🏗️  Proposed Refactored Architecture")
    print("=" * 50)
    print()
    print("✅ SINGLE ENTRY POINT:")
    print("   advance_slideshow(trigger, direction)")
    print()
    print("✅ SINGLE RESPONSIBILITIES:")
    print("   - _determine_next_slide(): Handle all slide determination")
    print("   - _display_slide_with_timer(): Handle all display + timer")
    print("   - _display_slide_content(): Handle actual content display")
    print()
    print("✅ NO DUPLICATION:")
    print("   - Timer logic only in _start_slide_timer()")
    print("   - Display logic only in _display_slide_with_timer()")
    print("   - Navigation logic only in _determine_next_slide()")
    print()
    print("✅ CLEAR FLOW:")
    print("   Trigger → Determine → Display → Timer")
