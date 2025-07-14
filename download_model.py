import os
import sys
import urllib.request
import zipfile
import shutil

def download_vosk_model():
    """Download the Vosk speech recognition model"""
    model_name = "vosk-model-en-us-0.22"
    model_url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
    zip_path = f"{model_name}.zip"
    
    print(f"Downloading Vosk model from {model_url}...")
    print("This may take a few minutes depending on your internet connection.")
    
    try:
        # Download the model
        urllib.request.urlretrieve(model_url, zip_path)
        
        # Extract the model
        print(f"Extracting model to {model_name}/...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Remove the zip file
        os.remove(zip_path)
        
        print(f"Model downloaded and extracted successfully to {model_name}/")
        print("You can now run the application with: python main.py")
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(download_vosk_model()) 