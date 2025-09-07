#!/usr/bin/env python3
"""
Test script to verify navigation behavior after slide advance.
"""

import sys
import os
import time
import threading
from unittest.mock import Mock

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slideshow_controller import SlideshowController
from config import SlideshowConfig

def test_navigation_after_advance():
    """Test that first back press works after slide advance."""
    print("Testing navigation after slide advance...")
    
    # Create mock objects
    mock_photo_manager = Mock()
    mock_photo_manager.get_photo_count.return_value = 10
    mock_photo_manager.get_random_photo_index.return_value = 5
    mock_photo_manager.get_photo_by_index.return_value = {
        'filename': 'test.jpg',
        'path': '/test/test.jpg',
        'media_type': 'image',
        'orientation': 'landscape'
    }
    
    mock_display_manager = Mock()
    mock_voice_service = Mock()
    mock_voice_service.is_available.return_value = False
    mock_location_service = Mock()
    
    # Create controller with correct signature
    config = SlideshowConfig()
    controller = SlideshowController(
        config,
        mock_photo_manager, 
        mock_display_manager
    )
    
    # Initialize some test state
    controller.photos = list(range(10))  # Mock photo list
    controller.current_index = 0
    controller.is_running = True
    controller.is_playing = True
    controller.is_paused = False
    
    # Simulate some photo history
    controller.photo_history = [0, 1, 2, 3, 4]
    controller.history_position = -1  # At current photo (after auto-advance)
    
    print(f"Initial state: history_position = {controller.history_position}")
    print(f"Photo history: {controller.photo_history}")
    
    # Test first back press
    print("\nTesting first back press...")
    controller.previous_photo()
    
    print(f"After first back press: history_position = {controller.history_position}")
    
    # Test second back press
    print("\nTesting second back press...")
    controller.previous_photo()
    
    print(f"After second back press: history_position = {controller.history_position}")
    
    # Verify the fix - after two back presses from position -1, we should be at position 2
    # (going from current photo back through history: -1 -> 3 -> 2)
    if controller.history_position == 2:
        print("✅ Navigation fix working correctly!")
        return True
    else:
        print(f"❌ Navigation fix not working as expected. Expected position 2, got {controller.history_position}")
        return False

if __name__ == "__main__":
    success = test_navigation_after_advance()
    sys.exit(0 if success else 1)
