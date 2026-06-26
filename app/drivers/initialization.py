from PySide6.QtWidgets import QMessageBox, QApplication
from app.drivers.odbc_manager import OdbcDriverManager


def check_odbc_drivers():
    """
    Check if ODBC drivers are installed.
    If not, show dialog with options.
    """
    if OdbcDriverManager.has_sql_server_driver():
        return True

    available_driver = OdbcDriverManager.get_available_driver()
    if available_driver:
        return True

    app = QApplication.instance()
    if not app:
        return False

    reply = QMessageBox.question(
        None,
        "ODBC Driver Missing",
        "SQL Server ODBC driver is not installed.\n\n"
        "Would you like to:\n"
        "- Yes: Attempt automatic installation\n"
        "- No: See manual installation instructions",
        QMessageBox.Yes | QMessageBox.No,
    )

    if reply == QMessageBox.Yes:
        return attempt_install_odbc()
    else:
        show_installation_instructions()
        return False


def attempt_install_odbc() -> bool:
    """Attempt to install ODBC driver and show progress."""
    app = QApplication.instance()
    if not app:
        return False

    progress_dialog = QMessageBox(
        QMessageBox.Information,
        "Installing ODBC Driver",
        "Downloading and installing ODBC Driver 18 for SQL Server...\n\n"
        "This may take a few minutes.",
        QMessageBox.NoButton,
    )
    progress_dialog.show()
    app.processEvents()

    success = OdbcDriverManager.install_odbc_driver()

    progress_dialog.close()

    if success:
        QMessageBox.information(
            None,
            "Installation Successful",
            "ODBC Driver 18 for SQL Server has been installed.\n\n"
            "The application will now restart.",
        )
        return True
    else:
        QMessageBox.warning(
            None,
            "Installation Failed",
            "Automatic installation failed.\n\n"
            "Please install manually:\n"
            "https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server",
        )
        return False


def show_installation_instructions():
    """Show ODBC installation instructions."""
    instructions = OdbcDriverManager.get_installation_instructions()
    QMessageBox.information(
        None,
        "Install ODBC Driver",
        instructions,
    )
