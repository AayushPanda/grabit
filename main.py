import subprocess
import cv2
from PIL import Image
import pytesseract

def take_screenshot():
    path = "test.png"
    
    try:
        # Call Spectacle directly to take a fullscreen screenshot silently
        subprocess.run(["spectacle", "-b", "-n", "--fullscreen", "-o", path], check=True)
        print(f"Screenshot saved to {path}")
    except subprocess.CalledProcessError as e:
        print(f"Error taking screenshot: {e}")
        return None
    
    return path

def show_screenshot(path):
    try:
        img = Image.open(path)
        img.show()
    except Exception as e:
        print(f"Error displaying screenshot: {e}")

import cv2
import pytesseract

def get_text(path):
    # Read the image
    img = cv2.imread(path)
    if img is None:
        print("Error: Unable to read the image from the provided path.")
        return

    # Convert image to grayscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Extract bounding box information using Tesseract
    boxes = pytesseract.image_to_boxes(img)
    
    # Iterate through each detected box
    for row in boxes.splitlines():
        vals = row.split(' ')
        try:
            # Unpack values from the row
            sym = vals[0]
            l,b,r,t,p = map(int, vals[1:])
            
            # Draw rectangle around the symbol (note: OpenCV uses (x, y) coordinates)
            cv2.rectangle(img, (l, img.shape[0] - t), (r, img.shape[0] - b), (255, 0, 0), 2)
        except ValueError:
            print(f"Error parsing row: {vals}")
        except IndexError:
            print(f"Incomplete row data: {vals}")

    # Display the image with rectangles (optional)
    cv2.imwrite("boxed.png", img)

def main():
    get_text("test.png")

if __name__ == "__main__":
    main()
