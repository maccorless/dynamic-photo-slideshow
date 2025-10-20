#!/usr/bin/env python3
"""
Voice Recognition Test App

Simple app to test voice recognition.
Displays what Google heard and whether it matched a command.
Press Ctrl+C to exit.
"""

import sys
import time

try:
    import speech_recognition as sr
except ImportError:
    print("ERROR: speech_recognition not installed")
    print("Install with: pip install SpeechRecognition")
    sys.exit(1)

# Command definitions - simple exact word matching
COMMANDS = {
    'next': ['next', 'advance', 'ahead', 'skip'],
    'back': ['back', 'prior', 'previous'],
    'pause': ['stop', 'pause', 'freeze', 'free'],
    'resume': ['go', 'unpause', 'restart', 'blueberry', 'blue', 'start', 'resume']
}


class VoiceRecognitionTester:
    """Simple voice recognition tester."""
    
    def __init__(self):
        """Initialize the tester."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Configure recognizer for single-word commands
        self.recognizer.energy_threshold = 50
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.3  # Fast response for single words
        self.recognizer.non_speaking_duration = 0.3
        self.recognizer.phrase_threshold = 0.3
        
        # Calibrate microphone
        print("\n" + "="*70)
        print("VOICE RECOGNITION TESTER - SIMPLIFIED")
        print("="*70)
        print("\nCalibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print(f"✓ Energy threshold set to: {self.recognizer.energy_threshold}")
        
        self.test_count = 0
        
    def match_command(self, text):
        """Match text to a command using simple exact word matching.
        
        Args:
            text: The recognized text
            
        Returns:
            Tuple of (command, matched_word) or (None, None)
        """
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        # Check each word against command keywords
        for word in words:
            for command, keywords in COMMANDS.items():
                if word in keywords:
                    return command, word
        
        return None, None
        
    def voice_callback(self, recognizer, audio):
        """Process audio and display results."""
        self.test_count += 1
        
        print("\n" + "-"*70)
        print(f"TEST #{self.test_count}")
        print("-"*70)
        
        try:
            # Get transcription from Google
            text = recognizer.recognize_google(audio).lower().strip()
            
            if text:
                print(f"🎤 HEARD: '{text}'")
                
                # Try to match command
                command, matched_word = self.match_command(text)
                
                if command:
                    print(f"✅ MATCHED: '{matched_word}' → {command.upper()}")
                else:
                    print(f"❌ NO MATCH: '{text}' did not match any command")
            
        except sr.UnknownValueError:
            print("❓ Could not understand audio")
        except sr.RequestError as e:
            print(f"❌ Google API Error: {e}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    def run(self):
        """Start listening for voice commands."""
        print("\n" + "="*70)
        print("🎤 LISTENING FOR VOICE COMMANDS")
        print("="*70)
        print("\nAcceptable words for each command:")
        print()
        for command, keywords in COMMANDS.items():
            print(f"  {command.upper():8} → {', '.join(keywords)}")
        
        print("\nPress Ctrl+C to exit")
        print("\nListening...")
        
        # Start background listening
        stop_listening = self.recognizer.listen_in_background(
            self.microphone,
            self.voice_callback,
            phrase_time_limit=2.0
        )
        
        try:
            # Keep running until Ctrl+C
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nStopping...")
            stop_listening(wait_for_stop=False)
            print("✓ Voice recognition stopped")
            print(f"\nTotal tests: {self.test_count}")
            print("\nGoodbye!")


if __name__ == "__main__":
    try:
        tester = VoiceRecognitionTester()
        tester.run()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        sys.exit(1)
