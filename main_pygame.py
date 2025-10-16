#!/usr/bin/env python3
"""
Dynamic Photo Slideshow - Pygame Main Application
A fullscreen photo slideshow that connects to Apple Photos with pygame-based display.
"""

import sys
import logging
import pygame
import os
import time
from pathlib import Path

from config import SlideshowConfig
from photo_manager import PhotoManager
from pygame_display_manager import PygameDisplayManager
from slideshow_controller import SlideshowController, TriggerType, Direction
from cache_manager import CacheManager
from path_config import PathConfig
from slideshow_exceptions import SlideshowError, ConfigurationError


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration based on verbose setting."""
    log_level = logging.DEBUG if verbose else logging.WARNING
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(PathConfig().log_file),
            logging.StreamHandler(sys.stdout) if verbose else logging.NullHandler()
        ]
    )


class PygameSlideshowController:
    """Pygame-compatible slideshow controller with event handling."""
    
    def __init__(self, config, photo_manager, display_manager, path_config=None):
        # Initialize the original controller
        self.controller = SlideshowController(config, photo_manager, display_manager, path_config)
        self.display_manager = display_manager
        self.logger = logging.getLogger(__name__)
        
        # REMOVED: Timer management - now handled by slideshow controller
        
        # Removed: Key state tracking for filename displays (per requirements)
        
        # Scroll wheel debouncing - prevent rapid-fire events
        self.last_scroll_time = 0
        self.scroll_debounce_ms = 500  # Minimum 500ms between scroll events
        
        # Input blocking during state transitions to prevent GPU crashes
        self.input_blocked = False
        self.input_block_reason = None
        
        # Set up controller reference for video navigation
        self.display_manager.set_controller_reference(self.controller)
        
        # Give controller access to input blocking
        self.controller.block_input = self.block_input
        self.controller.unblock_input = self.unblock_input
        
        # Set up pygame event loop
        self.controller.display_manager.start_event_loop = self._pygame_event_loop
    
    def block_input(self, reason: str) -> None:
        """Block all input during state transitions."""
        self.input_blocked = True
        self.input_block_reason = reason
        self.logger.info(f"[INPUT-BLOCK] Input blocked: {reason}")
    
    def unblock_input(self) -> None:
        """Unblock input after state transition completes."""
        if self.input_blocked:
            self.logger.info(f"[INPUT-UNBLOCK] Input unblocked (was: {self.input_block_reason})")
        
        # Add 50ms delay to ensure countdown thread's first flip() completes
        # This prevents race condition where input is processed in same millisecond as unblock
        time.sleep(0.05)  # 50ms delay
        
        self.input_blocked = False
        self.input_block_reason = None
        self.logger.debug(f"[INPUT-UNBLOCK] Input ready after 50ms safety delay")
    
    def _pygame_event_loop(self, key_callback):
        """Pygame-based event loop for slideshow control."""
        clock = pygame.time.Clock()
        self.last_advance_time = pygame.time.get_ticks()
        
        while self.display_manager.is_running():
            current_time = pygame.time.get_ticks()
            
            # No callback processing needed - pure pygame approach
            
            # Handle pygame events
            events = self.display_manager.handle_events()
            
            for event in events:
                if event.type == pygame.QUIT:
                    self.display_manager.stop()
                    self.controller.stop()
                    break
                elif event.type == pygame.KEYDOWN:
                    # Check if input is blocked
                    if self.input_blocked:
                        self.logger.debug(f"[INPUT-BLOCK] Keyboard event ignored: {self.input_block_reason}")
                        continue
                    # Handle ESC key for immediate exit
                    if event.key == pygame.K_ESCAPE:
                        self.logger.info("ESC key pressed - initiating immediate shutdown")
                        self.display_manager.stop()
                        self.controller.stop()
                        pygame.quit()
                        return  # Exit immediately without cleanup loop
                    # Handle Cmd+Q on macOS
                    elif event.key == pygame.K_q and (pygame.key.get_pressed()[pygame.K_LMETA] or pygame.key.get_pressed()[pygame.K_RMETA]):
                        self.logger.info("Cmd+Q pressed - initiating immediate shutdown")
                        self.display_manager.stop()
                        self.controller.stop()
                        pygame.quit()
                        return  # Exit immediately without cleanup loop
                    # Removed: Shift key handling for filename display (per requirements)
                    else:
                        # Convert pygame key events to normalized format
                        self._handle_pygame_key(event, key_callback)
                # Removed: KEYUP event handling for Shift key (per requirements)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if input is blocked
                    if self.input_blocked:
                        self.logger.debug(f"[INPUT-BLOCK] Mouse event ignored: {self.input_block_reason}")
                        continue
                    
                    # Handle mouse button clicks and scroll wheel
                    if event.button == 1:  # Left click
                        self.logger.info("Left mouse click - going to previous slide")
                        self.controller.advance_slideshow(TriggerType.MOUSE, Direction.PREVIOUS)
                    elif event.button == 3:  # Right click
                        self.logger.info("Right mouse click - going to next slide")
                        self.controller.advance_slideshow(TriggerType.MOUSE, Direction.NEXT)
                    elif event.button == 4 or event.button == 5:  # Scroll wheel UP or DOWN
                        # Debounce scroll wheel to prevent rapid-fire events
                        current_time = pygame.time.get_ticks()
                        if current_time - self.last_scroll_time >= self.scroll_debounce_ms:
                            self.last_scroll_time = current_time
                            direction = "UP" if event.button == 4 else "DOWN"
                            self.logger.info(f"Scroll wheel {direction} - toggling pause")
                            self.controller.toggle_pause()
                        else:
                            self.logger.debug(f"Scroll wheel event ignored (debounced, {current_time - self.last_scroll_time}ms since last)")
            
            # Check for timer-triggered advancement (macOS thread safety)
            if hasattr(self.controller, 'timer_advance_requested') and self.controller.timer_advance_requested:
                self.controller.timer_advance_requested = False
                try:
                    self.logger.debug("[PYGAME-MAIN] Processing timer advancement on main thread")
                    self.controller.advance_slideshow(TriggerType.TIMER, Direction.NEXT)
                except Exception as e:
                    self.logger.error(f"[PYGAME-MAIN] Error in timer advancement: {e}")
            
            # Check for voice-triggered commands (macOS/pygame thread safety)
            # Process all pending voice commands from queue
            if hasattr(self.controller, 'voice_command_queue'):
                while not self.controller.voice_command_queue.empty():
                    try:
                        command = self.controller.voice_command_queue.get_nowait()
                        self.logger.debug(f"[PYGAME-MAIN] Processing voice command '{command}' on main thread")
                        
                        if command == 'next':
                            self.controller.advance_slideshow(TriggerType.VOICE_NEXT, Direction.NEXT)
                        elif command == 'back':
                            self.controller.advance_slideshow(TriggerType.VOICE_PREVIOUS, Direction.PREVIOUS)
                        elif command == 'pause' or command == 'resume':
                            self.controller.toggle_pause()
                        
                        self.controller.voice_command_queue.task_done()
                    except Exception as e:
                        self.logger.error(f"[PYGAME-MAIN] Error processing voice command: {e}")
                        break  # Stop processing on error
            
            # Maintain reasonable frame rate
            clock.tick(30)  # Reduce to 30 FPS to prevent excessive CPU usage
        
        # Cleanup
        self.display_manager.cleanup()
    
    def _handle_pygame_key(self, pygame_event, key_callback):
        """Convert pygame key events to normalized format."""
        # Create a mock event object for compatibility
        class MockEvent:
            def __init__(self, keysym):
                self.keysym = keysym
        
        # Handle test mode keyboard shortcuts (Shift+T, Shift+C, Shift+D)
        mods = pygame.key.get_mods()
        shift_pressed = mods & pygame.KMOD_SHIFT
        
        if shift_pressed:
            if pygame_event.key == pygame.K_t:
                # Shift+T: Enable video load failure test mode
                self.display_manager.enable_video_failure_test_mode('load')
                self.logger.warning("[TEST-MODE] Video LOAD failure test enabled - next video will fail")
                return
            elif pygame_event.key == pygame.K_c:
                # Shift+C: Enable video codec failure test mode
                self.display_manager.enable_video_failure_test_mode('codec')
                self.logger.warning("[TEST-MODE] Video CODEC failure test enabled - next video will fail")
                return
            elif pygame_event.key == pygame.K_d:
                # Shift+D: Disable test mode
                self.display_manager.disable_video_failure_test_mode()
                self.logger.info("[TEST-MODE] Video failure test mode DISABLED - normal playback")
                return
        
        # Map pygame keys to normalized key identifiers
        key_mapping = {
            pygame.K_SPACE: 'space',
            pygame.K_ESCAPE: 'Escape',
            pygame.K_LEFT: 'Left',
            pygame.K_RIGHT: 'Right',
            pygame.K_UP: 'Up',
            pygame.K_DOWN: 'Down',
            pygame.K_p: 'p',
            pygame.K_n: 'n',
            pygame.K_b: 'b',
            pygame.K_f: 'f',
            pygame.K_q: 'q'
        }
        
        if pygame_event.key in key_mapping:
            mock_event = MockEvent(key_mapping[pygame_event.key])
            key_callback(mock_event)
            
            # Handle immediate exit for escape key
            if pygame_event.key == pygame.K_ESCAPE:
                self.logger.info("ESC key pressed - initiating immediate shutdown")
                self.display_manager.stop()
                self.controller.stop()
                return  # Exit immediately
    
    def start_slideshow(self):
        """Start the slideshow using pygame."""
        # Log test mode keyboard shortcuts
        self.logger.info("="*80)
        self.logger.info("VIDEO ERROR TESTING SHORTCUTS:")
        self.logger.info("  Shift+T = Enable video LOAD failure test (simulates missing file)")
        self.logger.info("  Shift+C = Enable video CODEC failure test (simulates bad codec)")
        self.logger.info("  Shift+D = Disable test mode (return to normal playback)")
        self.logger.info("="*80)
        return self.controller.start_slideshow()


def main() -> None:
    """Main application entry point using pygame display."""
    try:
        # Initialize path configuration
        path_config = PathConfig.create_from_env()
        
        # Load user configuration file
        config = SlideshowConfig(path_config)
        config.load_config()
        
        # Setup logging and get logger
        setup_logging(config.get('verbose', False))
        logger = logging.getLogger(__name__)
        
        # Initialize photo manager and load photos
        photo_manager = PhotoManager(config, path_config)
        photos = photo_manager.load_photos()
        
        if not photos:
            print("No photos found. Please check your album configuration.")
            logger.error("Please add photos to this album in Photos.")
            return
        
        album_name = config.get('album_name', 'photoframe')
        logger.info(f"Loaded {len(photos)} photos from album '{album_name}'")
        
        # Create pygame display manager
        display_manager = PygameDisplayManager(config)
        
        # Create pygame-compatible controller
        controller = PygameSlideshowController(config, photo_manager, display_manager, path_config)
        
        logger.info(f"Starting pygame slideshow with {len(photos)} photos...")
        logger.info("Controls: Spacebar (pause/play), Arrow keys (prev/next), Shift (show filename), Escape (exit)")
        
        controller.start_slideshow()
        
    except KeyboardInterrupt:
        logger.info("Slideshow stopped by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
