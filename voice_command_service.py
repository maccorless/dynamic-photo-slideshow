"""
Voice Command Service for Dynamic Photo Slideshow

Provides voice recognition capabilities to control slideshow navigation
using simple voice commands: "next", "back", "stop", "go"
"""

import logging
import re
import threading
import time
from typing import Optional, Callable, Dict, List

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

from voice_recognition_providers import VoiceRecognitionProviderFactory
from voice_command_matcher import VoiceCommandMatcher
from slideshow_exceptions import VoiceCommandError, VoiceRecognitionError


class VoiceCommandService:
    """Service for handling voice commands in the slideshow application."""
    
    def __init__(self, slideshow_controller, config: dict):
        """
        Initialize the voice command service.
        
        Args:
            slideshow_controller: Reference to the slideshow controller
            config: Configuration dictionary with voice command settings
        """
        self.controller = slideshow_controller
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Voice recognition components
        self.recognizer: Optional[sr.Recognizer] = None
        self.microphone: Optional[sr.Microphone] = None
        self.stop_listening: Optional[Callable] = None
        self.voice_provider: Optional[VoiceRecognitionProvider] = None
        self.command_matcher: Optional[VoiceCommandMatcher] = None
        
        # Service state
        self.is_listening = False
        self.is_enabled = False
        
        # Initialize if voice commands are enabled
        if self.config.get('voice_commands_enabled', False):
            self._initialize_voice_recognition()
    
    def _initialize_voice_recognition(self) -> bool:
        """
        Initialize speech recognition components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Create voice recognition provider
            provider_type = self.config.get('voice_provider', 'google')
            self.voice_provider = VoiceRecognitionProviderFactory.create_provider(provider_type, self.config)
            
            if not self.voice_provider:
                self.logger.error(f"Failed to create voice provider: {provider_type}")
                return False
            
            # Initialize command matcher
            matcher_config_path = self.config.get('voice_command_variants_path')
            self.command_matcher = VoiceCommandMatcher(matcher_config_path)
            
            # Initialize speech recognition components if using real providers
            if provider_type != 'mock' and SPEECH_RECOGNITION_AVAILABLE:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                
                # Configure recognizer for better sensitivity and ARM64 compatibility
                self.recognizer.energy_threshold = 50  # Lower threshold for better detection
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.dynamic_energy_adjustment_damping = 0.15
                self.recognizer.dynamic_energy_ratio = 1.5
                self.recognizer.pause_threshold = 0.5  # Optimized for short commands
                self.recognizer.non_speaking_duration = 0.3 # Optimized for short commands
                self.recognizer.phrase_threshold = 0.3  # Shorter phrase detection
                
                # Adjust for ambient noise
                with self.microphone as source:
                    self.logger.info("Calibrating microphone for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    self.logger.info(f"Energy threshold set to: {self.recognizer.energy_threshold}")
            
            # Add any custom variants from config
            custom_variants = self.config.get('custom_voice_variants', {})
            for command, variants in custom_variants.items():
                for variant in variants:
                    self.command_matcher.add_custom_variant(command, variant)
            
            self.is_enabled = True
            self.logger.info(f"Voice command service initialized with {self.voice_provider.get_provider_name()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize voice recognition: {e}")
            self.is_enabled = False
            return False
    
    def start_listening(self) -> bool:
        """
        Start listening for voice commands in the background.
        
        Returns:
            bool: True if listening started successfully, False otherwise
        """
        if not self.is_enabled or self.is_listening:
            return False
        
        try:
            # Start background listening
            self.stop_listening = self.recognizer.listen_in_background(
                self.microphone, 
                self._voice_callback,
                phrase_time_limit=self.config.get('voice_command_timeout', 2.0)
            )
            
            self.is_listening = True
            self.logger.info("Voice command listening started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start voice listening: {e}")
            return False
    
    def stop_listening_service(self) -> None:
        """Stop listening for voice commands."""
        if self.stop_listening and self.is_listening:
            try:
                self.stop_listening(wait_for_stop=False)
                self.is_listening = False
                self.logger.info("Voice command listening stopped")
            except Exception as e:
                self.logger.error(f"Error stopping voice listening: {e}")
    
    def _voice_callback(self, recognizer, audio) -> None:
        """
        Callback function for voice recognition.
        
        Args:
            recognizer: Speech recognition instance
            audio: Audio data to process
        """
        self.logger.debug("Audio detected, processing for voice commands...")
        
        # Store playing state but don't pause immediately - wait to see if it's actually a command
        self.was_playing_before_command = self.controller.is_playing
        
        # Use the abstracted voice provider
        try:
            text = self.voice_provider.recognize_speech(audio)
            if text:
                self._process_voice_command(text)
            else:
                self.logger.debug("Voice recognition could not understand audio")
        except Exception as e:
            self.logger.error(f"Unexpected error in voice callback: {e}")
    
    def _process_voice_command(self, text: str) -> None:
        """
        Process recognized voice command and trigger appropriate action.
        
        Args:
            text: Recognized speech text
        """
        # Log all voice recognition attempts for debugging
        self.logger.info(f"Voice recognition attempt: '{text}'")
        
        # Use the configurable command matcher
        match_result = self.command_matcher.find_matching_command(text)
        
        command_found = False
        paused_for_command = False
        
        if match_result:
            command, matched_variant, match_type = match_result
            
            # Pause timer if we found a valid command
            if self.was_playing_before_command:
                self.controller.pause_for_voice_command()
                paused_for_command = True
            
            self.logger.info(f"Voice command recognized: {match_type} match '{matched_variant}' -> {command} (from text: '{text}')")
            self._show_voice_feedback(command)
            self._schedule_command_execution(command, matched_variant)
            command_found = True
        
        if not command_found:
            self.logger.info(f"No matching voice command found for: '{text}'")
        
        # Resume timer if it was playing before the command AND we actually paused it
        if paused_for_command and self.was_playing_before_command:
            self.controller.resume_after_voice_command()
    
    def _show_voice_feedback(self, keyword: str) -> None:
        """
        Show visual feedback for recognized voice command.
        
        Args:
            keyword: The recognized keyword to display
        """
        try:
            # Get display manager from controller and show overlay
            if hasattr(self.controller, 'display_manager') and self.controller.display_manager:
                self.controller.display_manager.show_voice_command_overlay(keyword)
        except Exception as e:
            self.logger.debug(f"Error showing voice feedback: {e}")
    
    
    def _schedule_command_execution(self, command: str, keyword: str) -> None:
        """
        Schedule command execution after 1.5 second delay.
        
        Args:
            command: Command to execute
            keyword: The recognized keyword
        """
        try:
            def delayed_execution():
                time.sleep(1.5)  # Wait for overlay to show
                
                # Special handling for STOP command
                if command == 'pause':
                    # Show STOPPED overlay and pause slideshow
                    if hasattr(self.controller, 'display_manager') and self.controller.display_manager:
                        self.controller.display_manager.show_stopped_overlay()
                    if not self.controller.is_paused:
                        self.controller.toggle_pause()
                else:
                    # For other commands, execute normally
                    self._execute_command(command)
                    
                    # If this is GO command, clear stopped overlay
                    if command == 'resume':
                        if hasattr(self.controller, 'display_manager') and self.controller.display_manager:
                            self.controller.display_manager.clear_stopped_overlay()
            
            # Execute in background thread to avoid blocking
            thread = threading.Thread(target=delayed_execution, daemon=True)
            thread.start()
            
        except Exception as e:
            self.logger.error(f"Error scheduling command execution: {e}")
            # Fallback to immediate execution
            self._execute_command(command)
    
    def _execute_command(self, command: str) -> None:
        """Execute the voice command by calling appropriate controller method."""
        try:
            if command == 'next':
                self.controller.next_photo()
            elif command == 'back':
                self.controller.previous_photo()
            elif command == 'pause':
                self.controller.toggle_pause()
            elif command == 'resume':
                self.controller.toggle_pause()
            else:
                self.logger.warning(f"Unknown command: {command}")
        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {e}")
    
    def is_available(self) -> bool:
        """
        Check if voice commands are available.
        
        Returns:
            bool: True if voice commands are available, False otherwise
        """
        return SPEECH_RECOGNITION_AVAILABLE and self.is_enabled
    
    def get_status(self) -> Dict[str, any]:
        """
        Get current status of voice command service.
        
        Returns:
            dict: Status information
        """
        return {
            'available': SPEECH_RECOGNITION_AVAILABLE,
            'enabled': self.is_enabled,
            'listening': self.is_listening,
            'commands': list(self.command_keywords.keys())
        }
