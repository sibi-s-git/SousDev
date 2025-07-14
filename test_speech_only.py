import sys
import os
import threading
import time
import traceback
import signal

# Add src directory to path
sys.path.append(os.path.abspath('src'))

# Import only the voice detector
from speech_processing.voice_detector import VoiceActivityDetector

def on_word_recognized(is_talking, text=None):
    """Simple callback to print recognized words"""
    if text:
        print(f"WORD RECOGNIZED: '{text}'")

def main():
    """Main entry point for the test application"""
    print("Starting speech recognition test (no visualization)")
    
    # Initialize the voice detector
    detector = None
    try:
        # Create the voice detector
        detector = VoiceActivityDetector()
        detector.add_talking_callback(on_word_recognized)
        
        # Start the detector
        detector.start()
        
        print("Speech recognition started. Speak into the microphone.")
        print("Press Ctrl+C to exit.")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
    finally:
        # Clean up
        if detector:
            print("Stopping voice detector...")
            detector.stop()
            print("Voice detector stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 