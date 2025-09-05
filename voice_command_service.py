"""
Voice Command Service for Dynamic Photo Slideshow

Provides voice recognition capabilities to control slideshow navigation
using simple voice commands: "next", "back", "stop", "go"
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict, List

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None


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
        
        # Service state
        self.is_listening = False
        self.is_enabled = False
        
        # Voice command mappings
        self.command_keywords = {
            'next': ['next', 'forward', 'advance'],
            'back': ['back', 'previous', 'backward'],
            'pause': ['stop', 'pause', 'halt'],
            'resume': ['go', 'start', 'resume', 'play']
        }
        
        # Initialize if speech recognition is available and enabled
        if SPEECH_RECOGNITION_AVAILABLE and self.config.get('voice_commands_enabled', False):
            self._initialize_voice_recognition()
    
    def _initialize_voice_recognition(self) -> bool:
        """
        Initialize speech recognition components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Configure recognizer for better sensitivity and ARM64 compatibility
            self.recognizer.energy_threshold = 50  # Lower threshold for better detection
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.dynamic_energy_adjustment_damping = 0.15
            self.recognizer.dynamic_energy_ratio = 1.5
            self.recognizer.pause_threshold = 0.8  # Shorter pause detection
            self.recognizer.phrase_threshold = 0.3  # Shorter phrase detection
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.logger.info(f"Energy threshold set to: {self.recognizer.energy_threshold}")
            
            # Update command keywords from config if provided
            config_keywords = self.config.get('voice_keywords', {})
            if config_keywords:
                self.command_keywords.update(config_keywords)
            
            self.is_enabled = True
            self.logger.info("Voice command service initialized successfully")
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
    
    def _voice_callback(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        """
        Callback function for processing recognized audio.
        
        Args:
            recognizer: Speech recognizer instance
            audio: Audio data to process
        """
        self.logger.debug("Audio detected, processing...")
        
        try:
            # Use system FLAC encoder instead of bundled one
            import os
            import tempfile
            
            # Get WAV data and save to temporary file
            wav_data = audio.get_wav_data()
            
            # Try direct recognition first (fastest)
            try:
                text = recognizer.recognize_google(audio, show_all=False).lower().strip()
                self.logger.info(f"Voice recognition result: '{text}'")
                self._process_voice_command(text)
                return
            except OSError as direct_e:
                if "Bad CPU type" not in str(direct_e):
                    raise direct_e
                # Continue to alternative method
            
            # Alternative: Use system flac encoder
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_wav.write(wav_data)
                temp_wav_path = temp_wav.name
            
            try:
                # Create new AudioData from the temp file
                with sr.AudioFile(temp_wav_path) as source:
                    temp_audio = recognizer.record(source)
                
                text = recognizer.recognize_google(temp_audio, show_all=False).lower().strip()
                self.logger.info(f"Voice recognition result (temp file): '{text}'")
                self._process_voice_command(text)
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_wav_path)
                except:
                    pass
            
        except sr.UnknownValueError:
            # Speech was unintelligible - this is normal, don't log as error
            self.logger.debug("Voice recognition could not understand audio")
            
        except sr.RequestError as e:
            self.logger.warning(f"Voice recognition service error: {e}")
            
        except Exception as e:
            self.logger.error(f"Unexpected error in voice callback: {e}")
    
    def _process_voice_command(self, text: str) -> None:
        """
        Process recognized voice command and trigger appropriate action.
        
        Args:
            text: Recognized speech text
        """
        # Check confidence threshold if configured
        confidence_threshold = self.config.get('voice_confidence_threshold', 0.0)
        
        # Find matching command
        command_found = False
        
        for command, keywords in self.command_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    self.logger.info(f"Voice command recognized: '{keyword}' -> {command}")
                    self._execute_command(command)
                    command_found = True
                    break
            if command_found:
                break
        
        if not command_found:
            self.logger.debug(f"No matching voice command found for: '{text}'")
    
    def _execute_command(self, command: str) -> None:
        """
        Execute the specified command by calling appropriate controller methods.
        
        Args:
            command: Command to execute ('next', 'back', 'pause', 'resume')
        """
        try:
            if command == 'next':
                self.controller.next_photo()
            elif command == 'back':
                self.controller.previous_photo()
            elif command == 'pause':
                if not self.controller.is_paused:
                    self.controller.toggle_pause()
            elif command == 'resume':
                if self.controller.is_paused:
                    self.controller.toggle_pause()
            else:
                self.logger.warning(f"Unknown command: {command}")
                
        except Exception as e:
            self.logger.error(f"Error executing voice command '{command}': {e}")
    
    def is_voice_available(self) -> bool:
        """
        Check if voice recognition is available and enabled.
        
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
