import pytest
from unittest.mock import patch, MagicMock
from app.drivers.odbc_manager import OdbcDriverManager


class TestOdbcDriverManager:
    def test_preferred_drivers_list(self):
        """Test that preferred drivers are defined."""
        assert len(OdbcDriverManager.PREFERRED_DRIVERS) > 0
        assert "ODBC Driver 18 for SQL Server" in OdbcDriverManager.PREFERRED_DRIVERS
        assert "ODBC Driver 17 for SQL Server" in OdbcDriverManager.PREFERRED_DRIVERS

    @patch("subprocess.run")
    @patch("platform.system")
    def test_get_installed_drivers_windows(self, mock_system, mock_run):
        """Test getting installed drivers on Windows."""
        mock_system.return_value = "Windows"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ODBC Driver 17 for SQL Server\nODBC Driver 18 for SQL Server\n",
        )

        drivers = OdbcDriverManager.get_installed_drivers()

        assert "ODBC Driver 17 for SQL Server" in drivers
        assert "ODBC Driver 18 for SQL Server" in drivers

    @patch("platform.system")
    def test_get_installed_drivers_non_windows(self, mock_system):
        """Test that non-Windows systems return empty list."""
        mock_system.return_value = "Linux"

        drivers = OdbcDriverManager.get_installed_drivers()

        assert drivers == []

    @patch("subprocess.run")
    @patch("platform.system")
    def test_get_installed_drivers_command_failure(self, mock_system, mock_run):
        """Test handling of command failure."""
        mock_system.return_value = "Windows"
        mock_run.side_effect = Exception("Command failed")

        drivers = OdbcDriverManager.get_installed_drivers()

        assert drivers == []

    @patch.object(OdbcDriverManager, "get_installed_drivers")
    def test_has_sql_server_driver_found(self, mock_get_drivers):
        """Test detection when driver is installed."""
        mock_get_drivers.return_value = [
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 18 for SQL Server",
        ]

        assert OdbcDriverManager.has_sql_server_driver() is True

    @patch.object(OdbcDriverManager, "get_installed_drivers")
    def test_has_sql_server_driver_not_found(self, mock_get_drivers):
        """Test detection when driver is not installed."""
        mock_get_drivers.return_value = ["Some Other Driver"]

        assert OdbcDriverManager.has_sql_server_driver() is False

    @patch.object(OdbcDriverManager, "get_installed_drivers")
    def test_get_available_driver_preferred_order(self, mock_get_drivers):
        """Test that preferred driver order is respected."""
        mock_get_drivers.return_value = [
            "SQL Server Native Client 11.0",
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 18 for SQL Server",
        ]

        driver = OdbcDriverManager.get_available_driver()

        # Should return Driver 18 (highest preference)
        assert driver == "ODBC Driver 18 for SQL Server"

    @patch.object(OdbcDriverManager, "get_installed_drivers")
    def test_get_available_driver_not_found(self, mock_get_drivers):
        """Test when no driver is available."""
        mock_get_drivers.return_value = ["Some Other Driver"]

        driver = OdbcDriverManager.get_available_driver()

        assert driver is None

    @patch.object(OdbcDriverManager, "has_sql_server_driver")
    def test_install_odbc_driver_already_installed(self, mock_has_driver):
        """Test install when driver already exists."""
        mock_has_driver.return_value = True

        result = OdbcDriverManager.install_odbc_driver()

        assert result is True

    @patch.object(OdbcDriverManager, "_install_via_msi")
    @patch.object(OdbcDriverManager, "_install_via_choco")
    @patch.object(OdbcDriverManager, "has_sql_server_driver")
    @patch("platform.system")
    def test_install_odbc_driver_attempts_choco_first(
        self, mock_system, mock_has_driver, mock_choco, mock_msi
    ):
        """Test that Chocolatey installation is attempted first."""
        mock_system.return_value = "Windows"
        mock_has_driver.return_value = False
        mock_choco.return_value = True
        mock_msi.return_value = False

        result = OdbcDriverManager.install_odbc_driver()

        assert result is True
        mock_choco.assert_called_once()
        mock_msi.assert_not_called()

    @patch.object(OdbcDriverManager, "_install_via_msi")
    @patch.object(OdbcDriverManager, "_install_via_choco")
    @patch.object(OdbcDriverManager, "has_sql_server_driver")
    @patch("platform.system")
    def test_install_odbc_driver_fallback_to_msi(
        self, mock_system, mock_has_driver, mock_choco, mock_msi
    ):
        """Test fallback to MSI when Chocolatey fails."""
        mock_system.return_value = "Windows"
        mock_has_driver.return_value = False
        mock_choco.return_value = False
        mock_msi.return_value = True

        result = OdbcDriverManager.install_odbc_driver()

        assert result is True
        mock_choco.assert_called_once()
        mock_msi.assert_called_once()

    @patch.object(OdbcDriverManager, "has_sql_server_driver")
    @patch("platform.system")
    def test_install_odbc_driver_non_windows(self, mock_system, mock_has_driver):
        """Test install on non-Windows returns False."""
        mock_system.return_value = "Linux"
        mock_has_driver.return_value = False

        result = OdbcDriverManager.install_odbc_driver()

        assert result is False

    @patch("subprocess.run")
    def test_install_via_choco_success(self, mock_run):
        """Test successful Chocolatey installation."""
        mock_run.return_value = MagicMock(returncode=0)

        result = OdbcDriverManager._install_via_choco()

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_install_via_choco_failure(self, mock_run):
        """Test failed Chocolatey installation."""
        mock_run.return_value = MagicMock(returncode=1)

        result = OdbcDriverManager._install_via_choco()

        assert result is False

    @patch("subprocess.run")
    def test_install_via_choco_exception(self, mock_run):
        """Test exception during Chocolatey installation."""
        mock_run.side_effect = Exception("Command not found")

        result = OdbcDriverManager._install_via_choco()

        assert result is False

    def test_get_installation_instructions(self):
        """Test that installation instructions are provided."""
        instructions = OdbcDriverManager.get_installation_instructions()

        assert isinstance(instructions, str)
        assert "Microsoft" in instructions
        assert "ODBC Driver" in instructions
        assert len(instructions) > 50
