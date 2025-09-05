#!/usr/bin/env python3
"""
Voice recognition test script for debugging microphone and speech recognition issues.
"""

import speech_recognition as sr
import time

def test_microphone_list():
    """Test and list available microphones."""
    print("Available microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  {index}: {name}")
    print()

def test_microphone_input():
    """Test microphone input with lower energy threshold."""
    r = sr.Recognizer()
    
    # Lower the energy threshold for more sensitive detection
    r.energy_threshold = 50  # Much lower than default
    r.dynamic_energy_threshold = True
    r.dynamic_energy_adjustment_damping = 0.15
    r.dynamic_energy_ratio = 1.5
    
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... (speak during this time)")
        r.adjust_for_ambient_noise(source, duration=2)
        print(f"Energy threshold set to: {r.energy_threshold}")
        
    print("\nListening for speech... (say something)")
    
    def callback(recognizer, audio):
        print("Audio detected! Processing...")
        try:
            text = recognizer.recognize_google(audio)
            print(f"Recognized: '{text}'")
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print(f"Error with recognition service: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    # Start background listening
    stop_listening = r.listen_in_background(sr.Microphone(), callback, phrase_time_limit=3)
    
    try:
        print("Listening... Press Ctrl+C to stop")
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_listening(wait_for_stop=False)

if __name__ == "__main__":
    print("Voice Recognition Test")
    print("=" * 30)
    
    test_microphone_list()
    test_microphone_input()
