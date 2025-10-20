#!/usr/bin/env python3
"""Quick test to verify voice recognition is working."""

import speech_recognition as sr
import time

def test_microphone():
    """Test if microphone is accessible."""
    print("🎤 Testing microphone access...")
    try:
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        
        # Adjust for ambient noise
        with mic as source:
            print("📊 Calibrating for ambient noise (2 seconds)...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"✅ Energy threshold: {recognizer.energy_threshold}")
        
        print("✅ Microphone accessible!")
        return True
    except Exception as e:
        print(f"❌ Microphone test failed: {e}")
        return False

def test_voice_recognition():
    """Test voice recognition with a simple command."""
    print("\n🎙️  Testing voice recognition...")
    print("Say something (e.g., 'next', 'back', 'stop')...")
    
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    try:
        with mic as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Listen for audio
            print("🔴 Listening... (speak now)")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
            print("⏹️  Processing...")
        
        # Recognize speech using Google
        text = recognizer.recognize_google(audio)
        print(f"✅ Recognized: '{text}'")
        return True
        
    except sr.WaitTimeoutError:
        print("⏱️  No speech detected (timeout)")
        return False
    except sr.UnknownValueError:
        print("❓ Could not understand audio")
        return False
    except sr.RequestError as e:
        print(f"❌ Recognition service error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("=" * 60)
    print("Voice Recognition Quick Test")
    print("=" * 60)
    
    # Test 1: Microphone
    if not test_microphone():
        print("\n⚠️  Microphone test failed. Voice commands will not work.")
        return
    
    # Test 2: Recognition
    print("\n" + "=" * 60)
    if test_voice_recognition():
        print("\n🎉 Voice recognition is working!")
        print("\nYou can now use voice commands in the slideshow:")
        print("  - 'next' / 'forward' → Next slide")
        print("  - 'back' / 'previous' → Previous slide")
        print("  - 'stop' / 'pause' → Pause slideshow")
        print("  - 'go' / 'start' → Resume slideshow")
    else:
        print("\n⚠️  Voice recognition test did not complete successfully.")
        print("This may be due to:")
        print("  - No internet connection (Google API requires internet)")
        print("  - Microphone permissions not granted")
        print("  - Background noise interference")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
