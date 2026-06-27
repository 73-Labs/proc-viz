from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
from PySide6.QtCore import Qt
import pymssql
from app.dialogs import ConnectionDialog
from app.storage import ProfileManager
from app.widgets import DatabaseExplorer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Procedures Visualizer")
        self.setGeometry(100, 100, 1200, 800)
        self.profile_manager = ProfileManager()
        self.connection = None
        self.explorer = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Toolbar
        toolbar_layout = QHBoxLayout()
        new_conn_btn = QPushButton("New Connection")
        new_conn_btn.clicked.connect(self.open_connection_dialog)
        toolbar_layout.addWidget(new_conn_btn)

        self.connection_status = QLabel("Not connected")
        toolbar_layout.addWidget(self.connection_status)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # Explorer will go here
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)
        layout.addWidget(self.content_widget)

        central_widget.setLayout(layout)
        self.show_welcome()

    def show_welcome(self):
        """Show welcome screen."""
        while self.content_layout.count():
            widget = self.content_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        label = QLabel("Click 'New Connection' to connect to a database")
        label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(label)
        self.connection_status.setText("Not connected")

    def open_connection_dialog(self):
        """Open connection dialog."""
        dialog = ConnectionDialog(parent=self)
        if dialog.exec() == ConnectionDialog.Accepted:
            profile = dialog.get_profile()
            password = dialog.get_password()
            self.profile_manager.save_profile(profile, password)

            try:
                kwargs = profile.get_connection_kwargs(password)
                self.connection = pymssql.connect(**kwargs, timeout=10)
                self.show_explorer(profile)
            except pymssql.DatabaseError as e:
                QMessageBox.critical(
                    self,
                    "Connection Failed",
                    f"Failed to connect:\n\n{str(e)}",
                )
                self.show_welcome()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Unexpected error:\n\n{str(e)}",
                )
                self.show_welcome()

    def show_explorer(self, profile):
        """Display database explorer."""
        while self.content_layout.count():
            widget = self.content_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        self.explorer = DatabaseExplorer(self.connection, profile)
        self.content_layout.addWidget(self.explorer)
        self.connection_status.setText(f"Connected: {profile.name} @ {profile.server}")

    def closeEvent(self, event):
        """Close connection on window close."""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
        event.accept()
