#!/usr/bin/env python3
"""
Test script for SlideTimerManager to verify basic functionality.
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
        self.config = {'show_countdown_timer': False}  # Disable countdown for simple test
    
    def _schedule_advancement_on_main_thread(self):
        """Mock advancement method."""
        logger.info("[MOCK] Advancement scheduled!")
        self.advancement_called = True

def test_basic_timer_functionality():
    """Test basic timer start/cancel functionality."""
    logger.info("=== Testing Basic Timer Functionality ===")
    
    controller = MockController()
    timer_mgr = SlideTimerManager(controller, logger)
    
    # Test 1: Start and let timer expire
    logger.info("Test 1: Starting 2s timer...")
    timer_mgr.start_slide_timing(2.0, 'photo')
    
    # Check timer is active
    assert timer_mgr.is_timer_active(), "Timer should be active"
    logger.info(f"Timer status: {timer_mgr}")
    
    # Wait for timer to expire
    time.sleep(2.5)
    
    # Check advancement was called
    assert controller.advancement_called, "Advancement should have been called"
    logger.info("✓ Timer expired and called advancement")
    
    # Test 2: Start and cancel timer
    logger.info("Test 2: Starting timer and canceling...")
    controller.advancement_called = False
    timer_mgr.start_slide_timing(5.0, 'photo')
    
    assert timer_mgr.is_timer_active(), "Timer should be active"
    
    # Cancel after 1 second
    time.sleep(1.0)
    timer_mgr.cancel_all_timers()
    
    assert not timer_mgr.is_timer_active(), "Timer should be inactive after cancel"
    
    # Wait to ensure no advancement happens
    time.sleep(2.0)
    assert not controller.advancement_called, "Advancement should not be called after cancel"
    logger.info("✓ Timer canceled successfully")
    
    # Test 3: Immediate advancement
    logger.info("Test 3: Testing immediate advancement...")
    controller.advancement_called = False
    timer_mgr.start_slide_timing(10.0, 'photo')
    
    # Advance immediately
    timer_mgr.advance_immediately()
    
    assert controller.advancement_called, "Immediate advancement should work"
    assert not timer_mgr.is_timer_active(), "Timer should be inactive after immediate advance"
    logger.info("✓ Immediate advancement works")
    
    logger.info("=== All Basic Tests Passed! ===")

def test_pause_resume_functionality():
    """Test pause/resume functionality."""
    logger.info("=== Testing Pause/Resume Functionality ===")
    
    controller = MockController()
    timer_mgr = SlideTimerManager(controller, logger)
    
    # Start 5 second timer
    timer_mgr.start_slide_timing(5.0, 'photo')
    
    # Wait 2 seconds then pause
    time.sleep(2.0)
    remaining = timer_mgr.pause_timing()
    
    logger.info(f"Paused with {remaining:.1f}s remaining")
    assert 2.5 < remaining < 3.5, f"Expected ~3s remaining, got {remaining:.1f}s"
    
    # Wait 2 more seconds (should not advance)
    time.sleep(2.0)
    assert not controller.advancement_called, "Should not advance while paused"
    
    # Resume
    timer_mgr.resume_timing(remaining, 'photo')
    
    # Wait for remaining time + buffer
    time.sleep(remaining + 0.5)
    
    assert controller.advancement_called, "Should advance after resume"
    logger.info("✓ Pause/resume works correctly")
    
    logger.info("=== Pause/Resume Tests Passed! ===")

if __name__ == "__main__":
    try:
        test_basic_timer_functionality()
        test_pause_resume_functionality()
        logger.info("🎉 All tests passed! SlideTimerManager is working correctly.")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
