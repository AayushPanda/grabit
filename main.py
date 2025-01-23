import subprocess
from PIL import Image

def take_screenshot():
    screenshot_path = "/tmp/screenshot.png"
    
    try:
        # Call Spectacle directly to take a fullscreen screenshot silently
        subprocess.run(["spectacle", "-b", "-n", "--fullscreen", "-o", screenshot_path], check=True)
        print(f"Screenshot saved to {screenshot_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error taking screenshot: {e}")
        return None
    
    return screenshot_path

def show_screenshot(screenshot_path):
    try:
        img = Image.open(screenshot_path)
        img.show()
    except Exception as e:
        print(f"Error displaying screenshot: {e}")

def main():
    screenshot_path = take_screenshot()
    if screenshot_path:
        show_screenshot(screenshot_path)

if __name__ == "__main__":
    main()
