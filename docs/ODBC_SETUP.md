# ODBC Driver Setup and Auto-Installation

The application checks for required ODBC drivers when you click "Test Connection" and provides options to install them if missing.

## Automatic Driver Check

When you click "Test Connection":

1. **Checks** if SQL Server ODBC drivers are installed
2. **If found**: Proceeds with connection test
3. **If not found**: Shows dialog with installation options

## Installation Dialog

When you click "Test Connection" and driver is missing, dialog appears:

```
ODBC Driver Missing
---
ODBC driver required for [server] is not installed.

Would you like to attempt automatic installation?
```

Click **"Yes"** to attempt automatic installation via:
1. **Chocolatey** (if installed): `choco install msodbcsql18 -y`
2. **Direct MSI download**: Downloads from Microsoft (~100 MB)

If installation succeeds, connection test resumes automatically.

### Option 2: Manual Installation

Click **"No"** to see manual instructions. Or manually install:

**Windows:**
1. Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
2. Install "ODBC Driver 18 for SQL Server" or "ODBC Driver 17 for SQL Server"
3. Restart app

**PowerShell:**
```powershell
# Verify installation
Get-OdbcDriver | Select Name
```

**With Chocolatey:**
```powershell
choco install msodbcsql18 -y
```

## Supported Drivers

App supports (in preference order):

1. ODBC Driver 18 for SQL Server (latest)
2. ODBC Driver 17 for SQL Server
3. SQL Server Native Client 11.0

## How It Works

### OdbcDriverManager Class

Detects and installs ODBC drivers:

```python
from app.drivers import OdbcDriverManager

# Check if driver installed
if OdbcDriverManager.has_sql_server_driver():
    print("Driver found!")

# Get available driver
driver = OdbcDriverManager.get_available_driver()
# Returns: "ODBC Driver 18 for SQL Server" or similar

# Attempt installation
if OdbcDriverManager.install_odbc_driver():
    print("Installation successful")
else:
    print("Installation failed")

# Get all installed drivers
drivers = OdbcDriverManager.get_installed_drivers()
# Returns: ["ODBC Driver 18 for SQL Server", ...]
```

### Startup Initialization

Called in `main.py`:

```python
from app.drivers import check_odbc_drivers

app = QApplication(sys.argv)

# Show driver check dialog if needed
if not check_odbc_drivers():
    sys.exit(1)

window = MainWindow()
window.show()
```

## Error Handling

### Installation Fails

If automatic installation fails:
- Shows warning dialog
- Provides Microsoft download link
- App exits (driver required for connections)

### Driver Already Installed

- App continues without showing dialogs
- Automatically detects installed drivers

### Non-Windows Systems

- Skips driver check (returns True)
- Allows app to run (drivers handled by system)

## Troubleshooting

### "Data source name not found" Error

This means ODBC drivers aren't installed. Run app startup again or:

```powershell
# Windows 11/10
New-Item -Path "HKLM:\SYSTEM\CurrentControlSet\Services\ODBC"
choco install msodbcsql18 -y
```

### Chocolatey Not Found

App falls back to direct MSI download. Or install Chocolatey:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### Stuck on Installation

- Wait 5+ minutes (download can be large)
- If still stuck, restart computer and reinstall manually

## Integration

### In Connection Dialog

```python
from app.dialogs import ConnectionDialog

dialog = ConnectionDialog()
if dialog.exec() == ConnectionDialog.Accepted:
    profile = dialog.get_profile()
    password = dialog.get_password()
    
    # Driver is already checked and optionally installed
    # via ensure_driver_installed() during Test Connection
```

### Using OdbcDriverManager Directly

```python
from app.drivers import OdbcDriverManager

# Check if driver exists
if OdbcDriverManager.has_sql_server_driver():
    driver = OdbcDriverManager.get_available_driver()
    print(f"Using: {driver}")
else:
    # Attempt installation
    if OdbcDriverManager.install_odbc_driver():
        print("Driver installed successfully")
```

### Custom Driver List

Edit `OdbcDriverManager.PREFERRED_DRIVERS` to support additional drivers:

```python
PREFERRED_DRIVERS = [
    "ODBC Driver 18 for SQL Server",  # Most preferred
    "ODBC Driver 17 for SQL Server",
    "Custom Driver Name",              # Add custom drivers
]
```

## System Requirements

- Windows 7 or later (driver check runs on Windows only)
- Internet connection (for MSI download)
- Administrator privileges (for installation)
- ~100 MB disk space (for ODBC driver)

## Security Notes

- MSI downloads from official Microsoft servers only
- Installation is silent (no user interaction after confirmation)
- No malware bundled or installed
- Full installation audit available in Windows Event Viewer
