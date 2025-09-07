"""
Voice Recognition Provider Abstraction Layer

Provides a pluggable interface for different voice recognition services,
allowing easy swapping between Google, Azure, offline solutions, or mock providers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

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


class VoiceRecognitionProvider(ABC):
    """Abstract base class for voice recognition providers."""
    
    @abstractmethod
    def recognize_speech(self, audio_data) -> Optional[str]:
        """
        Recognize speech from audio data.
        
        Args:
            audio_data: Audio data to process
            
        Returns:
            str: Recognized text, or None if recognition failed
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        pass


class GoogleVoiceRecognitionProvider(VoiceRecognitionProvider):
    """Google Speech Recognition provider."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Reuse single recognizer instance for better performance
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
        
    def recognize_speech(self, audio_data) -> Optional[str]:
        """Recognize speech using Google's API."""
        if not SPEECH_RECOGNITION_AVAILABLE or not self.recognizer:
            return None
            
        try:
            # Apply audio normalization if pydub is available
            if PYDUB_AVAILABLE:
                audio_data = self._normalize_audio(audio_data)
            
            text = self.recognizer.recognize_google(audio_data).lower().strip()
            self.logger.debug(f"Google recognition result: '{text}'")
            return text
            
        except sr.UnknownValueError:
            self.logger.debug("Google could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.warning(f"Google recognition service error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in Google recognition: {e}")
            return None
    
    def _normalize_audio(self, audio_data):
        """Normalize audio for better recognition."""
        try:
            # Get raw audio data and convert to a pydub AudioSegment
            raw_data = audio_data.get_raw_data(convert_rate=audio_data.sample_rate, convert_width=audio_data.sample_width)
            audio_segment = AudioSegment(raw_data, sample_width=audio_data.sample_width, frame_rate=audio_data.sample_rate, channels=1)

            # Audio normalization
            if audio_segment.dBFS < -20:
                boost_db = abs(audio_segment.dBFS) - 15
                audio_segment = audio_segment + boost_db
                self.logger.debug(f"Boosted audio volume by {boost_db:.1f} dB")

            if audio_segment.frame_rate != 16000:
                audio_segment = audio_segment.set_frame_rate(16000)

            # Export normalized audio to WAV format in memory
            normalized_wav_data = audio_segment.export(format="wav").read()
            
            # Create new AudioData with the normalized audio
            return sr.AudioData(normalized_wav_data, 16000, 2)
            
        except Exception as e:
            self.logger.debug(f"Audio normalization failed, using original: {e}")
            return audio_data
    
    def is_available(self) -> bool:
        """Check if Google recognition is available."""
        return SPEECH_RECOGNITION_AVAILABLE
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Google Speech Recognition"


class MockVoiceRecognitionProvider(VoiceRecognitionProvider):
    """Mock provider for testing purposes."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mock_responses = config.get('mock_responses', ['next', 'back', 'stop', 'go'])
        self.response_index = 0
        self.logger = logging.getLogger(__name__)
        
    def recognize_speech(self, audio_data) -> Optional[str]:
        """Return mock responses in sequence."""
        if not self.mock_responses:
            return None
            
        response = self.mock_responses[self.response_index % len(self.mock_responses)]
        self.response_index += 1
        self.logger.debug(f"Mock recognition result: '{response}'")
        return response
    
    def is_available(self) -> bool:
        """Mock provider is always available."""
        return True
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Mock Voice Recognition (Testing)"


class VoiceRecognitionProviderFactory:
    """Factory for creating voice recognition providers."""
    
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, Any]) -> Optional[VoiceRecognitionProvider]:
        """
        Create a voice recognition provider.
        
        Args:
            provider_type: Type of provider ('google', 'mock', etc.)
            config: Configuration dictionary
            
        Returns:
            VoiceRecognitionProvider: The created provider, or None if unavailable
        """
        logger = logging.getLogger(__name__)
        
        if provider_type.lower() == 'google':
            provider = GoogleVoiceRecognitionProvider(config)
            if provider.is_available():
                logger.info(f"Created {provider.get_provider_name()} provider")
                return provider
            else:
                logger.warning("Google Speech Recognition not available")
                return None
                
        elif provider_type.lower() == 'mock':
            provider = MockVoiceRecognitionProvider(config)
            logger.info(f"Created {provider.get_provider_name()} provider")
            return provider
            
        else:
            logger.error(f"Unknown voice recognition provider: {provider_type}")
            return None
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available provider types."""
        providers = ['mock']  # Mock is always available
        
        if SPEECH_RECOGNITION_AVAILABLE:
            providers.append('google')
            
        return providers
