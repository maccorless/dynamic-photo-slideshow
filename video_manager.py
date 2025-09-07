"""
Video processing and management module for Dynamic Photo Slideshow v3.0.

This module handles video file detection, metadata extraction, and validation
to extend the slideshow capabilities beyond photos to include video content.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import mimetypes

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logging.warning("OpenCV not available - video processing will be limited")

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

from slideshow_exceptions import (
    VideoProcessingError,
    VideoFormatError,
    VideoCorruptionError
)


class VideoManager:
    """
    Manages video file detection, validation, and metadata extraction.
    
    Supports common video formats: MP4, MOV, AVI, MKV, WMV, FLV
    Uses OpenCV as primary processor with MoviePy as fallback.
    """
    
    # Supported video file extensions
    SUPPORTED_VIDEO_EXTENSIONS = {
        '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', 
        '.webm', '.m4v', '.3gp', '.ogv'
    }
    
    # Video MIME types for additional validation
    VIDEO_MIME_TYPES = {
        'video/mp4', 'video/quicktime', 'video/x-msvideo',
        'video/x-matroska', 'video/x-ms-wmv', 'video/x-flv',
        'video/webm', 'video/3gpp', 'video/ogg'
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize VideoManager with optional logger.
        
        Args:
            logger: Optional logger instance for debugging
        """
        self.logger = logger or logging.getLogger(__name__)
        self._validate_dependencies()
    
    def _validate_dependencies(self) -> None:
        """Validate that required video processing libraries are available."""
        if not OPENCV_AVAILABLE and not MOVIEPY_AVAILABLE:
            raise VideoProcessingError(
                "No video processing libraries available. "
                "Install opencv-python or moviepy to enable video support."
            )
        
        if OPENCV_AVAILABLE:
            self.logger.info("OpenCV available for video processing")
        if MOVIEPY_AVAILABLE:
            self.logger.info("MoviePy available as fallback for video processing")
    
    def is_video_file(self, file_path: str) -> bool:
        """
        Check if a file is a supported video format.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file is a supported video format, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.SUPPORTED_VIDEO_EXTENSIONS:
            return False
        
        # Additional MIME type validation
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type not in self.VIDEO_MIME_TYPES:
            self.logger.debug(f"File {file_path} has unexpected MIME type: {mime_type}")
        
        return True
    
    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing video metadata
            
        Raises:
            VideoProcessingError: If video cannot be processed
            VideoCorruptionError: If video file is corrupted
        """
        if not self.is_video_file(video_path):
            raise VideoFormatError(f"Unsupported video format: {video_path}")
        
        metadata = {
            'file_path': video_path,
            'file_size': os.path.getsize(video_path),
            'file_name': os.path.basename(video_path),
            'duration': 0.0,
            'fps': 0.0,
            'width': 0,
            'height': 0,
            'codec': 'unknown',
            'has_audio': False,
            'is_valid': False
        }
        
        # Try OpenCV first (faster, more reliable)
        if OPENCV_AVAILABLE:
            try:
                metadata.update(self._extract_metadata_opencv(video_path))
                metadata['processor'] = 'opencv'
                return metadata
            except Exception as e:
                self.logger.warning(f"OpenCV metadata extraction failed for {video_path}: {e}")
        
        # Fallback to MoviePy
        if MOVIEPY_AVAILABLE:
            try:
                metadata.update(self._extract_metadata_moviepy(video_path))
                metadata['processor'] = 'moviepy'
                return metadata
            except Exception as e:
                self.logger.error(f"MoviePy metadata extraction failed for {video_path}: {e}")
        
        raise VideoProcessingError(f"Failed to extract metadata from {video_path}")
    
    def _extract_metadata_opencv(self, video_path: str) -> Dict[str, Any]:
        """Extract metadata using OpenCV."""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise VideoCorruptionError(f"Cannot open video file: {video_path}")
        
        try:
            # Basic video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate duration
            duration = frame_count / fps if fps > 0 else 0.0
            
            # Try to get codec information
            fourcc = cap.get(cv2.CAP_PROP_FOURCC)
            codec = "".join([chr((int(fourcc) >> 8 * i) & 0xFF) for i in range(4)])
            
            return {
                'duration': duration,
                'fps': fps,
                'width': width,
                'height': height,
                'codec': codec.strip(),
                'frame_count': int(frame_count),
                'is_valid': True
            }
        
        finally:
            cap.release()
    
    def _extract_metadata_moviepy(self, video_path: str) -> Dict[str, Any]:
        """Extract metadata using MoviePy as fallback."""
        try:
            with VideoFileClip(video_path) as clip:
                return {
                    'duration': clip.duration,
                    'fps': clip.fps,
                    'width': clip.w,
                    'height': clip.h,
                    'has_audio': clip.audio is not None,
                    'is_valid': True
                }
        except Exception as e:
            raise VideoCorruptionError(f"MoviePy cannot process video: {e}")
    
    def validate_video_file(self, video_path: str) -> bool:
        """
        Validate that a video file is playable and not corrupted.
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if video is valid and playable, False otherwise
        """
        try:
            metadata = self.get_video_metadata(video_path)
            return metadata.get('is_valid', False) and metadata.get('duration', 0) > 0
        except (VideoProcessingError, VideoCorruptionError):
            return False
    
    def get_video_thumbnail(self, video_path: str, timestamp: float = 1.0) -> Optional[str]:
        """
        Extract a thumbnail frame from video at specified timestamp.
        
        Args:
            video_path: Path to video file
            timestamp: Time in seconds to extract frame from
            
        Returns:
            Path to saved thumbnail image, or None if extraction fails
        """
        if not OPENCV_AVAILABLE:
            self.logger.warning("OpenCV required for thumbnail extraction")
            return None
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            # Set position to desired timestamp
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Save thumbnail with video filename + _thumb.jpg
                video_name = Path(video_path).stem
                thumbnail_path = str(Path(video_path).parent / f"{video_name}_thumb.jpg")
                cv2.imwrite(thumbnail_path, frame)
                return thumbnail_path
            
        except Exception as e:
            self.logger.error(f"Thumbnail extraction failed for {video_path}: {e}")
        
        return None
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported video file extensions.
        
        Returns:
            List of supported video file extensions
        """
        return sorted(list(self.SUPPORTED_VIDEO_EXTENSIONS))
