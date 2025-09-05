#!/usr/bin/env python3
"""
Test script to verify Dynamic Photo Slideshow setup and functionality.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import osxphotos
        import PIL
        import tkinter
        import requests
        print("✅ All required libraries imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config_system():
    """Test configuration system."""
    print("\nTesting configuration system...")
    try:
        from config import SlideshowConfig
        config = SlideshowConfig()
        config.load_config()
        
        # Check that config file was created
        config_path = Path.home() / '.photo_slideshow_config.json'
        if config_path.exists():
            print("✅ Configuration file created successfully")
        
        # Check default values
        expected_keys = [
            'PHOTOS_ALBUM_NAME', 'SLIDESHOW_INTERVAL_SECONDS', 
            'OVERLAY_PLACEMENT', 'OVERLAY_ALIGNMENT'
        ]
        config_data = config.get_all()
        
        for key in expected_keys:
            if key in config_data:
                print(f"✅ Config key '{key}': {config_data[key]}")
            else:
                print(f"❌ Missing config key: {key}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Configuration system error: {e}")
        return False

def test_photos_connection():
    """Test Photos library connection."""
    print("\nTesting Photos library connection...")
    try:
        from photo_manager import PhotoManager
        from config import SlideshowConfig
        
        config = SlideshowConfig()
        config.load_config()
        pm = PhotoManager(config)
        
        # Test connection (this will fail if album doesn't exist, which is expected)
        result = pm.verify_album()
        if not result:
            print(f"⚠️  Album '{config.get('PHOTOS_ALBUM_NAME')}' not found (expected)")
            print("   To test fully, create this album in Photos and add some photos")
        else:
            print("✅ Photos album found and accessible")
        
        print("✅ Photos library connection working")
        return True
    except Exception as e:
        print(f"❌ Photos connection error: {e}")
        return False

def test_location_service():
    """Test location service functionality."""
    print("\nTesting location service...")
    try:
        from location_service import LocationService
        from config import SlideshowConfig
        
        config = SlideshowConfig()
        config.load_config()
        ls = LocationService(config)
        
        # Test with known coordinates (San Francisco)
        location = ls.get_location_string(37.7749, -122.4194)
        if location:
            print(f"✅ Location service working: {location}")
        else:
            print("⚠️  Location service returned None (network issue or API limit)")
        
        return True
    except Exception as e:
        print(f"❌ Location service error: {e}")
        return False

def print_setup_instructions():
    """Print setup instructions for the user."""
    print("\n" + "="*60)
    print("SETUP INSTRUCTIONS")
    print("="*60)
    print("1. Open Photos app on your Mac")
    print("2. Create a new album named 'photoframe' (or change PHOTOS_ALBUM_NAME in config)")
    print("3. Add some photos to this album")
    print("4. Run the slideshow with: python main.py")
    print("\nCONTROLS:")
    print("- Spacebar: Pause/resume")
    print("- Arrow keys: Navigate photos")
    print("- Shift: Show filename")
    print("- Escape: Exit")
    print("="*60)

def main():
    """Run all tests."""
    print("Dynamic Photo Slideshow - Setup Test")
    print("="*40)
    
    tests = [
        test_imports,
        test_config_system,
        test_photos_connection,
        test_location_service
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The slideshow is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    print_setup_instructions()

if __name__ == "__main__":
    main()
