"""
Path Configuration Service

Provides configurable paths for cache files, logs, and configuration,
enabling dependency injection and better testability.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any


class PathConfig:
    """Manages configurable paths for the slideshow application."""
    
    def __init__(self, 
                 base_dir: Optional[Path] = None,
                 config_dir: Optional[Path] = None,
                 cache_dir: Optional[Path] = None,
                 log_dir: Optional[Path] = None):
        """
        Initialize path configuration.
        
        Args:
            base_dir: Base directory for all files (defaults to user home)
            config_dir: Directory for configuration files
            cache_dir: Directory for cache files
            log_dir: Directory for log files
        """
        # Set base directory
        self.base_dir = base_dir or Path.home()
        
        # Set specific directories with fallbacks
        self.config_dir = config_dir or self.base_dir
        self.cache_dir = cache_dir or self.base_dir
        self.log_dir = log_dir or self.base_dir
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all configured directories exist."""
        for directory in [self.config_dir, self.cache_dir, self.log_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def config_file(self) -> Path:
        """Path to the main configuration file."""
        return self.config_dir / '.photo_slideshow_config.json'
    
    @property
    def log_file(self) -> Path:
        """Path to the main log file."""
        return self.log_dir / '.photo_slideshow.log'
    
    @property
    def cache_file(self) -> Path:
        """Path to the location cache file."""
        return self.cache_dir / '.photo_slideshow_cache.json'
    
    @property
    def download_signal_file(self) -> Path:
        """Path to the download signal file."""
        return self.cache_dir / '.photo_slideshow_download_signal.json'
    
    def get_custom_path(self, filename: str, directory_type: str = 'cache') -> Path:
        """
        Get a custom path in the specified directory.
        
        Args:
            filename: Name of the file
            directory_type: Type of directory ('config', 'cache', 'log')
            
        Returns:
            Path: Full path to the file
        """
        if directory_type == 'config':
            return self.config_dir / filename
        elif directory_type == 'cache':
            return self.cache_dir / filename
        elif directory_type == 'log':
            return self.log_dir / filename
        else:
            return self.base_dir / filename
    
    @classmethod
    def create_for_testing(cls, temp_dir: Path) -> 'PathConfig':
        """
        Create a PathConfig instance for testing with temporary directories.
        
        Args:
            temp_dir: Temporary directory to use as base
            
        Returns:
            PathConfig: Configured for testing
        """
        return cls(
            base_dir=temp_dir,
            config_dir=temp_dir / 'config',
            cache_dir=temp_dir / 'cache',
            log_dir=temp_dir / 'logs'
        )
    
    @classmethod
    def create_from_env(cls) -> 'PathConfig':
        """
        Create PathConfig from environment variables.
        
        Environment variables:
        - PHOTO_SLIDESHOW_BASE_DIR: Base directory
        - PHOTO_SLIDESHOW_CONFIG_DIR: Config directory
        - PHOTO_SLIDESHOW_CACHE_DIR: Cache directory
        - PHOTO_SLIDESHOW_LOG_DIR: Log directory
        
        Returns:
            PathConfig: Configured from environment
        """
        base_dir = None
        if base_env := os.getenv('PHOTO_SLIDESHOW_BASE_DIR'):
            base_dir = Path(base_env)
        
        config_dir = None
        if config_env := os.getenv('PHOTO_SLIDESHOW_CONFIG_DIR'):
            config_dir = Path(config_env)
        
        cache_dir = None
        if cache_env := os.getenv('PHOTO_SLIDESHOW_CACHE_DIR'):
            cache_dir = Path(cache_env)
        
        log_dir = None
        if log_env := os.getenv('PHOTO_SLIDESHOW_LOG_DIR'):
            log_dir = Path(log_env)
        
        return cls(
            base_dir=base_dir,
            config_dir=config_dir,
            cache_dir=cache_dir,
            log_dir=log_dir
        )
    
    def to_dict(self) -> Dict[str, str]:
        """Convert path configuration to dictionary for serialization."""
        return {
            'base_dir': str(self.base_dir),
            'config_dir': str(self.config_dir),
            'cache_dir': str(self.cache_dir),
            'log_dir': str(self.log_dir)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'PathConfig':
        """Create PathConfig from dictionary."""
        return cls(
            base_dir=Path(data.get('base_dir', Path.home())),
            config_dir=Path(data.get('config_dir', Path.home())),
            cache_dir=Path(data.get('cache_dir', Path.home())),
            log_dir=Path(data.get('log_dir', Path.home()))
        )
