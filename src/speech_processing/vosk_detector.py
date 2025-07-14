import threading
import time
import queue
import traceback
import json
import pyaudio
import os
import re
import subprocess
from vosk import Model, KaldiRecognizer
from collections import deque

class VoskVoiceDetector:
    def __init__(self, model_name="vosk-model-en-us-0.22", device_index=None, output_widget=None):
        """
        Voice detector using Vosk for speech recognition.
        
        Args:
            model_name: Name of the Vosk model to use
            device_index: Index of the audio device to use (None for default)
            output_widget: Optional IPython output widget for Jupyter notebooks
        """
        # Audio settings
        self.channels = 1
        self.frame_rate = 16000
        self.audio_format = pyaudio.paInt16
        self.chunk_size = 1024
        self.device_index = device_index
        
        # Initialize Vosk model
        self.model_path = self._ensure_model(model_name)
        self.model = Model(model_path=self.model_path)
        self.recognizer = KaldiRecognizer(self.model, self.frame_rate)
        self.recognizer.SetWords(True)  # Enable word timestamps
        self.recognizer.SetPartialWords(True)  # Enable partial results with word timestamps
        
        # State
        self.running = False
        self.callbacks = []
        self.callback_lock = threading.Lock()
        self.stop_event = threading.Event()
        
        # Thread management
        self.recording_thread = None
        self.recognition_thread = None
        
        # Communication queues (for both standard and Jupyter modes)
        self.messages = queue.Queue()  # Control messages for Jupyter mode
        self.recordings = queue.Queue()  # Audio recordings for Jupyter mode
        self.audio_queue = queue.Queue(maxsize=1000)  # For standard mode
        
        # Word history
        self.word_history = deque(maxlen=1000)
        self.word_lock = threading.Lock()
        
        # PyAudio instance
        self.audio = None
        self.stream = None
        
        # Word tracking
        self.last_processed_words = set()
        self.last_partial_words = set()
        
        # Last text results
        self.last_full_text = ""
        self.last_partial_text = ""
        
        # Output widget for Jupyter notebooks
        self.output_widget = output_widget
        
        # Transcript for Jupyter mode
        self.transcript = []
        self.max_transcript_lines = 20  # Maximum number of lines to keep in transcript
        
        # Print available microphones to help with debugging
        print("Available microphones:")
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                print(f"  {i}: {dev_info['name']} (Input Channels: {dev_info['maxInputChannels']})")
        p.terminate()
    
    def _ensure_model(self, model_name):
        """Ensure the Vosk model exists, return path to model"""
        # Check if model exists in current directory
        if os.path.isdir(model_name):
            return model_name
            
        # Check if model exists in home directory
        home_model_path = os.path.join(os.path.expanduser("~"), ".cache", "vosk", model_name)
        if os.path.isdir(home_model_path):
            return home_model_path
            
        # If model doesn't exist, return the name and let Vosk download it
        return model_name
    
    # Standard mode methods
    def start(self):
        """Start voice detection in standard mode"""
        if self.running:
            return
            
        self.running = True
        self.stop_event.clear()
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self._recording_loop)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        # Start recognition thread
        self.recognition_thread = threading.Thread(target=self._recognition_loop)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
        
        print("Voice detection started")
    
    def stop(self):
        """Stop voice detection"""
        if not self.running:
            return
            
        print("Stopping voice detection...")
        self.running = False
        self.stop_event.set()
        
        # For Jupyter mode, clear the control message
        if not self.messages.empty():
            self.messages.get()
        
        # Close audio stream if it's open
        self._close_audio_stream()
        
        # Wait for threads to terminate
        if self.recording_thread and self.recording_thread.is_alive():
            print("Waiting for recording thread to terminate...")
            self.recording_thread.join(timeout=2)
            if self.recording_thread.is_alive():
                print("Recording thread did not terminate cleanly")
            else:
                print("Recording thread terminated")
            self.recording_thread = None
            
        if self.recognition_thread and self.recognition_thread.is_alive():
            print("Waiting for recognition thread to terminate...")
            self.recognition_thread.join(timeout=2)
            if self.recognition_thread.is_alive():
                print("Recognition thread did not terminate cleanly")
            else:
                print("Recognition thread terminated")
            self.recognition_thread = None
            
        print("Voice detection stopped")
    
    def _close_audio_stream(self):
        """Safely close audio stream and PyAudio instance"""
        try:
            if self.stream:
                try:
                    self.stream.stop_stream()
                except Exception as e:
                    print(f"Error stopping stream: {e}")
                
                try:
                    self.stream.close()
                except Exception as e:
                    print(f"Error closing stream: {e}")
                
                self.stream = None
                
            if self.audio:
                try:
                    self.audio.terminate()
                except Exception as e:
                    print(f"Error terminating PyAudio: {e}")
                
                self.audio = None
        except Exception as e:
            print(f"Error during audio cleanup: {e}")
            traceback.print_exc()
    
    def add_talking_callback(self, callback):
        """Add a callback function that will be called when speech is recognized"""
        with self.callback_lock:
            self.callbacks.append(callback)
    
    def _notify_callbacks(self, text):
        """Notify all callbacks about recognized text"""
        if text and self.running:
            print(f"RECOGNIZED: {text}")
            with self.callback_lock:
                callbacks_copy = self.callbacks.copy()
            
            for callback in callbacks_copy:
                try:
                    callback(True, text)
                except Exception as e:
                    print(f"Error in callback: {e}")
                    traceback.print_exc()
    
    def _recording_loop(self):
        """Main recording loop for standard mode"""
        retry_count = 0
        max_retries = 3
        retry_delay = 1.0
        
        while self.running and not self.stop_event.is_set() and retry_count < max_retries:
            try:
                # Create PyAudio instance
                self.audio = pyaudio.PyAudio()
                
                # Open audio stream
                self.stream = self.audio.open(
                    format=self.audio_format,
                    channels=self.channels,
                    rate=self.frame_rate,
                    input=True,
                    input_device_index=self.device_index,
                    frames_per_buffer=self.chunk_size
                )
                
                print("Recording started. Speak into the microphone.")
                retry_count = 0
                
                # Record audio in chunks and add to queue
                while self.running and not self.stop_event.is_set():
                    try:
                        data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                        if not self.audio_queue.full():
                            self.audio_queue.put(data, block=False)
                        else:
                            # Queue is full, discard oldest data
                            try:
                                self.audio_queue.get_nowait()
                                self.audio_queue.put(data, block=False)
                            except queue.Empty:
                                pass
                    except OSError as e:
                        if "Stream closed" in str(e):
                            print("Audio stream closed, reopening...")
                            break
                        else:
                            print(f"Error reading audio: {e}")
                            time.sleep(0.1)  # Small delay before retry
                    except Exception as e:
                        print(f"Error reading audio: {e}")
                        traceback.print_exc()
                        time.sleep(0.1)  # Prevent rapid error loops
                
                # Clean up
                self._close_audio_stream()
                
            except Exception as e:
                print(f"Error in recording loop: {e}")
                traceback.print_exc()
                
                # Clean up any resources
                self._close_audio_stream()
                
                # Retry logic
                retry_count += 1
                if retry_count < max_retries and self.running and not self.stop_event.is_set():
                    print(f"Retrying audio setup in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
            
        print("Recording loop stopped")
    
    def _recognition_loop(self):
        """Main recognition loop for standard mode"""
        try:
            print("Recognition started")
            last_partial_text = ""
            
            while self.running and not self.stop_event.is_set():
                try:
                    # Get audio data from queue with timeout
                    try:
                        data = self.audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    
                    # Process audio data - ONLY use partial results
                    # Add the data to the recognizer but don't use the return value
                    self.recognizer.AcceptWaveform(data)
                    
                    # Get partial results
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get("partial", "")
                    
                    # Process partial results for real-time updates
                    if partial_text and partial_text != last_partial_text:
                        # Find new words that might have been added
                        new_words = partial_text.split()
                        last_words = last_partial_text.split() if last_partial_text else []
                        
                        # If we have more words now than before
                        if len(new_words) > len(last_words):
                            # Process the newly added words
                            for i in range(len(last_words), len(new_words)):
                                if new_words[i].strip():
                                    word = new_words[i].strip()
                                    self._notify_callbacks(word)
                        
                        last_partial_text = partial_text
                    
                except Exception as e:
                    print(f"Error processing audio: {e}")
                    traceback.print_exc()
                    time.sleep(0.1)  # Prevent rapid error loops
            
        except Exception as e:
            print(f"Error in recognition thread: {e}")
            traceback.print_exc()
        finally:
            print("Recognition thread stopped")
    
    # Jupyter notebook specific methods
    def start_jupyter(self, output_widget=None):
        """Start recording and speech recognition for Jupyter notebook"""
        if output_widget:
            self.output_widget = output_widget
            
        # Clear any existing messages
        while not self.messages.empty():
            self.messages.get()
            
        # Add control message
        self.messages.put(True)
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self.record_microphone_jupyter)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        # Start recognition thread
        self.recognition_thread = threading.Thread(target=self.speech_recognition_jupyter)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
        
        if self.output_widget:
            self.output_widget.append_stdout("Speech recognition started. Speak into the microphone.\n")
        else:
            print("Speech recognition started. Speak into the microphone.")
    
    def record_microphone_jupyter(self, seconds_per_chunk=1):
        """Record audio from the microphone in chunks for Jupyter notebook"""
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.frame_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            chunks_per_second = self.frame_rate / self.chunk_size
            chunks_per_recording = int(chunks_per_second * seconds_per_chunk)
            
            while not self.messages.empty():
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Process in chunks
                    if len(frames) >= chunks_per_recording:
                        self.recordings.put(frames.copy())
                        frames = []
                except Exception as e:
                    print(f"Error recording audio: {e}")
                    time.sleep(0.1)  # Small delay before retry
            
        except Exception as e:
            print(f"Error in recording thread: {e}")
            traceback.print_exc()
        finally:
            # Clean up
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
            
            try:
                p.terminate()
            except:
                pass
    
    def speech_recognition_jupyter(self):
        """Process recorded audio and perform speech recognition for Jupyter notebook"""
        last_partial_text = ""
        
        while not self.messages.empty():
            try:
                # Get frames from the recordings queue
                frames = self.recordings.get(timeout=1.0)
                
                # Process the audio data - add to recognizer but don't use return value
                audio_data = b''.join(frames)
                self.recognizer.AcceptWaveform(audio_data)
                
                # ONLY process partial results
                partial_result = self.recognizer.PartialResult()
                partial = json.loads(partial_result)
                partial_text = partial.get("partial", "")
                
                # Process partial results for real-time updates
                if partial_text and partial_text != last_partial_text:
                    # Find new words that might have been added
                    new_words = partial_text.split()
                    last_words = last_partial_text.split() if last_partial_text else []
                    
                    # If we have more words now than before
                    if len(new_words) > len(last_words):
                        # Process the newly added words
                        for i in range(len(last_words), len(new_words)):
                            if new_words[i].strip():
                                self._process_jupyter_word(new_words[i].strip())
                    
                    last_partial_text = partial_text
                
            except Exception as e:
                if "Empty" not in str(e):  # Ignore timeout exceptions
                    print(f"Error in recognition thread: {e}")
                    traceback.print_exc()
    
    def _process_jupyter_word(self, word):
        """Process a single word for Jupyter notebook output"""
        # Add to transcript
        if self.transcript:
            self.transcript[-1] = self.transcript[-1] + " " + word
        else:
            self.transcript.append(word)
            
        # Keep only the last max_transcript_lines
        if len(self.transcript) > self.max_transcript_lines:
            self.transcript = self.transcript[-self.max_transcript_lines:]
        
        # Display the updated transcript
        if self.output_widget:
            self.output_widget.clear_output()
            full_transcript = "\n".join(self.transcript)
            self.output_widget.append_stdout(full_transcript)
        else:
            print(word)
        
        # Also notify standard callbacks
        self._notify_callbacks(word)

# Simple test
if __name__ == "__main__":
    detector = VoskVoiceDetector()
    
    def on_talking_change(is_talking, text=None):
        if text:
            print(f"WORD RECOGNIZED: '{text}'")
    
    detector.add_talking_callback(on_talking_change)
    detector.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        detector.stop() 