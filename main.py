import sys
import os
import threading
import time
import traceback
import signal
import queue

# Add src directory to path
sys.path.append(os.path.abspath('src'))

# Import the PyGame visualizer and Vosk voice detector
from ui_components.pygame_visualizer import PyGameVisualizer
from speech_processing.vosk_detector import VoskVoiceDetector

class SousDev:
    def __init__(self):
        """Initialize the SousDev application"""
        print("Initializing SousDev - Voice Programming Assistant")
        
        # Application state
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Communication between threads
        self.word_queue = queue.Queue(maxsize=100)
        
        # Thread references
        self.voice_thread = None
        self.word_thread = None
        
        try:
            # Initialize the visualizer using PyGame
            self.visualizer = PyGameVisualizer(width=1000, height=500)
            
            # Initialize voice detector using Vosk with default microphone
            self.voice_detector = VoskVoiceDetector(device_index=None)  # Use default microphone
            self.voice_detector.add_talking_callback(self.on_word_recognized)
        except Exception as e:
            print(f"ERROR during initialization: {e}")
            traceback.print_exc()
            raise
    
    def start(self):
        """Start the application"""
        try:
            self.running = True
            self.shutdown_event.clear()
            
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start voice detection in a separate thread
            self.voice_thread = threading.Thread(target=self._run_voice_detection)
            self.voice_thread.daemon = True
            self.voice_thread.start()
            
            # Start word processing in a separate thread
            self.word_thread = threading.Thread(target=self._process_words)
            self.word_thread.daemon = True
            self.word_thread.start()
            
            # Start the visualizer in the main thread
            self.visualizer.run()
        except Exception as e:
            print(f"ERROR during startup: {e}")
            traceback.print_exc()
            raise
        finally:
            # Make sure we clean up properly
            self.stop()
    
    def _run_voice_detection(self):
        """Run voice detection in a separate thread"""
        try:
            self.voice_detector.start()
            print("Voice detection started")
            
            # Keep the thread alive until shutdown
            while self.running and not self.shutdown_event.is_set():
                time.sleep(0.1)
        except Exception as e:
            print(f"ERROR in voice detection thread: {e}")
            traceback.print_exc()
        finally:
            print("Voice detection thread exiting")
    
    def _process_words(self):
        """Process words from the queue and send to visualizer"""
        print("Word processing thread started")
        try:
            while self.running and not self.shutdown_event.is_set():
                try:
                    # Get a word from the queue with timeout
                    word = self.word_queue.get(timeout=0.1)
                    
                    # Send the word to the visualizer
                    if self.running and word:
                        print(f"Processing word: {word}")
                        self.visualizer.set_talking(True, word)
                    
                    # Mark task as done
                    self.word_queue.task_done()
                    
                except queue.Empty:
                    # No words in queue, just continue
                    pass
                except Exception as e:
                    print(f"Error processing word: {e}")
                    traceback.print_exc()
        except Exception as e:
            print(f"ERROR in word processing thread: {e}")
            traceback.print_exc()
        print("Word processing thread stopped")
    
    def on_word_recognized(self, is_talking, text=None):
        """Handle recognized words by adding to queue"""
        try:
            # Add recognized text to the queue
            if text and self.running:
                print(f"Main: Word recognized: {text}")
                try:
                    self.word_queue.put(text, block=False)
                except queue.Full:
                    print("Warning: Word queue is full, dropping word")
        except Exception as e:
            print(f"ERROR in word recognition callback: {e}")
            traceback.print_exc()
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals"""
        print(f"Received signal {sig}, shutting down...")
        self.stop()
    
    def stop(self):
        """Stop the application"""
        if not self.running:
            return
            
        self.running = False
        self.shutdown_event.set()
        
        try:
            # Stop components in reverse order
            print("Stopping components...")
            
            try:
                if hasattr(self, 'voice_detector'):
                    self.voice_detector.stop()
                    print("Voice detector stopped")
            except Exception as e:
                print(f"Error stopping voice detector: {e}")
                traceback.print_exc()
                
            try:
                if hasattr(self, 'visualizer'):
                    self.visualizer.stop()
                    print("Visualizer stopped")
            except Exception as e:
                print(f"Error stopping visualizer: {e}")
                traceback.print_exc()
            
            # Wait for threads to terminate
            if self.voice_thread and self.voice_thread.is_alive():
                print("Waiting for voice thread to terminate...")
                self.voice_thread.join(timeout=2)
                if self.voice_thread.is_alive():
                    print("Voice thread did not terminate cleanly")
                else:
                    print("Voice thread terminated")
            
            if self.word_thread and self.word_thread.is_alive():
                print("Waiting for word thread to terminate...")
                self.word_thread.join(timeout=2)
                if self.word_thread.is_alive():
                    print("Word thread did not terminate cleanly")
                else:
                    print("Word thread terminated")
                
            print("SousDev stopped")
        except Exception as e:
            print(f"ERROR during shutdown: {e}")
            traceback.print_exc()

def main():
    """Main entry point for the application"""
    app = None
    
    try:
        # Create and start the SousDev application
        app = SousDev()
        
        try:
            app.start()
        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            if app:
                app.stop()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 