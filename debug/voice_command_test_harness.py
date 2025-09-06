#!/usr/bin/env python3
"""
Voice Command Test Harness

Tests voice recognition accuracy using recorded m4a files and allows
iterative tuning of recognition parameters for optimal performance.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


class VoiceRecognitionTester:
    """Test harness for voice recognition using recorded audio files."""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.desktop_path = Path.home() / "Desktop"
        self.test_files = {
            "go": self.desktop_path / "go.m4a",
            "stop": self.desktop_path / "stop.m4a", 
            "next": self.desktop_path / "next.m4a",
            "back": self.desktop_path / "back.m4a"
        }
        
        # Voice recognition parameters (tunable)
        self.confidence_threshold = 0.3
        self.recognition_engine = "google"  # google, sphinx, etc.
        self.pause_threshold = 0.8  # Default value
        self.non_speaking_duration = 0.5 # Default value
        
        # Command keywords (copied from voice_command_service.py)
        self.command_keywords = {
            'next': ['next', 'forward', 'advance', 'right'],
            'back': ['back', 'previous', 'backward', 'left'],
            'pause': ['stop', 'pause', 'halt'],
            'resume': ['golly', 'gully', 'go', 'start', 'resume', 'play', 'continue', 'show', 'go-go', "don't"]
        }
        
        # Initialize recognizer
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            raise ImportError("speech_recognition library required")
            
        if not PYDUB_AVAILABLE:
            raise ImportError("pydub library required for m4a file processing")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the test harness."""
        logger = logging.getLogger('voice_test_harness')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def convert_m4a_to_wav(self, m4a_path: Path) -> Path:
        """Convert m4a file to wav for speech recognition with audio normalization."""
        try:
            # Create temporary wav file
            temp_dir = Path(tempfile.gettempdir())
            wav_path = temp_dir / f"{m4a_path.stem}_temp.wav"

            # Load and convert audio
            audio = AudioSegment.from_file(str(m4a_path), format="m4a")
            
            # --- Audio Normalization ---
            # Increase volume if too quiet, targeting -15 dBFS as a healthy level
            if audio.dBFS < -20:
                boost_db = abs(audio.dBFS) - 15
                audio = audio + boost_db
                self.logger.info(f"Audio is quiet ({audio.dBFS:.1f} dBFS). Boosting volume by {boost_db:.1f} dB.")
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
                self.logger.info("Converted stereo audio to mono.")
                
            # Ensure proper sample rate (16kHz is standard for speech recognition)
            if audio.frame_rate != 16000:
                original_rate = audio.frame_rate
                audio = audio.set_frame_rate(16000)
                self.logger.info(f"Resampled audio from {original_rate}Hz to 16000Hz.")
            
            # Export as WAV
            audio.export(str(wav_path), format="wav")
            self.logger.debug(f"Converted and normalized {m4a_path.name} to {wav_path.name}")
            return wav_path
            
        except Exception as e:
            self.logger.error(f"Error converting {m4a_path}: {e}")
            raise
    
    def recognize_audio_file(self, audio_path: Path) -> Tuple[Optional[str], float]:
        """
        Recognize speech from audio file.
        
        Returns:
            Tuple of (recognized_text, confidence_score)
        """
        try:
            with sr.AudioFile(str(audio_path)) as source:
                # Apply tunable parameters
                self.recognizer.pause_threshold = self.pause_threshold
                self.recognizer.non_speaking_duration = self.non_speaking_duration

                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                
                # Record the audio
                audio_data = self.recognizer.record(source)
                
                # Recognize speech
                if self.recognition_engine == "google":
                    try:
                        result = self.recognizer.recognize_google(
                            audio_data, 
                            show_all=True
                        )
                        
                        if result and 'alternative' in result:
                            # Get best result with confidence
                            best_result = result['alternative'][0]
                            text = best_result.get('transcript', '').lower().strip()
                            confidence = best_result.get('confidence', 0.0)
                            return text, confidence
                        else:
                            return None, 0.0
                            
                    except sr.UnknownValueError:
                        return None, 0.0
                    except sr.RequestError as e:
                        self.logger.error(f"Google Speech Recognition error: {e}")
                        return None, 0.0
                
                elif self.recognition_engine == "sphinx":
                    try:
                        text = self.recognizer.recognize_sphinx(audio_data).lower().strip()
                        return text, 1.0  # Sphinx doesn't provide confidence
                    except sr.UnknownValueError:
                        return None, 0.0
                    except sr.RequestError as e:
                        self.logger.error(f"Sphinx error: {e}")
                        return None, 0.0
                
        except Exception as e:
            import traceback
            self.logger.error(f"Error recognizing audio from {audio_path}: {e}")
            self.logger.error(traceback.format_exc())
            return None, 0.0
    
    def match_command(self, recognized_text: str) -> Optional[str]:
        """
        Match recognized text to a command using existing logic.
        
        Returns:
            Command name if matched, None otherwise
        """
        if not recognized_text:
            return None
            
        words = recognized_text.lower().split()
        
        # Exact word matching (copied from voice_command_service.py)
        for word in words:
            # Check resume commands (go variants)
            if word in ['left', 'back', 'previous', 'backward']:
                return 'back'
            elif word in ['right', 'next', 'forward', 'advance']:
                return 'next'  
            elif word in ['stop', 'pause', 'halt']:
                return 'pause'
            elif word in ['golly', 'gully', 'go', 'start', 'resume', 'play', 'continue']:
                return 'resume'
        
        # Fuzzy matching fallback
        return self._fuzzy_match_command(recognized_text)
    
    def _fuzzy_match_command(self, text: str) -> Optional[str]:
        """Fuzzy matching for commands (simplified version)."""
        text_lower = text.lower()
        
        # Simple phonetic matching
        if any(variant in text_lower for variant in ['go', 'gol', 'gul']):
            return 'resume'
        elif any(variant in text_lower for variant in ['bac', 'bak']):
            return 'back'
        elif any(variant in text_lower for variant in ['nex', 'nec']):
            return 'next'
        elif any(variant in text_lower for variant in ['sto', 'sta']):
            return 'pause'
            
        return None
    
    def test_single_file(self, command: str, file_path: Path) -> Dict:
        """Test recognition on a single audio file."""
        self.logger.info(f"Testing {command} command with {file_path.name}")
        
        if not file_path.exists():
            return {
                'command': command,
                'file': file_path.name,
                'success': False,
                'error': 'File not found'
            }
        
        try:
            # Convert m4a to wav
            wav_path = self.convert_m4a_to_wav(file_path)
            
            # Recognize speech
            recognized_text, confidence = self.recognize_audio_file(wav_path)
            
            # Match to command
            matched_command = self.match_command(recognized_text) if recognized_text else None
            
            # Determine success
            expected_command = 'resume' if command == 'go' else command
            if command == 'stop':
                expected_command = 'pause'
                
            success = (matched_command == expected_command and 
                      confidence >= self.confidence_threshold)
            
            result = {
                'command': command,
                'file': file_path.name,
                'recognized_text': recognized_text,
                'confidence': confidence,
                'matched_command': matched_command,
                'expected_command': expected_command,
                'success': success,
                'confidence_threshold': self.confidence_threshold
            }
            
            # Clean up temp file
            try:
                wav_path.unlink()
            except:
                pass
                
            return result
            
        except Exception as e:
            return {
                'command': command,
                'file': file_path.name,
                'success': False,
                'error': str(e)
            }
    
    def run_all_tests(self) -> List[Dict]:
        """Run tests on all audio files."""
        results = []
        
        self.logger.info("Starting voice recognition tests...")
        self.logger.info(f"Confidence threshold: {self.confidence_threshold}")
        self.logger.info(f"Recognition engine: {self.recognition_engine}")
        
        for command, file_path in self.test_files.items():
            result = self.test_single_file(command, file_path)
            results.append(result)
            
            # Log result
            if result['success']:
                self.logger.info(f"✅ {command}: SUCCESS")
            else:
                error_msg = result.get('error', 'Recognition failed')
                self.logger.warning(f"❌ {command}: FAILED - {error_msg}")
                
                if 'recognized_text' in result:
                    self.logger.info(f"   Recognized: '{result['recognized_text']}'")
                    self.logger.info(f"   Confidence: {result.get('confidence', 0):.2f}")
                    self.logger.info(f"   Matched: {result.get('matched_command', 'None')}")
        
        return results
    
    def print_summary(self, results: List[Dict]):
        """Print test summary."""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['success'])
        
        print(f"\n{'='*50}")
        print(f"VOICE RECOGNITION TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
        print(f"Confidence threshold: {self.confidence_threshold}")
        print(f"Recognition engine: {self.recognition_engine}")
        
        print(f"\nDetailed Results:")
        for result in results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {result['command']:>4}: {status}")
            if not result['success'] and 'recognized_text' in result:
                print(f"       Recognized: '{result.get('recognized_text', 'None')}'")
                print(f"       Confidence: {result.get('confidence', 0):.2f}")
    
    def interactive_tuning(self):
        """Interactive mode for tuning recognition parameters."""
        while True:
            print(f"\n{'='*50}")
            print("VOICE RECOGNITION TUNING MODE")
            print(f"{'='*50}")
            print("Current settings:")
            print(f"  Confidence threshold: {self.confidence_threshold}")
            print(f"  Recognition engine: {self.recognition_engine}")
            print(f"  Pause threshold: {self.pause_threshold}")
            print(f"  Non-speaking duration: {self.non_speaking_duration}")
            print("\nOptions:")
            print("1. Run all tests")
            print("2. Test single file")
            print("3. Adjust confidence threshold")
            print("4. Change recognition engine")
            print("5. Adjust pause threshold")
            print("6. Adjust non-speaking duration")
            print("7. Exit")
            
            choice = input("\nEnter choice (1-7): ").strip()
            
            if choice == '1':
                results = self.run_all_tests()
                self.print_summary(results)
                
            elif choice == '2':
                print("\nAvailable files:")
                for i, (cmd, _) in enumerate(self.test_files.items(), 1):
                    print(f"  {i}. {cmd}")
                
                try:
                    file_choice = int(input("Select file (1-4): ")) - 1
                    commands = list(self.test_files.keys())
                    if 0 <= file_choice < len(commands):
                        cmd = commands[file_choice]
                        result = self.test_single_file(cmd, self.test_files[cmd])
                        self.print_summary([result])
                except (ValueError, IndexError):
                    print("Invalid selection")
                    
            elif choice == '3':
                try:
                    new_threshold = float(input(f"Enter new confidence threshold (current: {self.confidence_threshold}): "))
                    if 0.0 <= new_threshold <= 1.0:
                        self.confidence_threshold = new_threshold
                        print(f"Confidence threshold set to {new_threshold}")
                    else:
                        print("Threshold must be between 0.0 and 1.0")
                except ValueError:
                    print("Invalid number")
                    
            elif choice == '4':
                print("Available engines:")
                print("1. google")
                print("2. sphinx")
                engine_choice = input("Select engine (1-2): ").strip()
                if engine_choice == '1':
                    self.recognition_engine = 'google'
                elif engine_choice == '2':
                    self.recognition_engine = 'sphinx'
                else:
                    print("Invalid selection")

            elif choice == '5':
                try:
                    new_pause_threshold = float(input(f"Enter new pause threshold (current: {self.pause_threshold}): "))
                    if 0.1 <= new_pause_threshold <= 2.0:
                        self.pause_threshold = new_pause_threshold
                        print(f"Pause threshold set to {new_pause_threshold}")
                    else:
                        print("Threshold must be between 0.1 and 2.0")
                except ValueError:
                    print("Invalid number")
                    
            elif choice == '6':
                try:
                    new_duration = float(input(f"Enter new non-speaking duration (current: {self.non_speaking_duration}): "))
                    if 0.1 <= new_duration <= 2.0:
                        self.non_speaking_duration = new_duration
                        print(f"Non-speaking duration set to {new_duration}")
                    else:
                        print("Duration must be between 0.1 and 2.0")
                except ValueError:
                    print("Invalid number")

            elif choice == '7':
                break
            else:
                print("Invalid choice")


def main():
    """Main function."""
    if not SPEECH_RECOGNITION_AVAILABLE:
        print("Error: speech_recognition library not installed")
        print("Install with: pip install SpeechRecognition")
        return 1
        
    if not PYDUB_AVAILABLE:
        print("Error: pydub library not installed") 
        print("Install with: pip install pydub")
        return 1
    
    try:
        tester = VoiceRecognitionTester()
        
        # Check if test files exist
        missing_files = []
        for cmd, path in tester.test_files.items():
            if not path.exists():
                missing_files.append(f"{cmd}.m4a")
        
        if missing_files:
            print(f"Error: Missing test files on Desktop: {', '.join(missing_files)}")
            return 1
        
        # Run interactive tuning mode
        tester.interactive_tuning()
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
