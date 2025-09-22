#!/usr/bin/env python3
"""
Analyze dead code in slideshow_controller.py
"""

import re
import sys
from pathlib import Path

def analyze_dead_code():
    """Find methods that are defined but never called."""
    
    # Read the slideshow controller file
    controller_file = Path("slideshow_controller.py")
    if not controller_file.exists():
        print("slideshow_controller.py not found")
        return
    
    content = controller_file.read_text()
    
    # Find all method definitions
    method_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    defined_methods = set(re.findall(method_pattern, content))
    
    print("🔍 DEFINED METHODS:")
    for method in sorted(defined_methods):
        print(f"   {method}")
    print(f"   Total: {len(defined_methods)}")
    
    # Find all method calls (self.method_name or controller.method_name)
    call_pattern = r'(?:self\.|controller\.|\.)([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    called_methods = set(re.findall(call_pattern, content))
    
    # Also check other files for calls to controller methods
    other_files = ["main_pygame.py", "main.py", "voice_command_service.py"]
    for file_path in other_files:
        file_obj = Path(file_path)
        if file_obj.exists():
            file_content = file_obj.read_text()
            file_calls = set(re.findall(call_pattern, file_content))
            called_methods.update(file_calls)
    
    print(f"\n📞 CALLED METHODS:")
    for method in sorted(called_methods):
        print(f"   {method}")
    print(f"   Total: {len(called_methods)}")
    
    # Find potentially dead methods
    potentially_dead = defined_methods - called_methods
    
    # Filter out special methods and known entry points
    special_methods = {
        '__init__', 'start_slideshow', 'stop', 'next_photo', 'previous_photo',
        'voice_next', 'voice_previous', 'toggle_pause', 'pause_for_voice_command',
        'resume_after_voice_command', 'pause_video', 'resume_video', 'stop_video',
        'timer_callback'  # Inner function
    }
    
    dead_methods = potentially_dead - special_methods
    
    print(f"\n💀 POTENTIALLY DEAD METHODS:")
    for method in sorted(dead_methods):
        print(f"   {method}")
    print(f"   Total: {len(dead_methods)}")
    
    # Find legacy methods that might be duplicates
    legacy_methods = [m for m in defined_methods if 'legacy' in content.lower() and m in content]
    
    print(f"\n🏚️  LEGACY METHODS (potential duplicates):")
    legacy_patterns = [
        '_display_slide_portrait_pair',
        '_display_slide_single_photo', 
        '_display_slide_video',
        '_display_current_photo',
        '_display_next_photo',
        '_get_next_photo',
        '_get_photo_from_history',
        '_handle_history_photo_pair',
        '_display_photo_pair',
        '_display_single_photo',
        '_handle_photo_display',
        '_handle_portrait_photo_display',
        '_display_photo_content'
    ]
    
    for method in legacy_patterns:
        if method in defined_methods:
            print(f"   {method}")
    
    return dead_methods, legacy_patterns

if __name__ == "__main__":
    analyze_dead_code()
