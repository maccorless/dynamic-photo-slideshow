"""
Display management for Dynamic Photo Slideshow.
Handles fullscreen display, image rendering, and overlay positioning.
"""

import tkinter as tk
from tkinter import ttk
import logging
from PIL import Image, ImageTk, ImageDraw, ImageFont
from typing import Dict, Any, Optional, Tuple, List
import os

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
        self.canvas = None
        self.screen_width = 0
        self.screen_height = 0
        self.current_image_id = None
        self.overlay_font = None
        self.stopped_overlay_id = None
        self.countdown_overlay_id = None
        
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
    
    def display_photo(self, photo_data: Dict[str, Any], location_string: Optional[str] = None) -> None:
        """Display a photo with overlays."""
        try:
            # Check if this is a paired display
            if isinstance(photo_data, list) and len(photo_data) == 2:
                self._display_paired_photos(photo_data, location_string)
            else:
                self._display_single_photo(photo_data, location_string)
                
        except Exception as e:
            self.logger.error(f"Error displaying photo: {e}")
    
    def _display_single_photo(self, photo_data: Dict[str, Any], location_string: Optional[str] = None) -> None:
        """Display a single photo with overlays."""
        try:
            # Load and process image
            image_path = photo_data['path']
            if not os.path.exists(image_path):
                self.logger.error(f"Image file not found: {image_path}")
                return
            
            # Load image
            image = Image.open(image_path)
            
            # Apply orientation correction
            image = self._apply_orientation_correction(image, photo_data.get('exif_orientation', 1))
            
            # Resize image to fit screen while maintaining aspect ratio
            display_image = self._resize_image_to_fit(image)
            
            # Convert to PhotoImage for tkinter
            photo_image = ImageTk.PhotoImage(display_image)
            
            # Clear canvas and display image (preserve overlays)
            self._clear_canvas_preserve_overlays()
            
            # Center image on canvas
            x = (self.screen_width - display_image.width) // 2
            y = (self.screen_height - display_image.height) // 2
            
            self.current_image_id = self.canvas.create_image(x, y, anchor=tk.NW, image=photo_image)
            
            # Keep reference to prevent garbage collection
            self.canvas.image = photo_image
            
            # Add overlays
            self._add_overlays(photo_data, location_string, x, y, display_image.width, display_image.height)
            
            # Update display
            self.root.update()
            
            # Show STOPPED overlay AFTER image is displayed if slideshow is paused
            self._refresh_stopped_overlay()
            
        except Exception as e:
            self.logger.error(f"Error displaying single photo: {e}")
            # Display error message instead of black screen
            self._display_error_message(f"Cannot load image: {os.path.basename(photo_data.get('path', 'Unknown'))}")
    
    def _display_paired_photos(self, photo_pair: List[Dict[str, Any]], location_string: Optional[str] = None) -> None:
        """Display two portrait photos side by side."""
        try:
            # Clear canvas (preserve overlays)
            self._clear_canvas_preserve_overlays()
            
            images = []
            photo_images = []
            
            # Load and process both images
            for photo_data in photo_pair:
                image_path = photo_data['path']
                if not os.path.exists(image_path):
                    self.logger.error(f"Image file not found: {image_path}")
                    return
                
                # Load image
                image = Image.open(image_path)
                
                # Apply orientation correction
                image = self._apply_orientation_correction(image, photo_data.get('exif_orientation', 1))
                images.append(image)
            
            # Calculate sizing for side-by-side display
            # Each image gets half the screen width minus a small gap
            gap = 20
            available_width = (self.screen_width - gap) // 2
            available_height = self.screen_height
            
            display_images = []
            for image in images:
                # Resize each image to fit in half screen
                img_width, img_height = image.size
                scale_x = available_width / img_width
                scale_y = available_height / img_height
                scale = min(scale_x, scale_y)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                display_images.append(display_image)
                
                # Convert to PhotoImage
                photo_image = ImageTk.PhotoImage(display_image)
                photo_images.append(photo_image)
            
            # Position images side by side
            left_x = (available_width - display_images[0].width) // 2
            right_x = available_width + gap + (available_width - display_images[1].width) // 2
            
            left_y = (self.screen_height - display_images[0].height) // 2
            right_y = (self.screen_height - display_images[1].height) // 2
            
            # Display both images
            self.canvas.create_image(left_x, left_y, anchor=tk.NW, image=photo_images[0])
            self.canvas.create_image(right_x, right_y, anchor=tk.NW, image=photo_images[1])
            
            # Keep references to prevent garbage collection
            self.canvas.image_left = photo_images[0]
            self.canvas.image_right = photo_images[1]
            
            # Add overlays for both photos
            self._add_overlays(photo_pair[0], location_string, left_x, left_y, 
                             display_images[0].width, display_images[0].height)
            
            # Get location for second photo if available
            location_string_2 = None
            if 'gps_coordinates' in photo_pair[1]:
                coords = photo_pair[1]['gps_coordinates']
                try:
                    # Use same location service as slideshow controller
                    from location_service import LocationService
                    location_service = LocationService(self.config)
                    location_string_2 = location_service.get_location_string(
                        coords['latitude'], coords['longitude']
                    )
                except Exception as e:
                    self.logger.debug(f"Error getting location for second photo: {e}")
                    location_string_2 = None
            
            self._add_overlays(photo_pair[1], location_string_2, right_x, right_y, 
                             display_images[1].width, display_images[1].height)
            
            # Update display
            self.root.update()
            
            # Show STOPPED overlay AFTER image is displayed if slideshow is paused
            self._refresh_stopped_overlay()
            
        except Exception as e:
            self.logger.error(f"Error displaying paired photos: {e}")
            # Display error message instead of black screen
            self._display_error_message(f"Cannot load photo pair images: {os.path.basename(photo_pair[0].get('path', 'Unknown'))}")
    
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
    
    def _display_error_message(self, message: str) -> None:
        """Display an error message instead of a black screen."""
        try:
            # Clear canvas (preserve overlays)
            self._clear_canvas_preserve_overlays()
            
            # Create a simple error display
            self.canvas.configure(bg='black')
            
            # Display error message in center of screen
            self.canvas.create_text(
                self.screen_width // 2, 
                self.screen_height // 2,
                text=message,
                fill='white',
                font=('Arial', 24),
                anchor='center'
            )
            
            # Add a smaller subtitle
            self.canvas.create_text(
                self.screen_width // 2, 
                self.screen_height // 2 + 50,
                text="Skipping to next photo in 3 seconds...",
                fill='gray',
                font=('Arial', 16),
                anchor='center'
            )
            
            self.root.update()
            
        except Exception as e:
            self.logger.error(f"Error displaying error message: {e}")

    def _add_overlays(self, photo_data: Dict[str, Any], location_string: Optional[str], 
                     x: int, y: int, image_width: int, image_height: int) -> None:
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
            font_size = self._calculate_optimal_font_size(overlay_text, font_size, image_width)
            
            try:
                font = ImageFont.truetype("Arial", font_size)
            except OSError:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Get text dimensions using canvas textsize method for accuracy
            temp_text = self.canvas.create_text(0, 0, text=overlay_text, font=('Arial', font_size))
            bbox = self.canvas.bbox(temp_text)
            self.canvas.delete(temp_text)
            
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate centered position based on alignment
            if alignment == 'LEFT':
                text_x = x + 20
            elif alignment == 'RIGHT':
                text_x = x + image_width - text_width - 20
            else:  # CENTER
                text_x = x + (image_width - text_width) // 2
            
            if placement == 'TOP':
                text_y = y + 20
            else:  # BOTTOM
                text_y = y + image_height - text_height - 20
            
            # Create background sized exactly to text dimensions
            padding = 8
            bg_x1 = text_x - padding
            bg_y1 = text_y - padding
            bg_x2 = text_x + text_width + padding
            bg_y2 = text_y + text_height + padding
            
            # Draw solid white background with proper sizing
            self.canvas.create_rectangle(
                bg_x1, bg_y1, bg_x2, bg_y2,
                fill='white', outline='', width=0
            )
            
            # Draw text centered on the background
            self.canvas.create_text(
                text_x + text_width // 2, text_y + text_height // 2,
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
            
            # Remove after 3 seconds
            self.root.after(3000, lambda: self.canvas.delete(overlay_id))
            
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
            
            # Remove after 1.5 seconds
            self.root.after(1500, lambda: self.canvas.delete(overlay_id))
            
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
        """Clear canvas completely - overlays will be recreated after image display."""
        try:
            # Clear entire canvas - no preservation needed
            self.canvas.delete("all")
            self.current_image_id = None
            self.stopped_overlay_id = None
            self.countdown_overlay_id = None
                
        except Exception as e:
            self.logger.error(f"Error clearing canvas: {e}")
            # Fallback to regular clear
            self.canvas.delete("all")
    
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
    
    def destroy(self) -> None:
        """Clean up display resources."""
        if self.root:
            self.root.destroy()
