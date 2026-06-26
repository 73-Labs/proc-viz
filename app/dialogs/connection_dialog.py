from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QMessageBox,
    QGroupBox,
)
from PySide6.QtCore import Qt
import pyodbc
from app.models import ConnectionProfile, AuthenticationMode
from app.drivers import OdbcDriverManager


class ConnectionDialog(QDialog):
    """Dialog for creating/editing database connection profiles."""

    DRIVERS = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "SQL Server Native Client 11.0",
    ]

    def __init__(self, profile: ConnectionProfile = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Connection")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.password = None
        self.profile = profile or ConnectionProfile(
            name="", server="", database=""
        )

        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Profile Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Profile Name:"))
        self.name_input = QLineEdit()
        self.name_input.setText(self.profile.name)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Server
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("Server:"))
        self.server_input = QLineEdit()
        self.server_input.setText(self.profile.server)
        self.server_input.setPlaceholderText("localhost or db.example.com")
        server_layout.addWidget(self.server_input)
        layout.addLayout(server_layout)

        # Port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_input = QSpinBox()
        self.port_input.setMinimum(1)
        self.port_input.setMaximum(65535)
        self.port_input.setValue(self.profile.port)
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        layout.addLayout(port_layout)

        # Database
        database_layout = QHBoxLayout()
        database_layout.addWidget(QLabel("Database:"))
        self.database_input = QLineEdit()
        self.database_input.setText(self.profile.database)
        self.database_input.setPlaceholderText("database name")
        database_layout.addWidget(self.database_input)
        layout.addLayout(database_layout)

        # Driver
        driver_layout = QHBoxLayout()
        driver_layout.addWidget(QLabel("Driver:"))
        self.driver_combo = QComboBox()
        self.driver_combo.addItems(self.DRIVERS)
        self.driver_combo.setCurrentText(self.profile.driver)
        driver_layout.addWidget(self.driver_combo)
        layout.addLayout(driver_layout)

        # Authentication Mode
        auth_layout = QHBoxLayout()
        auth_layout.addWidget(QLabel("Authentication:"))
        self.auth_combo = QComboBox()
        self.auth_combo.addItem("Windows Authentication", AuthenticationMode.WINDOWS)
        self.auth_combo.addItem("SQL Server Login", AuthenticationMode.SQL_SERVER)
        current_index = (
            1
            if self.profile.authentication_mode == AuthenticationMode.SQL_SERVER
            else 0
        )
        self.auth_combo.setCurrentIndex(current_index)
        self.auth_combo.currentIndexChanged.connect(self.on_auth_mode_changed)
        auth_layout.addWidget(self.auth_combo)
        layout.addLayout(auth_layout)

        # Username
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setText(self.profile.username or "")
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        # Password
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        # Save Password Checkbox
        self.save_password_check = QCheckBox("Save password (stored in keyring)")
        self.save_password_check.setChecked(self.profile.save_password)
        layout.addWidget(self.save_password_check)

        # Encryption Options
        encryption_group = QGroupBox("Encryption")
        encryption_layout = QVBoxLayout()
        self.encrypt_check = QCheckBox("Encrypt connection")
        self.encrypt_check.setChecked(self.profile.encrypt)
        encryption_layout.addWidget(self.encrypt_check)

        self.trust_cert_check = QCheckBox("Trust server certificate")
        self.trust_cert_check.setChecked(self.profile.trust_certificate)
        encryption_layout.addWidget(self.trust_cert_check)
        encryption_group.setLayout(encryption_layout)
        layout.addWidget(encryption_group)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_btn)

        button_layout.addStretch()

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.connect_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.on_auth_mode_changed()

    def on_auth_mode_changed(self):
        """Handle authentication mode change."""
        auth_mode = self.auth_combo.currentData()
        is_sql_auth = auth_mode == AuthenticationMode.SQL_SERVER

        self.username_input.setEnabled(is_sql_auth)
        self.password_input.setEnabled(is_sql_auth)
        self.save_password_check.setEnabled(is_sql_auth)

    def get_profile(self) -> ConnectionProfile:
        """Get configured connection profile."""
        self.profile = ConnectionProfile(
            name=self.name_input.text(),
            server=self.server_input.text(),
            port=self.port_input.value(),
            database=self.database_input.text(),
            authentication_mode=self.auth_combo.currentData(),
            username=self.username_input.text() or None,
            driver=self.driver_combo.currentText(),
            encrypt=self.encrypt_check.isChecked(),
            trust_certificate=self.trust_cert_check.isChecked(),
            save_password=self.save_password_check.isChecked(),
        )
        return self.profile

    def get_password(self) -> str:
        """Get entered password."""
        return self.password_input.text()

    def ensure_driver_installed(self, profile: ConnectionProfile) -> bool:
        """
        Ensure required ODBC driver is installed.
        Prompts user to install if missing.
        Returns True if driver available, False otherwise.
        """
        if OdbcDriverManager.has_sql_server_driver():
            return True

        reply = QMessageBox.question(
            self,
            "ODBC Driver Missing",
            f"ODBC driver required for {profile.server} is not installed.\n\n"
            "Would you like to attempt automatic installation?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.No:
            QMessageBox.information(
                self,
                "Manual Installation",
                OdbcDriverManager.get_installation_instructions(),
            )
            return False

        return self.attempt_driver_installation()

    def attempt_driver_installation(self) -> bool:
        """Attempt to install ODBC driver."""
        progress_dialog = QMessageBox(
            QMessageBox.Information,
            "Installing ODBC Driver",
            "Downloading and installing ODBC Driver 18 for SQL Server...\n\n"
            "This may take a few minutes.",
            QMessageBox.NoButton,
        )
        progress_dialog.show()
        self.window().repaint()

        try:
            success = OdbcDriverManager.install_odbc_driver()
        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(
                self,
                "Installation Error",
                f"Error during installation:\n\n{str(e)}",
            )
            return False

        progress_dialog.close()

        if success:
            QMessageBox.information(
                self,
                "Installation Successful",
                "ODBC Driver 18 for SQL Server has been installed.\n\n"
                "Ready to test connection.",
            )
            return True
        else:
            QMessageBox.critical(
                self,
                "Installation Failed",
                "Automatic installation failed.\n\n"
                "Please install manually:\n"
                "https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server",
            )
            return False

    def test_connection(self):
        """Test database connection."""
        profile = self.get_profile()

        if not profile.server:
            QMessageBox.warning(self, "Validation Error", "Server is required.")
            return

        password = self.get_password()

        if profile.authentication_mode == AuthenticationMode.SQL_SERVER and not password:
            QMessageBox.warning(self, "Validation Error", "Password is required for SQL Server authentication.")
            return

        # Check for ODBC driver
        if not self.ensure_driver_installed(profile):
            return

        try:
            conn_str = profile.get_connection_string(password)
            pyodbc.connect(conn_str, timeout=5)
            QMessageBox.information(
                self,
                "Connection Successful",
                f"Successfully connected to {profile.server}",
            )
        except pyodbc.Error as e:
            error_msg = str(e)
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"Failed to connect to database:\n\n{error_msg}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred:\n\n{str(e)}",
            )

    def accept(self):
        """Validate and accept dialog."""
        profile = self.get_profile()

        if not profile.name:
            QMessageBox.warning(self, "Validation Error", "Profile name is required.")
            return

        if not profile.server:
            QMessageBox.warning(self, "Validation Error", "Server is required.")
            return

        if profile.authentication_mode == AuthenticationMode.SQL_SERVER:
            if not profile.username:
                QMessageBox.warning(self, "Validation Error", "Username is required for SQL Server authentication.")
                return
            if not self.get_password():
                QMessageBox.warning(self, "Validation Error", "Password is required for SQL Server authentication.")
                return

        self.password = self.password_input.text()
        super().accept()
