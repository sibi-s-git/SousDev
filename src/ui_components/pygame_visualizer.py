import pygame
import time
import sys
import random
import threading
import queue
import os
import traceback

class PyGameVisualizer:
    def __init__(self, width=1000, height=500):
        """
        Creates a visualization of a circle bouncing on a line when talking.
        
        Args:
            width: Width of the window
            height: Height of the window
        """
        # Thread safety and communication
        self.word_queue = queue.Queue(maxsize=100)
        self.running = False
        self.initialized = False
        self.lock = threading.RLock()
        
        # Configuration
        self.width = width
        self.height = height
        
        # Set environment variables for PyGame
        os.environ['SDL_VIDEO_CENTERED'] = '1'  # Center the window
        os.environ['SDL_AUDIODRIVER'] = 'dummy'  # Disable audio to prevent conflicts
        
        # Prevent PyGame from using too much CPU
        os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0'
        
        # Additional environment variables to prevent segfaults
        os.environ['SDL_HINT_RENDER_DRIVER'] = 'software'  # Use software renderer
        os.environ['SDL_HINT_RENDER_VSYNC'] = '0'  # Disable vsync
        
        # PyGame resources
        self.screen = None
        self.font = None
        self.clock = None
        
        print("PyGame visualizer initialized")
    
    def set_talking(self, is_talking, text=None):
        """
        Update recognized text and trigger animation
        
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
        print("PyGame visualizer stopping...")
        
        with self.lock:
            self.running = False
        
        # Give time for the main loop to clean up
        time.sleep(0.5)
        
        # Force quit pygame if it was initialized
        if self.initialized:
            try:
                # Clean up resources in the correct order
                if self.font:
                    del self.font
                    self.font = None
                
                if self.screen:
                    del self.screen
                    self.screen = None
                
                if self.clock:
                    del self.clock
                    self.clock = None
                
                # Finally quit pygame
                pygame.quit()
                
                # Reset initialization flag
                self.initialized = False
            except Exception as e:
                print(f"Error quitting PyGame: {e}")
                traceback.print_exc()
                
        print("PyGame visualizer stopped")
    
    def run(self):
        """Run the visualization in the main thread"""
        try:
            # Initialize pygame here in the main thread
            pygame.init()
            self.initialized = True
            
            # Set up the display with a lower resolution for stability
            try:
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.HWSURFACE | pygame.DOUBLEBUF)
            except pygame.error:
                print("Failed to create hardware surface, falling back to software")
                self.screen = pygame.display.set_mode((self.width, self.height))
                
            pygame.display.set_caption("SousDev - Voice Programming Assistant")
            
            # Create a clock to control frame rate
            self.clock = pygame.time.Clock()
            self.fps = 30  # Lower FPS for stability
            
            # Set up colors
            self.WHITE = (255, 255, 255)
            self.BLACK = (0, 0, 0)
            self.RED = (255, 50, 50)
            self.GREEN = (50, 255, 50)
            self.BLUE = (50, 150, 255)
            
            # Line properties
            self.line_y = self.height // 2  # Center of the screen
            self.line_start_x = 50
            self.line_end_x = self.width - 50
            
            # Circle properties
            self.circle_radius = 25
            self.circle_x = self.width // 2  # Start in the middle
            self.circle_y = self.line_y  # Position exactly on the line
            self.circle_color = self.WHITE
            
            # Movement properties
            self.direction = 1  # 1 = right, -1 = left
            self.base_speed = 5  # Even slower speed for stability
            self.speed = self.base_speed
            
            # Reactivity properties
            self.pulse_size = 0
            self.max_pulse_size = 5  # Smaller pulse for stability
            self.pulse_direction = 1
            
            # Text display properties
            self.words = []  # List of all words to display
            self.transcript = []  # List of full text lines
            self.max_words_per_line = 8  # Fewer words per line to prevent overflow
            self.max_lines = 6  # More lines to display more text
            self.line_spacing = 30  # Smaller spacing between lines
            self.font_size = 24  # Smaller font size to fit more text
            self.max_line_width = self.width - 100  # Maximum width for a line of text
            
            # Animation flags
            self.new_word_recognized = False
            self.should_bounce = False
            self.bounce_frames = 0
            self.max_bounce_frames = 15  # Even fewer frames for stability
            
            # Pre-create font to avoid creating it during rendering
            try:
                self.font = pygame.font.SysFont(None, self.font_size)
            except pygame.error as e:
                print(f"Error creating font: {e}")
                self.font = None
            
            print("PyGame visualizer started")
            print("Speak to see words appear! (Press ESC to exit)")
            
            # Start the main loop
            with self.lock:
                self.running = True
                
            self._main_loop()
            
        except Exception as e:
            print(f"Error initializing PyGame: {e}")
            traceback.print_exc()
        finally:
            # Make sure pygame is properly shut down
            with self.lock:
                self.running = False
                
            try:
                # Clean up resources in the correct order
                if self.font:
                    del self.font
                    self.font = None
                
                if self.screen:
                    del self.screen
                    self.screen = None
                
                if self.clock:
                    del self.clock
                    self.clock = None
                
                pygame.quit()
                self.initialized = False
            except Exception as e:
                print(f"Error quitting PyGame: {e}")
                traceback.print_exc()
    
    def _main_loop(self):
        """Main rendering loop"""
        try:
            last_render_time = time.time()
            frame_interval = 1.0 / self.fps
            
            while True:
                # Check if we should exit
                with self.lock:
                    if not self.running:
                        break
                        
                # Process events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        with self.lock:
                            self.running = False
                        break
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            with self.lock:
                                self.running = False
                            break
                
                # Process any words in the queue
                self._process_word_queue()
                
                # Update state
                self._update()
                
                # Only render at the specified FPS
                current_time = time.time()
                if current_time - last_render_time >= frame_interval:
                    # Render
                    self._render()
                    last_render_time = current_time
                else:
                    # Sleep to reduce CPU usage
                    time.sleep(0.001)
                
                # Control frame rate (use try/except to avoid crashes)
                try:
                    self.clock.tick(self.fps)
                except Exception as e:
                    print(f"Error in clock tick: {e}")
                    # Don't crash on clock errors, just add a small delay
                    time.sleep(frame_interval)
                
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
            while not self.word_queue.empty() and words_processed < 3:  # Process fewer words at once for stability
                word = self.word_queue.get(block=False)
                
                try:
                    with self.lock:
                        # Set flag to move the circle
                        self.new_word_recognized = True
                        self.should_bounce = True
                        self.bounce_frames = 0
                        
                        # Pick a random direction when starting to bounce
                        self.direction = random.choice([-1, 1])
                        
                        # Add word to the list
                        self.words.append(word)
                        
                        # Update transcript with word wrapping
                        self._update_transcript(word)
                        
                        print(f"Current words: {self.words}")
                        words_processed += 1
                        
                    # Mark the task as done
                    self.word_queue.task_done()
                except Exception as e:
                    print(f"Error processing word: {e}")
                    traceback.print_exc()
                
        except queue.Empty:
            pass  # No more words to process
        except Exception as e:
            print(f"Error processing word queue: {e}")
            traceback.print_exc()
    
    def _update_transcript(self, new_word):
        """Update the transcript with proper word wrapping"""
        try:
            if not self.font:
                return
            
            # Split the incoming text into individual words
            words_to_add = new_word.split()
            
            # Process each word
            for word in words_to_add:
                # If we have no lines yet, start a new one
                if not self.transcript:
                    self.transcript.append(word)
                    continue
                    
                # Try to add to the last line
                last_line = self.transcript[-1]
                test_line = last_line + " " + word
                
                # Check if adding the word would make the line too wide
                text_surface = self.font.render(test_line, True, self.BLACK)
                if text_surface.get_width() <= self.max_line_width:
                    # Word fits on the current line
                    self.transcript[-1] = test_line
                else:
                    # Word doesn't fit, start a new line
                    self.transcript.append(word)
                    
            # Keep only the last max_lines
            if len(self.transcript) > self.max_lines:
                self.transcript = self.transcript[-self.max_lines:]
                
        except Exception as e:
            print(f"Error updating transcript: {e}")
            traceback.print_exc()
    
    def _update(self):
        """Update the circle position and color"""
        try:
            with self.lock:
                if self.new_word_recognized:
                    # Reset the flag but keep bouncing
                    self.new_word_recognized = False
                    
                    # Set color to red when new word recognized
                    self.circle_color = self.RED
                    
                    # Update pulse effect
                    self.pulse_size += self.pulse_direction
                    if self.pulse_size >= self.max_pulse_size:
                        self.pulse_direction = -1
                    elif self.pulse_size <= 0:
                        self.pulse_direction = 1
                        
                # Handle bouncing animation when words are recognized
                if self.should_bounce:
                    # When bouncing: move left and right with increasing speed
                    self.circle_x += self.direction * self.speed
                    
                    # Bounce when hitting edges
                    if self.circle_x > self.line_end_x - self.circle_radius:
                        self.circle_x = self.line_end_x - self.circle_radius
                        self.direction = -1
                        # Increase speed slightly on bounce
                        self.speed = min(self.speed * 1.1, self.base_speed * 1.5)  # Less speed increase for stability
                    elif self.circle_x < self.line_start_x + self.circle_radius:
                        self.circle_x = self.line_start_x + self.circle_radius
                        self.direction = 1
                        # Increase speed slightly on bounce
                        self.speed = min(self.speed * 1.1, self.base_speed * 1.5)  # Less speed increase for stability
                        
                    # Set color to red when bouncing
                    self.circle_color = self.RED
                    
                    # Count frames and stop bouncing after max_bounce_frames
                    self.bounce_frames += 1
                    if self.bounce_frames >= self.max_bounce_frames:
                        self.should_bounce = False
                        self.bounce_frames = 0
                        self.speed = self.base_speed
                        
                        # Return to center when done bouncing
                        center_x = self.width // 2
                        self.circle_x = center_x
                        self.circle_color = self.WHITE
                else:
                    # Reset pulse when not bouncing
                    self.pulse_size = 0
        except Exception as e:
            print(f"Error in update: {e}")
            traceback.print_exc()
    
    def _render(self):
        """Render the current state to the screen"""
        try:
            if not self.running or not self.initialized or not self.screen:
                return
                
            # Fill the background
            self.screen.fill(self.WHITE)
            
            # Draw the horizontal line
            pygame.draw.line(
                self.screen, self.BLACK, 
                (self.line_start_x, self.line_y), (self.line_end_x, self.line_y), 
                width=3
            )
            
            # Calculate actual circle radius with pulse effect
            actual_radius = self.circle_radius + self.pulse_size
            
            # Draw the circle
            pygame.draw.circle(
                self.screen, self.circle_color,
                (int(self.circle_x), int(self.circle_y)), 
                int(actual_radius)
            )
            
            # Draw a black outline around the circle
            pygame.draw.circle(
                self.screen, self.BLACK,
                (int(self.circle_x), int(self.circle_y)), 
                int(actual_radius), width=2
            )
            
            # Draw recognized words above the line
            with self.lock:
                transcript_lines = self.transcript.copy()  # Make a copy to avoid changes during rendering
                
            if transcript_lines and self.font:
                try:
                    # Calculate starting position for the first line
                    # Position text higher up to make room for more lines
                    start_y = self.line_y - 80 - ((len(transcript_lines) - 1) * self.line_spacing)
                    
                    # Draw each line
                    for i, line in enumerate(transcript_lines):
                        # Render the text
                        text_surface = self.font.render(line, True, self.BLACK)
                        
                        # Center the text horizontally
                        text_width = text_surface.get_width()
                        text_x = (self.width - text_width) // 2
                        
                        # Draw the text
                        self.screen.blit(text_surface, (text_x, start_y + i * self.line_spacing))
                except Exception as e:
                    print(f"Error rendering text: {e}")
                    traceback.print_exc()
            
            # Update the display
            try:
                pygame.display.flip()
            except Exception as e:
                print(f"Error flipping display: {e}")
                traceback.print_exc()
                
        except Exception as e:
            print(f"Error in render: {e}")
            traceback.print_exc()

# Only used for testing the visualizer directly
if __name__ == "__main__":
    # Create and run the visualizer
    visualizer = PyGameVisualizer()
    
    # Start a thread to simulate speech recognition
    def simulate_speech():
        words = ["Hello", "world", "this", "is", "a", "test", "of", "the", "voice", 
                "recognition", "system", "with", "many", "words"]
        
        time.sleep(2)  # Wait for pygame to initialize
        
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