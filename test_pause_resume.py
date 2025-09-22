#!/usr/bin/env python3
"""
Test script for pause/resume functionality with SlideTimerManager.
"""

import time
import logging
from slide_timer_manager import SlideTimerManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockController:
    """Mock controller for testing."""
    
    def __init__(self):
        self.advancement_called = False
        self.config = {'show_countdown_timer': True}  # Enable countdown for test
        self.current_slide = {'type': 'photo'}
    
    def _schedule_advancement_on_main_thread(self):
        """Mock advancement method."""
        logger.info("[MOCK] Advancement scheduled!")
        self.advancement_called = True

def test_pause_resume_cycle():
    """Test complete pause/resume cycle."""
    logger.info("=== Testing Pause/Resume Cycle ===")
    
    controller = MockController()
    timer_mgr = SlideTimerManager(controller, logger)
    
    # Start 10 second timer
    logger.info("Starting 10s timer...")
    timer_mgr.start_slide_timing(10.0, 'photo')
    
    # Wait 3 seconds
    logger.info("Waiting 3 seconds...")
    time.sleep(3.0)
    
    # Check remaining time
    remaining_before_pause = timer_mgr.get_remaining_time()
    logger.info(f"Remaining time before pause: {remaining_before_pause:.1f}s")
    
    # Pause
    logger.info("Pausing timer...")
    paused_time = timer_mgr.pause_timing()
    logger.info(f"Timer paused with {paused_time:.1f}s remaining")
    
    # Verify timer is inactive
    assert not timer_mgr.is_timer_active(), "Timer should be inactive after pause"
    
    # Wait 3 seconds while paused (should not advance)
    logger.info("Waiting 3 seconds while paused...")
    time.sleep(3.0)
    
    # Should not have advanced
    assert not controller.advancement_called, "Should not advance while paused"
    logger.info("✓ No advancement during pause")
    
    # Resume
    logger.info(f"Resuming with {paused_time:.1f}s remaining...")
    timer_mgr.resume_timing(paused_time, 'photo')
    
    # Verify timer is active again
    assert timer_mgr.is_timer_active(), "Timer should be active after resume"
    
    # Wait for remaining time + buffer
    logger.info(f"Waiting {paused_time + 0.5:.1f}s for timer to expire...")
    time.sleep(paused_time + 0.5)
    
    # Should have advanced
    assert controller.advancement_called, "Should advance after resume timer expires"
    logger.info("✓ Advancement occurred after resume")
    
    logger.info("=== Pause/Resume Test Passed! ===")

def test_multiple_pause_resume():
    """Test multiple pause/resume cycles."""
    logger.info("=== Testing Multiple Pause/Resume Cycles ===")
    
    controller = MockController()
    timer_mgr = SlideTimerManager(controller, logger)
    
    # Start 15 second timer
    timer_mgr.start_slide_timing(15.0, 'photo')
    
    # First pause/resume cycle
    time.sleep(2.0)
    paused_time1 = timer_mgr.pause_timing()
    logger.info(f"First pause: {paused_time1:.1f}s remaining")
    
    time.sleep(1.0)  # Paused for 1 second
    timer_mgr.resume_timing(paused_time1, 'photo')
    
    # Second pause/resume cycle
    time.sleep(2.0)
    paused_time2 = timer_mgr.pause_timing()
    logger.info(f"Second pause: {paused_time2:.1f}s remaining")
    
    time.sleep(1.0)  # Paused for 1 second
    timer_mgr.resume_timing(paused_time2, 'photo')
    
    # Wait for final timer expiration
    time.sleep(paused_time2 + 0.5)
    
    assert controller.advancement_called, "Should advance after multiple pause/resume cycles"
    logger.info("✓ Multiple pause/resume cycles work correctly")
    
    logger.info("=== Multiple Pause/Resume Test Passed! ===")

if __name__ == "__main__":
    try:
        test_pause_resume_cycle()
        test_multiple_pause_resume()
        logger.info("🎉 All pause/resume tests passed! Timer manager pause/resume is working correctly.")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
