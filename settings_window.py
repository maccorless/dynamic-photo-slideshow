"""
Settings Window - pygame_gui based settings interface
"""

import pygame
import pygame_gui
import logging
from typing import Optional, Callable, Dict, Any
from settings_manager import SettingsManager


class SettingsWindow:
    """Settings window overlay for slideshow configuration."""
    
    def __init__(self, screen: pygame.Surface, settings_manager: SettingsManager, controller=None):
        """
        Initialize settings window.
        
        Args:
            screen: Pygame display surface
            settings_manager: SettingsManager instance
            controller: Optional slideshow controller for live updates
        """
        self.logger = logging.getLogger(__name__)
        self.screen = screen
        self.settings_manager = settings_manager
        self.controller = controller
        
        # Get screen dimensions
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # Calculate window size (80% of screen)
        self.window_width = int(self.screen_width * 0.8)
        self.window_height = int(self.screen_height * 0.8)
        
        # Calculate window position (centered)
        self.window_x = (self.screen_width - self.window_width) // 2
        self.window_y = (self.screen_height - self.window_height) // 2
        
        # Window state
        self.is_visible = False
        self.manager: Optional[pygame_gui.UIManager] = None
        self.window: Optional[pygame_gui.elements.UIWindow] = None
        
        # Background overlay surface (semi-transparent)
        self.overlay = pygame.Surface((self.screen_width, self.screen_height))
        self.overlay.set_alpha(128)  # 50% transparency
        self.overlay.fill((0, 0, 0))  # Black
        
        # Callback for when window closes
        self.on_close_callback: Optional[Callable] = None
        
        # UI elements (will be created in show())
        self.tab_container: Optional[pygame_gui.elements.UITabContainer] = None
        self.ok_button: Optional[pygame_gui.elements.UIButton] = None
        self.setting_widgets: Dict[str, Any] = {}  # Track all setting widgets
        
        self.logger.info(f"Settings window initialized: {self.window_width}x{self.window_height}")
    
    def show(self) -> None:
        """Show the settings window."""
        if self.is_visible:
            self.logger.warning("Settings window already visible")
            return
        
        self.logger.info("Showing settings window")
        
        # Create UI manager with custom theme
        import os
        theme_path = os.path.join(os.path.dirname(__file__), "settings_theme.json")
        self.manager = pygame_gui.UIManager(
            (self.screen_width, self.screen_height),
            theme_path=theme_path
        )
        
        # Create main window
        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(self.window_x, self.window_y, 
                           self.window_width, self.window_height),
            manager=self.manager,
            window_display_title="Slideshow Settings",
            object_id="#settings_window",
            resizable=False
        )
        
        # Calculate content area (leave space for OK button at bottom)
        button_height = 40
        button_margin = 20
        content_height = self.window_height - button_height - button_margin - 40
        
        # Create tab container
        tab_rect = pygame.Rect(10, 10, self.window_width - 20, content_height)
        self.tab_container = pygame_gui.elements.UITabContainer(
            relative_rect=tab_rect,
            manager=self.manager,
            container=self.window,
            object_id="#tab_container"
        )
        
        # Create tabs
        self._create_display_tab()
        # TODO: Add other tabs in future milestones
        
        # Add OK button at bottom
        button_width = 100
        button_x = (self.window_width - button_width) // 2
        button_y = self.window_height - button_height - button_margin
        
        self.ok_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(button_x, button_y, button_width, button_height),
            text='OK',
            manager=self.manager,
            container=self.window,
            object_id="#ok_button"
        )
        
        self.is_visible = True
        self.logger.info("Settings window shown")
    
    def _create_display_tab(self) -> None:
        """Create the Display settings tab."""
        # Get schema for display settings
        schema = self.settings_manager.get_schema()
        display_schema = schema["schema"]["display"]
        
        # Create tab and get the container panel
        self.tab_container.add_tab("Display", "display_tab")
        display_tab = self.tab_container.tabs[0]['container']
        
        # Layout parameters
        y_offset = 20
        label_width = 200
        control_width = 300
        row_height = 50
        info_icon_size = 20
        spacing = 10
        
        # Create settings for each item in display group
        for setting_name, setting_data in display_schema["settings"].items():
            # Create label
            label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(20, y_offset, label_width, 30),
                text=setting_data["label"] + ":",
                manager=self.manager,
                container=display_tab
            )
            
            # Create control based on type
            control_x = 20 + label_width + spacing
            current_value = self.settings_manager.get_setting("display", setting_name)
            
            if setting_data["type"] == "integer":
                # Number input with spinner
                control = pygame_gui.elements.UITextEntryLine(
                    relative_rect=pygame.Rect(control_x, y_offset, control_width, 30),
                    manager=self.manager,
                    container=display_tab
                )
                control.set_text(str(current_value))
                # Store metadata for validation
                control.setting_group = "display"
                control.setting_name = setting_name
                control.setting_type = "integer"
                
            elif setting_data["type"] == "boolean":
                # Checkbox - show clear ON/OFF state with green checkmark
                checkbox_text = "✓ ON" if current_value else "OFF"
                checkbox_id = "#checkbox_on" if current_value else "#checkbox_off"
                control = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(control_x, y_offset, 100, 30),
                    text=checkbox_text,
                    manager=self.manager,
                    container=display_tab,
                    object_id=checkbox_id
                )
                control.setting_group = "display"
                control.setting_name = setting_name
                control.setting_type = "boolean"
                control.setting_value = current_value
                
            elif setting_data["type"] == "enum":
                # Dropdown
                control = pygame_gui.elements.UIDropDownMenu(
                    options_list=setting_data["options"],
                    starting_option=current_value,
                    relative_rect=pygame.Rect(control_x, y_offset, control_width, 30),
                    manager=self.manager,
                    container=display_tab
                )
                control.setting_group = "display"
                control.setting_name = setting_name
                control.setting_type = "enum"
            
            # Create info icon with tooltip - make it clearly different from controls
            info_x = control_x + control_width + spacing
            tooltip_text = setting_data["description"]
            if "default" in setting_data:
                tooltip_text += f"\n\nDefault: {setting_data['default']}"
            if "min" in setting_data and "max" in setting_data:
                tooltip_text += f"\nRange: {setting_data['min']}-{setting_data['max']}"
            if "unit" in setting_data:
                tooltip_text += f" {setting_data['unit']}"
            
            # Info icon - use button but make it look like an icon
            info_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(info_x, y_offset + 3, 24, 24),
                text="?",  # Question mark is clearer than ⓘ
                manager=self.manager,
                container=display_tab,
                tool_tip_text=tooltip_text,
                object_id="#info_icon"
            )
            
            # Store widget reference
            widget_key = f"display.{setting_name}"
            self.setting_widgets[widget_key] = control
            
            # Move to next row
            y_offset += row_height
        
        self.logger.info("Display tab created with all settings")
    
    def _save_pending_changes(self) -> None:
        """Save any pending changes from text entry fields before closing."""
        if not self.manager:
            return
        
        # Iterate through all UI elements and save text entry values
        for widget_key, widget in self.setting_widgets.items():
            if hasattr(widget, 'setting_type') and widget.setting_type == "integer":
                if isinstance(widget, pygame_gui.elements.UITextEntryLine):
                    # Save the current value
                    try:
                        group = widget.setting_group
                        setting = widget.setting_name
                        new_value = int(widget.get_text())
                        
                        # Get current value to check if changed
                        old_value = self.settings_manager.get_setting(group, setting)
                        if new_value != old_value:
                            self.logger.info(f"Saving pending change: {group}.{setting} = {new_value}")
                            success = self.settings_manager.set_setting(group, setting, new_value)
                            if success:
                                self._apply_live_setting(group, setting, new_value)
                    except (ValueError, AttributeError) as e:
                        self.logger.debug(f"Skipping widget {widget_key}: {e}")
    
    def hide(self) -> None:
        """Hide the settings window."""
        if not self.is_visible:
            return
        
        self.logger.info("Hiding settings window")
        
        # Save any pending text entry changes before closing
        self._save_pending_changes()
        
        # Mark as not visible first
        self.is_visible = False
        
        # Clean up UI elements
        if self.window:
            self.window.kill()
            self.window = None
        
        if self.manager:
            self.manager.clear_and_reset()
            self.manager = None
        
        # Clear the setting widgets dictionary
        self.setting_widgets.clear()
        
        # Call close callback if set (this will trigger resume)
        if self.on_close_callback:
            self.on_close_callback()
        
        self.logger.info("Settings window hidden")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events for the settings window.
        
        Args:
            event: Pygame event to handle
            
        Returns:
            True if event was handled, False otherwise
        """
        if not self.is_visible or not self.manager:
            return False
        
        # Let UI manager process the event
        handled = self.manager.process_events(event)
        
        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.logger.info("ESC pressed - closing settings window")
                self.hide()
                return True
            elif event.key == pygame.K_TAB:
                # Tab key should be handled by pygame_gui for field navigation
                # Just let it pass through to the UI manager
                pass
        
        # Handle UI button clicks
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.ok_button:
                self.logger.info("OK button clicked - closing settings window")
                self.hide()
                return True
            # Handle checkbox toggles
            elif hasattr(event.ui_element, 'setting_type') and event.ui_element.setting_type == "boolean":
                self._handle_checkbox_toggle(event.ui_element)
                return True
        
        # Handle text entry changes (for integer inputs)
        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            if hasattr(event.ui_element, 'setting_type') and event.ui_element.setting_type == "integer":
                self._handle_integer_change(event.ui_element)
                return True
        
        # Handle dropdown changes (for enum inputs)
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if hasattr(event.ui_element, 'setting_type') and event.ui_element.setting_type == "enum":
                self._handle_enum_change(event.ui_element)
                return True
        
        # Handle window close button
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.window:
                self.logger.info("Window close button clicked")
                self.hide()
                return True
        
        return handled
    
    def _handle_checkbox_toggle(self, checkbox) -> None:
        """Handle checkbox toggle for boolean settings."""
        group = checkbox.setting_group
        setting = checkbox.setting_name
        
        # Toggle value
        new_value = not checkbox.setting_value
        checkbox.setting_value = new_value
        
        # Update text and styling
        checkbox.set_text("✓ ON" if new_value else "OFF")
        # Change the object_id to apply different styling
        new_id = "#checkbox_on" if new_value else "#checkbox_off"
        checkbox.change_object_id(new_id)
        
        # Save to settings manager (auto-saves)
        success = self.settings_manager.set_setting(group, setting, new_value)
        if success:
            self.logger.info(f"Setting changed: {group}.{setting} = {new_value}")
            # Apply live if controller is available and setting doesn't require restart
            self._apply_live_setting(group, setting, new_value)
        else:
            self.logger.error(f"Failed to set {group}.{setting} = {new_value}")
    
    def _handle_integer_change(self, text_entry) -> None:
        """Handle integer input change."""
        group = text_entry.setting_group
        setting = text_entry.setting_name
        
        try:
            new_value = int(text_entry.get_text())
            
            # Validate and save
            success = self.settings_manager.set_setting(group, setting, new_value)
            if success:
                self.logger.info(f"Setting changed: {group}.{setting} = {new_value}")
                # Apply live if controller is available and setting doesn't require restart
                self._apply_live_setting(group, setting, new_value)
            else:
                # Validation failed, restore previous value
                old_value = self.settings_manager.get_setting(group, setting)
                text_entry.set_text(str(old_value))
                self.logger.warning(f"Invalid value for {group}.{setting}, restored to {old_value}")
        except ValueError:
            # Not a valid integer, restore previous value
            old_value = self.settings_manager.get_setting(group, setting)
            text_entry.set_text(str(old_value))
            self.logger.warning(f"Invalid integer for {group}.{setting}, restored to {old_value}")
    
    def _handle_enum_change(self, dropdown) -> None:
        """Handle dropdown selection change."""
        group = dropdown.setting_group
        setting = dropdown.setting_name
        new_value = dropdown.selected_option
        
        # Save to settings manager (auto-saves)
        success = self.settings_manager.set_setting(group, setting, new_value)
        if success:
            self.logger.info(f"Setting changed: {group}.{setting} = {new_value}")
            # Apply live if controller is available and setting doesn't require restart
            self._apply_live_setting(group, setting, new_value)
        else:
            self.logger.error(f"Failed to set {group}.{setting} = {new_value}")
    
    def _apply_live_setting(self, group: str, setting: str, value: Any) -> None:
        """
        Apply settings that can be changed without restart.
        
        Args:
            group: Setting group name
            setting: Setting name
            value: New value
        """
        if not self.controller:
            self.logger.debug(f"No controller available, cannot apply {group}.{setting} live")
            return
        
        # Only apply Display settings live (all Display settings support live updates)
        if group == 'display':
            try:
                if setting == 'slideshow_interval':
                    # Update controller config with correct key (uppercase for internal use)
                    self.controller.config.set('SLIDESHOW_INTERVAL', value)
                    self.logger.info(f"✅ Applied live: slideshow_interval = {value}s (takes effect on next slide)")
                elif setting == 'video_max_duration':
                    # Update controller config with correct key (uppercase for internal use)
                    self.controller.config.set('VIDEO_MAX_DURATION', value)
                    self.logger.info(f"✅ Applied live: video_max_duration = {value}s (takes effect on next video)")
                elif setting == 'show_countdown_timer':
                    self.controller.config.set('show_countdown_timer', value)
                    self.logger.info(f"✅ Applied live: show_countdown_timer = {value} (takes effect immediately)")
                elif setting == 'show_date_overlay':
                    self.controller.config.set('show_date_overlay', value)
                    self.logger.info(f"✅ Applied live: show_date_overlay = {value} (takes effect on next slide)")
                elif setting == 'show_location_overlay':
                    self.controller.config.set('show_location_overlay', value)
                    self.logger.info(f"✅ Applied live: show_location_overlay = {value} (takes effect on next slide)")
            except Exception as e:
                self.logger.error(f"Error applying live setting {group}.{setting}: {e}")
    
    def update(self, time_delta: float) -> None:
        """
        Update the settings window.
        
        Args:
            time_delta: Time since last update in seconds
        """
        if not self.is_visible or not self.manager:
            return
        
        self.manager.update(time_delta)
    
    def draw(self) -> None:
        """Draw the settings window."""
        if not self.is_visible or not self.manager:
            return
        
        # Draw semi-transparent overlay over frozen slide
        self.screen.blit(self.overlay, (0, 0))
        
        # Draw UI elements
        self.manager.draw_ui(self.screen)
    
    def set_on_close_callback(self, callback: Callable) -> None:
        """
        Set callback to be called when window closes.
        
        Args:
            callback: Function to call when window closes
        """
        self.on_close_callback = callback
    
    def is_open(self) -> bool:
        """Check if settings window is currently open."""
        return self.is_visible
