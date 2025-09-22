#!/usr/bin/env python3
"""
Test script to verify video detection and test video functionality.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from slideshow_controller import SlideshowController
from photo_manager import PhotoManager
from display_manager import DisplayManager
from config import SlideshowConfig
from path_config import PathConfig

def test_video_detection():
    """Test video detection logic and test video creation."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        config.load_config()  # Explicitly load config
        
        logger.info("Testing video detection functionality...")
        
        # Check if video test mode is enabled
        video_test_mode = config.get('video_test_mode', False)
        logger.info(f"Video test mode enabled: {video_test_mode}")
        logger.info(f"Config file path: {config.config_path}")
        logger.info(f"Full config keys: {list(config.config.keys())}")
        
        if video_test_mode:
            short_path = config.get('video_test_short_path')
            long_path = config.get('video_test_long_path')
            
            logger.info(f"Short test video path: {short_path}")
            logger.info(f"Long test video path: {long_path}")
            
            # Check if test videos exist
            if short_path and os.path.exists(short_path):
                logger.info(f"✓ Short test video exists: {os.path.getsize(short_path)} bytes")
            else:
                logger.error(f"✗ Short test video missing: {short_path}")
                
            if long_path and os.path.exists(long_path):
                logger.info(f"✓ Long test video exists: {os.path.getsize(long_path)} bytes")
            else:
                logger.error(f"✗ Long test video missing: {long_path}")
        
        # Initialize components
        photo_manager = PhotoManager(config, path_config)
        display_manager = DisplayManager(config)
        
        # Create slideshow controller
        controller = SlideshowController(config, photo_manager, display_manager, path_config)
        
        # Test video detection logic
        logger.info("\n=== Testing Video Detection Logic ===")
        
        # Create test video dict to simulate test video
        if video_test_mode and short_path and os.path.exists(short_path):
            test_video = controller._create_test_video_dict(short_path, "short")
            logger.info(f"Created test video dict: {test_video}")
            
            # Test video detection
            is_video = controller._is_video_content(test_video)
            logger.info(f"Video detection result: {is_video}")
            
            if is_video:
                logger.info("✓ Test video correctly detected as video content")
            else:
                logger.error("✗ Test video NOT detected as video content")
        
        # Test the test video injection logic
        logger.info("\n=== Testing Test Video Injection ===")
        
        # Test each position individually by setting display_count
        positions_to_test = [1, 2, 3, 4, 5, 6]
        
        for pos in positions_to_test:
            # Reset and set display count to test specific position
            controller.display_count = pos - 1  # Will be incremented to pos
            test_video = controller._get_test_video_if_applicable()
            
            if pos == 2:
                expected = "short video"
                logger.info(f"Position {pos} test video: {test_video is not None} (expected: {expected})")
                if test_video:
                    logger.info(f"  Video type: {test_video.get('uuid', 'unknown')}")
            elif pos == 5:
                expected = "long video"
                logger.info(f"Position {pos} test video: {test_video is not None} (expected: {expected})")
                if test_video:
                    logger.info(f"  Video type: {test_video.get('uuid', 'unknown')}")
            else:
                logger.info(f"Position {pos} test video: {test_video is not None} (expected: None)")
        
        logger.info("\n=== Video Detection Test Complete ===")
        
    except Exception as e:
        logger.error(f"Error during video detection test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_video_detection()
