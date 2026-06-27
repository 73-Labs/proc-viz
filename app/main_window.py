from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from app.dialogs import ConnectionDialog
from app.storage import ProfileManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Procedures Visualizer")
        self.setGeometry(100, 100, 800, 600)
        self.profile_manager = ProfileManager()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        label = QLabel("Process Visualization Application")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        new_conn_btn = QPushButton("New Connection")
        new_conn_btn.clicked.connect(self.open_connection_dialog)
        layout.addWidget(new_conn_btn)

        layout.addStretch()

        central_widget.setLayout(layout)

    def open_connection_dialog(self):
        """Open connection dialog."""
        dialog = ConnectionDialog(parent=self)
        if dialog.exec() == ConnectionDialog.Accepted:
            profile = dialog.get_profile()
            password = dialog.get_password()
            self.profile_manager.save_profile(profile, password)
            QLabel(f"Connected: {profile.name}").show()
