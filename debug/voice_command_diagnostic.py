#!/usr/bin/env python3
"""
Enhanced Voice Command Diagnostic Tool
Provides detailed audio analysis and recognition debugging for voice command files.
"""

import os
import sys
import logging
from pathlib import Path
import json
from typing import Dict, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    import speech_recognition as sr
    from pydub import AudioSegment
    from pydub.utils import which
except ImportError as e:
    print(f"Error: Required library not installed")
    if "speech_recognition" in str(e):
        print("Install with: pip install SpeechRecognition")
    elif "pydub" in str(e):
        print("Install with: pip install pydub")
    sys.exit(1)

class VoiceCommandDiagnostic:
    def __init__(self):
        self.logger = self._setup_logging()
        self.recognizer = sr.Recognizer()
        self.desktop_path = Path.home() / "Desktop"
        
        # Voice command mappings from the main application
        self.command_keywords = {
            'resume': ['go', 'start', 'play', 'resume', 'begin', 'golly', 'gully', 'goal'],
            'pause': ['stop', 'pause', 'halt', 'wait', 'stomp', 'stopped'],
            'next': ['next', 'forward', 'advance', 'right', 'neck', 'necks'],
            'back': ['left', 'back', 'previous', 'backward', 'beck', 'backs']
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for diagnostic output."""
        logger = logging.getLogger('voice_diagnostic')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def analyze_audio_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze audio file properties and quality."""
        try:
            # Load audio file
            audio = AudioSegment.from_file(str(file_path))
            
            # Basic audio properties
            analysis = {
                'file_size_bytes': file_path.stat().st_size,
                'duration_ms': len(audio),
                'duration_seconds': len(audio) / 1000.0,
                'channels': audio.channels,
                'sample_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'frame_count': audio.frame_count(),
                'max_possible_amplitude': audio.max_possible_amplitude,
                'rms': audio.rms,
                'dBFS': audio.dBFS,
                'max_dBFS': audio.max_dBFS
            }
            
            # Audio quality indicators
            analysis['is_silent'] = audio.rms == 0
            analysis['is_very_quiet'] = audio.dBFS < -30
            analysis['is_too_short'] = len(audio) < 500  # Less than 0.5 seconds
            analysis['is_too_long'] = len(audio) > 5000   # More than 5 seconds
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
            
    def convert_m4a_to_wav(self, m4a_path: Path) -> Path:
        """Convert m4a file to wav format for speech recognition."""
        wav_path = m4a_path.parent / f"{m4a_path.stem}_temp.wav"
        
        try:
            # Load and convert audio
            audio = AudioSegment.from_file(str(m4a_path), format="m4a")
            
            # Normalize audio for better recognition
            # Increase volume if too quiet
            if audio.dBFS < -20:
                audio = audio + (abs(audio.dBFS) - 10)
                self.logger.info(f"Boosted audio volume from {audio.dBFS:.1f} dBFS")
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
                self.logger.info("Converted stereo to mono")
                
            # Ensure proper sample rate (16kHz is good for speech recognition)
            if audio.frame_rate != 16000:
                audio = audio.set_frame_rate(16000)
                self.logger.info(f"Resampled from {audio.frame_rate}Hz to 16000Hz")
            
            # Export as WAV
            audio.export(str(wav_path), format="wav")
            return wav_path
            
        except Exception as e:
            self.logger.error(f"Error converting {m4a_path}: {e}")
            raise
            
    def recognize_with_multiple_engines(self, wav_path: Path) -> Dict[str, Any]:
        """Try recognition with multiple engines and settings."""
        results = {}
        
        with sr.AudioFile(str(wav_path)) as source:
            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
            audio = self.recognizer.record(source)
            
        # Try Google Speech Recognition with different settings
        for energy_threshold in [300, 100, 50]:
            self.recognizer.energy_threshold = energy_threshold
            try:
                text = self.recognizer.recognize_google(audio, show_all=False)
                confidence = 1.0  # Google doesn't return confidence in simple mode
                results[f'google_energy_{energy_threshold}'] = {
                    'text': text,
                    'confidence': confidence,
                    'success': True
                }
                self.logger.info(f"Google (energy {energy_threshold}): '{text}'")
            except sr.UnknownValueError:
                results[f'google_energy_{energy_threshold}'] = {
                    'text': None,
                    'confidence': 0.0,
                    'success': False,
                    'error': 'No speech detected'
                }
            except Exception as e:
                results[f'google_energy_{energy_threshold}'] = {
                    'text': None,
                    'confidence': 0.0,
                    'success': False,
                    'error': str(e)
                }
        
        # Try Google with show_all=True for detailed results
        try:
            detailed_result = self.recognizer.recognize_google(audio, show_all=True)
            if detailed_result and 'alternative' in detailed_result:
                alternatives = detailed_result['alternative']
                if alternatives:
                    best_alt = alternatives[0]
                    results['google_detailed'] = {
                        'text': best_alt.get('transcript', ''),
                        'confidence': best_alt.get('confidence', 0.0),
                        'success': True,
                        'alternatives': alternatives[:3]  # Top 3 alternatives
                    }
        except Exception as e:
            results['google_detailed'] = {
                'text': None,
                'confidence': 0.0,
                'success': False,
                'error': str(e)
            }
            
        return results
        
    def match_command(self, text: str) -> Optional[str]:
        """Match recognized text to voice commands using exact and fuzzy matching."""
        if not text:
            return None
            
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        # Exact word matching
        for command, keywords in self.command_keywords.items():
            for word in words:
                if word in keywords:
                    return command
                    
        return None
        
    def diagnose_file(self, command: str) -> Dict[str, Any]:
        """Comprehensive diagnosis of a voice command file."""
        file_path = self.desktop_path / f"{command}.m4a"
        
        self.logger.info(f"Diagnosing {command} command with {file_path.name}")
        
        if not file_path.exists():
            return {
                'command': command,
                'file_exists': False,
                'error': f'File not found: {file_path}'
            }
            
        diagnosis = {
            'command': command,
            'file_path': str(file_path),
            'file_exists': True
        }
        
        # Audio analysis
        self.logger.info("Analyzing audio properties...")
        diagnosis['audio_analysis'] = self.analyze_audio_file(file_path)
        
        # Convert to WAV
        try:
            self.logger.info("Converting to WAV...")
            wav_path = self.convert_m4a_to_wav(file_path)
            diagnosis['conversion_success'] = True
            
            # Recognition attempts
            self.logger.info("Testing speech recognition...")
            diagnosis['recognition_results'] = self.recognize_with_multiple_engines(wav_path)
            
            # Command matching
            best_result = None
            best_confidence = 0
            
            for engine, result in diagnosis['recognition_results'].items():
                if result['success'] and result['confidence'] > best_confidence:
                    best_result = result
                    best_confidence = result['confidence']
                    
            if best_result:
                matched_command = self.match_command(best_result['text'])
                diagnosis['best_recognition'] = {
                    'text': best_result['text'],
                    'confidence': best_result['confidence'],
                    'matched_command': matched_command,
                    'expected_command': 'resume' if command == 'go' else ('pause' if command == 'stop' else command),
                    'success': matched_command == ('resume' if command == 'go' else ('pause' if command == 'stop' else command))
                }
            else:
                diagnosis['best_recognition'] = {
                    'text': None,
                    'confidence': 0.0,
                    'matched_command': None,
                    'success': False
                }
            
            # Clean up temp file
            try:
                wav_path.unlink()
            except:
                pass
                
        except Exception as e:
            diagnosis['conversion_success'] = False
            diagnosis['conversion_error'] = str(e)
            
        return diagnosis
        
    def print_diagnosis(self, diagnosis: Dict[str, Any]):
        """Print formatted diagnosis results."""
        print(f"\n{'='*60}")
        print(f"DIAGNOSTIC REPORT: {diagnosis['command'].upper()}")
        print(f"{'='*60}")
        
        if not diagnosis['file_exists']:
            print(f"❌ FILE NOT FOUND: {diagnosis.get('error', 'Unknown error')}")
            return
            
        # Audio Analysis
        audio = diagnosis.get('audio_analysis', {})
        if 'error' in audio:
            print(f"❌ AUDIO ANALYSIS FAILED: {audio['error']}")
        else:
            print(f"\n📊 AUDIO PROPERTIES:")
            print(f"   Duration: {audio.get('duration_seconds', 0):.2f} seconds")
            print(f"   Sample Rate: {audio.get('sample_rate', 0)} Hz")
            print(f"   Channels: {audio.get('channels', 0)}")
            print(f"   Volume (dBFS): {audio.get('dBFS', 0):.1f}")
            print(f"   RMS: {audio.get('rms', 0)}")
            
            # Quality warnings
            warnings = []
            if audio.get('is_silent'):
                warnings.append("⚠️  Audio appears to be silent")
            if audio.get('is_very_quiet'):
                warnings.append("⚠️  Audio is very quiet (< -30 dBFS)")
            if audio.get('is_too_short'):
                warnings.append("⚠️  Audio is very short (< 0.5 seconds)")
            if audio.get('is_too_long'):
                warnings.append("⚠️  Audio is long (> 5 seconds)")
                
            if warnings:
                print(f"\n⚠️  QUALITY WARNINGS:")
                for warning in warnings:
                    print(f"   {warning}")
        
        # Recognition Results
        if not diagnosis.get('conversion_success'):
            print(f"❌ CONVERSION FAILED: {diagnosis.get('conversion_error', 'Unknown error')}")
            return
            
        print(f"\n🎤 RECOGNITION ATTEMPTS:")
        recognition = diagnosis.get('recognition_results', {})
        for engine, result in recognition.items():
            status = "✅" if result['success'] else "❌"
            text = result.get('text', 'None')
            conf = result.get('confidence', 0.0)
            print(f"   {status} {engine}: '{text}' (confidence: {conf:.2f})")
            
        # Best Result
        best = diagnosis.get('best_recognition', {})
        print(f"\n🏆 BEST RESULT:")
        print(f"   Text: '{best.get('text', 'None')}'")
        print(f"   Confidence: {best.get('confidence', 0.0):.2f}")
        print(f"   Matched Command: {best.get('matched_command', 'None')}")
        print(f"   Expected Command: {best.get('expected_command', 'None')}")
        print(f"   Success: {'✅' if best.get('success') else '❌'}")
        
def main():
    """Main diagnostic function."""
    diagnostic = VoiceCommandDiagnostic()
    
    print("Voice Command Diagnostic Tool")
    print("============================")
    
    # Test all commands
    commands = ['go', 'stop', 'next', 'back']
    
    for command in commands:
        diagnosis = diagnostic.diagnose_file(command)
        diagnostic.print_diagnosis(diagnosis)
        
    print(f"\n{'='*60}")
    print("DIAGNOSTIC COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
