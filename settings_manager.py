"""
Settings Manager - Handles configuration persistence and validation
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
from copy import deepcopy


class SettingsManager:
    """Manages application settings with JSON persistence and validation."""
    
    def __init__(self, schema_path: str = "config_schema.json", 
                 config_path: str = "config.json"):
        """
        Initialize settings manager.
        
        Args:
            schema_path: Path to config schema JSON file
            config_path: Path to user config JSON file
        """
        self.logger = logging.getLogger(__name__)
        self.schema_path = Path(schema_path)
        self.config_path = Path(config_path)
        
        self.logger.debug(f"SettingsManager initialized with config_path: {self.config_path.absolute()}")
        
        # Load schema
        self.schema = self._load_schema()
        
        # Load or create user config
        self.config = self._load_or_create_config()
        
        # Track changes for revert functionality
        self._original_config = deepcopy(self.config)
        
        # Change listeners
        self._change_listeners: List[callable] = []
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load configuration schema from JSON file."""
        try:
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            self.logger.debug(f"Loaded config schema from {self.schema_path}")
            return schema
        except FileNotFoundError:
            self.logger.error(f"Schema file not found: {self.schema_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in schema file: {e}")
            raise
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load user config from JSON or create from defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    flat_config = json.load(f)
                self.logger.debug(f"Loaded user config from {self.config_path}")
                
                # Convert flat format to grouped format
                grouped_config = self._flat_to_grouped(flat_config)
                
                # Validate and merge with defaults
                return self._merge_with_defaults(grouped_config)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in config file: {e}")
                self.logger.debug("Creating new config from defaults")
        
        # Create config from defaults
        config = self._create_default_config()
        self.save_config()
        return config
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create configuration dictionary from schema defaults."""
        config = {"version": self.schema["version"]}
        
        for group_name, group_data in self.schema["schema"].items():
            config[group_name] = {}
            for setting_name, setting_data in group_data["settings"].items():
                config[group_name][setting_name] = setting_data["default"]
        
        self.logger.debug("Created default configuration")
        return config
    
    def _merge_with_defaults(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge user config with defaults, filling in missing values.
        
        Args:
            user_config: User's configuration dictionary
            
        Returns:
            Merged configuration with all required settings
        """
        merged = self._create_default_config()
        
        # Override defaults with user values
        for group_name, group_data in self.schema["schema"].items():
            if group_name in user_config:
                for setting_name in group_data["settings"].keys():
                    if setting_name in user_config[group_name]:
                        value = user_config[group_name][setting_name]
                        # Validate before accepting
                        if self.validate_setting(group_name, setting_name, value):
                            merged[group_name][setting_name] = value
                        else:
                            self.logger.warning(
                                f"Invalid value for {group_name}.{setting_name}: {value}, "
                                f"using default"
                            )
        
        return merged
    
    def get_setting(self, group: str, setting: str) -> Any:
        """
        Get a setting value.
        
        Args:
            group: Setting group name (e.g., 'display', 'video')
            setting: Setting name within group
            
        Returns:
            Setting value
        """
        try:
            return self.config[group][setting]
        except KeyError:
            self.logger.error(f"Setting not found: {group}.{setting}")
            # Return default if available
            try:
                return self.schema["schema"][group]["settings"][setting]["default"]
            except KeyError:
                return None
    
    def set_setting(self, group: str, setting: str, value: Any) -> bool:
        """
        Set a setting value with validation.
        
        Args:
            group: Setting group name
            setting: Setting name within group
            value: New value to set
            
        Returns:
            True if setting was updated, False if validation failed
        """
        if not self.validate_setting(group, setting, value):
            self.logger.error(f"Validation failed for {group}.{setting} = {value}")
            return False
        
        old_value = self.config[group][setting]
        self.config[group][setting] = value
        
        self.logger.info(f"Setting changed: {group}.{setting} = {value} (was {old_value})")
        
        # Notify listeners
        self._notify_change(group, setting, value, old_value)
        
        # Auto-save
        self.save_config()
        
        return True
    
    def validate_setting(self, group: str, setting: str, value: Any) -> bool:
        """
        Validate a setting value against schema constraints.
        
        Args:
            group: Setting group name
            setting: Setting name within group
            value: Value to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            setting_schema = self.schema["schema"][group]["settings"][setting]
        except KeyError:
            self.logger.error(f"Unknown setting: {group}.{setting}")
            return False
        
        setting_type = setting_schema["type"]
        
        # Type validation
        if setting_type == "integer":
            if not isinstance(value, int):
                return False
            if "min" in setting_schema and value < setting_schema["min"]:
                return False
            if "max" in setting_schema and value > setting_schema["max"]:
                return False
        
        elif setting_type == "float":
            if not isinstance(value, (int, float)):
                return False
            if "min" in setting_schema and value < setting_schema["min"]:
                return False
            if "max" in setting_schema and value > setting_schema["max"]:
                return False
        
        elif setting_type == "boolean":
            if not isinstance(value, bool):
                return False
        
        elif setting_type == "string":
            if not isinstance(value, str):
                return False
        
        elif setting_type == "enum":
            if value not in setting_schema["options"]:
                return False
        
        return True
    
    def save_config(self) -> bool:
        """
        Save current configuration to JSON file.
        Converts grouped format to flat format for SlideshowConfig compatibility.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert grouped format to flat format for SlideshowConfig
            flat_config = self._grouped_to_flat(self.config)
            
            with open(self.config_path, 'w') as f:
                json.dump(flat_config, f, indent=2)
            self.logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
    
    def reload_config(self) -> bool:
        """
        Reload configuration from JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config = self._load_or_create_config()
            self._original_config = deepcopy(self.config)
            self.logger.info("Reloaded configuration")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload config: {e}")
            return False
    
    def revert_changes(self) -> None:
        """Revert all changes since last save/load."""
        self.config = deepcopy(self._original_config)
        self.logger.info("Reverted configuration changes")
    
    def reset_to_defaults(self, group: Optional[str] = None) -> None:
        """
        Reset settings to defaults.
        
        Args:
            group: If specified, only reset this group. Otherwise reset all.
        """
        if group:
            # Reset specific group
            for setting_name, setting_data in self.schema["schema"][group]["settings"].items():
                self.config[group][setting_name] = setting_data["default"]
            self.logger.info(f"Reset {group} settings to defaults")
        else:
            # Reset all
            self.config = self._create_default_config()
            self.logger.info("Reset all settings to defaults")
        
        self.save_config()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get complete configuration dictionary."""
        return deepcopy(self.config)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return self.schema
    
    def add_change_listener(self, listener: callable) -> None:
        """Add a listener to be notified of configuration changes."""
        self._change_listeners.append(listener)
    
    def _flat_to_grouped(self, flat_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert flat config format to grouped format.
        Maps SlideshowConfig keys (some uppercase) to schema keys (lowercase).
        
        Flat format (SlideshowConfig):
        {
            "SLIDESHOW_INTERVAL": 10,
            "VIDEO_MAX_DURATION": 15,
            ...
        }
        
        Grouped format (SettingsManager):
        {
            "version": "1.0",
            "display": {
                "slideshow_interval": 10,
                "video_max_duration": 15
            },
            ...
        }
        """
        grouped = {"version": self.schema["version"]}
        
        # Create mapping of setting_name -> group_name from schema
        setting_to_group = {}
        for group_name, group_data in self.schema["schema"].items():
            for setting_name in group_data["settings"].keys():
                setting_to_group[setting_name] = group_name
        
        # Initialize all groups
        for group_name in self.schema["schema"].keys():
            grouped[group_name] = {}
        
        # Distribute flat settings into groups
        for key, value in flat_config.items():
            if key == "version":
                continue
            
            # Find which group this setting belongs to
            group_name = setting_to_group.get(key)
            if group_name:
                grouped[group_name][key] = value
            else:
                # Unknown setting, skip it (it's not in our schema)
                self.logger.debug(f"Skipping unknown setting: {key}")
        
        return grouped
    
    def _grouped_to_flat(self, grouped_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert grouped config format to flat format.
        
        Grouped format (SettingsManager):
        {
            "version": "1.0",
            "display": {
                "slideshow_interval": 10,
                "video_max_duration": 15
            },
            ...
        }
        
        Flat format (SlideshowConfig):
        {
            "SLIDESHOW_INTERVAL": 10,
            "VIDEO_MAX_DURATION": 15,
            ...
        }
        """
        flat = {}
        
        for key, value in grouped_config.items():
            if key == "version":
                continue
            
            # If value is a dict, it's a group - flatten it
            if isinstance(value, dict):
                for setting_key, setting_value in value.items():
                    flat[setting_key] = setting_value
            else:
                # Not a group, add directly
                flat[key] = value
        
        return flat
    
    def remove_change_listener(self, listener: callable) -> None:
        """Remove a change listener."""
        if callback in self._change_listeners:
            self._change_listeners.remove(callback)
    
    def _notify_change(self, group: str, setting: str, new_value: Any, old_value: Any) -> None:
        """Notify all listeners of a setting change."""
        for listener in self._change_listeners:
            try:
                listener(group, setting, new_value, old_value)
            except Exception as e:
                self.logger.error(f"Error in change listener: {e}")
