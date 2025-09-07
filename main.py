#!/usr/bin/env python3
"""
Dynamic Photo Slideshow - Main Application
A fullscreen photo slideshow that connects to Apple Photos with intelligent layout and EXIF overlays.
"""

import sys
import logging
import sys
from pathlib import Path

from config import SlideshowConfig
from photo_manager import PhotoManager
from display_manager import DisplayManager
from slideshow_controller import SlideshowController
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


def main() -> None:
    """Main application entry point following startup sequence from requirements."""
    try:
        # Initialize path configuration (can be overridden by environment variables)
        path_config = PathConfig.create_from_env()
        
        # 1. Load user configuration file
        config = SlideshowConfig(path_config)
        config.load_config()
        
        # Setup logging and get logger
        setup_logging(config.get('verbose', False))
        logger = logging.getLogger(__name__)
        
        # 2. Initialize photo manager and load photos
        photo_manager = PhotoManager(config, path_config)
        photos = photo_manager.load_photos()
        
        if not photos:
            print("No photos found. Please check your album configuration.")
            logger.error("Please add photos to this album in Photos.")
            return
        
        album_name = config.get('album_name', 'photoframe')
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
