import pytest
from app.main_window import MainWindow


def test_main_window_creation():
    window = MainWindow()
    assert window is not None
    assert window.windowTitle() == "Process Visualizer"
