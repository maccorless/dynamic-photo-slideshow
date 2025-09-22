#!/usr/bin/env python3
"""
Test script to verify slideshow timer and auto-advance functionality.
"""

import os
import sys
import json
import logging
import time
import threading
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from slideshow_controller import SlideshowController
from photo_manager import PhotoManager
from display_manager import DisplayManager
from config import SlideshowConfig
from path_config import PathConfig

def test_slideshow_timer():
    """Test slideshow timer and auto-advance functionality."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        config.load_config()
        
        logger.info("Testing slideshow timer functionality...")
        
        # Initialize components
        photo_manager = PhotoManager(config, path_config)
        display_manager = DisplayManager(config)
        
        # Create slideshow controller
        controller = SlideshowController(config, photo_manager, display_manager, path_config)
        
        # Check initial state
        logger.info(f"Initial state - is_playing: {controller.is_playing}, is_running: {controller.is_running}")
        logger.info(f"Slideshow interval: {controller.interval} seconds")
        
        # Test timer attributes
        has_timer_thread = hasattr(controller, 'timer_thread')
        logger.info(f"Has timer_thread attribute: {has_timer_thread}")
        
        # Simulate starting slideshow state
        controller.is_running = True
        controller.is_playing = True
        
        logger.info("Testing _start_timer method...")
        
        # Test timer start
        controller._start_timer()
        
        # Check if timer thread was created
        has_timer_after_start = hasattr(controller, 'timer_thread')
        logger.info(f"Timer thread created after _start_timer: {has_timer_after_start}")
        
        if has_timer_after_start:
            timer_alive = controller.timer_thread.is_alive()
            logger.info(f"Timer thread is alive: {timer_alive}")
            
            if timer_alive:
                logger.info("✓ Timer thread started successfully")
                
                # Wait a short time to see if timer is working
                logger.info("Waiting 3 seconds to test timer functionality...")
                time.sleep(3)
                
                # Check if timer thread is still alive
                still_alive = controller.timer_thread.is_alive()
                logger.info(f"Timer thread still alive after 3 seconds: {still_alive}")
                
            else:
                logger.error("✗ Timer thread created but not alive")
        else:
            logger.error("✗ Timer thread not created")
        
        # Test timer stop
        logger.info("Testing _stop_timer method...")
        controller._stop_timer()
        
        has_timer_after_stop = hasattr(controller, 'timer_thread')
        logger.info(f"Timer thread attribute exists after stop: {has_timer_after_stop}")
        
        # Clean up
        controller.is_running = False
        controller.is_playing = False
        
        logger.info("Timer test complete")
        
    except Exception as e:
        logger.error(f"Error during timer test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_slideshow_timer()
