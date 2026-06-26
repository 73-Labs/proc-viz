import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox
from app.models import ConnectionProfile, AuthenticationMode
from app.dialogs.connection_dialog import ConnectionDialog


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def empty_profile():
    """Create empty connection profile."""
    return ConnectionProfile(name="", server="", database="")


@pytest.fixture
def windows_profile():
    """Create Windows Auth profile."""
    return ConnectionProfile(
        name="Test Windows",
        server="localhost",
        port=1433,
        database="TestDB",
        authentication_mode=AuthenticationMode.WINDOWS,
    )


@pytest.fixture
def sql_profile():
    """Create SQL Server Auth profile."""
    return ConnectionProfile(
        name="Test SQL",
        server="db.example.com",
        port=1434,
        database="ProdDB",
        authentication_mode=AuthenticationMode.SQL_SERVER,
        username="admin",
        save_password=True,
    )


class TestConnectionDialog:
    def test_dialog_creation_empty_profile(self, qapp, empty_profile):
        dialog = ConnectionDialog(empty_profile)
        assert dialog is not None
        assert dialog.windowTitle() == "Database Connection"
        assert dialog.isModal() is True

    def test_dialog_creation_with_windows_profile(self, qapp, windows_profile):
        dialog = ConnectionDialog(windows_profile)
        assert dialog.name_input.text() == "Test Windows"
        assert dialog.server_input.text() == "localhost"
        assert dialog.port_input.value() == 1433
        assert dialog.database_input.text() == "TestDB"
        assert dialog.auth_combo.currentData() == AuthenticationMode.WINDOWS

    def test_dialog_creation_with_sql_profile(self, qapp, sql_profile):
        dialog = ConnectionDialog(sql_profile)
        assert dialog.name_input.text() == "Test SQL"
        assert dialog.server_input.text() == "db.example.com"
        assert dialog.port_input.value() == 1434
        assert dialog.database_input.text() == "ProdDB"
        assert dialog.username_input.text() == "admin"
        assert dialog.auth_combo.currentData() == AuthenticationMode.SQL_SERVER
        assert dialog.save_password_check.isChecked() is True

    def test_windows_auth_disables_credentials(self, qapp, windows_profile):
        dialog = ConnectionDialog(windows_profile)
        assert dialog.username_input.isEnabled() is False
        assert dialog.password_input.isEnabled() is False
        assert dialog.save_password_check.isEnabled() is False

    def test_sql_auth_enables_credentials(self, qapp, sql_profile):
        dialog = ConnectionDialog(sql_profile)
        assert dialog.username_input.isEnabled() is True
        assert dialog.password_input.isEnabled() is True
        assert dialog.save_password_check.isEnabled() is True

    def test_auth_mode_change_to_sql(self, qapp, windows_profile):
        dialog = ConnectionDialog(windows_profile)
        # Initially Windows auth, credentials disabled
        assert dialog.username_input.isEnabled() is False

        # Switch to SQL Server auth
        dialog.auth_combo.setCurrentIndex(1)
        assert dialog.username_input.isEnabled() is True
        assert dialog.password_input.isEnabled() is True

    def test_auth_mode_change_to_windows(self, qapp, sql_profile):
        dialog = ConnectionDialog(sql_profile)
        # Initially SQL auth, credentials enabled
        assert dialog.username_input.isEnabled() is True

        # Switch to Windows auth
        dialog.auth_combo.setCurrentIndex(0)
        assert dialog.username_input.isEnabled() is False
        assert dialog.password_input.isEnabled() is False

    def test_get_profile_windows_auth(self, qapp, windows_profile):
        dialog = ConnectionDialog(windows_profile)
        profile = dialog.get_profile()

        assert profile.name == "Test Windows"
        assert profile.server == "localhost"
        assert profile.database == "TestDB"
        assert profile.authentication_mode == AuthenticationMode.WINDOWS

    def test_get_profile_sql_auth(self, qapp, sql_profile):
        dialog = ConnectionDialog(sql_profile)
        dialog.password_input.setText("TestPassword123")
        profile = dialog.get_profile()

        assert profile.name == "Test SQL"
        assert profile.server == "db.example.com"
        assert profile.username == "admin"
        assert profile.authentication_mode == AuthenticationMode.SQL_SERVER

    def test_get_password(self, qapp, empty_profile):
        dialog = ConnectionDialog(empty_profile)
        dialog.password_input.setText("SecretPassword")
        assert dialog.get_password() == "SecretPassword"

    def test_encrypt_options(self, qapp, windows_profile):
        dialog = ConnectionDialog(windows_profile)
        assert dialog.encrypt_check.isChecked() is True
        assert dialog.trust_cert_check.isChecked() is False

        dialog.encrypt_check.setChecked(False)
        dialog.trust_cert_check.setChecked(True)
        profile = dialog.get_profile()

        assert profile.encrypt is False
        assert profile.trust_certificate is True

    def test_driver_selector(self, qapp, empty_profile):
        dialog = ConnectionDialog(empty_profile)
        assert dialog.driver_combo.count() == 3
        assert "ODBC Driver 17 for SQL Server" in dialog.driver_combo.currentText()

    @patch("app.dialogs.connection_dialog.OdbcDriverManager.has_sql_server_driver")
    @patch("pyodbc.connect")
    def test_test_connection_success(self, mock_connect, mock_has_driver, qapp, windows_profile):
        """Test successful connection."""
        mock_connect.return_value = MagicMock()
        mock_has_driver.return_value = True
        dialog = ConnectionDialog(windows_profile)

        with patch.object(dialog, "test_connection", wraps=dialog.test_connection):
            dialog.test_connection()
            mock_connect.assert_called_once()

    def test_test_connection_missing_server(self, qapp, empty_profile):
        """Test connection validation for missing server."""
        dialog = ConnectionDialog(empty_profile)
        with patch("app.dialogs.connection_dialog.QMessageBox.warning") as mock_warning:
            dialog.test_connection()
            mock_warning.assert_called_once()
            assert "Server is required" in str(mock_warning.call_args)

    def test_test_connection_missing_password(self, qapp, sql_profile):
        """Test connection validation for missing password."""
        dialog = ConnectionDialog(sql_profile)
        # SQL auth requires password
        with patch("app.dialogs.connection_dialog.QMessageBox.warning") as mock_warning:
            dialog.test_connection()
            mock_warning.assert_called_once()
            assert "Password is required" in str(mock_warning.call_args)

    @patch("app.dialogs.connection_dialog.OdbcDriverManager.has_sql_server_driver")
    @patch("pyodbc.connect")
    def test_test_connection_failure(self, mock_connect, mock_has_driver, qapp, windows_profile):
        """Test connection error handling."""
        import pyodbc
        mock_connect.side_effect = pyodbc.Error("Connection refused")
        mock_has_driver.return_value = True
        dialog = ConnectionDialog(windows_profile)

        with patch("app.dialogs.connection_dialog.QMessageBox.critical") as mock_critical:
            dialog.test_connection()
            mock_critical.assert_called_once()
            assert "Connection Failed" in str(mock_critical.call_args)

    def test_accept_missing_name(self, qapp, windows_profile):
        """Test accept validation for missing name."""
        dialog = ConnectionDialog(windows_profile)
        dialog.name_input.setText("")

        with patch("app.dialogs.connection_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()
            mock_warning.assert_called_once()
            assert "Profile name is required" in str(mock_warning.call_args)

    def test_accept_missing_server(self, qapp, windows_profile):
        """Test accept validation for missing server."""
        dialog = ConnectionDialog(windows_profile)
        dialog.server_input.setText("")

        with patch("app.dialogs.connection_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()
            mock_warning.assert_called_once()
            assert "Server is required" in str(mock_warning.call_args)

    def test_accept_sql_auth_missing_username(self, qapp, sql_profile):
        """Test accept validation for SQL auth missing username."""
        dialog = ConnectionDialog(sql_profile)
        dialog.username_input.setText("")
        dialog.password_input.setText("password")

        with patch("app.dialogs.connection_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()
            mock_warning.assert_called_once()
            assert "Username is required" in str(mock_warning.call_args)

    def test_accept_sql_auth_missing_password(self, qapp, sql_profile):
        """Test accept validation for SQL auth missing password."""
        dialog = ConnectionDialog(sql_profile)
        dialog.password_input.setText("")

        with patch("app.dialogs.connection_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()
            mock_warning.assert_called_once()
            assert "Password is required" in str(mock_warning.call_args)

    def test_accept_valid_windows_auth(self, qapp, windows_profile):
        """Test successful accept for Windows auth."""
        dialog = ConnectionDialog(windows_profile)

        with patch("PySide6.QtWidgets.QDialog.accept") as mock_accept:
            dialog.accept()
            mock_accept.assert_called_once()
            assert dialog.password == ""

    def test_accept_valid_sql_auth(self, qapp, sql_profile):
        """Test successful accept for SQL auth."""
        dialog = ConnectionDialog(sql_profile)
        dialog.password_input.setText("MyPassword123")

        with patch("PySide6.QtWidgets.QDialog.accept") as mock_accept:
            dialog.accept()
            mock_accept.assert_called_once()
            assert dialog.password == "MyPassword123"

    @patch("app.dialogs.connection_dialog.OdbcDriverManager.has_sql_server_driver")
    def test_ensure_driver_installed_found(self, mock_has_driver, qapp, windows_profile):
        """Test ensure_driver_installed when driver exists."""
        mock_has_driver.return_value = True
        dialog = ConnectionDialog(windows_profile)

        result = dialog.ensure_driver_installed(windows_profile)

        assert result is True

    @patch("app.dialogs.connection_dialog.OdbcDriverManager.get_installation_instructions")
    @patch("app.dialogs.connection_dialog.OdbcDriverManager.has_sql_server_driver")
    def test_ensure_driver_installed_user_declines(
        self, mock_has_driver, mock_instructions, qapp, windows_profile
    ):
        """Test ensure_driver_installed when user declines installation."""
        mock_has_driver.return_value = False
        mock_instructions.return_value = "Install instructions"
        dialog = ConnectionDialog(windows_profile)

        with patch("app.dialogs.connection_dialog.QMessageBox.question") as mock_question:
            with patch("app.dialogs.connection_dialog.QMessageBox.information"):
                mock_question.return_value = QMessageBox.No

                result = dialog.ensure_driver_installed(windows_profile)

                assert result is False

    @patch("app.dialogs.connection_dialog.OdbcDriverManager.install_odbc_driver")
    @patch("app.dialogs.connection_dialog.OdbcDriverManager.has_sql_server_driver")
    def test_ensure_driver_installed_user_accepts_success(
        self, mock_has_driver, mock_install, qapp, windows_profile
    ):
        """Test ensure_driver_installed when user accepts and install succeeds."""
        mock_has_driver.return_value = False
        mock_install.return_value = True
        dialog = ConnectionDialog(windows_profile)

        with patch("app.dialogs.connection_dialog.QMessageBox.question") as mock_question:
            with patch("app.dialogs.connection_dialog.QMessageBox.information"):
                mock_question.return_value = QMessageBox.Yes

                result = dialog.ensure_driver_installed(windows_profile)

                assert result is True
                mock_install.assert_called_once()

    @patch("app.dialogs.connection_dialog.OdbcDriverManager.install_odbc_driver")
    @patch("app.dialogs.connection_dialog.OdbcDriverManager.has_sql_server_driver")
    def test_ensure_driver_installed_user_accepts_failure(
        self, mock_has_driver, mock_install, qapp, windows_profile
    ):
        """Test ensure_driver_installed when user accepts but install fails."""
        mock_has_driver.return_value = False
        mock_install.return_value = False
        dialog = ConnectionDialog(windows_profile)

        with patch("app.dialogs.connection_dialog.QMessageBox.question") as mock_question:
            with patch("app.dialogs.connection_dialog.QMessageBox.critical"):
                mock_question.return_value = QMessageBox.Yes

                result = dialog.ensure_driver_installed(windows_profile)

                assert result is False
