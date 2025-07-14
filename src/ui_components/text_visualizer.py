import threading
import time
import queue
import os
import sys
import traceback

class TextVisualizer:
    """
    A simple text-based visualizer that displays recognized words in the terminal.
    This is a fallback for when PyGame causes segmentation faults.
    """
    
    def __init__(self, width=80, height=20):
        """
        Initialize the text visualizer
        
        Args:
            width: Width of the display area in characters
            height: Height of the display area in characters
        """
        # Thread safety and communication
        self.word_queue = queue.Queue()
        self.running = False
        self.lock = threading.RLock()
        
        # Configuration
        self.width = width
        self.height = height
        
        # Words storage
        self.words = []
        self.max_words = 100  # Maximum number of words to store
        
        print("Text visualizer initialized")
    
    def set_talking(self, is_talking, text=None):
        """
        Update recognized text
        
        Args:
            is_talking: Boolean indicating if the user is talking (ignored)
            text: Recognized text from speech recognition
        """
        # Only care about text, not talking state
        if text and text.strip() and self.running:
            print(f"Visualizer received word: {text}")
            
            # Add word to the queue for processing in the main thread
            try:
                self.word_queue.put(text.strip(), block=False)
            except queue.Full:
                print("Warning: Word queue is full, dropping word")
    
    def stop(self):
        """Stop the visualization"""
        print("Text visualizer stopping...")
        
        with self.lock:
            self.running = False
        
        print("Text visualizer stopped")
    
    def run(self):
        """Run the visualization in the main thread"""
        try:
            print("\n" + "="*self.width)
            print("Text Visualizer Started - Press Ctrl+C to exit")
            print("="*self.width)
            print("Speak to see words appear below:")
            print("-"*self.width + "\n")
            
            # Start the main loop
            with self.lock:
                self.running = True
                
            self._main_loop()
            
        except KeyboardInterrupt:
            print("\nVisualization stopped by user")
        except Exception as e:
            print(f"Error in text visualizer: {e}")
            traceback.print_exc()
        finally:
            # Make sure we clean up
            with self.lock:
                self.running = False
            
            print("\n" + "="*self.width)
            print("Text Visualizer Stopped")
            print("="*self.width)
    
    def _main_loop(self):
        """Main loop for the text visualizer"""
        try:
            while True:
                # Check if we should exit
                with self.lock:
                    if not self.running:
                        break
                
                # Process any words in the queue
                self._process_word_queue()
                
                # Render the current state
                self._render()
                
                # Small delay to prevent CPU usage
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error in main loop: {e}")
            traceback.print_exc()
            with self.lock:
                self.running = False
    
    def _process_word_queue(self):
        """Process any words in the queue"""
        try:
            # Process all available words
            words_processed = 0
            while not self.word_queue.empty() and words_processed < 10:  # Process up to 10 words at once
                word = self.word_queue.get(block=False)
                
                try:
                    with self.lock:
                        # Add word to the list
                        self.words.append(word)
                        
                        # If we have more words than the limit, remove oldest
                        if len(self.words) > self.max_words:
                            self.words = self.words[-self.max_words:]
                        
                        words_processed += 1
                    
                    # Mark task as done
                    self.word_queue.task_done()
                except Exception as e:
                    print(f"Error processing word: {e}")
                    traceback.print_exc()
                
        except queue.Empty:
            pass  # No more words to process
        except Exception as e:
            print(f"Error processing word queue: {e}")
            traceback.print_exc()
    
    def _render(self):
        """Render the current state to the terminal"""
        try:
            with self.lock:
                # Only render if we have words
                if not self.words:
                    return
                
                # Create a formatted string of all words
                text = " ".join(self.words)
                
                # Clear the terminal (platform-specific)
                if os.name == 'nt':  # For Windows
                    os.system('cls')
                else:  # For Unix/Linux/MacOS
                    os.system('clear')
                
                print("\n" + "="*self.width)
                print("Text Visualizer - Press Ctrl+C to exit")
                print("="*self.width)
                print("Recognized Speech:")
                print("-"*self.width)
                
                # Print the text, wrapped to the width
                for i in range(0, len(text), self.width - 10):
                    print(text[i:i + self.width - 10])
                
                print("\n" + "-"*self.width)
                print(f"Total words: {len(self.words)}")
                print("="*self.width)
                
        except Exception as e:
            print(f"Error in render: {e}")
            traceback.print_exc()

# Only used for testing the visualizer directly
if __name__ == "__main__":
    # Create and run the visualizer
    visualizer = TextVisualizer()
    
    # Start a thread to simulate speech recognition
    def simulate_speech():
        words = ["Hello", "world", "this", "is", "a", "test", "of", "the", "voice", 
                "recognition", "system", "with", "many", "words"]
        
        time.sleep(2)  # Wait for initialization
        
        for word in words:
            if not visualizer.running:
                break
            visualizer.set_talking(True, word)
            time.sleep(0.5)
    
    speech_thread = threading.Thread(target=simulate_speech)
    speech_thread.daemon = True
    speech_thread.start()
    
    try:
        # Run the visualizer
        visualizer.run()
    finally:
        # Make sure to clean up
        visualizer.stop() 