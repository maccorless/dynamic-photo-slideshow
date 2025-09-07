"""
Display management for Dynamic Photo Slideshow.
Handles fullscreen display, image rendering, and overlay positioning.
"""

import tkinter as tk
import logging
import os
from typing import Dict, Any, Optional, List

from PIL import Image, ImageTk, ImageDraw, ImageFont

# Enable HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

class DisplayManager:
    """Manages fullscreen display and image rendering."""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.root = None
        self.screen_width = 0
        self.screen_height = 0
        self.canvas = None
        self.current_image_id = None
        self.overlay_labels = []
        self.countdown_overlay_id = None
        self.stopped_overlay_id = None
        self.controller_ref = None
        
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

    def display_photo(self, photo_data, location_string: Optional[str] = None) -> None:
        """Display a photo or a pair of photos."""
        try:
            if isinstance(photo_data, list) and len(photo_data) == 2:
                self._display_paired_photos(photo_data, location_string)
            else:
                self._display_single_photo(photo_data, location_string)
        except Exception as e:
            self.logger.error(f"Error in display_photo: {e}")

    def _display_single_photo(self, photo_data: Dict[str, Any], location_string: Optional[str]) -> None:
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

    def _display_paired_photos(self, photo_pair: List[Dict[str, Any]], location_string: Optional[str]) -> None:
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
            
            # Safe deletion that won't affect countdown timer
            def safe_delete_filename_overlay():
                try:
                    # Only delete if the overlay still exists and isn't the countdown timer
                    if (overlay_id in self.canvas.find_all() and 
                        overlay_id != getattr(self, 'countdown_overlay_id', None) and
                        overlay_id != getattr(self, 'stopped_overlay_id', None)):
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
                text=f"🎤 {command.upper()}",
                font=('Arial', font_size, 'bold'),
                fill='lime',
                anchor=tk.S
            )
            
            # Safe deletion that won't affect countdown timer
            def safe_delete_voice_overlay():
                try:
                    # Only delete if the overlay still exists and isn't the countdown timer
                    if (overlay_id in self.canvas.find_all() and 
                        overlay_id != getattr(self, 'countdown_overlay_id', None) and
                        overlay_id != getattr(self, 'stopped_overlay_id', None)):
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
                text="⏹️ STOPPED",
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
        """Clear canvas but preserve countdown timer by using tags."""
        try:
            # Clear only image-related items, not persistent overlays
            if hasattr(self, 'current_image_id') and self.current_image_id:
                self.canvas.delete(self.current_image_id)
                self.current_image_id = None
            
            # Clear all items except countdown timer and stopped overlay
            all_items = self.canvas.find_all()
            for item in all_items:
                # Keep countdown timer and stopped overlay
                if (hasattr(self, 'countdown_overlay_id') and item == self.countdown_overlay_id):
                    continue
                if (hasattr(self, 'stopped_overlay_id') and item == self.stopped_overlay_id):
                    continue
                # Delete everything else (images, overlays, backgrounds)
                self.canvas.delete(item)
            
            # Reset only the image ID, keep overlay IDs intact
            self.current_image_id = None
                
        except Exception as e:
            self.logger.error(f"Error clearing canvas: {e}")
            # Fallback to clearing everything except countdown
            try:
                countdown_id = getattr(self, 'countdown_overlay_id', None)
                stopped_id = getattr(self, 'stopped_overlay_id', None)
                self.canvas.delete("all")
                self.current_image_id = None
                # Reset overlay IDs if they were cleared
                if countdown_id and countdown_id not in self.canvas.find_all():
                    self.countdown_overlay_id = None
                if stopped_id and stopped_id not in self.canvas.find_all():
                    self.stopped_overlay_id = None
            except:
                self.canvas.delete("all")
                self.current_image_id = None
                self.countdown_overlay_id = None
                self.stopped_overlay_id = None
    
    def update_countdown_timer(self, seconds_remaining: int) -> None:
        """Update countdown timer display in lower right corner."""
        try:
            # Check if countdown timer is enabled
            if not self.config.get('show_countdown_timer', False):
                return
            
            # Clear existing countdown overlay
            if hasattr(self, 'countdown_overlay_id') and self.countdown_overlay_id:
                self.canvas.delete(self.countdown_overlay_id)
                self.countdown_overlay_id = None
            
            # Don't show countdown if paused or stopped
            if seconds_remaining <= 0:
                return
            
            # Position countdown in lower right corner
            font_size = 18
            text_x = self.screen_width - 20
            text_y = self.screen_height - 20
            
            # Create countdown overlay
            self.countdown_overlay_id = self.canvas.create_text(
                text_x, text_y,
                text=f"{seconds_remaining}s",
                font=('Arial', font_size),
                fill='white',
                anchor=tk.SE
            )
            
        except Exception as e:
            self.logger.error(f"Error updating countdown timer: {e}")
    
    def clear_countdown_timer(self) -> None:
        """Clear the countdown timer display."""
        try:
            if hasattr(self, 'countdown_overlay_id') and self.countdown_overlay_id:
                self.canvas.delete(self.countdown_overlay_id)
                self.countdown_overlay_id = None
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
        try:
            self.bind_key_events(key_callback)
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error in event loop: {e}")
            raise
    
    def clear_overlays(self) -> None:
        """Clear all overlay elements."""
        try:
            self.clear_stopped_overlay()
            self.clear_countdown_timer()
        except Exception as e:
            self.logger.error(f"Error clearing overlays: {e}")
    
    def destroy(self) -> None:
        """Clean up display resources."""
        if self.root:
            self.root.destroy()
