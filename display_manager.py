"""
Display management for Dynamic Photo Slideshow v3.0.
Handles fullscreen display, image rendering, video playback, and overlay positioning.
"""

import tkinter as tk
import logging
import os
import threading
import time
import numpy as np
from typing import Dict, Any, Optional, List, Union

from PIL import Image, ImageTk, ImageDraw, ImageFont

# Video processing imports
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from video_manager import VideoManager
from slideshow_exceptions import VideoProcessingError, DisplayError

# Enable HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

class DisplayManager:
    """Manages fullscreen display, image rendering, and video playback."""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize video-related attributes
        self.video_manager = None
        self.video_thread = None
        self.video_process = None  # ffplay subprocess
        self.video_playing = False
        self.video_stop_event = threading.Event()
        self.audio_process = None
        self.audio_thread = None
        self.video_complete_callback = None
        self.video_overlay_id = None
        
        # Initialize video support
        try:
            from video_manager import VideoManager
            self.video_manager = VideoManager(self.logger)
            self.logger.info("Video support initialized")
        except Exception as e:
            self.logger.warning(f"Video support not available: {e}")
        
        # Initialize display components
        self.root = None
        self.canvas = None
        self.current_image_id = None
        self.overlay_labels = []
        self.screen_width = 0
        self.screen_height = 0
        
        # Countdown timer attributes (simplified)
        self.countdown_overlay_id = None
        
        # Initialize display
        self._setup_display()

    def _setup_display(self) -> None:
        """Setup fullscreen tkinter display."""
        self.root = tk.Tk()
        self.root.title("Dynamic Photo Slideshow")
        
        # Get screen dimensions
        if self.config.get('MONITOR_RESOLUTION') == 'auto':
            self.screen_width = self.root.winfo_screenwidth()
            self.screen_height = self.root.winfo_screenheight()
        else:
            try:
                resolution = self.config.get('MONITOR_RESOLUTION')
                width, height = resolution.split('x')
                self.screen_width = int(width)
                self.screen_height = int(height)
            except (ValueError, AttributeError):
                self.logger.warning("Invalid monitor resolution config, using auto-detection")
                self.screen_width = self.root.winfo_screenwidth()
                self.screen_height = self.root.winfo_screenheight()
        
        # Configure fullscreen
        self.root.geometry(f"{self.screen_width}x{self.screen_height}")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        self.root.focus_set()
        
        # Create canvas for image display
        self.canvas = tk.Canvas(
            self.root,
            width=self.screen_width,
            height=self.screen_height,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.logger.info(f"Display initialized: {self.screen_width}x{self.screen_height}")

    def display_photo(self, photo_data, location_string: Optional[str] = None, slideshow_timer: Optional[int] = None) -> None:
        """Display a photo or a pair of photos."""
        try:
            if isinstance(photo_data, list) and len(photo_data) == 2:
                self._display_paired_photos(photo_data, location_string, slideshow_timer)
            else:
                self._display_single_photo(photo_data, location_string, slideshow_timer)
        except Exception as e:
            self.logger.error(f"Error in display_photo: {e}")

    def _display_single_photo(self, photo_data: Dict[str, Any], location_string: Optional[str], slideshow_timer: Optional[int] = None) -> None:
        """Display a single photo with overlays."""
        try:
            self._clear_canvas_preserve_overlays()
            
            if not self._validate_image_path(photo_data):
                return
            
            display_image, photo_image = self._load_and_process_image(photo_data)
            if not display_image or not photo_image:
                return
            
            self._center_and_display_image(display_image, photo_image)
            self._add_overlays(photo_data, location_string, 
                             (self.screen_width - display_image.width) // 2,
                             (self.screen_height - display_image.height) // 2,
                             display_image.width, display_image.height)
            
            self._finalize_display()
            
        except (OSError, IOError) as e:
            self.logger.error(f"Error loading image file: {e}")
            self._display_error_message(f"Cannot load image: {os.path.basename(photo_data.get('path', 'Unknown'))}")
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error processing image data: {e}")
            self._display_error_message(f"Invalid image data: {os.path.basename(photo_data.get('path', 'Unknown'))}")
        except Exception as e:
            self.logger.exception(f"Unexpected error displaying single photo: {e}")
            self._display_error_message(f"Cannot load image: {os.path.basename(photo_data.get('path', 'Unknown'))}")

    def _validate_image_path(self, photo_data: Dict[str, Any]) -> bool:
        """Validate that the image path exists."""
        image_path = photo_data.get('path')
        if not image_path or not os.path.exists(image_path):
            self._display_error_message(f"File not found:\n{os.path.basename(image_path)}")
            return False
        return True
    
    def _load_and_process_image(self, photo_data: Dict[str, Any]) -> tuple[Optional[Image.Image], Optional[ImageTk.PhotoImage]]:
        """Load and process image from photo data."""
        try:
            image_path = photo_data.get('path')
            with Image.open(image_path) as image:
                image = self._apply_orientation_correction(image, photo_data.get('exif_orientation', 1))
                display_image = self._resize_image_to_fit(image)
                photo_image = ImageTk.PhotoImage(display_image)
                return display_image, photo_image
        except (OSError, IOError, ValueError, TypeError) as e:
            self.logger.error(f"Error processing image {image_path}: {e}")
            return None, None
    
    def _center_and_display_image(self, display_image: Image.Image, photo_image: ImageTk.PhotoImage) -> None:
        """Center and display the image on canvas."""
        x = (self.screen_width - display_image.width) // 2
        y = (self.screen_height - display_image.height) // 2
        
        self.current_image_id = self.canvas.create_image(x, y, anchor=tk.NW, image=photo_image)
        self.canvas.image = photo_image  # Keep a reference
    
    def _finalize_display(self) -> None:
        """Finalize the display by updating and showing overlays."""
        self.root.update()
        self._refresh_stopped_overlay()

    def _display_paired_photos(self, photo_pair: List[Dict[str, Any]], location_string: Optional[str], slideshow_timer: Optional[int] = None) -> None:
        """Display two portrait photos side-by-side."""
        try:
            # Clear previous display
            self._clear_canvas_preserve_overlays()
            
            # Calculate dimensions for each photo (half screen width)
            target_width = self.screen_width // 2
            target_height = self.screen_height
            
            images = []
            for i, photo_data in enumerate(photo_pair):
                image_path = photo_data.get('path')
                if not image_path or not os.path.exists(image_path):
                    # Create error placeholder
                    error_img = self._create_error_image("Image not found")
                    images.append((error_img, photo_data))
                    continue
                
                try:
                    # Load and process image
                    with Image.open(image_path) as image:
                        image = self._apply_orientation_correction(image, photo_data.get('exif_orientation', 1))
                        
                        # Scale to fit half screen
                        img_width, img_height = image.size
                        aspect_ratio = img_width / img_height
                        
                        if target_width / aspect_ratio <= target_height:
                            new_width = target_width
                            new_height = int(new_width / aspect_ratio)
                        else:
                            new_height = target_height
                            new_width = int(new_height * aspect_ratio)
                        
                        display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    images.append((display_image, photo_data))
                    
                except (OSError, IOError) as e:
                    self.logger.error(f"Error loading paired photo {i}: {e}")
                    error_img = self._create_error_image("Error loading image")
                    images.append((error_img, photo_data))
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Error processing paired photo {i}: {e}")
                    error_img = self._create_error_image("Invalid image data")
                    images.append((error_img, photo_data))
            
            # Display images side by side
            photo_images = []
            for i, (display_image, photo_data) in enumerate(images):
                photo_image = ImageTk.PhotoImage(display_image)
                photo_images.append(photo_image)
                
                # Position: left image at x=0, right image at x=screen_width//2
                x_offset = i * (self.screen_width // 2)
                x = x_offset + (target_width - display_image.width) // 2
                y = (self.screen_height - display_image.height) // 2
                
                self.canvas.create_image(x, y, anchor=tk.NW, image=photo_image)
                
                # Add overlays for each photo
                if i == 0:
                    # Use provided location string for first photo
                    self._add_overlays(photo_data, location_string, x, y, display_image.width, display_image.height)
                else:
                    # Get location for second photo if available
                    loc_str_2 = None
                    if 'gps_coordinates' in photo_data:
                        try:
                            coords = photo_data['gps_coordinates']
                            if hasattr(self, 'controller_ref') and self.controller_ref and hasattr(self.controller_ref, 'location_service'):
                                loc_str_2 = self.controller_ref.location_service.get_location_string(coords['latitude'], coords['longitude'])
                        except Exception as e:
                            self.logger.warning(f"Could not get location for second photo: {e}")
                    
                    self._add_overlays(photo_data, loc_str_2, x, y, display_image.width, display_image.height)
            
            # Keep references to prevent garbage collection
            self.canvas.images = photo_images
            
            # Update display
            self.root.update()
            
            # Show STOPPED overlay AFTER images are displayed if slideshow is paused
            self._refresh_stopped_overlay()
            
        except (OSError, IOError) as e:
            self.logger.error(f"Error loading paired photos: {e}")
            self._display_error_message(f"Cannot load photo pair")
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error processing paired photos: {e}")
            self._display_error_message(f"Invalid photo pair data")
        except Exception as e:
            self.logger.exception(f"Unexpected error displaying paired photos: {e}")
            self._display_error_message(f"Cannot load photo pair")

    def _apply_orientation_correction(self, image: Image.Image, orientation: int) -> Image.Image:
        """Apply EXIF orientation correction."""
        try:
            # Try to get EXIF orientation from the image itself
            try:
                exif = image.getexif()
                if exif and 274 in exif:  # 274 is the EXIF orientation tag
                    orientation = exif[274]
            except:
                pass
            
            # EXIF orientation values and corresponding transformations
            orientation_transforms = {
                1: lambda img: img,  # Normal
                2: lambda img: img.transpose(Image.FLIP_LEFT_RIGHT),  # Mirrored
                3: lambda img: img.rotate(180, expand=True),  # Rotated 180
                4: lambda img: img.rotate(180, expand=True).transpose(Image.FLIP_LEFT_RIGHT),  # Mirrored and rotated 180
                5: lambda img: img.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT),  # Mirrored and rotated 270 CW
                6: lambda img: img.rotate(-90, expand=True),  # Rotated 90 CW
                7: lambda img: img.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT),  # Mirrored and rotated 90 CW
                8: lambda img: img.rotate(90, expand=True)  # Rotated 270 CW
            }
            
            if orientation in orientation_transforms:
                corrected_image = orientation_transforms[orientation](image)
                self.logger.debug(f"Applied orientation correction: {orientation}")
                return corrected_image
            else:
                return image
                
        except Exception as e:
            self.logger.warning(f"Error applying orientation correction: {e}")
            return image
    
    def _resize_image_to_fit(self, image: Image.Image) -> Image.Image:
        """Resize image to fit screen while maintaining aspect ratio."""
        img_width, img_height = image.size
        
        # Calculate scaling factor
        scale_x = self.screen_width / img_width
        scale_y = self.screen_height / img_height
        scale = min(scale_x, scale_y)
        
        # Calculate new dimensions
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _create_error_image(self, message: str) -> Image.Image:
        """Create a placeholder error image."""
        error_img = Image.new('RGB', (self.screen_width // 4, self.screen_height // 2), color='black')
        draw = ImageDraw.Draw(error_img)
        try:
            font = ImageFont.truetype("Helvetica.ttc", 24)
        except OSError:
            font = ImageFont.load_default()
        draw.text((10, 10), message, fill='red', font=font)
        return error_img

    def _display_error_message(self, message: str) -> None:
        """Display an error message instead of a black screen."""
        try:
            # Clear canvas (preserve overlays)
            self._clear_canvas_preserve_overlays()
            
            # Create a simple error display
            font_size = 24
            text_x = self.screen_width // 2
            text_y = self.screen_height // 2
            
            self.canvas.create_text(
                text_x, text_y,
                text=message,
                font=('Arial', font_size),
                fill='white',
                anchor=tk.CENTER
            )
            
            # Add a smaller subtitle
            self.canvas.create_text(
                text_x, text_y + 40,
                text="Skipping to next photo in 3 seconds...",
                font=('Arial', 16),
                fill='gray',
                anchor=tk.CENTER
            )
            
            self.root.update()
            
        except Exception as e:
            self.logger.error(f"Error displaying error message: {e}")

    def _add_overlays(self, photo_data: Dict[str, Any], location_string: Optional[str], 
                     x: int, y: int, width: int, height: int) -> None:
        """Add date and location overlays to the displayed image."""
        try:
            overlay_texts = []
            
            # Format date if available
            if photo_data.get('date_taken'):
                date_str = photo_data['date_taken'].strftime('%B %d, %Y')
                overlay_texts.append(date_str)
            
            # Add location if available
            if location_string:
                overlay_texts.append(location_string)
            
            if not overlay_texts:
                return
            
            # Combine texts
            overlay_text = ' • '.join(overlay_texts)
            
            # Calculate overlay position based on config
            placement = self.config.get('OVERLAY_PLACEMENT', 'TOP')
            alignment = self.config.get('OVERLAY_ALIGNMENT', 'CENTER')
            
            # Font size from requirements (36px) - will be adjusted if text is too wide
            font_size = 36
            
            # Calculate optimal font size to fit within image width
            font_size = self._calculate_optimal_font_size(overlay_text, font_size, width)
            
            # Get text dimensions
            temp_text = self.canvas.create_text(0, 0, text=overlay_text, font=('Arial', font_size))
            bbox = self.canvas.bbox(temp_text)
            self.canvas.delete(temp_text)
            
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Create background sized exactly to text dimensions
            padding = 8
            
            # Calculate background dimensions first
            bg_width = text_width + 2 * padding
            bg_height = text_height + 2 * padding
            
            # Determine background position based on overlay type and alignment
            if placement == 'TOP':
                bg_y = y + 20
            else:  # BOTTOM
                bg_y = y + height - bg_height - 20
            
            if alignment == 'LEFT':
                bg_x = x + 20
            elif alignment == 'RIGHT':
                bg_x = x + width - bg_width - 20
            else:  # CENTER
                bg_x = x + (width - bg_width) // 2
            
            # Draw solid white background
            self.canvas.create_rectangle(
                bg_x, bg_y, bg_x + bg_width, bg_y + bg_height,
                fill='white', outline='', width=0
            )
            
            # Position text at the center of the background
            text_x = bg_x + bg_width // 2
            text_y = bg_y + bg_height // 2
            
            # Draw text centered on the background
            self.canvas.create_text(
                text_x, text_y,
                text=overlay_text,
                font=('Arial', font_size),
                fill='black',
                anchor=tk.CENTER
            )
            
        except Exception as e:
            self.logger.error(f"Error adding overlays: {e}")
    
    def _calculate_optimal_font_size(self, text: str, initial_font_size: int, max_width: int) -> int:
        """Calculate optimal font size to fit text within given width."""
        try:
            # Reserve some padding (40px total - 20px on each side)
            available_width = max_width - 40
            
            font_size = initial_font_size
            min_font_size = 12  # Don't go below 12px
            
            while font_size >= min_font_size:
                # Test current font size
                temp_text = self.canvas.create_text(0, 0, text=text, font=('Arial', font_size))
                bbox = self.canvas.bbox(temp_text)
                self.canvas.delete(temp_text)
                
                if bbox:
                    text_width = bbox[2] - bbox[0]
                    if text_width <= available_width:
                        return font_size
                
                # Reduce font size and try again
                font_size -= 2
            
            return min_font_size
            
        except Exception as e:
            self.logger.debug(f"Error calculating optimal font size: {e}")
            return initial_font_size
    
    def show_filename_overlay(self, filename: str) -> None:
        """Show filename overlay (activated by Shift key)."""
        try:
            # Always position filename at top-center as per requirements
            font_size = 24
            
            # Calculate position
            text_x = self.screen_width // 2
            text_y = 20
            
            # Create temporary overlay
            overlay_id = self.canvas.create_text(
                text_x, text_y,
                text=filename,
                font=('Arial', font_size),
                fill='yellow',
                anchor=tk.N
            )
            
            # Safe deletion of filename overlay
            def safe_delete_filename_overlay():
                try:
                    if overlay_id in self.canvas.find_all():
                        self.canvas.delete(overlay_id)
                except Exception as e:
                    self.logger.debug(f"Error deleting filename overlay: {e}")
            
            # Remove after 3 seconds using safe deletion
            self.root.after(3000, safe_delete_filename_overlay)
            
        except Exception as e:
            self.logger.error(f"Error showing filename overlay: {e}")
    
    def show_voice_command_overlay(self, command: str) -> None:
        """Show voice command overlay for 1.5 seconds."""
        try:
            # Position voice command at bottom-center
            font_size = 32
            text_x = self.screen_width // 2
            text_y = self.screen_height - 50
            
            # Create voice command overlay with distinctive styling
            overlay_id = self.canvas.create_text(
                text_x, text_y,
                text=f" {command.upper()}",
                font=('Arial', font_size, 'bold'),
                fill='lime',
                anchor=tk.S
            )
            
            # Safe deletion of voice overlay
            def safe_delete_voice_overlay():
                try:
                    if overlay_id in self.canvas.find_all():
                        self.canvas.delete(overlay_id)
                except Exception as e:
                    self.logger.debug(f"Error deleting voice overlay: {e}")
            
            # Remove after 1.5 seconds using safe deletion
            self.root.after(1500, safe_delete_voice_overlay)
            
        except Exception as e:
            self.logger.error(f"Error showing voice command overlay: {e}")
    
    def show_stopped_overlay(self) -> None:
        """Show persistent STOPPED overlay at bottom of screen."""
        try:
            # Clear any existing stopped overlay
            self.clear_stopped_overlay()
            
            # Position STOPPED overlay lower on screen to avoid conflicts
            font_size = 28
            text_x = self.screen_width // 2
            text_y = self.screen_height - 20
            
            # Create persistent STOPPED overlay
            self.stopped_overlay_id = self.canvas.create_text(
                text_x, text_y,
                text=" STOPPED",
                font=('Arial', font_size, 'bold'),
                fill='red',
                anchor=tk.S
            )
            
        except Exception as e:
            self.logger.error(f"Error showing stopped overlay: {e}")
    
    def clear_stopped_overlay(self) -> None:
        """Clear the persistent STOPPED overlay."""
        try:
            if hasattr(self, 'stopped_overlay_id') and self.stopped_overlay_id:
                self.canvas.delete(self.stopped_overlay_id)
                self.stopped_overlay_id = None
        except Exception as e:
            self.logger.error(f"Error clearing stopped overlay: {e}")
    
    def _clear_canvas_preserve_overlays(self) -> None:
        """Clear canvas but preserve persistent overlays using tags."""
        try:
            # Clear only image-related items, not persistent overlays
            if hasattr(self, 'current_image_id') and self.current_image_id:
                self.canvas.delete(self.current_image_id)
                self.current_image_id = None
            
            # Clear all items except tagged persistent overlays
            all_items = self.canvas.find_all()
            for item in all_items:
                # Get tags for this item
                tags = self.canvas.gettags(item)
                # Keep items with persistent tags
                if any(tag in ['countdown', 'stopped_overlay'] for tag in tags):
                    continue
                self.canvas.delete(item)
                
        except Exception as e:
            self.logger.error(f"Error clearing canvas: {e}")
            # Fallback - clear everything except tagged items
            try:
                self.canvas.delete("all")
                # Don't delete tagged persistent overlays
                for tag in ['countdown', 'stopped_overlay']:
                    # These will be preserved automatically by tag-based approach
                    pass
                self.current_image_id = None
            except:
                self.canvas.delete("all")
                self.current_image_id = None
    
    def show_countdown(self, remaining_seconds: int) -> None:
        """Show countdown timer display in top-right corner."""
        try:
            if not self.config.get('show_countdown_timer', False):
                return
                
            if not self.canvas or not self.canvas.winfo_exists():
                return
            
            # Clear previous countdown
            self.canvas.delete("countdown")
            
            # Don't show countdown if paused or stopped
            if remaining_seconds <= 0:
                return
            
            # Show countdown in top-right corner
            countdown_text = f"{remaining_seconds}s"
            self.canvas.create_text(
                self.screen_width - 50, 50,
                text=countdown_text,
                font=('Arial', 24, 'bold'),
                fill='white',
                tags="countdown"
            )
        except Exception as e:
            self.logger.error(f"Error showing countdown: {e}")
    
    def clear_countdown_timer(self) -> None:
        """Clear countdown timer display."""
        try:
            if self.canvas and self.canvas.winfo_exists():
                self.canvas.delete("countdown")
        except Exception as e:
            self.logger.error(f"Error clearing countdown timer: {e}")
    
    def _refresh_stopped_overlay(self) -> None:
        """Show STOPPED overlay if slideshow is paused - called after image display."""
        try:
            # Check if we should show stopped overlay by checking controller state
            # This is called after image display to ensure overlay is on top
            if hasattr(self, 'controller_ref') and self.controller_ref:
                if hasattr(self.controller_ref, 'is_paused') and self.controller_ref.is_paused:
                    self.show_stopped_overlay()
        except Exception as e:
            self.logger.error(f"Error refreshing stopped overlay: {e}")
    
    def set_controller_reference(self, controller) -> None:
        """Set reference to controller for state checking."""
        self.controller_ref = controller
    
    def bind_key_events(self, callback) -> None:
        """Bind keyboard events to callback function."""
        self.root.bind('<Key>', callback)
        self.root.focus_set()
    
    def bind_mouse_events(self, callback) -> None:
        """Bind mouse events to callback function."""
        self.root.bind('<Button-1>', lambda e: callback('single_click'))
        self.root.bind('<Double-Button-1>', lambda e: callback('double_click'))
    
    def update(self) -> None:
        """Update the display."""
        if self.root:
            self.root.update()
    
    def start_event_loop(self, key_callback) -> None:
        """Start the tkinter event loop with key bindings."""
        self.root.bind('<Key>', key_callback)
        self.root.focus_set()
        self.root.mainloop()
    
    def _initialize_video_support(self) -> None:
        """Initialize video processing support if available."""
        try:
            if OPENCV_AVAILABLE and self.config.get('video_playback_enabled', False):
                self.video_manager = VideoManager(self.logger)
                self.logger.info("Video playback support enabled")
            else:
                self.logger.info("Video playback disabled in configuration or OpenCV unavailable")
        except Exception as e:
            self.logger.warning(f"Failed to initialize video support: {e}")
            self.video_manager = None
    
    def is_video_supported(self) -> bool:
        """Check if video playback is supported and enabled."""
        return self.video_manager is not None
    
    def is_video_playing(self) -> bool:
        """Check if video is currently playing."""
        return self.video_playing
    
    def display_video(self, video_path: str, overlays: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Display video content with overlays."""
        if not self.is_video_supported():
            self.logger.warning("Video playback not supported")
            return False
            
        try:
            # Stop any currently playing video
            self.stop_video()
            
            # Validate video file
            if not self.video_manager.validate_video_file(video_path):
                self.logger.error(f"Invalid video file: {video_path}")
                return False
            
            # Get video metadata
            metadata = self.video_manager.get_video_metadata(video_path)
            if not metadata or not metadata.get('is_valid', False):
                self.logger.error(f"Cannot read video metadata: {video_path}")
                return False
            
            # Check duration limits
            max_duration = self.config.get('video_max_duration', 15)
            if metadata.get('duration', 0) > max_duration:
                self.logger.info(f"Video duration {metadata.get('duration')}s will be limited to {max_duration}s")
            
            # Clear existing display
            self._clear_display()
            
            # Add overlays if provided
            if overlays:
                # Get screen dimensions for overlay positioning
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                location_string = overlays.get('location_string') if isinstance(overlays, dict) else None
                video_data = overlays if isinstance(overlays, dict) else {}
                self._add_video_overlays(video_data, location_string, 0, 0, screen_width, screen_height)
            
            # Start audio playback if enabled
            if self.config.get('video_audio_enabled', True):
                self._start_video_audio(video_path, metadata)
            
            # Use new ffplay-based video playback
            return self._start_full_video_playback(video_path, metadata)
            
        except Exception as e:
            self.logger.error(f"Failed to start video playback: {e}")
            return False
    
    def _start_full_video_playback(self, video_path: str, metadata: Dict[str, Any]) -> bool:
        """Start full video playback using ffplay for smooth native rendering."""
        import subprocess
        import time
        try:
            # Stop any existing video first
            self.stop_video()
            
            video_duration = metadata.get('duration', 0)
            max_duration = self.config.get('video_max_duration', 15)
            actual_duration = min(video_duration, max_duration)
            
            self.logger.info(f"Playing video with ffplay: {video_path} ({video_duration:.1f}s, limited to {actual_duration:.1f}s)")
            
            # Clear canvas completely for video display
            self._clear_display()
            
            # Reset video state
            self.video_stop_event.clear()
            
            # Get window position for video player
            self.root.update_idletasks()  # Ensure window geometry is current
            window_x = self.root.winfo_rootx()
            window_y = self.root.winfo_rooty()
            
            # Start ffplay video playback
            def play_video():
                try:
                    self.video_playing = True
                    
                    # Hide Tkinter window during video playback to prevent blocking
                    self.root.withdraw()
                    
                    # ffplay command for fullscreen video
                    ffplay_cmd = [
                        'ffplay',
                        '-i', video_path,
                        '-fs',  # Use fullscreen mode
                        '-autoexit',
                        '-loglevel', 'quiet'
                    ]
                    
                    # Start ffplay process
                    self.video_process = subprocess.Popen(
                        ffplay_cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    
                    # Monitor playback duration
                    start_time = time.time()
                    while self.video_playing and not self.video_stop_event.is_set():
                        # Check if process ended naturally
                        if self.video_process.poll() is not None:
                            self.logger.info("Video playback completed naturally")
                            break
                        
                        # Check duration limit
                        elapsed = time.time() - start_time
                        if elapsed >= actual_duration:
                            self.logger.info(f"Video duration limit reached ({actual_duration:.1f}s)")
                            # Terminate ffplay
                            self.video_process.terminate()
                            try:
                                self.video_process.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                self.video_process.kill()
                            break
                        
                        time.sleep(0.1)  # Check every 100ms
                    
                    # Signal completion
                    self.root.after(0, self._on_video_complete)
                    
                except Exception as e:
                    self.logger.error(f"ffplay video playback error: {e}")
                    self.root.after(0, self._on_video_complete)
                finally:
                    self.video_playing = False
                    # Restore Tkinter window after video
                    self.root.after(0, lambda: self.root.deiconify())
                    # Ensure process is cleaned up
                    if hasattr(self, 'video_process') and self.video_process:
                        try:
                            if self.video_process.poll() is None:
                                self.video_process.terminate()
                                self.video_process.wait(timeout=2)
                        except:
                            pass
                        self.video_process = None
            
            # Start video playback in separate thread
            self.video_thread = threading.Thread(target=play_video, daemon=True)
            self.video_thread.start()
            
            # Don't add overlays here - they should be added by the caller
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting ffplay video playback: {e}")
            return False
    
    # Old OpenCV video playback method removed - now using ffplay
    
    # _resize_video_frame method removed - ffplay handles video scaling
    
    # OpenCV video playback method removed - using ffplay instead
    
    # _update_video_frame method removed - ffplay handles video rendering
    
    def stop_video(self) -> None:
        """Stop video playback if currently playing."""
        try:
            self.logger.info("Stopping video playback...")
            
            # Signal stop to video thread
            self.video_stop_event.set()
            self.video_playing = False
            
            # Stop ffplay process if running
            if hasattr(self, 'video_process') and self.video_process:
                import subprocess
                try:
                    if self.video_process.poll() is None:
                        self.video_process.terminate()
                        self.video_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:
                        self.video_process.kill()
                        self.video_process.wait(timeout=1)
                    except:
                        pass
                except Exception as e:
                    self.logger.debug(f"Error terminating video process: {e}")
                finally:
                    self.video_process = None
            
            # Stop audio playback
            self._stop_audio_playback()
            
            # Clear all video-related UI elements
            self._clear_video_overlays()
            self.clear_countdown_timer()
            
            # Clear any scheduled callbacks
            try:
                if hasattr(self, 'canvas') and self.canvas:
                    self.canvas.delete("video_countdown")
                    self.canvas.delete("loading")
            except:
                pass
            
            self.logger.info("Video playback stopped successfully")
                
        except Exception as e:
            self.logger.error(f"Error stopping video: {e}")
            # Force cleanup even if there are errors
            self.video_playing = False
            self.video_stop_event.set()
    
    # resume_video method removed - ffplay doesn't support pause/resume
    
    def _clear_display(self) -> None:
        """Clear the display canvas and overlays."""
        try:
            if self.canvas:
                self.canvas.delete("all")
            self.clear_overlays()
            self.current_image_id = None
            self.video_overlay_id = None
        except Exception as e:
            self.logger.error(f"Error clearing display: {e}")
    
    def _add_video_overlays(self, video_data: Dict[str, Any], location_string: Optional[str], 
                           x: int, y: int, width: int, height: int) -> None:
        """Add overlays for video content using same positioning as photos."""
        try:
            overlay_texts = []
            
            # Format date if available
            if video_data.get('date_taken'):
                date_str = video_data['date_taken'].strftime('%B %d, %Y')
                overlay_texts.append(date_str)
            
            # Add location if available
            if location_string:
                overlay_texts.append(location_string)
            
            # Add video duration
            if video_data.get('duration'):
                duration = video_data['duration']
                duration_str = f"{duration:.1f}s"
                overlay_texts.append(duration_str)
            
            if not overlay_texts:
                return
            
            # Combine overlay texts
            overlay_text = " • ".join(overlay_texts)
            
            # Position overlay at bottom center of screen for video
            overlay_x = self.screen_width // 2
            overlay_y = self.screen_height - 50
            
            # Create text overlay with background (store ID for later removal)
            self.video_overlay_id = self.canvas.create_text(
                overlay_x, overlay_y,
                text=overlay_text,
                font=('Arial', 18, 'bold'),
                fill='white',
                anchor=tk.S,
                tags="video_overlay"
            )
            
            self.logger.info(f"Added video overlay: {overlay_text}")
            
        except Exception as e:
            self.logger.error(f"Error adding video overlays: {e}")
    
    def _ensure_video_overlays_on_top(self) -> None:
        """Ensure video overlays remain visible on top of video frames."""
        try:
            # Move all video overlay elements to the top
            for tag in ["video_overlay", "video_countdown"]:
                items = self.canvas.find_withtag(tag)
                for item in items:
                    self.canvas.tag_raise(item)
        except Exception as e:
            self.logger.debug(f"Error ensuring overlays on top: {e}")

    def _on_video_complete(self) -> None:
        """Called when video playback completes naturally."""
        try:
            self.logger.info("Video playback completed")
            # Clear video countdown timer and overlays
            self.canvas.delete("video_countdown")
            self.canvas.delete("video_overlay")
            self.video_playing = False
            # Remove video overlays
            self._clear_video_overlays()
            # Notify slideshow controller that video is done
            if hasattr(self, 'video_complete_callback') and self.video_complete_callback:
                self.video_complete_callback()
        except Exception as e:
            self.logger.error(f"Error handling video completion: {e}")
    
    def set_video_complete_callback(self, callback):
        """Set callback to be called when video playback completes."""
        self.video_complete_callback = callback
    
    def _start_video_audio(self, video_path: str, metadata: Dict[str, Any]) -> None:
        """Start audio playback for video using system commands."""
        try:
            import subprocess
            import threading
            
            # Get duration limit
            max_duration = self.config.get('video_max_duration', 15)
            video_duration = metadata.get('duration', 0)
            actual_duration = min(video_duration, max_duration)
            
            # Use afplay on macOS to play audio
            def play_audio():
                try:
                    # Start afplay process
                    cmd = ['afplay', video_path]
                    self.audio_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Wait for the duration limit or until stopped
                    try:
                        self.audio_process.wait(timeout=actual_duration)
                    except subprocess.TimeoutExpired:
                        # Duration limit reached, terminate audio
                        self.audio_process.terminate()
                        try:
                            self.audio_process.wait(timeout=1)
                        except subprocess.TimeoutExpired:
                            self.audio_process.kill()
                    
                except Exception as e:
                    self.logger.error(f"Audio playback error: {e}")
                finally:
                    self.audio_process = None
            
            # Start audio in separate thread
            self.audio_thread = threading.Thread(target=play_audio, daemon=True)
            self.audio_thread.start()
            
            self.logger.info(f"Started audio playback for {actual_duration:.1f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to start audio playback: {e}")
    
    def _stop_audio_playback(self) -> None:
        """Stop audio playback if currently running."""
        try:
            if hasattr(self, 'audio_process') and self.audio_process:
                import subprocess
                try:
                    if self.audio_process.poll() is None:
                        self.audio_process.terminate()
                        self.audio_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    try:
                        self.audio_process.kill()
                        self.audio_process.wait(timeout=1)
                    except:
                        pass
                except Exception as e:
                    self.logger.debug(f"Error stopping audio process: {e}")
                finally:
                    self.audio_process = None
            
            # Wait for audio thread to complete
            if hasattr(self, 'audio_thread') and self.audio_thread and self.audio_thread.is_alive():
                try:
                    self.audio_thread.join(timeout=1)
                except:
                    pass
                self.audio_thread = None
                
        except Exception as e:
            self.logger.error(f"Error stopping audio playback: {e}")
    
    def _clear_video_overlays(self) -> None:
        """Clear video-specific overlays."""
        try:
            # Clear by tag to ensure all video overlays are removed
            self.canvas.delete("video_overlay")
            if self.video_overlay_id and self.canvas:
                self.canvas.delete(self.video_overlay_id)
                self.video_overlay_id = None
        except Exception as e:
            self.logger.error(f"Error clearing video overlays: {e}")

    def display_video_with_overlays(self, video_path: str, video_data: Dict[str, Any], location_string: Optional[str]) -> bool:
        """Display video with overlays using full video playback."""
        try:
            # Get metadata for video
            if not self.is_video_supported():
                self.logger.warning("Video playback not supported")
                return False
            
            metadata = self.video_manager.get_video_metadata(video_path)
            if not metadata or not metadata.get('is_valid', False):
                self.logger.error(f"Cannot read video metadata: {video_path}")
                return False
            
            # Start full video playback
            success = self._start_full_video_playback(video_path, metadata)
            
            # Add overlays after video starts to prevent clearing
            if success:
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                # Delay overlay creation to ensure video is displaying
                self.root.after(100, lambda: self._add_video_overlays(video_data, location_string, 0, 0, screen_width, screen_height))
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error displaying video with overlays: {e}")
            return False


    def show_loading_message(self, message: str) -> None:
        """Show a loading message overlay."""
        try:
            self.canvas.delete("loading")
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            self.canvas.create_text(
                screen_width // 2, screen_height // 2,
                text=message,
                font=('Arial', 24, 'bold'),
                fill='white',
                tags="loading"
            )
            self.root.update()
        except Exception as e:
            self.logger.error(f"Error showing loading message: {e}")

    
    def _show_video_thumbnail(self, video_path: str) -> None:
        """Show video thumbnail/first frame."""
        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # Simple black screen placeholder - ffplay will handle actual video display
                    self._clear_display()
                cap.release()
        except Exception as e:
            self.logger.debug(f"Could not show video thumbnail: {e}")
    
    # Video countdown methods removed - videos don't use countdown timers

    # Duplicate show_countdown method removed - consolidated above

    def destroy(self) -> None:
        """Clean up display manager resources."""
        self.stop_video()
        if hasattr(self, 'root') and self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except Exception as e:
                print(f"Error destroying display manager: {e}")

    def clear_overlays(self) -> None:
        """Clear all overlay elements."""
        try:
            self.clear_stopped_overlay()
            self.clear_countdown_timer()
            
            # Clear any remaining overlay labels
            for label in self.overlay_labels:
                try:
                    label.destroy()
                except:
                    pass
            self.overlay_labels.clear()
            
        except Exception as e:
            self.logger.error(f"Error clearing overlays: {e}")
