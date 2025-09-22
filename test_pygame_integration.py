#!/usr/bin/env python3
"""
Test script for pygame slideshow integration.
Tests basic functionality without requiring full photo library setup.
"""

import sys
import logging
import pygame
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pygame_display_manager import PygameDisplayManager
from config import SlideshowConfig
from path_config import PathConfig

def test_pygame_display_manager():
    """Test basic pygame display manager functionality."""
    
    # Setup minimal logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Create minimal config
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        
        # Load default config values
        config.config = {
            'slideshow_interval': 5,
            'video_max_duration': 15,
            'video_playback_enabled': True,
            'video_audio_enabled': True,
            'verbose': True
        }
        
        logger.info("Creating pygame display manager...")
        display_manager = PygameDisplayManager(config)
        
        logger.info(f"Display initialized: {display_manager.screen_width}x{display_manager.screen_height}")
        
        # Test basic functionality
        logger.info("Testing error message display...")
        display_manager._display_error_message("Test error message")
        
        # Wait for a few seconds
        import time
        time.sleep(2)
        
        logger.info("Testing message display...")
        display_manager.show_message("Pygame integration test successful!", 3.0)
        
        logger.info("Testing stopped overlay...")
        display_manager.show_stopped_overlay()
        time.sleep(2)
        
        # Test video support methods
        logger.info(f"Video supported: {display_manager.is_video_supported()}")
        logger.info(f"Video playing: {display_manager.is_video_playing()}")
        
        # Cleanup
        display_manager.cleanup()
        logger.info("Test completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

def test_video_playback():
    """Test video playback if test videos are available."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Check for test videos
    test_video_dir = Path("test_videos")
    if not test_video_dir.exists():
        logger.info("No test_videos directory found, skipping video test")
        return True
    
    test_videos = list(test_video_dir.glob("*.mov"))
    if not test_videos:
        logger.info("No test videos found, skipping video test")
        return True
    
    try:
        # Create minimal config
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        config.config = {
            'slideshow_interval': 5,
            'video_max_duration': 5,  # Short duration for test
            'video_playback_enabled': True,
            'video_audio_enabled': False,  # Disable audio for test
            'verbose': True
        }
        
        display_manager = PygameDisplayManager(config)
        
        # Test with first available video
        test_video = str(test_videos[0])
        logger.info(f"Testing video playback with: {test_video}")
        
        success = display_manager.play_video(test_video, max_duration=3)
        
        display_manager.cleanup()
        
        if success:
            logger.info("Video test completed successfully!")
        else:
            logger.warning("Video test completed with issues")
        
        return success
        
    except Exception as e:
        logger.error(f"Video test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing pygame display manager integration...")
    
    # Test basic display functionality
    if test_pygame_display_manager():
        print("✓ Basic display test passed")
    else:
        print("✗ Basic display test failed")
        sys.exit(1)
    
    # Test video playback
    if test_video_playback():
        print("✓ Video playback test passed")
    else:
        print("✗ Video playback test failed")
    
    print("\nPygame integration tests completed!")
    print("You can now run: python main_pygame.py")
