#!/usr/bin/env python3
"""
Dynamic Photo Slideshow - Main Application
A fullscreen photo slideshow that connects to Apple Photos with intelligent layout and EXIF overlays.
"""

import sys
import logging
from pathlib import Path

from config import SlideshowConfig
from photo_manager import PhotoManager
from display_manager import DisplayManager
from slideshow_controller import SlideshowController


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration based on verbose setting."""
    log_level = logging.DEBUG if verbose else logging.WARNING
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(Path.home() / '.photo_slideshow.log'),
            logging.StreamHandler(sys.stdout) if verbose else logging.NullHandler()
        ]
    )


def main() -> None:
    """Main application entry point following startup sequence from requirements."""
    try:
        # 1. Load user configuration file
        config = SlideshowConfig()
        config.load_config()
        
        # Setup logging based on config
        setup_logging(config.get('LOGGING_VERBOSE', False))
        logger = logging.getLogger(__name__)
        logger.info("Starting Dynamic Photo Slideshow")
        
        # 2. Connect to Photos library via osxphotos
        photo_manager = PhotoManager(config)
        
        # 3. Verify configured album exists
        album_name = config.get('album_name', 'photoframe')
        if not photo_manager.verify_album():
            logger.error(f"Album '{album_name}' not found in Photos library.")
            logger.error("Please create this album in Photos or update the configuration file.")
            return
        
        # 4. Load initial batch of photos with orientation detection
        photos = photo_manager.load_photos()
        if not photos:
            logger.error(f"No photos found in album '{album_name}'.")
            logger.error("Please add photos to this album in Photos.")
            return
        
        logger.info(f"Loaded {len(photos)} photos from album '{album_name}'")
        
        # 5. Start slideshow automatically
        display_manager = DisplayManager(config)
        controller = SlideshowController(config, photo_manager, display_manager)
        
        logger.info(f"Starting slideshow with {len(photos)} photos...")
        logger.info("Controls: Spacebar (pause/play), Arrow keys (prev/next), Shift (show filename), Escape (exit)")
        
        controller.start_slideshow()
        
    except KeyboardInterrupt:
        logger.info("Slideshow stopped by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
