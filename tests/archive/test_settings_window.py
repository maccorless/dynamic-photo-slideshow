#!/usr/bin/env python3
"""
Test script for Settings Window
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

def test_settings_window():
    """Test basic settings window functionality."""
    print("=" * 60)
    print("Testing Settings Window")
    print("=" * 60)
    print("\nInstructions:")
    print("- Settings window should appear centered")
    print("- Background should be semi-transparent (slide visible around edges)")
    print("- Click OK or press ESC to close")
    print("- Press Cmd+S/Ctrl+S to reopen")
    print("- Press ESC twice to exit test")
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
    pygame.display.set_caption("Settings Window Test")
    
    # Create a test background (simulating a frozen slide)
    # Draw a colorful gradient to make it obvious when visible around edges
    for y in range(screen_height):
        color_value = int(255 * (y / screen_height))
        pygame.draw.line(screen, (color_value, 100, 255 - color_value), 
                        (0, y), (screen_width, y))
    
    # Add some text to the background
    font = pygame.font.Font(None, 72)
    text = font.render("Test Slide Background", True, (255, 255, 255))
    text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2))
    screen.blit(text, text_rect)
    
    pygame.display.flip()
    
    # Wait 2 seconds
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
                        # First ESC closes settings
                        settings_window.hide()
                    else:
                        # Second ESC exits test
                        running = False
                elif event.key == pygame.K_s:
                    # Cmd+S or Ctrl+S to toggle settings
                    mods = pygame.key.get_mods()
                    if (mods & pygame.KMOD_META) or (mods & pygame.KMOD_CTRL):
                        if settings_window.is_open():
                            settings_window.hide()
                        else:
                            settings_window.show()
            
            # Let settings window handle event
            settings_window.handle_event(event)
        
        # Update settings window
        settings_window.update(time_delta)
        
        # Draw
        # Note: We don't redraw the background, so the frozen slide stays visible
        settings_window.draw()
        
        pygame.display.flip()
    
    # Cleanup
    pygame.quit()
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_settings_window()
