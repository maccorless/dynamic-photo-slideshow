"""
Configuration management for Dynamic Photo Slideshow.
Handles loading, validation, and defaults for user configuration.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Union


class SlideshowConfig:
    """Manages slideshow configuration with validation and defaults."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "album_name": "photoframe",
        "filter_by_people": False,
        "filter_people_names": [],
        "filter_by_places": [],
        "filter_by_keywords": [],
        "people_filter_logic": "OR",
        "places_filter_logic": "OR",
        "overall_filter_logic": "AND",
        "min_people_count": 1,
        "max_photos_limit": 500,
        "shuffle_photos": True,
        "slideshow_interval": 10,
        "portrait_pairing": True,
        "MONITOR_RESOLUTION": "auto",
        "OVERLAY_PLACEMENT": "TOP",
        "OVERLAY_ALIGNMENT": "CENTER",
        "TRANSITION_EFFECT": "fade",
        "CACHE_SIZE_LIMIT_GB": 20,
        "FORCE_CACHE_REFRESH": False,
        "max_recent_photos": 50,
        "fallback_photo_limit": 20,
        "min_fallback_photos": 10,
        "progress_log_interval": 1000,
        "download_batch_size": 100,
        "max_year_percentage": 0.3,
        "cache_refresh_check_interval": 3600,
        "DEBUG_SCALING": False,
        "LOGGING_VERBOSE": False
    }
    
    # Valid values for validation
    VALID_VALUES = {
        "OVERLAY_PLACEMENT": ["TOP", "BOTTOM"],
        "OVERLAY_ALIGNMENT": ["LEFT", "CENTER", "RIGHT"],
        "TRANSITION_EFFECT": ["fade", "crossfade", "cut"],
        "people_filter_logic": ["AND", "OR"],
        "places_filter_logic": ["AND", "OR"],
        "overall_filter_logic": ["AND", "OR"]
    }
    
    def __init__(self):
        self.config_path = Path.home() / '.photo_slideshow_config.json'
        self.config = self.DEFAULT_CONFIG.copy()
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> None:
        """Load configuration from file, using defaults for missing/invalid values."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Validate and merge user config with defaults
                for key, value in user_config.items():
                    if key in self.DEFAULT_CONFIG:
                        if self._validate_config_value(key, value):
                            self.config[key] = value
                        else:
                            self.logger.warning(f"Invalid value for {key}: {value}. Using default: {self.DEFAULT_CONFIG.get(key, value)}")
                    else:
                        # Allow additional config keys not in defaults
                        self.config[key] = value
                
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.info("No config file found, using defaults")
                self._create_default_config()
        
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading config file: {e}. Using defaults.")
            self.config = self.DEFAULT_CONFIG.copy()
    
    def _validate_config_value(self, key: str, value: Any) -> bool:
        """Validate a configuration value."""
        if key in ["SLIDESHOW_INTERVAL_SECONDS", "slideshow_interval"]:
            return isinstance(value, int) and 1 <= value <= 86400
        elif key == "CACHE_SIZE_LIMIT_GB":
            return isinstance(value, int) and 1 <= value <= 100
        elif key in self.VALID_VALUES:
            return value in self.VALID_VALUES[key]
        elif key == "MONITOR_RESOLUTION":
            if value == "auto":
                return True
            if isinstance(value, str) and 'x' in value:
                try:
                    width, height = value.split('x')
                    return int(width) > 0 and int(height) > 0
                except ValueError:
                    return False
            return False
        elif key in ["FORCE_CACHE_REFRESH", "DEBUG_SCALING", "LOGGING_VERBOSE", "portrait_pairing"]:
            return isinstance(value, bool)
        elif key in ["PHOTOS_ALBUM_NAME", "album_name"]:
            return isinstance(value, str)
        elif key in ["max_photos_limit", "min_people_count", "slideshow_interval", 
                     "CACHE_SIZE_LIMIT_GB", "max_recent_photos", "fallback_photo_limit",
                     "min_fallback_photos", "progress_log_interval", "download_batch_size",
                     "cache_refresh_check_interval"]:
            return isinstance(value, int) and value > 0
        elif key == "max_year_percentage":
            return isinstance(value, (int, float)) and 0 < value <= 1
        
        return True
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=2)
            self.logger.info(f"Created default config file at {self.config_path}")
        except IOError as e:
            self.logger.error(f"Could not create config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self.config.copy()
