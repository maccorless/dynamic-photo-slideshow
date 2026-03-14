"""
Photo and Video management for Dynamic Photo Slideshow v3.0.
Handles Apple Photos integration, album verification, photo loading, and video detection.
"""

import logging
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

try:
    import osxphotos
except ImportError:
    osxphotos = None

from cache_manager import CacheManager
from path_config import PathConfig
from slideshow_exceptions import (
    PhotoLibraryError, AlbumNotFoundError, PhotoLoadError, 
    PhotoMetadataError, SlideshowError, VideoProcessingError
)
from video_manager import VideoManager


class PhotoManager:
    """Manages photo and video loading with Apple Photos integration."""
    
    def __init__(self, config_path_or_dict, path_config: Optional[PathConfig] = None):
        # Handle both config file path and config dict
        if isinstance(config_path_or_dict, str):
            from config import SlideshowConfig
            self.config = SlideshowConfig.from_file(config_path_or_dict, path_config)
        else:
            self.config = config_path_or_dict
            
        self.path_config = path_config or PathConfig()
        self.logger = logging.getLogger(__name__)
        self.photos_db = None
        self.album_name = self.config.get('album_name', 'photoframe')
        self.photos_cache = []
        self.cache_manager = CacheManager(self.config, self.path_config)
        self.last_cache_check = None
        
        # Initialize video manager for v3.0 video support
        try:
            self.video_manager = VideoManager(self.logger)
            self.video_support_enabled = True
            self.logger.debug("Video processing support enabled")
        except VideoProcessingError as e:
            self.video_manager = None
            self.video_support_enabled = False
            self.logger.warning(f"Video support disabled: {e}")
        
        # Check if osxphotos is available
        if osxphotos is None:
            raise PhotoLibraryError("osxphotos library is required but not installed. Please install with: pip install osxphotos")
    
    def _connect_to_photos(self) -> bool:
        """Connect to Photos library using osxphotos."""
        try:
            self.photos_db = osxphotos.PhotosDB()
            self.logger.debug("Successfully connected to Photos library")
            return True
        except (OSError, PermissionError) as e:
            self.logger.error(f"Failed to connect to Photos library: {e}")
            self.logger.error("Make sure Photos is installed and accessible.")
            return False
        except Exception as e:
            raise PhotoLibraryError(f"Unexpected error connecting to Photos library: {e}")
    
    def verify_album(self) -> bool:
        """Verify that the specified album exists in the Photos library."""
        try:
            albums = self.photos_db.albums
            album_names = []
            smart_albums = []
            
            for album in albums:
                try:
                    if hasattr(album, 'title'):
                        title = album.title
                        if callable(title):
                            title = title()
                        title_str = str(title)
                        album_names.append(title_str)
                        
                        # Track if it's a smart album
                        if hasattr(album, 'smart') and album.smart:
                            smart_albums.append(title_str)
                            
                    elif isinstance(album, str):
                        album_names.append(album)
                except (AttributeError, TypeError) as e:
                    self.logger.debug(f"Error processing album: {e}")
                    continue
            
            self.logger.info(f"Found {len(album_names)} albums ({len(smart_albums)} smart albums) in Photos library")
            
            # Check for exact match (case insensitive)
            album_found = None
            for name in album_names:
                if name.lower() == self.album_name.lower():
                    album_found = name
                    break
            
            if album_found:
                album_type = "Smart Album" if album_found in smart_albums else "Album"
                self.logger.info(f"{album_type} '{album_found}' found in Photos library")
                return True
            else:
                self.logger.warning(f"Album '{self.album_name}' not found.")
                self.logger.info(f"Available albums: {', '.join(album_names[:10])}")
                if len(album_names) > 10:
                    self.logger.info(f"... and {len(album_names) - 10} more")
                self.logger.info("To use a specific album:")
                self.logger.info("1. Open settings (Cmd+S) and change 'Album Name'")
                self.logger.info("2. Or create a new album/Smart Album in Photos app")
                self.logger.info("Using all photos from library as fallback for now...")
                return True  # Allow fallback
                
        except (OSError, AttributeError) as e:
            self.logger.error(f"Error verifying album: {e}")
            return True  # Allow fallback
        except Exception as e:
            raise AlbumNotFoundError(f"Unexpected error verifying album '{self.album_name}': {e}")
    
    def load_photos(self) -> List[Dict[str, Any]]:
        """Load photos with filtering by people, places, or album."""
        if not self.photos_db:
            if not self._connect_to_photos():
                return []
        
        try:
            photos = []
            
            # Check if any filters are set (non-empty arrays)
            use_filters = (
                self.config.get('FILTER_PEOPLE', []) or
                self.config.get('FILTER_PLACES', []) or
                self.config.get('FILTER_KEYWORD', [])
            )
            
            if use_filters:
                return self._load_photos_with_filters()
            
            # Original album-based loading
            target_album = None
            for album in self.photos_db.albums:
                try:
                    album_title = album.title
                    if callable(album_title):
                        album_title = album_title()
                    if str(album_title).lower() == self.album_name.lower():
                        target_album = album
                        break
                except (AttributeError, TypeError):
                    continue
            
            if not target_album:
                self.logger.warning(f"Album '{self.album_name}' not found, falling back to all photos")
                # Clear any existing cache and force fresh load
                self.photos_cache = None
                # Use the filtering system instead of fallback
                return self._load_photos_with_filters()
            else:
                # Process photos from the album
                try:
                    # Handle Smart Albums that may not have accessible photos attribute
                    if hasattr(target_album, 'photos'):
                        album_photos = target_album.photos
                        if callable(album_photos):
                            album_photos = album_photos()
                        
                        if album_photos:
                            self.logger.info(f"Found {len(album_photos)} photos in album '{self.album_name}'")
                            for photo in album_photos:
                                photo_data = self._extract_photo_metadata(photo)
                                if photo_data:
                                    photos.append(photo_data)
                        else:
                            self.logger.warning(f"Album '{self.album_name}' exists but has no photos or photos not accessible")
                            self.logger.info("This may be a Smart Album with no matching photos or macOS compatibility issue")
                            # Fallback to shuffled photos from entire library
                            all_photos = list(self.photos_db.photos())
                            if self.config.get('shuffle_photos', True):
                                random.shuffle(all_photos)
                                self.logger.info("Fallback photos shuffled for random selection")
                            photos_to_process = all_photos[:self.config.get('fallback_photo_limit')]
                            for photo in photos_to_process:
                                photo_data = self._extract_photo_metadata(photo)
                                if photo_data:
                                    photos.append(photo_data)
                                    if len(photos) >= self.config.get('min_fallback_photos'):
                                        break
                    else:
                        self.logger.warning(f"Album '{self.album_name}' found but photos not accessible due to macOS compatibility")
                        # Fallback to shuffled photos from entire library
                        all_photos = list(self.photos_db.photos())
                        if self.config.get('shuffle_photos', True):
                            random.shuffle(all_photos)
                            self.logger.info("Fallback photos shuffled for random selection")
                        photos_to_process = all_photos[:self.config.get('min_fallback_photos')]
                        for photo in photos_to_process:
                            photo_data = self._extract_photo_metadata(photo)
                            if photo_data:
                                photos.append(photo_data)
                                if len(photos) >= self.config.get('min_fallback_photos'):
                                    break
                except (OSError, AttributeError, MemoryError) as e:
                    self.logger.error(f"Error accessing album photos: {e}")
                    # Final fallback with shuffle
                    all_photos = list(self.photos_db.photos())
                    if self.config.get('shuffle_photos', True):
                        random.shuffle(all_photos)
                        self.logger.info("Final fallback photos shuffled for random selection")
                    photos_to_process = all_photos[:self.config.get('min_fallback_photos')]
                    for photo in photos_to_process:
                        photo_data = self._extract_photo_metadata(photo)
                        if photo_data:
                            photos.append(photo_data)
                            if len(photos) >= self.config.get('min_fallback_photos'):
                                break
            
            self.logger.info(f"Successfully processed {len(photos)} photos from album '{self.album_name}'")
            self.logger.info(f"Rejected {0} photos during metadata extraction")
            return photos
        
        except (OSError, MemoryError) as e:
            self.logger.error(f"Error loading photos: {e}")
            return []
        except Exception as e:
            raise PhotoLoadError(f"Unexpected error loading photos: {e}")
    
    def _load_photos_with_filters(self, log_search: bool = True) -> List[Dict[str, Any]]:
        """Load photos using configured filters (people, places, keywords).

        Filter logic (FILTER_AND_OR):
        - AND: photo must match ALL active filter types (e.g., person AND place)
        - OR:  photo must match ANY active filter type
        Within a single filter type, multiple values always use OR
        (e.g., ["Alice", "Bob"] matches photos with Alice OR Bob).
        """
        try:
            # Get filter configurations
            filter_people_names = self.config.get('FILTER_PEOPLE', [])
            filter_places = self.config.get('FILTER_PLACES', [])
            filter_keywords = self.config.get('FILTER_KEYWORD', [])
            filter_logic = self.config.get('FILTER_AND_OR', 'AND')

            # Log active filters
            if log_search:
                total_library_count = len(list(self.photos_db.photos()))
                self.logger.info(f"Photo library: {total_library_count} total items (photos + videos)")
                filters = []
                if filter_people_names:
                    filters.append(f"people={filter_people_names}")
                if filter_places:
                    filters.append(f"places={filter_places}")
                if filter_keywords:
                    filters.append(f"keywords={filter_keywords}")
                filter_str = f" {filter_logic} ".join(filters) if filters else "None"
                self.logger.info(f"Filters: {filter_str}")

            # Step 1: Build people UUID set via osxphotos direct search
            people_uuids = None
            if filter_people_names:
                people_uuids = set()
                for person_name in filter_people_names:
                    try:
                        person_photos = self.photos_db.photos(persons=[person_name.strip()])
                        people_uuids.update(p.uuid for p in person_photos)
                        self.logger.debug(f"Found {len(person_photos)} photos with person '{person_name}'")
                    except (OSError, AttributeError, ValueError) as e:
                        self.logger.warning(f"Error searching for person '{person_name}': {e}")
                self.logger.debug(f"People filter: {len(people_uuids)} unique photos")

            # Determine candidate set:
            # - AND mode with only people filter: use people-matched photos (faster)
            # - OR mode with multiple filters: must scan full library
            has_other_filters = bool(filter_places or filter_keywords)
            if filter_people_names and not (filter_logic == 'OR' and has_other_filters):
                # AND mode or people-only: start from people-matched photos
                all_photos = [p for p in self.photos_db.photos() if p.uuid in people_uuids]
            else:
                all_photos = list(self.photos_db.photos())

            # Step 2: Apply places and keywords filters with FILTER_AND_OR logic
            photos = []
            processed_count = 0
            rejected_count = 0
            for photo in all_photos:
                try:
                    # Evaluate each active filter type
                    results = []
                    if filter_people_names:
                        results.append(photo.uuid in people_uuids if people_uuids else False)
                    if filter_places:
                        results.append(self._check_places_filter(photo, filter_places, 'OR'))
                    if filter_keywords:
                        results.append(self._check_keywords_filter(photo, filter_keywords))

                    # Combine results using configured logic
                    if filter_logic == 'AND':
                        passes_filter = all(results)
                    else:  # OR
                        passes_filter = any(results)

                    if passes_filter:
                        photo_data = self._extract_photo_metadata(photo)
                        if photo_data:
                            photos.append(photo_data)
                        else:
                            rejected_count += 1

                except (AttributeError, OSError, ValueError) as e:
                    self.logger.debug(f"Error filtering photo: {e}")
                    rejected_count += 1
                    continue

                processed_count += 1
                if processed_count % self.config.get('progress_log_interval') == 0:
                    self.logger.debug(f"Processed {processed_count}/{len(all_photos)} photos, found {len(photos)} matches")
            
            # Use all available photos - no need to limit since they're all locally cached
            if self.config.get('shuffle_photos', True):
                random.shuffle(photos)
                self.logger.debug(f"Using all {len(photos)} photos in random order")
            
            if log_search:
                matched_count = len(all_photos)
                self.logger.info(f"Filter results: {matched_count} items matched filters, {len(photos)} loaded ({rejected_count} rejected)")
            
            # Clear any existing cache and force fresh load
            old_cache_count = len(self.photos_cache) if self.photos_cache else 0
            self.photos_cache = None
            self.photos_cache = photos
            
            if log_search:
                new_count = len(photos) - old_cache_count
                if new_count > 0:
                    self.logger.info(f"Cache status: {len(photos)} items in cache ({new_count} new this session)")
                else:
                    self.logger.info(f"Cache status: {len(photos)} items in cache (0 new this session)")
            
            return photos
            
        except (OSError, MemoryError) as e:
            self.logger.error(f"Error applying filters: {e}")
            return []
        except Exception as e:
            raise PhotoLoadError(f"Unexpected error applying filters: {e}")
    
    def _check_places_filter(self, photo, filter_places, logic):
        """Check if photo matches places filter with substring matching."""
        if not hasattr(photo, 'place') or not photo.place:
            return False
        
        place_name = getattr(photo.place, 'name', str(photo.place))
        if not place_name or place_name == 'None':
            return False
        
        place_name_lower = place_name.lower()
        
        if logic == 'AND':
            # All place filters must match
            return all(place_filter.lower() in place_name_lower for place_filter in filter_places)
        else:  # OR
            # Any place filter must match
            return any(place_filter.lower() in place_name_lower for place_filter in filter_places)
    
    def _check_keywords_filter(self, photo, filter_keywords):
        """Check if photo matches keywords filter."""
        if not hasattr(photo, 'keywords') or not photo.keywords:
            return False
        
        photo_keywords = [k.lower() for k in photo.keywords]
        return any(keyword.lower() in photo_keywords for keyword in filter_keywords)
    
    def _extract_photo_metadata(self, photo) -> Optional[Dict[str, Any]]:
        """Extract metadata from a photo object."""
        try:
            # Skip hidden photos and RAW images
            if photo.hidden or photo.has_raw:
                self.logger.debug(f"[EXTRACT-DEBUG] Rejecting {photo.filename}: hidden={photo.hidden}, has_raw={photo.has_raw}")
                return None

            # Determine media type
            media_type = 'image'
            if photo.ismovie:
                media_type = 'video'
            elif photo.live_photo:
                media_type = 'live_photo'

            # Get basic photo information with error handling
            photo_date = getattr(photo, 'date', None)
            date_str = None
            if photo_date:
                try:
                    date_str = photo_date.isoformat()
                except:
                    date_str = str(photo_date)

            photo_data = {
                'uuid': photo.uuid,
                'filename': photo.filename,
                'path': photo.path,
                'media_type': media_type,
                'date_taken': photo_date,
                'date': date_str,
                'width': photo.width,
                'height': photo.height,
                'orientation': 'landscape', # default
                'exif_orientation': 1 # default
            }

            # Try to get EXIF orientation from osxphotos
            try:
                if hasattr(photo, 'exif_info') and photo.exif_info:
                    exif_info = photo.exif_info
                    if hasattr(exif_info, 'orientation'):
                        photo_data['exif_orientation'] = exif_info.orientation
                    elif hasattr(exif_info, 'get'):
                        photo_data['exif_orientation'] = exif_info.get('Orientation', 1)
            except (AttributeError, KeyError, ValueError) as e:
                self.logger.debug(f"Could not extract EXIF orientation: {e}")

            # Determine orientation safely
            if photo_data['width'] and photo_data['height']:
                photo_data['orientation'] = self._determine_orientation(photo_data['width'], photo_data['height'])

            # Extract GPS coordinates if available
            try:
                if hasattr(photo, 'location') and photo.location:
                    photo_data['gps_coordinates'] = {
                        'latitude': photo.location[0],
                        'longitude': photo.location[1]
                    }
            except (AttributeError, TypeError):
                pass  # GPS not available

            # Handle photos/videos that need to be exported from Apple Photos
            if not photo_data['path'] or photo_data['path'] == '':
                self.logger.debug(f"[EXTRACT-DEBUG] {photo_data['filename']}: path is empty, media_type={media_type}, hasattr(export)={hasattr(photo, 'export')}")
                
                # Check if photo is missing (in iCloud but not downloadable)
                is_missing = getattr(photo, 'ismissing', False)
                if is_missing:
                    # Try to use derivative/thumbnail as fallback for missing photos
                    if hasattr(photo, 'path_derivatives') and photo.path_derivatives:
                        import os
                        # Use the largest derivative (usually the last one)
                        for derivative_path in reversed(photo.path_derivatives):
                            if os.path.exists(derivative_path):
                                photo_data['path'] = derivative_path
                                photo_data['is_derivative'] = True
                                self.logger.debug(f"[EXTRACT-DEBUG] Using derivative for missing {media_type}: {photo_data.get('filename', 'unknown')} -> {os.path.basename(derivative_path)}")
                                break
                        
                        # If we found a derivative, use it
                        if photo_data.get('path'):
                            return photo_data
                    
                    # No derivatives available, reject the photo
                    self.logger.debug(f"[EXTRACT-DEBUG] Rejecting {media_type} - ismissing=True and no derivatives available: {photo_data.get('filename', 'unknown')}")
                    return None
                
                if hasattr(photo, 'export'):
                    # For photos/videos without direct paths, we'll handle export during display
                    photo_data['needs_export'] = True
                    photo_data['osxphoto_object'] = photo  # Store reference for export
                    self.logger.debug(f"[EXTRACT-DEBUG] {media_type} needs export: {photo_data.get('filename', 'unknown')}")
                else:
                    self.logger.debug(f"[EXTRACT-DEBUG] Rejecting {media_type} due to missing path and no export capability: {photo_data.get('filename', 'unknown')}")
                    return None

            self.logger.debug(f"[EXTRACT-DEBUG] Returning photo_data for {photo_data['filename']}: needs_export={photo_data.get('needs_export', False)}")
            return photo_data

        except (OSError, AttributeError, ValueError) as e:
            self.logger.warning(f"Error extracting metadata for photo {photo.filename if hasattr(photo, 'filename') else 'unknown'}: {e}")
            return None
        except Exception as e:
            raise PhotoMetadataError(f"Unexpected error extracting photo metadata: {e}")
    
    def _determine_orientation(self, width: int, height: int) -> str:
        """Determine photo orientation based on dimensions."""
        if height > width:
            return 'portrait'
        else:
            return 'landscape'
    
    def get_cached_photos(self) -> List[Dict[str, Any]]:
        """Get cached photos list."""
        return self.photos_cache.copy()
    
    def get_photo_count(self) -> int:
        """Get total number of photos in cache."""
        return len(self.photos_cache)
    
    def get_photo_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get photo by index (0-based)."""
        if 0 <= index < len(self.photos_cache):
            return self.photos_cache[index]
        return None
    
    def get_random_photo_index(self) -> int:
        """Get a random photo index."""
        if not self.photos_cache:
            return 0
        return random.randint(0, len(self.photos_cache) - 1)
    
    def _get_random_portrait_index_by_type(self, media_types: List[str]) -> Optional[int]:
        """Get a random portrait index for a specific media type."""
        portrait_indices = [i for i, photo in enumerate(self.photos_cache)
                          if photo.get('orientation') == 'portrait' and photo.get('media_type') in media_types]
        if not portrait_indices:
            return None
        return random.choice(portrait_indices)

    def get_random_portrait_image_index(self) -> Optional[int]:
        """Get a random portrait image index."""
        return self._get_random_portrait_index_by_type(['image'])

    def get_random_portrait_video_index(self) -> Optional[int]:
        """Get a random portrait video or live photo index."""
        return self._get_random_portrait_index_by_type(['video', 'live_photo'])

    def get_random_portrait_index(self) -> Optional[int]:
        """Get a random portrait photo index, or None if no portraits available."""
        return self._get_random_portrait_index_by_type(['image', 'video', 'live_photo'])
    
    def check_and_load_new_photos(self) -> bool:
        """Check for new photos and load them incrementally. Returns True if new photos were loaded.

        Always re-queries the Photos library when the refresh interval has elapsed,
        so new photos added directly to Apple Photos are picked up automatically.
        The signal file from download scripts can also trigger an early refresh.
        """
        # Check if a download script wrote a signal file (triggers immediate refresh)
        signal_triggered = self.cache_manager.check_for_new_photos() is not None

        # Also refresh on the regular interval, regardless of signal file
        if not signal_triggered and not self.cache_manager.should_check_cache(self.last_cache_check):
            return False

        # Load new photos incrementally
        old_count = len(self.photos_cache)
        self.logger.debug(f"Checking for new photos (had {old_count} photos)")

        # Get fresh photos from the library (suppress logging for incremental check)
        new_photos = self._load_photos_with_filters(log_search=False)

        if len(new_photos) != old_count:
            change = len(new_photos) - old_count
            self.photos_cache = new_photos
            self.logger.info(f"Cache updated: {change:+d} items (now {len(self.photos_cache)} total)")
            self.last_cache_check = datetime.now(timezone.utc)
            return True

        self.last_cache_check = datetime.now(timezone.utc)
        return False
    
    def refresh_photos(self) -> List[Dict[str, Any]]:
        """Refresh photos from the album."""
        self.logger.info("Refreshing photos from album")
        return self.load_photos()
    
    def _get_filtered_photos_including_missing(self) -> List[Any]:
        """
        Get all photos that match slideshow filters, including those with missing local files.
        Returns raw osxphotos photo objects, not metadata dictionaries.
        """
        try:
            if not self._connect_to_photos():
                return []
            
            # Get filter configurations
            filter_people_names = self.config.get('FILTER_PEOPLE', [])
            filter_places = self.config.get('FILTER_PLACES', [])
            filter_keywords = self.config.get('FILTER_KEYWORD', [])
            
            # Use direct osxphotos search for people if specified
            if filter_people_names:
                self.logger.info(f"Getting all photos (including missing) for people: {filter_people_names}")
                
                # Get photos using direct search
                filtered_photos = []
                for person_name in filter_people_names:
                    try:
                        person_photos = self.photos_db.photos(persons=[person_name.strip()])
                        filtered_photos.extend(person_photos)
                        self.logger.info(f"Found {len(person_photos)} photos with person '{person_name}' (including missing)")
                    except Exception as e:
                        self.logger.warning(f"Error searching for person '{person_name}': {e}")
                
                # Remove duplicates while preserving order
                seen_uuids = set()
                unique_photos = []
                for photo in filtered_photos:
                    if photo.uuid not in seen_uuids:
                        unique_photos.append(photo)
                        seen_uuids.add(photo.uuid)
                
                all_photos = unique_photos
            else:
                all_photos = list(self.photos_db.photos())
            
            # Apply places, keywords, and hidden filters using FILTER_AND_OR logic
            filter_logic = self.config.get('FILTER_AND_OR', 'AND')
            filtered_photos = []
            for photo in all_photos:
                try:
                    # Skip hidden photos
                    if photo.hidden:
                        continue

                    results = []
                    if filter_people_names:
                        results.append(True)  # Already filtered by people above
                    if filter_places:
                        results.append(self._check_places_filter(photo, filter_places, 'OR'))
                    if filter_keywords:
                        results.append(self._check_keywords_filter(photo, filter_keywords))

                    passes = all(results) if filter_logic == 'AND' else any(results)
                    if passes:
                        filtered_photos.append(photo)
                        
                except Exception as e:
                    self.logger.debug(f"Error filtering photo: {e}")
                    continue
            
            self.logger.info(f"Found {len(filtered_photos)} photos matching filters (including missing local files)")
            return filtered_photos
            
        except Exception as e:
            self.logger.error(f"Error getting filtered photos including missing: {e}")
            return []
    
    def is_video_supported(self) -> bool:
        """Check if video processing is available."""
        return self.video_support_enabled and self.video_manager is not None
    
    def get_supported_video_formats(self) -> List[str]:
        """Get list of supported video formats."""
        if self.is_video_supported():
            return self.video_manager.get_supported_formats()
        return []
    
    def validate_video_file(self, file_path: str) -> bool:
        """Validate a video file for slideshow compatibility."""
        if not self.is_video_supported():
            return False
        return self.video_manager.validate_video_file(file_path)
    
    def get_video_metadata(self, photo_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get video metadata for a photo if it's a video."""
        if not self.video_support_enabled:
            return None
            
        if photo_data.get('media_type') != 'video':
            return None
            
        video_path = photo_data.get('path')
        if not video_path and photo_data.get('needs_export'):
            # Export video temporarily to get metadata
            video_path = self._export_video_temporarily(photo_data)
            if not video_path:
                return None
            
        if not video_path:
            return None
            
        return self.video_manager.get_video_metadata(video_path)
    
    def preload_video_exports(self, photos: List[Dict[str, Any]], max_exports: int = 5) -> None:
        """Preload video exports in background to reduce latency."""
        if not self.video_support_enabled:
            return
            
        import threading
        
        def export_videos_background():
            """Background thread to export videos."""
            export_count = 0
            for photo in photos:
                if export_count >= max_exports:
                    break
                    
                if (photo.get('media_type') == 'video' and 
                    photo.get('needs_export') and 
                    not photo.get('path')):
                    
                    try:
                        self.logger.debug(f"Pre-exporting video: {photo.get('filename')}")
                        exported_path = self._export_video_temporarily(photo)
                        if exported_path:
                            export_count += 1
                            self.logger.info(f"Pre-exported video {export_count}/{max_exports}: {photo.get('filename')}")
                    except Exception as e:
                        self.logger.error(f"Error pre-exporting video {photo.get('filename')}: {e}")
        
        # Start background export thread
        export_thread = threading.Thread(target=export_videos_background, daemon=True)
        export_thread.start()
        self.logger.info(f"Started background video pre-export for up to {max_exports} videos")
    
    def _export_photo_temporarily(self, photo_data: Dict[str, Any]) -> Optional[str]:
        """Export a photo from Apple Photos (iCloud) to a temporary location with caching."""
        if not photo_data.get('needs_export'):
            self.logger.debug(f"[EXPORT-DEBUG] Photo does not need export: needs_export={photo_data.get('needs_export')}")
            return None
        if not photo_data.get('osxphoto_object'):
            self.logger.error(f"[EXPORT-DEBUG] No osxphoto_object found in photo data")
            return None
            
        try:
            import tempfile
            import os
            import hashlib
            
            osxphoto = photo_data['osxphoto_object']
            
            # Create persistent cache directory for photo exports
            cache_dir = os.path.join(os.path.expanduser('~'), '.photo_slideshow_cache', 'photos')
            os.makedirs(cache_dir, exist_ok=True)
            
            # Generate cache filename based on photo UUID
            photo_uuid = photo_data.get('uuid', '')
            if not photo_uuid:
                # Fallback to filename hash if no UUID
                filename = photo_data.get('filename', 'unknown')
                photo_uuid = hashlib.md5(filename.encode()).hexdigest()
            
            # Get original filename extension
            original_filename = photo_data.get('filename', 'photo.jpg')
            file_ext = os.path.splitext(original_filename)[1] or '.jpg'
            
            # Check if already cached
            cached_path = os.path.join(cache_dir, f"{photo_uuid}{file_ext}")
            if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
                self.logger.debug(f"Using cached photo: {cached_path}")
                photo_data['path'] = cached_path
                photo_data['needs_export'] = False
                return cached_path
            
            # Export with timing measurement
            import time
            start_time = time.time()
            self.logger.info(f"Exporting photo from iCloud: {photo_data.get('filename', 'unknown')}...")
            
            # Export to cache directory with UUID filename
            self.logger.debug(f"[EXPORT-DEBUG] About to call osxphoto.export() with cache_dir={cache_dir}, filename={photo_uuid}{file_ext}")
            export_paths = osxphoto.export(cache_dir, filename=f"{photo_uuid}{file_ext}", overwrite=True)
            self.logger.debug(f"[EXPORT-DEBUG] osxphoto.export() returned: {export_paths}")
            
            export_time = time.time() - start_time
            
            if export_paths:
                exported_path = export_paths[0]
                file_size = os.path.getsize(exported_path) if os.path.exists(exported_path) else 0
                self.logger.info(f"Photo exported from iCloud in {export_time:.2f}s ({file_size} bytes): {exported_path}")
                
                # Update photo_data with exported path for future use
                photo_data['path'] = exported_path
                photo_data['needs_export'] = False
                return exported_path
            else:
                self.logger.warning(f"Failed to export photo from iCloud: {photo_data.get('filename', 'unknown')} - export_paths was empty")
                return None
                
        except Exception as e:
            self.logger.error(f"Error exporting photo from iCloud {photo_data.get('filename', 'unknown')}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _export_video_temporarily(self, photo_data: Dict[str, Any]) -> Optional[str]:
        """Export a video from Apple Photos to a temporary location with caching."""
        if not photo_data.get('needs_export'):
            self.logger.error(f"[EXPORT-DEBUG] Video does not need export: needs_export={photo_data.get('needs_export')}")
            return None
        if not photo_data.get('osxphoto_object'):
            self.logger.error(f"[EXPORT-DEBUG] No osxphoto_object found in video data")
            return None
            
        try:
            import tempfile
            import os
            import hashlib
            
            osxphoto = photo_data['osxphoto_object']
            
            # Create persistent cache directory for video exports
            cache_dir = os.path.join(os.path.expanduser('~'), '.photo_slideshow_cache', 'videos')
            os.makedirs(cache_dir, exist_ok=True)
            
            # Generate cache filename based on photo UUID
            photo_uuid = photo_data.get('uuid', '')
            if not photo_uuid:
                # Fallback to filename hash if no UUID
                filename = photo_data.get('filename', 'unknown')
                photo_uuid = hashlib.md5(filename.encode()).hexdigest()
            
            # Check if already cached
            cached_path = os.path.join(cache_dir, f"{photo_uuid}.mov")
            if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
                self.logger.debug(f"Using cached video: {cached_path}")
                photo_data['path'] = cached_path
                photo_data['needs_export'] = False
                return cached_path
            
            # Export with timing measurement
            import time
            start_time = time.time()
            self.logger.info(f"Exporting video: {photo_data.get('filename', 'unknown')}...")
            
            # Export to cache directory with UUID filename
            self.logger.info(f"[EXPORT-DEBUG] About to call osxphoto.export() with cache_dir={cache_dir}, filename={photo_uuid}.mov")
            export_paths = osxphoto.export(cache_dir, filename=f"{photo_uuid}.mov", overwrite=True)
            self.logger.info(f"[EXPORT-DEBUG] osxphoto.export() returned: {export_paths}")
            
            export_time = time.time() - start_time
            
            if export_paths:
                exported_path = export_paths[0]
                file_size = os.path.getsize(exported_path) if os.path.exists(exported_path) else 0
                self.logger.info(f"Video exported in {export_time:.2f}s ({file_size} bytes): {exported_path}")
                
                # Update photo_data with exported path for future use
                photo_data['path'] = exported_path
                photo_data['needs_export'] = False
                return exported_path
            else:
                self.logger.warning(f"Failed to export video: {photo_data.get('filename', 'unknown')} - export_paths was empty")
                return None
                
        except Exception as e:
            self.logger.error(f"Error exporting video {photo_data.get('filename', 'unknown')}: {e}")
            return None
