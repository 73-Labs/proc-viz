import subprocess
import os
import platform
import logging
import tempfile
import time
import urllib.request
from typing import List, Optional
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class OdbcDriverManager:
    """Detects and manages ODBC drivers for SQL Server."""

    DRIVER_NAME = "ODBC Driver 18 for SQL Server"
    PREFERRED_DRIVERS = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server Native Client 11.0",
    ]

    DOWNLOAD_URLS = {
        "AMD64": "https://go.microsoft.com/fwlink/?linkid=2249006",
        "x86": "https://go.microsoft.com/fwlink/?linkid=2249005",
        "ARM64": "https://go.microsoft.com/fwlink/?linkid=2249004",
    }

    @staticmethod
    def _is_driver_in_registry() -> bool:
        """Check Windows registry for ODBC driver installation."""
        if platform.system() != "Windows":
            return False

        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers",
                0,
                winreg.KEY_READ
            )
            index = 0
            while True:
                try:
                    driver_name, _, _ = winreg.EnumValue(key, index)
                    if OdbcDriverManager.DRIVER_NAME in driver_name:
                        winreg.CloseKey(key)
                        logger.info(f"Found driver in registry: {driver_name}")
                        return True
                    index += 1
                except WindowsError:
                    break
            winreg.CloseKey(key)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"Registry check error: {e}")

        return False

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
        """Check if ODBC Driver 18 for SQL Server is installed. Returns True only if preferred drivers found."""
        # Check registry first (faster)
        if OdbcDriverManager._is_driver_in_registry():
            return True

        # Fallback to PowerShell check - only preferred drivers (not generic "SQL Server")
        installed = OdbcDriverManager.get_installed_drivers()
        for driver in OdbcDriverManager.PREFERRED_DRIVERS:
            if driver in installed:
                logger.info(f"SQL Server driver found: {driver}")
                return True

        logger.warning("ODBC Driver 18 not found, installation needed")
        return False

    @staticmethod
    def get_available_driver() -> Optional[str]:
        """Get first available SQL Server ODBC driver."""
        installed = OdbcDriverManager.get_installed_drivers()
        for driver in OdbcDriverManager.PREFERRED_DRIVERS:
            if driver in installed:
                logger.info(f"Using driver: {driver}")
                return driver

        # Return any driver with "SQL Server" in name
        for driver in installed:
            if "SQL Server" in driver:
                logger.info(f"Using driver: {driver}")
                return driver

        logger.warning("No preferred driver available")
        return None

    @staticmethod
    def install_odbc_driver() -> bool:
        """
        Silent download and install ODBC Driver 18 for SQL Server.
        Returns True if installation successful or driver already exists.
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

        # Determine system architecture
        arch = platform.machine()
        if arch not in OdbcDriverManager.DOWNLOAD_URLS:
            logger.error(f"Unsupported architecture: {arch}")
            return False

        download_url = OdbcDriverManager.DOWNLOAD_URLS[arch]
        logger.info(f"Detected architecture: {arch}")

        # Download and install
        temp_dir = Path(tempfile.gettempdir())
        msi_path = temp_dir / "msodbcsql18.msi"
        log_path = temp_dir / "msodbcsql18_install.log"

        try:
            logger.info(f"Downloading driver from {download_url}")
            urllib.request.urlretrieve(download_url, str(msi_path))
            logger.info(f"Downloaded to {msi_path}, size: {msi_path.stat().st_size} bytes")

            if not msi_path.exists():
                logger.error("MSI file not found after download")
                return False

            logger.info("Starting MSI installation via msiexec with verbose logging")
            result = subprocess.run(
                [
                    "msiexec",
                    "/i",
                    str(msi_path),
                    "IACCEPTMSODBCSQLLICENSETERMS=YES",
                    "/qn",
                    "/norestart",
                    f"/l*v",
                    str(log_path),
                ],
                capture_output=True,
                timeout=600,
            )

            # Read verbose log if available
            if log_path.exists():
                try:
                    with open(log_path, 'r', errors='ignore') as f:
                        log_content = f.read()
                        logger.info(f"MSI Log:\n{log_content[-2000:]}")  # Last 2000 chars
                except Exception as e:
                    logger.warning(f"Could not read MSI log: {e}")

            # msiexec return codes: 0 = success, 3010 = success + reboot needed, 1641 = reboot initiated
            if result.returncode in (0, 3010, 1641):
                logger.info(f"MSI installation completed with code {result.returncode}")
                time.sleep(2)  # Wait for registry to update

                if OdbcDriverManager.has_sql_server_driver():
                    logger.info("Driver verified in registry")
                    return True
                else:
                    logger.warning("Driver not found in registry after installation")
                    return False
            else:
                logger.error(f"MSI installation failed with code {result.returncode}")
                logger.error(f"stdout: {result.stdout.decode('utf-8', errors='ignore')}")
                logger.error(f"stderr: {result.stderr.decode('utf-8', errors='ignore')}")
                return False

        except urllib.error.URLError as e:
            logger.error(f"URL error during download: {e}")
            return False
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP error during download: {e.code} {e.reason}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Installation timed out")
            return False
        except Exception as e:
            logger.error(f"Installation error: {e}", exc_info=True)
            return False
        finally:
            # Cleanup temp files
            for path in [msi_path, log_path]:
                if path.exists():
                    try:
                        path.unlink()
                        logger.info(f"Cleaned up {path.name}")
                    except Exception as e:
                        logger.warning(f"Could not delete {path.name}: {e}")

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

After installation, restart the app.
        """.strip()
