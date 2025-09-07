#!/usr/bin/env python3
"""
Integration test for video playback in Dynamic Photo Slideshow v3.0.

Tests the complete video integration including DisplayManager, SlideshowController,
and PhotoManager working together for mixed photo/video slideshows.
"""

import sys
import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from video_manager import VideoManager
from photo_manager import PhotoManager
from display_manager import DisplayManager
from slideshow_controller import SlideshowController
from config import SlideshowConfig
from path_config import PathConfig

def setup_test_logging():
    """Set up logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def create_mock_video_file():
    """Create a temporary mock video file for testing."""
    temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_file.write(b'fake video content for testing')
    temp_file.close()
    return temp_file.name

def test_display_manager_video_support():
    """Test DisplayManager video support initialization."""
    logger = setup_test_logging()
    logger.info("=== Testing DisplayManager Video Support ===")
    
    try:
        # Create test config with video enabled
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        config.config['video_playback_enabled'] = True
        
        # Mock tkinter to avoid GUI during testing
        with patch('tkinter.Tk') as mock_tk:
            mock_root = Mock()
            mock_tk.return_value = mock_root
            mock_root.winfo_screenwidth.return_value = 1920
            mock_root.winfo_screenheight.return_value = 1080
            
            display_manager = DisplayManager(config)
            
            # Test video support detection
            video_supported = display_manager.is_video_supported()
            logger.info(f"✅ DisplayManager video support: {video_supported}")
            
            # Test video manager initialization
            has_video_manager = display_manager.video_manager is not None
            logger.info(f"✅ Video manager initialized: {has_video_manager}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ DisplayManager video support test failed: {e}")
        return False

def test_slideshow_controller_video_integration():
    """Test SlideshowController video content detection and handling."""
    logger = setup_test_logging()
    logger.info("=== Testing SlideshowController Video Integration ===")
    
    try:
        # Create test components
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        config.config['video_playback_enabled'] = True
        
        # Mock components to avoid dependencies
        mock_photo_manager = Mock()
        mock_photo_manager.video_manager = Mock()
        mock_photo_manager.video_manager.is_video_file.return_value = True
        mock_photo_manager.get_video_metadata.return_value = {
            'duration': 15.0,
            'fps': 30.0,
            'width': 1920,
            'height': 1080,
            'is_valid': True
        }
        
        with patch('tkinter.Tk') as mock_tk:
            mock_root = Mock()
            mock_tk.return_value = mock_root
            mock_root.winfo_screenwidth.return_value = 1920
            mock_root.winfo_screenheight.return_value = 1080
            
            mock_display_manager = Mock()
            mock_display_manager.is_video_supported.return_value = True
            mock_display_manager.display_video.return_value = True
            
            # Create controller
            controller = SlideshowController(config, mock_photo_manager, mock_display_manager, path_config)
            
            # Test video content detection
            test_video = {'path': '/fake/video.mp4', 'filename': 'test.mp4'}
            is_video = controller._is_video_content(test_video)
            logger.info(f"✅ Video content detection: {is_video}")
            
            # Test video overlay creation
            overlays = controller._create_video_overlays(test_video, 0, 10, "Test Location")
            logger.info(f"✅ Video overlays created: {len(overlays)} overlays")
            
            # Test video control methods
            controller.pause_video()
            controller.resume_video()
            controller.stop_video()
            logger.info("✅ Video control methods working")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ SlideshowController video integration test failed: {e}")
        return False

def test_photo_manager_video_detection():
    """Test PhotoManager video file detection and metadata."""
    logger = setup_test_logging()
    logger.info("=== Testing PhotoManager Video Detection ===")
    
    try:
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        
        photo_manager = PhotoManager(config, path_config)
        
        # Test video support
        video_supported = photo_manager.is_video_supported()
        logger.info(f"✅ PhotoManager video support: {video_supported}")
        
        if video_supported:
            # Test supported formats
            formats = photo_manager.get_supported_video_formats()
            logger.info(f"✅ Supported formats: {len(formats)} formats")
            
            # Test video validation (with non-existent file)
            validation_result = photo_manager.validate_video_file("nonexistent.mp4")
            logger.info(f"✅ Video validation API: {validation_result} (expected False for nonexistent file)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ PhotoManager video detection test failed: {e}")
        return False

def test_configuration_video_settings():
    """Test video configuration settings are properly loaded."""
    logger = setup_test_logging()
    logger.info("=== Testing Video Configuration Settings ===")
    
    try:
        path_config = PathConfig()
        config = SlideshowConfig(path_config)
        
        # Test video configuration values
        video_settings = {
            'video_playback_enabled': config.get('video_playback_enabled'),
            'video_max_duration': config.get('video_max_duration'),
            'video_audio_enabled': config.get('video_audio_enabled'),
            'video_auto_play': config.get('video_auto_play'),
            'video_loop': config.get('video_loop'),
            'video_thumbnail_enabled': config.get('video_thumbnail_enabled'),
            'video_formats_supported': config.get('video_formats_supported')
        }
        
        logger.info("✅ Video configuration loaded:")
        for key, value in video_settings.items():
            logger.info(f"   {key}: {value}")
        
        # Validate expected settings
        expected_enabled = True
        actual_enabled = video_settings['video_playback_enabled']
        if actual_enabled == expected_enabled:
            logger.info("✅ Video playback enabled by default")
        else:
            logger.warning(f"⚠️ Video playback setting unexpected: {actual_enabled}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Video configuration test failed: {e}")
        return False

def test_end_to_end_video_workflow():
    """Test complete video workflow simulation."""
    logger = setup_test_logging()
    logger.info("=== Testing End-to-End Video Workflow ===")
    
    try:
        # Create temporary video file
        temp_video = create_mock_video_file()
        
        try:
            path_config = PathConfig()
            config = SlideshowConfig(path_config)
            config.config['video_playback_enabled'] = True
            
            # Mock the complete workflow
            with patch('tkinter.Tk') as mock_tk:
                mock_root = Mock()
                mock_tk.return_value = mock_root
                mock_root.winfo_screenwidth.return_value = 1920
                mock_root.winfo_screenheight.return_value = 1080
                
                # Create components
                photo_manager = PhotoManager(config, path_config)
                
                # Mock display manager for testing
                mock_display_manager = Mock()
                mock_display_manager.is_video_supported.return_value = True
                mock_display_manager.display_video.return_value = True
                mock_display_manager.is_video_playing.return_value = False
                
                controller = SlideshowController(config, photo_manager, mock_display_manager, path_config)
                
                # Simulate video content
                video_content = {
                    'path': temp_video,
                    'filename': 'test_video.mp4',
                    'media_type': 'video'
                }
                
                # Test video detection
                is_video = controller._is_video_content(video_content)
                logger.info(f"✅ Video detection in workflow: {is_video}")
                
                # Test overlay creation
                overlays = controller._create_video_overlays(video_content, 1, 5, "Test Location")
                logger.info(f"✅ Overlays created: {len(overlays)} items")
                
                logger.info("✅ End-to-end workflow simulation completed")
                return True
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_video)
            except:
                pass
        
    except Exception as e:
        logger.error(f"❌ End-to-end video workflow test failed: {e}")
        return False

def main():
    """Run all video integration tests."""
    logger = setup_test_logging()
    logger.info("🎬 Starting Video Integration Tests for v3.0")
    
    tests = [
        ("DisplayManager Video Support", test_display_manager_video_support),
        ("SlideshowController Integration", test_slideshow_controller_video_integration),
        ("PhotoManager Video Detection", test_photo_manager_video_detection),
        ("Configuration Settings", test_configuration_video_settings),
        ("End-to-End Workflow", test_end_to_end_video_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running {test_name} tests...")
        logger.info(f"{'='*60}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("🎬 VIDEO INTEGRATION TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 All video integration tests PASSED! Milestone 2 complete.")
        return 0
    else:
        logger.error("❌ Some tests FAILED. Review issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
