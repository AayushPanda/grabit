from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QFontMetrics, QFont, QFontDatabase, QTextOption
from PyQt5.QtWidgets import QApplication, QTextEdit, QMainWindow


class OverlaySelectableArea(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("grabit")
        self.setMaximumSize

        # Make the window frameless and transparent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        font_id = QFontDatabase.addApplicationFont("./assets/ankacodernarrow.ttf")
        if font_id == -1:
            print("Failed to load the font!")

        # Get the font family name
        self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

    def makeTextEdit(self, text: str, lSpace: int, fontSize: int, ax: int, ay: int):
        # Create a QTextEdit as the "selectable" area
        self.text_edit = QTextEdit(self)

        self.text_edit.setReadOnly(True)  # Make it non-editable
        self.text_edit.setPlainText(text)
        self.text_edit.setFont(QFont(self.font_family, fontSize))
        
        # Remove padding and margins via stylesheet
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(255, 0, 0, 0.8); /* Semi-transparent red */
                color: black;
                padding: 0px; /* No padding */
                margin: 0px; /* No margin */
                border: none; /* Optional: Remove border */
            }}
        """)

        self.text_edit.document().setDocumentMargin(0)
        self.text_edit.setWordWrapMode(QTextOption.NoWrap)

        # Text metics
        lines = text.split('\n')
        nlines = len(lines)
        maxl = max(len(line) for line in lines) if lines else 0
        print(maxl)

        # Get the font and metrics
        font = self.text_edit.font()
        font.setPointSize(fontSize) # might be causing errors by setting font after display, but needed to assert font size
        self.text_edit.setFont(font)
        font_metrics = QFontMetrics(font)

        # Retrieve line spacing and character width
        line_spacing = font_metrics.lineSpacing()  # Get the line spacing in pixels
        char_width = font_metrics.horizontalAdvance("c")  # Width of a single character

        # TODO 1.01 is a magic number rn, gotta fix later
        # why is horizontalAdvance not accurate? find a better way to get char width?
        total_width = int(1.01 *  char_width) * maxl
        total_height = int(1.01 * line_spacing * nlines)

        self.text_edit.setGeometry(ax, ay, total_width, total_height)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())  # Cover the whole window


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    overlay = OverlaySelectableArea()
    overlay.makeTextEdit("s", 15, 100, 50, 50)
    overlay.showFullScreen()  # Display the overlay fullscreen
    sys.exit(app.exec_())
