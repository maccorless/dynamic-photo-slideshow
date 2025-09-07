"""
Custom exceptions for the Dynamic Photo Slideshow application.

Provides specific exception types for better error handling and debugging.
"""


class SlideshowError(Exception):
    """Base exception for all slideshow-related errors."""
    pass


class PhotoLibraryError(SlideshowError):
    """Raised when there are issues with the Photos library connection or access."""
    pass


class AlbumNotFoundError(PhotoLibraryError):
    """Raised when a specified album cannot be found."""
    pass


class PhotoLoadError(SlideshowError):
    """Raised when there are issues loading or processing photos."""
    pass


class PhotoMetadataError(PhotoLoadError):
    """Raised when there are issues extracting photo metadata."""
    pass


class ConfigurationError(SlideshowError):
    """Raised when there are configuration-related issues."""
    pass


class PathConfigurationError(ConfigurationError):
    """Raised when there are issues with path configuration."""
    pass


class VoiceCommandError(SlideshowError):
    """Raised when there are issues with voice command processing."""
    pass


class VoiceRecognitionError(VoiceCommandError):
    """Raised when voice recognition fails."""
    pass


class LocationServiceError(SlideshowError):
    """Raised when there are issues with location/geocoding services."""
    pass


class GeocodingError(LocationServiceError):
    """Raised when geocoding requests fail."""
    pass


class CacheError(SlideshowError):
    """Raised when there are issues with cache operations."""
    pass


class DisplayError(SlideshowError):
    """Raised when there are issues with photo display."""
    pass


class NavigationError(SlideshowError):
    """Raised when there are issues with slideshow navigation."""
    pass
