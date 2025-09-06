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

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None


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
            'resume': ['blueberry', 'start', 'resume', 'play']
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
            self.recognizer.pause_threshold = 0.5  # Optimized for short commands
            self.recognizer.non_speaking_duration = 0.3 # Optimized for short commands
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
        
        if not PYDUB_AVAILABLE:
            self.logger.warning("pydub not available, skipping audio normalization.")
            try:
                text = recognizer.recognize_google(audio).lower().strip()
                self._process_voice_command(text)
            except (sr.UnknownValueError, sr.RequestError) as e:
                self.logger.debug(f"Standard recognition failed: {e}")
            return

        try:
            # Get raw audio data and convert to a pydub AudioSegment
            raw_data = audio.get_raw_data(convert_rate=audio.sample_rate, convert_width=audio.sample_width)
            audio_segment = AudioSegment(raw_data, sample_width=audio.sample_width, frame_rate=audio.sample_rate, channels=1) # Assuming mono

            # --- Audio Normalization ---
            if audio_segment.dBFS < -20:
                boost_db = abs(audio_segment.dBFS) - 15
                audio_segment = audio_segment + boost_db
                self.logger.info(f"Live audio is quiet ({audio_segment.dBFS:.1f} dBFS). Boosting volume by {boost_db:.1f} dB.")

            if audio_segment.frame_rate != 16000:
                audio_segment = audio_segment.set_frame_rate(16000)

            # Export normalized audio to a WAV format in memory
            normalized_wav_data = audio_segment.export(format="wav").read()
            
            # Create new AudioData with the normalized audio
            normalized_audio = sr.AudioData(normalized_wav_data, 16000, 2) # 16kHz, 16-bit (2 bytes)

            # Recognize the normalized audio
            text = recognizer.recognize_google(normalized_audio).lower().strip()
            self._process_voice_command(text)

        except sr.UnknownValueError:
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
        # Log all voice recognition attempts for debugging
        self.logger.info(f"Voice recognition attempt: '{text}'")
        
        # Check confidence threshold if configured
        confidence_threshold = self.config.get('voice_confidence_threshold', 0.0)
        
        # Find matching command using simplified approach
        command_found = False
        
        # Only pause timer if we actually find a valid command
        paused_for_command = False
        
        # Try exact word matching with very permissive approach
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        # Check for exact matches first
        for word in words:
            if word == 'left' or word == 'back' or word == 'previous' or word == 'backward':
                if not paused_for_command and self.was_playing_before_command:
                    self.controller.pause_for_voice_command()
                    paused_for_command = True
                self.logger.info(f"Voice command recognized: exact word '{word}' -> back (from text: '{text}')")
                self._show_voice_feedback('previous' if word == 'previous' else 'back')
                self._schedule_command_execution('back', word)
                command_found = True
                break
            elif word == 'right' or word == 'next' or word == 'forward' or word == 'advance':
                if not paused_for_command and self.was_playing_before_command:
                    self.controller.pause_for_voice_command()
                    paused_for_command = True
                self.logger.info(f"Voice command recognized: exact word '{word}' -> next (from text: '{text}')")
                self._show_voice_feedback('next')
                self._schedule_command_execution('next', word)
                command_found = True
                break
            elif word == 'stop' or word == 'pause' or word == 'halt':
                if not paused_for_command and self.was_playing_before_command:
                    self.controller.pause_for_voice_command()
                    paused_for_command = True
                self.logger.info(f"Voice command recognized: exact word '{word}' -> pause (from text: '{text}')")
                self._show_voice_feedback('stop')
                self._schedule_command_execution('pause', word)
                command_found = True
                break
            elif word == 'go' or word == 'play' or word == 'resume' or word == 'start':
                if not paused_for_command and self.was_playing_before_command:
                    self.controller.pause_for_voice_command()
                    paused_for_command = True
                self.logger.info(f"Voice command recognized: exact word '{word}' -> resume (from text: '{text}')")
                self._show_voice_feedback('go')
                self._schedule_command_execution('resume', word)
                command_found = True
                break
        
        # If no exact match, try fuzzy matching
        if not command_found:
            for keyword, command in self.command_keywords.items():
                for variant in command:
                    if self._fuzzy_match(variant, text_lower):
                        if not paused_for_command and self.was_playing_before_command:
                            self.controller.pause_for_voice_command()
                            paused_for_command = True
                        self.logger.info(f"Voice command recognized: fuzzy match '{variant}' -> {keyword} (from text: '{text}')")
                        self._show_voice_feedback(keyword)
                        self._schedule_command_execution(keyword, variant)
                        command_found = True
                        break
                if command_found:
                    break
        
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
    
    def _fuzzy_match(self, keyword: str, text: str) -> bool:
        """
        Fuzzy matching for voice commands to improve recognition.
        
        Args:
            keyword: The target keyword to match
            text: The recognized speech text
            
        Returns:
            bool: True if keyword matches text with fuzzy logic
        """
        # Convert to lowercase for case-insensitive matching
        keyword = keyword.lower().strip()
        text = text.lower().strip()
        
        # Exact match (original behavior)
        if keyword in text:
            return True
        
        # Word boundary matching - keyword as whole word
        if re.search(r'\b' + re.escape(keyword) + r'\b', text):
            return True
        
        # Handle common speech recognition errors
        
        # "back" often gets recognized as "bag", "pack", "beck", etc.
        if keyword == "back":
            back_variants = ["bag", "pack", "beck", "bak", "backed", "backing", "bat", "black", "track", "lack", "sack", "rack", "crack", "stack", "attack", "snack", "jack", "hack", "tack", "whack", "smack", "quack", "mac", "tak", "ak", "ack", "bac", "bck"]
            for variant in back_variants:
                if variant in text:
                    return True
        
        # Also handle "previous" variants since user mentioned it works
        if keyword == "previous":
            previous_variants = ["precious", "previus", "prev", "previously"]
            for variant in previous_variants:
                if variant in text:
                    return True
        
        # "next" variants
        if keyword == "next":
            next_variants = ["neck", "text", "nest", "nets"]
            for variant in next_variants:
                if variant in text:
                    return True
        
        # "stop" variants
        if keyword == "stop":
            stop_variants = ["top", "shop", "stopped", "stopping"]
            for variant in stop_variants:
                if variant in text:
                    return True
        
        # Partial matching for very short words (2-3 characters)
        if len(keyword) <= 3:
            # Check if keyword is at start or end of any word in text
            words = text.split()
            for word in words:
                if word.startswith(keyword) or word.endswith(keyword):
                    return True
        
        # Phonetic similarity for difficult words
        if keyword == "go":
            # Single syllable words that sound similar to "go"
            phonetic_go = ["oh", "so", "no", "low", "bow", "row", "show", "flow", "slow", "know", "throw", "grow", "glow"]
            for phonetic in phonetic_go:
                if phonetic in text:
                    return True
        
        if keyword == "back":
            # Words ending in "-ack" sound
            phonetic_back = ["sack", "rack", "crack", "stack", "attack", "snack", "jack", "hack", "tack", "whack", "smack", "quack", "track", "pack", "lack", "black"]
            for phonetic in phonetic_back:
                if phonetic in text:
                    return True
        
        # Levenshtein distance for very close matches (1-2 character differences)
        if len(keyword) >= 3:
            words = text.split()
            for word in words:
                if len(word) >= 2 and abs(len(word) - len(keyword)) <= 2:
                    # Simple character difference check
                    differences = sum(1 for a, b in zip(keyword, word) if a != b)
                    if differences <= 1 and len(keyword) == len(word):
                        return True
        
        return False
    
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
