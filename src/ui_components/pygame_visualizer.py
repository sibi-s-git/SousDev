import pygame
import pygame.gfxdraw  # For anti-aliased shapes
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
        
        # Additional environment variables for smooth rendering
        os.environ['SDL_HINT_RENDER_DRIVER'] = 'opengl'  # Use hardware acceleration
        os.environ['SDL_HINT_RENDER_VSYNC'] = '1'  # Enable vsync for smooth animation
        
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
            text: Complete phrase or sentence from speech recognition
        """
        # Only care about text, not talking state
        if text and text.strip() and self.running:
            print(f"Visualizer received phrase: {text}")
            
            # Add complete phrase to the queue for processing in the main thread
            try:
                self.word_queue.put(text.strip(), block=False)
            except queue.Full:
                print("Warning: Phrase queue is full, dropping phrase")
    
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
            
            # Set up the display with hardware acceleration and double buffering
            try:
                # Try hardware surface with double buffering for best performance
                self.screen = pygame.display.set_mode(
                    (self.width, self.height), 
                    pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.ANYFORMAT
                )
            except pygame.error:
                try:
                    print("Failed to create hardware surface, trying software with double buffering")
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height), 
                        pygame.DOUBLEBUF
                    )
                except pygame.error:
                    print("Failed to create double buffered surface, using basic mode")
                    self.screen = pygame.display.set_mode((self.width, self.height))
                
            pygame.display.set_caption("SousDev - Voice Programming Assistant")
            
            # Create a clock to control frame rate
            self.clock = pygame.time.Clock()
            self.fps = 60  # Higher FPS for smooth animation
            
            # Set up colors
            self.WHITE = (255, 255, 255)
            self.BLACK = (0, 0, 0)
            self.RED = (255, 50, 50)
            self.GREEN = (50, 255, 50)
            self.BLUE = (50, 150, 255)
            self.LIGHT_GRAY = (220, 220, 220)
            self.DARK_GRAY = (100, 100, 100)
            self.BUTTON_COLOR = (70, 130, 255)
            self.BUTTON_HOVER = (90, 150, 255)
            
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
            self.transcript = []  # List of complete spoken phrases/sentences
            self.max_words_per_line = 8  # Fewer words per line to prevent overflow
            self.max_lines = 6  # More lines to display more text
            self.line_spacing = 30  # Smaller spacing between lines
            self.font_size = 24  # Smaller font size to fit more text
            self.max_line_width = self.width - 100  # Maximum width for a line of text
            
            # Input box properties
            self.input_box_height = 120
            self.input_box_y = self.height - self.input_box_height - 10
            self.input_box_x = 50
            self.input_box_width = self.width - 200
            self.input_text = ""
            self.input_lines = [""]  # List of lines in the input box
            self.input_cursor_pos = 0
            self.input_active = False
            self.input_scroll = 0  # For scrolling through input lines
            self.max_input_lines = 4  # Max visible lines in input box
            
            # Send button properties
            self.button_width = 100
            self.button_height = 40
            self.button_x = self.width - 130
            self.button_y = self.height - 60
            self.button_hovered = False
            
            # Animation flags
            self.new_word_recognized = False
            self.should_bounce = False
            self.bounce_frames = 0
            self.max_bounce_frames = 15  # Even fewer frames for stability
            
            # Pre-create font to avoid creating it during rendering
            try:
                # Try to use a nice font, fallback to system default
                font_options = ['arial', 'helvetica', 'calibri', 'segoeui', None]
                self.font = None
                for font_name in font_options:
                    try:
                        self.font = pygame.font.SysFont(font_name, self.font_size, bold=False)
                        if self.font:
                            break
                    except:
                        continue
                
                # Final fallback if no fonts work
                if not self.font:
                    self.font = pygame.font.Font(None, self.font_size)
                    
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
                        else:
                            self._handle_keydown(event)
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self._handle_mouse_click(event)
                    elif event.type == pygame.MOUSEMOTION:
                        self._handle_mouse_motion(event)
                
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
        """Process any phrases in the queue"""
        try:
            # Process all available phrases
            phrases_processed = 0
            while not self.word_queue.empty() and phrases_processed < 2:  # Process fewer phrases at once
                phrase = self.word_queue.get(block=False)
                
                try:
                    with self.lock:
                        # Set flag to move the circle
                        self.new_word_recognized = True
                        self.should_bounce = True
                        self.bounce_frames = 0
                        
                        # Pick a random direction when starting to bounce
                        self.direction = random.choice([-1, 1])
                        
                        # Add complete phrase to transcript
                        self._update_transcript(phrase)
                        
                        print(f"Displaying: {phrase}")
                        phrases_processed += 1
                        
                    # Mark the task as done
                    self.word_queue.task_done()
                except Exception as e:
                    print(f"Error processing phrase: {e}")
                    traceback.print_exc()
                
        except queue.Empty:
            pass  # No more phrases to process
        except Exception as e:
            print(f"Error processing phrase queue: {e}")
            traceback.print_exc()
    
    def _update_transcript(self, new_phrase):
        """Update the transcript with complete phrases"""
        try:
            if not self.font:
                return
            
            # Add the complete phrase as a new entry
            phrase_lines = self._wrap_text(new_phrase)
            
            # Add all lines from the phrase
            for line in phrase_lines:
                self.transcript.append(line)
                    
            # Keep only the last max_lines
            if len(self.transcript) > self.max_lines:
                self.transcript = self.transcript[-self.max_lines:]
                
        except Exception as e:
            print(f"Error updating transcript: {e}")
            traceback.print_exc()
    
    def _wrap_text(self, text):
        """Wrap text to fit within the display width"""
        if not self.font or not text:
            return [text] if text else []
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            text_surface = self.font.render(test_line, True, self.BLACK)
            
            if text_surface.get_width() <= self.max_line_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
            
        return lines
    
    def _handle_keydown(self, event):
        """Handle keyboard input for the text box"""
        if not self.input_active:
            # Click to activate input box
            return
            
        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            # Send the message
            self._send_message()
        elif event.key == pygame.K_BACKSPACE:
            # Delete character
            if self.input_text:
                self.input_text = self.input_text[:-1]
                self._update_input_lines()
        elif event.key == pygame.K_UP:
            # Scroll up in input box
            if self.input_scroll > 0:
                self.input_scroll -= 1
        elif event.key == pygame.K_DOWN:
            # Scroll down in input box
            max_scroll = max(0, len(self.input_lines) - self.max_input_lines)
            if self.input_scroll < max_scroll:
                self.input_scroll += 1
        else:
            # Add character to input
            if event.unicode and event.unicode.isprintable():
                self.input_text += event.unicode
                self._update_input_lines()
    
    def _handle_mouse_click(self, event):
        """Handle mouse clicks"""
        mouse_x, mouse_y = event.pos
        
        # Check if clicking on input box
        if (self.input_box_x <= mouse_x <= self.input_box_x + self.input_box_width and
            self.input_box_y <= mouse_y <= self.input_box_y + self.input_box_height):
            self.input_active = True
        # Check if clicking on send button
        elif (self.button_x <= mouse_x <= self.button_x + self.button_width and
              self.button_y <= mouse_y <= self.button_y + self.button_height):
            self._send_message()
        else:
            self.input_active = False
    
    def _handle_mouse_motion(self, event):
        """Handle mouse motion for button hover effects"""
        mouse_x, mouse_y = event.pos
        
        # Check if hovering over send button
        self.button_hovered = (
            self.button_x <= mouse_x <= self.button_x + self.button_width and
            self.button_y <= mouse_y <= self.button_y + self.button_height
        )
    
    def _update_input_lines(self):
        """Update the input lines for word wrapping"""
        if not self.input_text:
            self.input_lines = [""]
            return
            
        self.input_lines = self._wrap_text(self.input_text)
        if not self.input_lines:
            self.input_lines = [""]
    
    def _send_message(self):
        """Send the current input text"""
        if self.input_text.strip():
            # Add to transcript
            self._update_transcript(self.input_text.strip())
            print(f"User typed: {self.input_text.strip()}")
            
            # Clear input
            self.input_text = ""
            self.input_lines = [""]
            self.input_scroll = 0
    
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
            
            # Draw the circle with anti-aliasing
            circle_x, circle_y = int(self.circle_x), int(self.circle_y)
            radius = int(actual_radius)
            
            # Draw filled anti-aliased circle
            pygame.gfxdraw.aacircle(self.screen, circle_x, circle_y, radius, self.circle_color)
            pygame.gfxdraw.filled_circle(self.screen, circle_x, circle_y, radius, self.circle_color)
            
            # Draw anti-aliased outline
            pygame.gfxdraw.aacircle(self.screen, circle_x, circle_y, radius, self.BLACK)
            if radius > 1:
                pygame.gfxdraw.aacircle(self.screen, circle_x, circle_y, radius-1, self.BLACK)
            
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
            
            # Draw input box and send button
            self._render_input_elements()
            
            # Update the display
            try:
                pygame.display.flip()
            except Exception as e:
                print(f"Error flipping display: {e}")
                traceback.print_exc()
                
        except Exception as e:
            print(f"Error in render: {e}")
            traceback.print_exc()
    
    def _render_input_elements(self):
        """Render the input box and send button"""
        try:
            if not self.font:
                return
                
            # Draw input box background
            input_box_rect = pygame.Rect(self.input_box_x, self.input_box_y, 
                                       self.input_box_width, self.input_box_height)
            
            # Input box border color based on active state
            border_color = self.BLUE if self.input_active else self.DARK_GRAY
            
            # Draw input box
            pygame.draw.rect(self.screen, self.WHITE, input_box_rect)
            pygame.draw.rect(self.screen, border_color, input_box_rect, 2)
            
            # Draw input text with scrolling
            if self.input_lines:
                line_height = self.font_size + 2
                start_line = self.input_scroll
                end_line = min(len(self.input_lines), start_line + self.max_input_lines)
                
                for i in range(start_line, end_line):
                    if i < len(self.input_lines):
                        line = self.input_lines[i]
                        text_surface = self.font.render(line, True, self.BLACK)
                        
                        y_pos = self.input_box_y + 10 + (i - start_line) * line_height
                        self.screen.blit(text_surface, (self.input_box_x + 10, y_pos))
            
            # Draw cursor if input is active
            if self.input_active:
                cursor_x = self.input_box_x + 10
                if self.input_lines and len(self.input_lines) > 0:
                    last_line_index = min(len(self.input_lines) - 1, 
                                        self.input_scroll + self.max_input_lines - 1)
                    if last_line_index >= self.input_scroll:
                        last_line = self.input_lines[last_line_index]
                        if last_line:
                            text_surface = self.font.render(last_line, True, self.BLACK)
                            cursor_x += text_surface.get_width()
                        
                        cursor_y = (self.input_box_y + 10 + 
                                  (last_line_index - self.input_scroll) * (self.font_size + 2))
                        
                        # Draw blinking cursor
                        if int(time.time() * 2) % 2:  # Blink every 0.5 seconds
                            pygame.draw.line(self.screen, self.BLACK, 
                                           (cursor_x, cursor_y), 
                                           (cursor_x, cursor_y + self.font_size), 2)
            
            # Draw send button
            button_rect = pygame.Rect(self.button_x, self.button_y, 
                                    self.button_width, self.button_height)
            
            # Button color based on hover state
            button_color = self.BUTTON_HOVER if self.button_hovered else self.BUTTON_COLOR
            
            # Draw button
            pygame.draw.rect(self.screen, button_color, button_rect)
            pygame.draw.rect(self.screen, self.WHITE, button_rect, 2)
            
            # Draw button text
            button_text = self.font.render("Send", True, self.WHITE)
            text_rect = button_text.get_rect(center=button_rect.center)
            self.screen.blit(button_text, text_rect)
            
            # Draw scroll indicators if needed
            if len(self.input_lines) > self.max_input_lines:
                # Up arrow if can scroll up
                if self.input_scroll > 0:
                    arrow_x = self.input_box_x + self.input_box_width - 20
                    arrow_y = self.input_box_y + 10
                    pygame.draw.polygon(self.screen, self.DARK_GRAY, 
                                      [(arrow_x, arrow_y + 10), 
                                       (arrow_x + 10, arrow_y + 10),
                                       (arrow_x + 5, arrow_y)])
                
                # Down arrow if can scroll down
                max_scroll = len(self.input_lines) - self.max_input_lines
                if self.input_scroll < max_scroll:
                    arrow_x = self.input_box_x + self.input_box_width - 20
                    arrow_y = self.input_box_y + self.input_box_height - 20
                    pygame.draw.polygon(self.screen, self.DARK_GRAY, 
                                      [(arrow_x, arrow_y), 
                                       (arrow_x + 10, arrow_y),
                                       (arrow_x + 5, arrow_y + 10)])
                
        except Exception as e:
            print(f"Error rendering input elements: {e}")
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