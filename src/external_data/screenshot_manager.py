import os
import time
import datetime
import threading
import requests
import base64
from PIL import ImageGrab
from pathlib import Path
import json

class ScreenshotManager:
    """
    Manages screenshot capture and uploading functionality.
    """
    
    def __init__(self, save_local=True, upload_service=None, api_key=None):
        """
        Initialize the screenshot manager.
        
        Args:
            save_local (bool): Whether to save screenshots locally
            upload_service (str): Upload service to use ('imgur', 'cloudinary', etc.)
            api_key (str): API key for upload service
        """
        self.save_local = save_local
        self.upload_service = upload_service
        self.api_key = api_key
        
        # Create screenshots directory if it doesn't exist
        self.screenshots_dir = Path("screenshots")
        if self.save_local:
            self.screenshots_dir.mkdir(exist_ok=True)
    
    def capture_screenshot(self, filename=None, region=None):
        """
        Capture a screenshot of the screen.
        
        Args:
            filename (str): Optional filename for the screenshot
            region (tuple): Optional region to capture (left, top, right, bottom)
            
        Returns:
            tuple: (PIL Image object, file path if saved locally)
        """
        try:
            # Capture screenshot
            if region:
                screenshot = ImageGrab.grab(bbox=region)
            else:
                screenshot = ImageGrab.grab()
            
            file_path = None
            if self.save_local:
                # Use main screenshot filename if not provided
                if not filename:
                    filename = "main_screenshot.png"
                
                # Ensure filename has .png extension
                if not filename.endswith('.png'):
                    filename += '.png'
                
                file_path = self.screenshots_dir / filename
                screenshot.save(file_path)
                print(f"Screenshot saved to: {file_path}")
            
            return screenshot, file_path
            
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None, None
    
    def upload_to_imgur(self, image_data):
        """
        Upload image to Imgur.
        
        Args:
            image_data (bytes): Image data to upload
            
        Returns:
            dict: Response from Imgur API
        """
        if not self.api_key:
            raise ValueError("Imgur API key required for uploading")
        
        headers = {
            'Authorization': f'Client-ID {self.api_key}',
        }
        
        data = {
            'image': base64.b64encode(image_data).decode('utf-8'),
            'type': 'base64',
        }
        
        try:
            response = requests.post('https://api.imgur.com/3/image', headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error uploading to Imgur: {e}")
            return None
    
    def upload_to_cloudinary(self, image_data):
        """
        Upload image to Cloudinary.
        
        Args:
            image_data (bytes): Image data to upload
            
        Returns:
            dict: Response from Cloudinary API
        """
        # This would require cloudinary SDK
        # pip install cloudinary
        try:
            import cloudinary
            import cloudinary.uploader
            
            # Configure Cloudinary (you'd need to set these)
            cloudinary.config(
                cloud_name="your_cloud_name",
                api_key="your_api_key",
                api_secret="your_api_secret"
            )
            
            # Upload image
            result = cloudinary.uploader.upload(image_data)
            return result
            
        except ImportError:
            print("Cloudinary SDK not installed. Run: pip install cloudinary")
            return None
        except Exception as e:
            print(f"Error uploading to Cloudinary: {e}")
            return None
    
    def capture_and_upload(self, filename=None, region=None):
        """
        Capture a screenshot and upload it.
        
        Args:
            filename (str): Optional filename for the screenshot
            region (tuple): Optional region to capture
            
        Returns:
            dict: Upload response with URL and other details
        """
        # Capture screenshot
        screenshot, file_path = self.capture_screenshot(filename, region)
        
        if not screenshot:
            return None
        
        # Convert PIL Image to bytes for uploading
        import io
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format='PNG')
        img_bytes = img_bytes.getvalue()
        
        # Upload based on configured service
        upload_result = None
        if self.upload_service == 'imgur':
            upload_result = self.upload_to_imgur(img_bytes)
        elif self.upload_service == 'cloudinary':
            upload_result = self.upload_to_cloudinary(img_bytes)
        else:
            print("No upload service configured")
        
        result = {
            'local_path': str(file_path) if file_path else None,
            'upload_result': upload_result,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        if upload_result and self.upload_service == 'imgur':
            if upload_result.get('success'):
                result['url'] = upload_result['data']['link']
                print(f"Screenshot uploaded: {result['url']}")
            else:
                print("Upload failed")
        
        return result
    
    def capture_region(self, x, y, width, height):
        """
        Capture a specific region of the screen.
        
        Args:
            x (int): Left coordinate
            y (int): Top coordinate
            width (int): Width of region
            height (int): Height of region
            
        Returns:
            tuple: (PIL Image object, file path if saved locally)
        """
        region = (x, y, x + width, y + height)
        return self.capture_screenshot(region=region)
    
    def capture_with_delay(self, delay_seconds=3, filename=None):
        """
        Capture a screenshot after a delay.
        
        Args:
            delay_seconds (int): Delay before capturing
            filename (str): Optional filename
            
        Returns:
            tuple: (PIL Image object, file path if saved locally)
        """
        print(f"Capturing screenshot in {delay_seconds} seconds...")
        time.sleep(delay_seconds)
        return self.capture_screenshot(filename)
    
    def start_periodic_capture(self, interval_seconds=60, max_captures=None):
        """
        Start capturing screenshots periodically in a background thread.
        
        Args:
            interval_seconds (int): Interval between captures
            max_captures (int): Maximum number of captures (None for unlimited)
        """
        def capture_loop():
            captures = 0
            while True:
                if max_captures and captures >= max_captures:
                    break
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"periodic_{timestamp}.png"
                self.capture_screenshot(filename)
                captures += 1
                
                time.sleep(interval_seconds)
        
        thread = threading.Thread(target=capture_loop, daemon=True)
        thread.start()
        print(f"Started periodic screenshot capture (every {interval_seconds}s)")
        return thread

# Example usage functions
def quick_screenshot():
    """Quick screenshot with default settings."""
    manager = ScreenshotManager()
    screenshot, path = manager.capture_screenshot()
    return screenshot, path

def screenshot_and_upload_imgur(api_key):
    """Capture and upload to Imgur."""
    manager = ScreenshotManager(upload_service='imgur', api_key=api_key)
    return manager.capture_and_upload()

def screenshot_region(x, y, width, height):
    """Capture a specific screen region."""
    manager = ScreenshotManager()
    return manager.capture_region(x, y, width, height)

# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Screenshot Manager")
    parser.add_argument("--delay", type=int, default=0, help="Delay before capture (seconds)")
    parser.add_argument("--filename", type=str, help="Output filename")
    parser.add_argument("--region", nargs=4, type=int, metavar=('X', 'Y', 'W', 'H'), 
                       help="Capture region: x y width height")
    parser.add_argument("--upload", choices=['imgur'], help="Upload service")
    parser.add_argument("--api-key", type=str, help="API key for upload service")
    parser.add_argument("--periodic", type=int, help="Start periodic capture (interval in seconds)")
    
    args = parser.parse_args()
    
    # Create manager
    manager = ScreenshotManager(
        upload_service=args.upload,
        api_key=args.api_key
    )
    
    if args.periodic:
        # Start periodic capture
        manager.start_periodic_capture(args.periodic)
        print("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping periodic capture...")
    else:
        # Single screenshot
        if args.region:
            x, y, w, h = args.region
            screenshot, path = manager.capture_region(x, y, w, h)
        else:
            if args.delay > 0:
                screenshot, path = manager.capture_with_delay(args.delay, args.filename)
            else:
                screenshot, path = manager.capture_screenshot(args.filename)
        
        # Upload if service specified
        if args.upload and screenshot:
            result = manager.capture_and_upload(args.filename, 
                                              tuple(args.region) if args.region else None)
            if result and result.get('url'):
                print(f"Uploaded to: {result['url']}")
    
    print("Screenshot operation completed.") 