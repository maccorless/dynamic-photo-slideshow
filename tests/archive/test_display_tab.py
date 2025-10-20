#!/usr/bin/env python3
"""
Test script for Display Tab in Settings Window
"""

import pygame
import logging
from settings_manager import SettingsManager
from settings_window import SettingsWindow

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_display_tab():
    """Test Display tab with all settings."""
    print("=" * 60)
    print("Testing Display Tab")
    print("=" * 60)
    print("\nInstructions:")
    print("- Display tab should show 5 settings:")
    print("  1. Slideshow Interval (text input)")
    print("  2. Show Countdown Timer (checkbox)")
    print("  3. Countdown Position (dropdown)")
    print("  4. Show Date Overlay (checkbox)")
    print("  5. Show Location Overlay (checkbox)")
    print("- Each setting has an info icon (ⓘ) - hover to see tooltip")
    print("- Change values and they should auto-save")
    print("- Check config.json after closing to verify saves")
    print("- Press ESC or click OK to close")
    print("\nStarting in 2 seconds...")
    print("=" * 60)
    
    # Initialize pygame
    pygame.init()
    
    # Get screen info
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h
    
    # Create fullscreen display
    screen = pygame.display.set_mode(
        (screen_width, screen_height),
        pygame.FULLSCREEN | pygame.DOUBLEBUF
    )
    pygame.display.set_caption("Display Tab Test")
    
    # Create a test background
    for y in range(screen_height):
        color_value = int(255 * (y / screen_height))
        pygame.draw.line(screen, (color_value, 100, 255 - color_value), 
                        (0, y), (screen_width, y))
    
    font = pygame.font.Font(None, 72)
    text = font.render("Test Slide Background", True, (255, 255, 255))
    text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2))
    screen.blit(text, text_rect)
    
    pygame.display.flip()
    pygame.time.wait(2000)
    
    # Create settings manager and window
    settings_manager = SettingsManager()
    settings_window = SettingsWindow(screen, settings_manager)
    
    # Show settings window
    settings_window.show()
    
    # Main loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        time_delta = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if settings_window.is_open():
                        settings_window.hide()
                    else:
                        running = False
            
            # Let settings window handle event
            settings_window.handle_event(event)
        
        # Update settings window
        settings_window.update(time_delta)
        
        # Draw
        settings_window.draw()
        
        pygame.display.flip()
    
    # Cleanup
    pygame.quit()
    
    # Show final config
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
    print("\nFinal Display Settings:")
    config = settings_manager.get_all_settings()
    for key, value in config["display"].items():
        print(f"  {key}: {value}")
    print("\nCheck config.json to verify all changes were saved!")
    print("=" * 60)

if __name__ == "__main__":
    test_display_tab()
