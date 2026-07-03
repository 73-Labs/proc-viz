from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent


class ZoomableTextEdit(QTextEdit):
    """QTextEdit with Ctrl+Scroll zoom support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_callback = None

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle wheel events for Ctrl+Scroll zoom."""
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                if self.zoom_callback:
                    self.zoom_callback("zoom_in")
            elif event.angleDelta().y() < 0:
                if self.zoom_callback:
                    self.zoom_callback("zoom_out")
            event.accept()
            return
        super().wheelEvent(event)

    def set_zoom_callback(self, callback) -> None:
        """Set callback for zoom events."""
        self.zoom_callback = callback
