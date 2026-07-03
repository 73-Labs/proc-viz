from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QToolBar, QLineEdit, QComboBox, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt
from app.dialogs import ConnectionDialog, ConnectionManagerDialog
from app.storage import ProfileManager, SettingsManager
from app.themes.theme_manager import ThemeManager
from app.themes.theme_definitions import ThemeDefinition
from app.widgets import DatabaseExplorer
from app.widgets.loading_spinner import LoadingOverlay
from app.drivers.connection_manager import ConnectionManager
from app.drivers.database_driver import DatabaseDriver


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DB Procedure Explorer")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(self.create_icon())
        self.profile_manager = ProfileManager()
        self.settings_manager = SettingsManager()
        self.theme_manager = ThemeManager()
        self.driver: DatabaseDriver = None
        self.explorer = None
        self.current_profile = None

        self.init_theme()
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
        self.loading_overlay = LoadingOverlay(central_widget, "Connecting to database...")
        self.create_status_bar()
        self.show_welcome()

    def create_icon(self):
        """Create window icon placeholder."""
        from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(70, 130, 180))
        return QIcon(pixmap)

    def init_theme(self) -> None:
        """Initialize theme on startup."""
        theme_name = self.settings_manager.get_theme()
        self.theme_manager.set_theme(theme_name)
        self.apply_theme()

    def apply_theme(self) -> None:
        """Apply current theme to application."""
        stylesheet = self.theme_manager.generate_stylesheet()
        QApplication.instance().setStyleSheet(stylesheet)
        if self.explorer:
            self.explorer.update_theme(self.theme_manager.get_syntax_colors())

    def on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change."""
        self.settings_manager.set_theme(theme_name)
        self.theme_manager.set_theme(theme_name)
        self.apply_theme()

    def on_zoom_in(self) -> None:
        """Zoom in code editor."""
        if self.explorer:
            self.explorer.zoom_in()

    def on_zoom_out(self) -> None:
        """Zoom out code editor."""
        if self.explorer:
            self.explorer.zoom_out()

    def on_zoom_reset(self) -> None:
        """Reset zoom to 100%."""
        if self.explorer:
            self.explorer.reset_zoom()

    def on_explorer_zoom_changed(self, zoom_level: int) -> None:
        """Handle zoom change from explorer."""
        self.settings_manager.set_zoom_level(zoom_level)
        self.zoom_level_label.setText(f"Zoom: {zoom_level}%")

    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Connection", self.open_connection_dialog)
        file_menu.addAction("Manage Connections", self.open_connection_manager)
        file_menu.addAction("Close Connection", self.close_connection)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        edit_menu = menubar.addMenu("Edit")

        view_menu = menubar.addMenu("View")
        view_menu.addAction("Refresh", self.refresh_explorer)
        view_menu.addSeparator()
        view_menu.addAction("Zoom In (Ctrl++)", self.on_zoom_in)
        view_menu.addAction("Zoom Out (Ctrl+-)", self.on_zoom_out)
        view_menu.addAction("Reset Zoom (Ctrl+0)", self.on_zoom_reset)
        view_menu.addSeparator()
        theme_menu = view_menu.addMenu("Theme")
        for theme_name in self.theme_manager.get_available_themes():
            theme_menu.addAction(theme_name, lambda name=theme_name: self.on_theme_changed(name))

        database_menu = menubar.addMenu("Database")
        database_menu.addAction("Connect", self.open_connection_dialog)
        database_menu.addAction("Manage Connections", self.open_connection_manager)
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
        self.conn_dropdown.currentIndexChanged.connect(self.on_profile_selected)
        toolbar.addWidget(QLabel("Connection: "))
        toolbar.addWidget(self.conn_dropdown)
        self.conn_dropdown.currentIndexChanged.connect(self.on_profile_selected)
        self.load_profiles_dropdown()

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.open_connection_dialog)
        toolbar.addWidget(self.connect_btn)

        self.manage_btn = QPushButton("Manage")
        self.manage_btn.clicked.connect(self.open_connection_manager)
        toolbar.addWidget(self.manage_btn)

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
        self.search_box.setPlaceholderText("Search routines...")
        toolbar.addWidget(self.search_box)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

    def create_status_bar(self):
        """Create status bar."""
        self.status_label = QLabel("Not connected")
        self.statusBar().addWidget(self.status_label, 1)

        self.zoom_level_label = QLabel("")
        self.statusBar().addPermanentWidget(self.zoom_level_label)

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
        self.zoom_level_label.setText("")
        self.proc_count_label.setText("")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.search_box.setEnabled(False)
        self.search_box.clear()

    def load_profiles_dropdown(self):
        """Load saved profiles into dropdown."""
        self.conn_dropdown.blockSignals(True)
        self.conn_dropdown.clear()
        self.conn_dropdown.addItem("Select a connection...")
        profiles = self.profile_manager.load_all_profiles()
        for profile in profiles:
            self.conn_dropdown.addItem(profile.name, profile)
        self.conn_dropdown.blockSignals(False)

    def on_profile_selected(self):
        """Handle profile selection from dropdown."""
        profile = self.conn_dropdown.currentData()
        if profile is None:
            return

        self.loading_overlay.start()
        password = self.profile_manager.get_password(profile.name)
        try:
            self.driver = ConnectionManager.create_connection(profile, password)
            self.current_profile = profile
            self.show_explorer(profile)
        except ConnectionError as e:
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
        finally:
            self.loading_overlay.stop()

    def open_connection_dialog(self):
        """Open connection dialog."""
        dialog = ConnectionDialog(parent=self)
        if dialog.exec() == ConnectionDialog.Accepted:
            profile = dialog.get_profile()
            password = dialog.get_password()
            self.profile_manager.save_profile(profile, password)
            self.load_profiles_dropdown()

            self.loading_overlay.start()
            try:
                self.driver = ConnectionManager.create_connection(profile, password)
                self.current_profile = profile
                self.show_explorer(profile)
            except ConnectionError as e:
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
            finally:
                self.loading_overlay.stop()

    def open_connection_manager(self):
        """Open connection manager dialog."""
        dialog = ConnectionManagerDialog(parent=self)
        if dialog.exec() == ConnectionManagerDialog.Accepted:
            self.load_profiles_dropdown()

    def show_explorer(self, profile):
        """Display database explorer."""
        while self.content_layout.count():
            widget = self.content_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        syntax_colors = self.theme_manager.get_syntax_colors()
        zoom_level = self.settings_manager.get_zoom_level()
        self.explorer = DatabaseExplorer(self.driver, profile, syntax_colors, zoom_level)
        self.explorer.zoom_changed.connect(self.on_explorer_zoom_changed)
        self.content_layout.addWidget(self.explorer)

        self.status_label.setText(f"Connected to: {profile.server} - {profile.database}")
        actual_zoom = self.explorer.get_zoom_level()
        self.zoom_level_label.setText(f"Zoom: {actual_zoom}%")
        proc_count = self.explorer.get_procedure_count()
        self.proc_count_label.setText(f"{proc_count} routines")

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
            self.loading_overlay.set_message("Refreshing schemas...")
            self.loading_overlay.start()
            self.explorer.load_procedures()
            proc_count = self.explorer.get_procedure_count()
            self.proc_count_label.setText(f"{proc_count} procedures")
            self.loading_overlay.stop()

    def close_connection(self):
        """Close connection."""
        if self.driver:
            try:
                self.driver.close()
            except:
                pass
            self.driver = None

        self.conn_dropdown.setCurrentIndex(0)
        self.show_welcome()

    def closeEvent(self, event):
        """Close connection on window close."""
        if self.driver:
            try:
                self.driver.close()
            except:
                pass
        event.accept()
