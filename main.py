#!/home/aayushvp/.conda/envs/main3129/bin/python

import subprocess
import cv2
from PIL import Image
import pytesseract
from display_boxes import OverlaySelectableArea
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSlot
from PyQt5.QtGui import QPainter, QColor
import sys
import os

from rangeTree2d import RangeTree, Point


class Box(Point):
    def __init__(self, text, l: int, b: int, r: int, t: int, p: int) -> None:
        super().__init__([l, b])
        self.text = text
        self.l = l
        self.b = b
        self.r = r
        self.t = t
        self.p = p
    
    def __repr__(self) -> str:
        return f"Box(text={self.text}, l={self.l}, b={self.b})"
    
    def __eq__(self, value: "Box") -> bool:
        if not isinstance(value, Box):
            return False
        return super().__eq__(value) and self.text == value.text and self.l == value.l and self.b == value.b and self.r == value.r and self.t == value.t and self.p == value.p


def take_screenshot():
    path = "test.png"
    
    try:
        # Call Spectacle directly to take a fullscreen screenshot silently
        if os.path.exists(path): os.remove(path)
        if os.path.exists("boxed.png"): os.remove("boxed.png")

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

def get_text(path):
    # Read the image
    img = cv2.imread(path)
    if img is None:
        print("Error: Unable to read the image from the provided path.")
        return None

    # Convert image to grayscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Define chunk size
    chunk_height, chunk_width = 1000, 1000
    height, width = img.shape
    pts = []

    # Process image in chunks
    for y in range(0, height, chunk_height):
        for x in range(0, width, chunk_width):
            # Extract chunk
            chunk = img[y:min(y + chunk_height, height), x:min(x + chunk_width, width)]
            
            # Process chunk with Tesseract
            boxes = pytesseract.image_to_boxes(chunk)
            
            # Iterate through each detected box
            for row in boxes.splitlines():
                vals = row.split(' ')
                try:
                    # Unpack values from the row
                    sym = vals[0]
                    l, b, r, t, p = map(int, vals[1:])
                    
                    # Adjust coordinates to original image space
                    l, r = l + x, r + x
                    b, t = chunk.shape[0] - b + y, chunk.shape[0] - t + y
                    
                    pts.append(Box(sym, l, b, r, t, p))
                    
                    # Draw rectangle around the symbol
                    cv2.rectangle(img, (l, t), (r, b), (255, 0, 0), 2)
                except ValueError:
                    print(f"Error parsing row: {vals}")
                except IndexError:
                    print(f"Incomplete row data: {vals}")

    tree = RangeTree(pts)

    # Save the visualization
    cv2.imwrite("boxed.png", img)
    return tree

def query_text_in_region(text_container, x1, y1, x2, y2):
    """
    Query text within the specified rectangular region.
    Args:
        text_container: TextBoxContainer instance
        x1, y1: Top-left corner coordinates
        x2, y2: Bottom-right corner coordinates
    Returns:
        String containing all text in the region, ordered left to right, top to bottom
    """
    if text_container is None:
        return ""
    return text_container.query_rectangle(x1, y1, x2, y2)

class SelectionWindow(QMainWindow):
    def __init__(self, tree):
        super().__init__()
        self.tree: RangeTree = tree
        self.start_pos = None
        self.last_click_time = None
        self.timeout_timer = QTimer()
        # self.timeout_timer.timeout.connect(self.handle_timeout)
        self.timeout_timer.setInterval(5000)  # 5 second timeout
        self.highlighted_points = []  # Store points to highlight
        self.clipboard = QApplication.clipboard()  # Initialize clipboard
        
        # Set up the window
        self.setWindowTitle("Select Text Area")
        self.showFullScreen()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    @pyqtSlot()
    def handle_timeout(self):
        self.close()

    def copy_selected_text(self):
        if self.highlighted_points:
            text = ''.join(r.text for r in self.highlighted_points)
            self.clipboard.setText(text)
            print(f"Copied text: {text}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.copy_selected_text()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Semi-transparent overlay
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

        # Draw highlight boxes
        painter.setBrush(QColor(255, 255, 0, 100))  # Semi-transparent yellow
        painter.setPen(QColor(255, 255, 0))  # Yellow border
        screen_height = self.height()
        
        for point in self.highlighted_points:
            x, y = point.l, point.b
            width = point.r - point.l
            height = point.t - point.b
            painter.drawRect(x, y, width, height)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()
            self.highlighted_points = []  # Clear previous highlights
            self.update()  # Trigger repaint
            self.timeout_timer.start()  # Reset timer on click

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.start_pos:
            end_pos = event.pos()
            screen_height = self.height()
            
            x1, x2 = sorted([self.start_pos.x(), end_pos.x()])
            y1, y2 = sorted([self.start_pos.y(), end_pos.y()])
            print(f"Coords: {(x1, y1)} to {(x2, y2)}")
            results = self.tree.range_query([x1, y1], [x2, y2])
            if results:
                text = ''.join(r.text for r in results)
                print(f"Selected text: {text}")
                self.clipboard.setText(text)  # Copy text to clipboard
                for r in results:
                    print(r)
                self.highlighted_points = [r for r in results]  # Store points for highlighting
                self.update()  # Trigger repaint
            
            self.start_pos = None
            self.timeout_timer.start()  # Reset timer on release

def main():
    app = QApplication(sys.argv)
    
    # Get the text tree from the image
    take_screenshot()
    tree = get_text("test.png")
    if tree is None:
        print("No text container available.")
        return

    # Create and show the selection window
    window = SelectionWindow(tree)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
