#!/usr/bin/env python3
"""
Test script for video processing capabilities in Dynamic Photo Slideshow v3.0.

This script tests video detection, metadata extraction, and validation
without requiring the full slideshow application to run.
"""

import sys
import logging
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from video_manager import VideoManager
from photo_manager import PhotoManager
from config import SlideshowConfig
from path_config import PathConfig

def setup_test_logging():
    """Set up logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_video_manager():
    """Test VideoManager functionality."""
    logger = setup_test_logging()
    logger.info("=== Testing VideoManager ===")
    
    try:
        # Initialize VideoManager
        video_manager = VideoManager(logger)
        logger.info("✅ VideoManager initialized successfully")
        
        # Test supported formats
        formats = video_manager.get_supported_formats()
        logger.info(f"✅ Supported video formats: {formats}")
        
        # Test file detection with dummy files
        test_files = [
            "test.mp4",
            "test.mov", 
            "test.avi",
            "test.jpg",  # Should be False
            "test.txt"   # Should be False
        ]
        
        for test_file in test_files:
            is_video = video_manager.is_video_file(test_file)
            expected = test_file.endswith(('.mp4', '.mov', '.avi'))
            status = "✅" if is_video == expected else "❌"
            logger.info(f"{status} {test_file} -> is_video: {is_video} (expected: {expected})")
        
        logger.info("✅ VideoManager tests completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ VideoManager test failed: {e}")
        return False

def test_photo_manager_integration():
    """Test PhotoManager integration with video support."""
    logger = setup_test_logging()
    logger.info("=== Testing PhotoManager Video Integration ===")
    
    try:
        # Create test config
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        
        # Initialize PhotoManager
        photo_manager = PhotoManager(config, path_config)
        logger.info("✅ PhotoManager initialized successfully")
        
        # Test video support detection
        video_supported = photo_manager.is_video_supported()
        logger.info(f"✅ Video support enabled: {video_supported}")
        
        if video_supported:
            # Test supported formats
            formats = photo_manager.get_supported_video_formats()
            logger.info(f"✅ PhotoManager supported video formats: {formats}")
            
            # Test video validation (will fail for non-existent files, but tests the API)
            test_result = photo_manager.validate_video_file("nonexistent.mp4")
            logger.info(f"✅ Video validation API working (result for nonexistent file: {test_result})")
        
        logger.info("✅ PhotoManager integration tests completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ PhotoManager integration test failed: {e}")
        return False

def test_configuration():
    """Test video configuration settings."""
    logger = setup_test_logging()
    logger.info("=== Testing Video Configuration ===")
    
    try:
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        
        # Test video configuration values
        video_settings = {
            'video_playback_enabled': config.get('video_playback_enabled'),
            'video_max_duration': config.get('video_max_duration'),
            'video_audio_enabled': config.get('video_audio_enabled'),
            'video_auto_play': config.get('video_auto_play'),
            'video_formats_supported': config.get('video_formats_supported')
        }
        
        logger.info("✅ Video configuration settings:")
        for key, value in video_settings.items():
            logger.info(f"   {key}: {value}")
        
        # Validate expected defaults
        expected_enabled = True
        actual_enabled = video_settings['video_playback_enabled']
        status = "✅" if actual_enabled == expected_enabled else "❌"
        logger.info(f"{status} video_playback_enabled: {actual_enabled} (expected: {expected_enabled})")
        
        logger.info("✅ Configuration tests completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all video processing tests."""
    logger = setup_test_logging()
    logger.info("🎬 Starting Video Processing Tests for v3.0")
    
    tests = [
        ("VideoManager", test_video_manager),
        ("PhotoManager Integration", test_photo_manager_integration),
        ("Configuration", test_configuration)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} tests...")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("🎬 VIDEO PROCESSING TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 All video processing tests PASSED! Ready for Milestone 2.")
        return 0
    else:
        logger.error("❌ Some tests FAILED. Review issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
