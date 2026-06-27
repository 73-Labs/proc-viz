from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QToolBar, QLineEdit, QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt
import pymssql
from app.dialogs import ConnectionDialog
from app.storage import ProfileManager
from app.widgets import DatabaseExplorer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DB Procedure Explorer")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(self.create_icon())
        self.profile_manager = ProfileManager()
        self.connection = None
        self.explorer = None
        self.current_profile = None

        self.create_menu_bar()
        self.create_toolbar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)
        layout.addWidget(self.content_widget)

        central_widget.setLayout(layout)
        self.create_status_bar()
        self.show_welcome()

    def create_icon(self):
        """Create window icon placeholder."""
        from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(70, 130, 180))
        return QIcon(pixmap)

    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Connection", self.open_connection_dialog)
        file_menu.addAction("Close Connection", self.close_connection)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Preferences")

        view_menu = menubar.addMenu("View")
        view_menu.addAction("Refresh", self.refresh_explorer)

        database_menu = menubar.addMenu("Database")
        database_menu.addAction("Connect", self.open_connection_dialog)
        database_menu.addAction("Disconnect", self.close_connection)

        tools_menu = menubar.addMenu("Tools")
        help_menu = menubar.addMenu("Help")

    def create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.conn_dropdown = QComboBox()
        self.conn_dropdown.setMaximumWidth(200)
        toolbar.addWidget(QLabel("Connection: "))
        toolbar.addWidget(self.conn_dropdown)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.open_connection_dialog)
        toolbar.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.close_connection)
        self.disconnect_btn.setEnabled(False)
        toolbar.addWidget(self.disconnect_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_explorer)
        self.refresh_btn.setEnabled(False)
        toolbar.addWidget(self.refresh_btn)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel("Search (Ctrl+F): "))
        self.search_box = QLineEdit()
        self.search_box.setMaximumWidth(300)
        self.search_box.setPlaceholderText("Search procedures...")
        toolbar.addWidget(self.search_box)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

    def create_status_bar(self):
        """Create status bar."""
        self.status_label = QLabel("Not connected")
        self.statusBar().addWidget(self.status_label, 1)

        self.proc_count_label = QLabel("")
        self.statusBar().addPermanentWidget(self.proc_count_label)

    def show_welcome(self):
        """Show welcome screen."""
        while self.content_layout.count():
            widget = self.content_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        label = QLabel("Click 'Connect' to connect to a database server")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 14pt; color: gray;")
        self.content_layout.addWidget(label)

        self.status_label.setText("Not connected")
        self.proc_count_label.setText("")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.search_box.setEnabled(False)
        self.search_box.clear()

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
                self.current_profile = profile
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

        self.status_label.setText(f"Connected to: {profile.server} - {profile.database}")
        proc_count = self.explorer.get_procedure_count()
        self.proc_count_label.setText(f"{proc_count} procedures")

        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.search_box.setEnabled(True)
        self.search_box.textChanged.connect(self.on_search_text_changed)

    def on_search_text_changed(self, text: str):
        """Handle search box text changes."""
        if self.explorer:
            self.explorer.filter_input.setText(text)

    def refresh_explorer(self):
        """Refresh explorer."""
        if self.explorer and self.current_profile:
            self.explorer.load_procedures()
            proc_count = self.explorer.get_procedure_count()
            self.proc_count_label.setText(f"{proc_count} procedures")

    def close_connection(self):
        """Close connection."""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None

        self.show_welcome()

    def closeEvent(self, event):
        """Close connection on window close."""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
        event.accept()
