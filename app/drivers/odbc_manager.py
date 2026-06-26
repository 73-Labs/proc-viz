import subprocess
import os
import platform
import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class OdbcDriverManager:
    """Detects and manages ODBC drivers for SQL Server."""

    PREFERRED_DRIVERS = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server Native Client 11.0",
    ]

    @staticmethod
    def get_installed_drivers() -> List[str]:
        """Get list of installed ODBC drivers on Windows."""
        if platform.system() != "Windows":
            logger.debug("Non-Windows system, skipping driver detection")
            return []

        try:
            logger.debug("Detecting installed ODBC drivers via PowerShell")
            result = subprocess.run(
                ["powershell", "-Command", "Get-OdbcDriver | Select -ExpandProperty Name"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                drivers = [line.strip() for line in result.stdout.split("\n") if line.strip()]
                logger.info(f"Found {len(drivers)} ODBC drivers: {drivers}")
                return drivers
            else:
                logger.warning(f"PowerShell command failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("Driver detection timed out after 5 seconds")
        except Exception as e:
            logger.error(f"Error detecting drivers: {e}", exc_info=True)

        return []

    @staticmethod
    def has_sql_server_driver() -> bool:
        """Check if any SQL Server ODBC driver is installed."""
        installed = OdbcDriverManager.get_installed_drivers()
        for driver in OdbcDriverManager.PREFERRED_DRIVERS:
            if driver in installed:
                logger.info(f"SQL Server driver found: {driver}")
                return True
        logger.warning("No SQL Server ODBC driver found")
        return False

    @staticmethod
    def get_available_driver() -> Optional[str]:
        """Get first available SQL Server ODBC driver."""
        installed = OdbcDriverManager.get_installed_drivers()
        for driver in OdbcDriverManager.PREFERRED_DRIVERS:
            if driver in installed:
                logger.info(f"Using driver: {driver}")
                return driver
        logger.warning("No preferred driver available")
        return None

    @staticmethod
    def install_odbc_driver() -> bool:
        """
        Attempt to install ODBC Driver 18 for SQL Server.
        Returns True if installation was successful or driver already exists.
        """
        logger.info("=" * 60)
        logger.info("Starting ODBC Driver installation process")
        logger.info(f"Platform: {platform.system()}")

        if OdbcDriverManager.has_sql_server_driver():
            logger.info("SQL Server driver already installed, skipping installation")
            return True

        if platform.system() != "Windows":
            logger.warning("Not on Windows, installation not supported")
            return False

        logger.info("Attempting installation via Chocolatey")
        if OdbcDriverManager._install_via_choco():
            logger.info("Installation successful via Chocolatey")
            return True

        logger.info("Chocolatey failed, attempting MSI installation")
        if OdbcDriverManager._install_via_msi():
            logger.info("Installation successful via MSI")
            return True

        logger.error("All installation methods failed")
        return False

    @staticmethod
    def _install_via_choco() -> bool:
        """Try to install via Chocolatey."""
        try:
            logger.info("Attempting Chocolatey installation: choco install msodbcsql18 -y")
            result = subprocess.run(
                ["choco", "install", "msodbcsql18", "-y"],
                capture_output=True,
                timeout=300,
            )
            if result.returncode == 0:
                logger.info("Chocolatey installation successful")
                return True
            else:
                logger.warning(f"Chocolatey installation failed: {result.stderr.decode('utf-8', errors='ignore')}")
                return False
        except FileNotFoundError:
            logger.warning("Chocolatey not found on system")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Chocolatey installation timed out after 300 seconds")
            return False
        except Exception as e:
            logger.error(f"Chocolatey installation error: {e}", exc_info=True)
            return False

    @staticmethod
    def _install_via_msi() -> bool:
        """
        Download and install ODBC Driver 18 via MSI.
        This downloads from Microsoft's official source.
        """
        try:
            import urllib.request
            import tempfile

            msi_url = "https://go.microsoft.com/fwlink/?linkid=2249004"
            temp_dir = Path(tempfile.gettempdir())
            installer_path = temp_dir / "msodbcsql18.msi"

            logger.info(f"MSI download URL: {msi_url}")
            logger.info(f"Temp directory: {temp_dir}")
            logger.info(f"Installer path: {installer_path}")

            logger.info("Starting ODBC Driver 18 MSI download...")
            try:
                urllib.request.urlretrieve(msi_url, installer_path)
                logger.info(f"Download complete. File size: {installer_path.stat().st_size} bytes")
            except urllib.error.URLError as e:
                logger.error(f"URL error during download: {e}", exc_info=True)
                return False
            except urllib.error.HTTPError as e:
                logger.error(f"HTTP error during download: {e.code} {e.reason}", exc_info=True)
                return False
            except Exception as e:
                logger.error(f"Download error: {e}", exc_info=True)
                return False

            if not installer_path.exists():
                logger.error("MSI file not found after download")
                return False

            logger.info("Starting MSI installation via msiexec")
            result = subprocess.run(
                [
                    "msiexec",
                    "/i",
                    str(installer_path),
                    "/quiet",
                    "/norestart",
                    "IACCEPTMSODBCSQLLICENSETERMS=YES",
                ],
                capture_output=True,
                timeout=300,
            )

            if result.returncode == 0:
                logger.info("MSI installation successful")
            else:
                logger.error(f"MSI installation failed with code {result.returncode}")
                logger.error(f"stdout: {result.stdout.decode('utf-8', errors='ignore')}")
                logger.error(f"stderr: {result.stderr.decode('utf-8', errors='ignore')}")

            installer_path.unlink(missing_ok=True)
            return result.returncode == 0

        except subprocess.TimeoutExpired:
            logger.error("MSI installation timed out after 300 seconds")
            return False
        except Exception as e:
            logger.error(f"MSI installation error: {e}", exc_info=True)
            return False

    @staticmethod
    def get_installation_instructions() -> str:
        """Get user-friendly installation instructions."""
        return """
ODBC Driver for SQL Server is not installed.

To install manually:
1. Download from Microsoft:
   https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

2. Install "ODBC Driver 18 for SQL Server" or "ODBC Driver 17 for SQL Server"

3. Restart the application

Alternative (requires Chocolatey):
   choco install msodbcsql18 -y

After installation, restart the app.
        """.strip()
