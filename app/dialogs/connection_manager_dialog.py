from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QMessageBox,
    QInputDialog,
)
from PySide6.QtCore import Qt
from app.models import ConnectionProfile
from app.storage import ProfileManager
from app.dialogs.connection_dialog import ConnectionDialog


class ConnectionManagerDialog(QDialog):
    """Dialog for managing saved database connections."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Connections")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.profile_manager = ProfileManager()
        self.init_ui()
        self.load_connections()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_connection)
        button_layout.addWidget(self.edit_btn)

        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self.rename_connection)
        button_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_connection)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_connections(self):
        """Load all connections into list."""
        self.list_widget.clear()
        profiles = self.profile_manager.load_all_profiles()
        for profile in profiles:
            item = QListWidgetItem(profile.name)
            item.setData(Qt.UserRole, profile)
            self.list_widget.addItem(item)

    def get_selected_profile(self) -> ConnectionProfile:
        """Get currently selected profile."""
        current_item = self.list_widget.currentItem()
        if not current_item:
            return None
        return current_item.data(Qt.UserRole)

    def edit_connection(self):
        """Edit selected connection."""
        profile = self.get_selected_profile()
        if not profile:
            QMessageBox.warning(self, "Selection Error", "Please select a connection to edit.")
            return

        dialog = ConnectionDialog(profile=profile, parent=self)
        if dialog.exec() == ConnectionDialog.Accepted:
            new_profile = dialog.get_profile()
            password = dialog.get_password()

            if new_profile.name != profile.name:
                self.profile_manager.rename_profile(profile.name, new_profile.name)

            self.profile_manager.save_profile(new_profile, password)
            self.load_connections()

    def rename_connection(self):
        """Rename selected connection."""
        profile = self.get_selected_profile()
        if not profile:
            QMessageBox.warning(self, "Selection Error", "Please select a connection to rename.")
            return

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Connection",
            f"New name for '{profile.name}':",
            text=profile.name
        )

        if ok and new_name:
            if new_name == profile.name:
                return

            try:
                self.profile_manager.rename_profile(profile.name, new_name)
                self.load_connections()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Connection renamed from '{profile.name}' to '{new_name}'."
                )
            except ValueError as e:
                QMessageBox.critical(self, "Rename Failed", str(e))

    def delete_connection(self):
        """Delete selected connection."""
        profile = self.get_selected_profile()
        if not profile:
            QMessageBox.warning(self, "Selection Error", "Please select a connection to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete connection '{profile.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.profile_manager.delete_profile(profile.name)
            self.load_connections()
            QMessageBox.information(
                self,
                "Success",
                f"Connection '{profile.name}' deleted."
            )
