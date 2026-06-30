"""Loading spinner widget for async operations."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QPen


class LoadingSpinner(QWidget):
    """Animated rotating spinner."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        self.setStyleSheet("background-color: transparent;")
        self.setFixedSize(60, 60)

    def start(self):
        """Start spinning animation."""
        self.timer.start(50)

    def stop(self):
        """Stop spinning animation."""
        self.timer.stop()

    def rotate(self):
        """Rotate spinner."""
        self.angle = (self.angle + 12) % 360
        self.update()

    def paintEvent(self, event):
        """Paint rotating spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = 20

        painter.translate(center_x, center_y)
        painter.rotate(self.angle)

        color = QColor(100, 180, 255)
        pen = QPen(color)
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawArc(QRect(-radius, -radius, radius * 2, radius * 2), 0, 45 * 16)


class LoadingOverlay(QWidget):
    """Semi-transparent overlay with spinner and message."""
    finished = Signal()

    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.setCursor(Qt.WaitCursor)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.raise_()
        self.setFocusPolicy(Qt.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        self.spinner = LoadingSpinner()
        layout.addWidget(self.spinner, alignment=Qt.AlignCenter)

        self.message_label = QLabel(message)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.message_label.setFont(font)
        self.message_label.setStyleSheet("color: white; margin-top: 10px;")
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

        self.setLayout(layout)
        self.hide()

    def start(self):
        """Show overlay and start spinner."""
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
        self.spinner.start()

    def stop(self):
        """Hide overlay and stop spinner."""
        self.spinner.stop()
        self.hide()

    def set_message(self, message: str):
        """Update overlay message."""
        self.message_label.setText(message)

    def resizeEvent(self, event):
        """Adjust overlay size when parent resizes."""
        if self.isVisible() and self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)
