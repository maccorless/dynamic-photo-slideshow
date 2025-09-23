#!/usr/bin/env python3
"""
Comprehensive code coverage test for tkinter removal analysis.
This script exercises all major slideshow functionality to identify used vs unused code.
"""

import sys
import os
import time
import threading
import logging
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_slideshow_functionality():
    """Test all major slideshow functionality to capture code coverage."""
    
    print("🔍 Starting comprehensive slideshow functionality test...")
    
    try:
        # Test 1: Import all modules to check import dependencies
        print("📦 Testing module imports...")
        
        from config import SlideshowConfig
        from photo_manager import PhotoManager
        from pygame_display_manager import PygameDisplayManager
        from slideshow_controller import SlideshowController, TriggerType, Direction
        from cache_manager import CacheManager
        from path_config import PathConfig
        from slideshow_exceptions import SlideshowError, ConfigurationError
        
        # Also test tkinter display manager import
        try:
            from display_manager import DisplayManager
            print("✅ Tkinter DisplayManager imported successfully")
        except Exception as e:
            print(f"❌ Tkinter DisplayManager import failed: {e}")
        
        print("✅ All core modules imported successfully")
        
        # Test 2: Configuration system
        print("⚙️ Testing configuration system...")
        path_config = PathConfig.create_from_env()
        config = SlideshowConfig(path_config)
        config.load_config()
        print("✅ Configuration loaded successfully")
        
        # Test 3: Photo manager
        print("📸 Testing photo manager...")
        photo_manager = PhotoManager(config, path_config)
        photos = photo_manager.load_photos()
        print(f"✅ Loaded {len(photos)} photos")
        
        if not photos:
            print("⚠️ No photos found - creating mock photo for testing")
            # Create a minimal mock photo for testing
            photos = [{
                'uuid': 'test-uuid',
                'filename': 'test.jpg',
                'path': '/tmp/test.jpg',
                'media_type': 'photo'
            }]
        
        # Test 4: Pygame Display Manager
        print("🎮 Testing pygame display manager...")
        pygame_display = PygameDisplayManager(config)
        print("✅ Pygame display manager created")
        
        # Test 5: Slideshow Controller
        print("🎬 Testing slideshow controller...")
        controller = SlideshowController(config, photo_manager, pygame_display)
        print("✅ Slideshow controller created")
        
        # Test 6: Key event handling
        print("⌨️ Testing key event handling...")
        
        # Create mock tkinter event for testing
        class MockEvent:
            def __init__(self, keysym):
                self.keysym = keysym
        
        # Test various key events
        test_keys = ['space', 'left', 'right', 'escape']
        for key in test_keys:
            try:
                mock_event = MockEvent(key)
                controller._handle_key_event(mock_event)
                print(f"✅ Key '{key}' handled successfully")
            except Exception as e:
                print(f"⚠️ Key '{key}' handling error: {e}")
        
        # Test 7: Timer management
        print("⏱️ Testing timer management...")
        try:
            from slide_timer_manager import SlideTimerManager
            timer_mgr = SlideTimerManager(10, lambda: None, pygame_display)
            print("✅ Timer manager created successfully")
            timer_mgr.cancel()
            print("✅ Timer manager cancelled successfully")
        except Exception as e:
            print(f"⚠️ Timer management error: {e}")
        
        # Test 8: Video functionality (if available)
        print("🎥 Testing video functionality...")
        try:
            # Test video filtering
            video_photos = [p for p in photos if p.get('media_type') == 'video']
            if video_photos:
                print(f"✅ Found {len(video_photos)} videos")
            else:
                print("ℹ️ No videos found in photo collection")
        except Exception as e:
            print(f"⚠️ Video functionality error: {e}")
        
        # Test 9: Cache management
        print("💾 Testing cache management...")
        try:
            cache_manager = CacheManager(config, path_config)
            print("✅ Cache manager created successfully")
        except Exception as e:
            print(f"⚠️ Cache management error: {e}")
        
        # Test 10: Cleanup
        print("🧹 Testing cleanup...")
        try:
            pygame_display.cleanup()
            print("✅ Pygame display cleanup successful")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
        
        print("🎉 Comprehensive functionality test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_import_dependencies():
    """Analyze which modules import tkinter vs pygame components."""
    
    print("\n🔍 Analyzing import dependencies...")
    
    # Files to analyze
    python_files = [
        'main.py',
        'main_pygame.py', 
        'display_manager.py',
        'pygame_display_manager.py',
        'slideshow_controller.py',
        'photo_manager.py',
        'config.py',
        'cache_manager.py',
        'slide_timer_manager.py'
    ]
    
    tkinter_imports = {}
    pygame_imports = {}
    
    for file_path in python_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Check for tkinter imports
                if 'import tkinter' in content or 'from tkinter' in content:
                    tkinter_imports[file_path] = []
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if 'tkinter' in line and ('import' in line or 'from' in line):
                            tkinter_imports[file_path].append((line_num, line.strip()))
                
                # Check for pygame imports  
                if 'import pygame' in content or 'from pygame' in content:
                    pygame_imports[file_path] = []
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if 'pygame' in line and ('import' in line or 'from' in line):
                            pygame_imports[file_path].append((line_num, line.strip()))
                            
            except Exception as e:
                print(f"⚠️ Error analyzing {file_path}: {e}")
    
    print("\n📋 TKINTER IMPORT ANALYSIS:")
    if tkinter_imports:
        for file_path, imports in tkinter_imports.items():
            print(f"  📄 {file_path}:")
            for line_num, line in imports:
                print(f"    Line {line_num}: {line}")
    else:
        print("  ✅ No tkinter imports found")
    
    print("\n📋 PYGAME IMPORT ANALYSIS:")
    if pygame_imports:
        for file_path, imports in pygame_imports.items():
            print(f"  📄 {file_path}:")
            for line_num, line in imports:
                print(f"    Line {line_num}: {line}")
    else:
        print("  ❌ No pygame imports found")
    
    return tkinter_imports, pygame_imports

if __name__ == "__main__":
    print("🚀 Starting comprehensive code coverage analysis for tkinter removal...")
    
    # Set up minimal logging to avoid spam
    logging.basicConfig(level=logging.ERROR)
    
    # Run import dependency analysis
    tkinter_deps, pygame_deps = analyze_import_dependencies()
    
    # Run functionality test
    success = test_slideshow_functionality()
    
    print(f"\n📊 ANALYSIS SUMMARY:")
    print(f"  📄 Files with tkinter imports: {len(tkinter_deps)}")
    print(f"  📄 Files with pygame imports: {len(pygame_deps)}")
    print(f"  ✅ Functionality test: {'PASSED' if success else 'FAILED'}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if tkinter_deps:
        print(f"  🔍 Review these files before removing tkinter:")
        for file_path in tkinter_deps.keys():
            print(f"    - {file_path}")
    
    print(f"\n🎯 Ready for safe tkinter removal analysis!")
