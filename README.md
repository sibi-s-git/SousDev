# SousDev - Real-time Speech Visualization

SousDev is a real-time speech recognition and visualization tool that displays recognized words with animated circles in PyGame. It uses the Vosk speech recognition library for accurate, low-latency speech detection.

## Features

- Real-time speech recognition with Vosk
- Word-by-word visualization as you speak
- Animated PyGame interface with bouncing circles
- Text-based visualization fallback option
- Jupyter notebook integration

## Requirements

- Python 3.6+
- PyAudio
- Vosk
- PyGame
- Vosk speech recognition model

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/SousDev.git
cd SousDev
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Download the Vosk model (if not already present):
```bash
python download_model.py
```

## Usage

Run the main application:
```bash
python main.py
```

For speech recognition only (no visualization):
```bash
python test_speech_only.py
```

## Jupyter Notebook Integration

SousDev can also be used in Jupyter notebooks. Example:

```python
import ipywidgets as widgets
from IPython.display import display
from src.speech_processing.vosk_detector import VoskVoiceDetector

# Create widgets
record_button = widgets.Button(
    description='Record',
    disabled=False,
    button_style='success',
    tooltip='Record',
    icon='microphone'
)

stop_button = widgets.Button(
    description='Stop',
    disabled=False,
    button_style='warning',
    tooltip='Stop',
    icon='stop'
)

output = widgets.Output()

# Initialize detector
detector = VoskVoiceDetector(device_index=2)  # Change device_index as needed

def start_recording(data):
    with output:
        output.clear_output()
        detector.start_jupyter(output_widget=output)

def stop_recording(data):
    detector.stop()
    
record_button.on_click(start_recording)
stop_button.on_click(stop_recording)

display(record_button, stop_button, output)
```

## License

MIT 