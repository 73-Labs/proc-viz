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
from app.models import ConnectionProfile, AuthenticationMode, DatabaseType
from app.storage import ProfileManager

try:
    import pymssql  # type: ignore
except ImportError:  # pragma: no cover - fallback for optional dependency
    class _PymssqlShim:
        class DatabaseError(Exception):
            pass

        class Error(Exception):
            pass

        @staticmethod
        def connect(*args, **kwargs):
            raise ImportError("pymssql is not installed")

    pymssql = _PymssqlShim()


class ConnectionDialog(QDialog):
    """Dialog for creating/editing database connection profiles."""

    def __init__(self, profile: ConnectionProfile = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Connection")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.password = None
        self.profile = profile or ConnectionProfile(
            name="", server="", database=""
        )
        self.profile_manager = ProfileManager()

        self.init_ui()
        self.load_saved_password()

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

        # Database Type
        db_type_layout = QHBoxLayout()
        db_type_layout.addWidget(QLabel("Database Type:"))
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItem("SQL Server", DatabaseType.SQL_SERVER)
        self.db_type_combo.addItem("PostgreSQL", DatabaseType.POSTGRESQL)
        self.db_type_combo.addItem("Oracle", DatabaseType.ORACLE)
        self.db_type_combo.addItem("MySQL", DatabaseType.MYSQL)
        current_db_type_index = self._find_db_type_index(self.profile.db_type)
        self.db_type_combo.setCurrentIndex(current_db_type_index)
        self.db_type_combo.currentIndexChanged.connect(self.on_db_type_changed)
        db_type_layout.addWidget(self.db_type_combo)
        layout.addLayout(db_type_layout)

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

        # Authentication Mode
        auth_layout = QHBoxLayout()
        auth_layout.addWidget(QLabel("Authentication:"))
        self.auth_combo = QComboBox()
        self.auth_combo.currentIndexChanged.connect(self.on_auth_mode_changed)
        self._populate_auth_options()
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
        self.on_db_type_changed()
        self.on_auth_mode_changed()

    def _find_db_type_index(self, db_type: DatabaseType) -> int:
        """Find database type combo index."""
        if not hasattr(self, "db_type_combo"):
            return 0
        for idx in range(self.db_type_combo.count()):
            if self.db_type_combo.itemData(idx) == db_type:
                return idx
        return 0

    def _populate_auth_options(self) -> None:
        """Populate auth options based on db type."""
        selected_auth = self.auth_combo.currentData() if self.auth_combo.count() else None
        self.auth_combo.blockSignals(True)
        self.auth_combo.clear()

        db_type = self.db_type_combo.currentData()
        if db_type == DatabaseType.SQL_SERVER:
            self.auth_combo.addItem("Windows Authentication", AuthenticationMode.WINDOWS)
            self.auth_combo.addItem("SQL Server Login", AuthenticationMode.SQL_SERVER)
        else:
            self.auth_combo.addItem("Username / Password", AuthenticationMode.PASSWORD)

        desired_mode = selected_auth or self.profile.authentication_mode
        match_index = 0
        for idx in range(self.auth_combo.count()):
            if self.auth_combo.itemData(idx) == desired_mode:
                match_index = idx
                break
        self.auth_combo.setCurrentIndex(match_index)
        self.auth_combo.blockSignals(False)

    def on_db_type_changed(self, *_args):
        """Handle database type change."""
        self._populate_auth_options()
        self.on_auth_mode_changed()

    def on_auth_mode_changed(self, *_args):
        """Handle authentication mode change."""
        auth_mode = self.auth_combo.currentData()
        db_type = self.db_type_combo.currentData()
        is_sql_server = db_type == DatabaseType.SQL_SERVER
        needs_credentials = (
            auth_mode in (AuthenticationMode.SQL_SERVER, AuthenticationMode.PASSWORD)
            and is_sql_server
        ) or (
            auth_mode == AuthenticationMode.PASSWORD and db_type != DatabaseType.SQL_SERVER
        )

        self.username_input.setEnabled(needs_credentials)
        self.password_input.setEnabled(needs_credentials)
        self.save_password_check.setEnabled(needs_credentials)

    def get_profile(self) -> ConnectionProfile:
        """Get configured connection profile."""
        self.profile = ConnectionProfile(
            name=self.name_input.text(),
            server=self.server_input.text(),
            port=self.port_input.value(),
            database=self.database_input.text(),
            db_type=self.db_type_combo.currentData(),
            authentication_mode=self.auth_combo.currentData(),
            username=self.username_input.text() or None,
            encrypt=self.encrypt_check.isChecked(),
            trust_certificate=self.trust_cert_check.isChecked(),
            save_password=self.save_password_check.isChecked(),
        )
        return self.profile

    def get_password(self) -> str:
        """Get entered password."""
        return self.password_input.text()

    def _auth_requires_credentials(self, profile: ConnectionProfile) -> bool:
        """Check if current auth mode needs username/password."""
        if profile.db_type == DatabaseType.SQL_SERVER:
            return profile.authentication_mode in (
                AuthenticationMode.SQL_SERVER,
                AuthenticationMode.PASSWORD,
            )
        return profile.authentication_mode == AuthenticationMode.PASSWORD

    def test_connection(self):
        """Test database connection."""
        profile = self.get_profile()

        if not profile.server:
            QMessageBox.warning(self, "Validation Error", "Server is required.")
            return

        password = self.get_password()
        needs_password = self._auth_requires_credentials(profile)

        if needs_password and not password:
            QMessageBox.warning(self, "Validation Error", "Password is required for selected authentication mode.")
            return

        try:
            kwargs = profile.get_connection_kwargs(password)
            if profile.db_type == DatabaseType.SQL_SERVER:
                import pymssql

                conn = pymssql.connect(**kwargs, timeout=5)
            else:
                raise NotImplementedError(f"{profile.db_type.value} connection test not wired yet")
            conn.close()
            QMessageBox.information(
                self,
                "Connection Successful",
                f"Successfully connected to {profile.server}",
            )
        except Exception as e:
            error_msg = str(e)
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"An error occurred while connecting to database:\n\n{error_msg}",
            )

    def load_saved_password(self):
        """Load saved password from keyring if profile exists."""
        if self.profile.name:
            password = self.profile_manager.get_password(self.profile.name)
            if password:
                self.password_input.setText(password)

    def accept(self):
        """Validate and accept dialog."""
        profile = self.get_profile()

        if not profile.name:
            QMessageBox.warning(self, "Validation Error", "Profile name is required.")
            return

        if not profile.server:
            QMessageBox.warning(self, "Validation Error", "Server is required.")
            return

        if self._auth_requires_credentials(profile):
            if not profile.username:
                QMessageBox.warning(self, "Validation Error", "Username is required.")
                return
            if not self.get_password():
                QMessageBox.warning(self, "Validation Error", "Password is required.")
                return

        self.password = self.password_input.text()
        super().accept()
