# Connection Dialog

Interactive dialog for creating and editing database connection profiles with support for Windows Authentication and SQL Server login.

## Features

- **Profile Configuration**: Set profile name, server, port, database, and ODBC driver
- **Authentication Modes**: Switch between Windows Authentication and SQL Server Login
- **Dynamic UI**: Username/password fields automatically enable/disable based on auth type
- **Encryption Options**: Configure connection encryption and certificate trust settings
- **Test Connection**: Validate connectivity before saving
- **Error Handling**: Clear, detailed error messages for connection issues
- **Password Management**: Optional password saving via keyring

## Usage

### Basic Setup

```python
from PySide6.QtWidgets import QApplication
from app.dialogs import ConnectionDialog
from app.models import ConnectionProfile, AuthenticationMode

app = QApplication([])

# Create new profile dialog
dialog = ConnectionDialog()

# Or edit existing profile
existing_profile = ConnectionProfile(
    name="My Server",
    server="db.example.com",
    database="MyDB",
    authentication_mode=AuthenticationMode.WINDOWS
)
dialog = ConnectionDialog(existing_profile)

if dialog.exec() == ConnectionDialog.Accepted:
    profile = dialog.get_profile()
    password = dialog.get_password()
    print(f"Connected to {profile.server}")
```

### Authentication Modes

#### Windows Authentication

```python
dialog = ConnectionDialog()
dialog.auth_combo.setCurrentIndex(0)  # Select "Windows Authentication"

# Username and password fields are automatically disabled
if dialog.exec() == ConnectionDialog.Accepted:
    profile = dialog.get_profile()
    # profile.authentication_mode == AuthenticationMode.WINDOWS
    # Connection uses Trusted_Connection=yes
```

#### SQL Server Login

```python
dialog = ConnectionDialog()
dialog.auth_combo.setCurrentIndex(1)  # Select "SQL Server Login"

# Username and password fields are automatically enabled
if dialog.exec() == ConnectionDialog.Accepted:
    profile = dialog.get_profile()
    password = dialog.get_password()
    # profile.authentication_mode == AuthenticationMode.SQL_SERVER
    # profile.username is set
    # Connection uses UID and PWD
```

### Testing Connections

```python
dialog = ConnectionDialog()

# User can click "Test Connection" button to validate before saving
# Connection errors are displayed in message boxes:
# - Missing required fields: "Server is required"
# - Connection failures: Shows detailed error from pyodbc
# - Other errors: Shows unexpected error details
```

### Encryption Options

```python
dialog = ConnectionDialog()

# Configure encryption
dialog.encrypt_check.setChecked(True)         # Encrypt=yes
dialog.trust_cert_check.setChecked(True)      # TrustServerCertificate=yes

if dialog.exec() == ConnectionDialog.Accepted:
    profile = dialog.get_profile()
    # profile.encrypt == True
    # profile.trust_certificate == True
```

### Driver Selection

```python
dialog = ConnectionDialog()

# Available drivers:
# - ODBC Driver 17 for SQL Server (default)
# - ODBC Driver 18 for SQL Server
# - SQL Server Native Client 11.0

dialog.driver_combo.setCurrentText("ODBC Driver 18 for SQL Server")

if dialog.exec() == ConnectionDialog.Accepted:
    profile = dialog.get_profile()
    # profile.driver == "ODBC Driver 18 for SQL Server"
```

### Save Password Option

```python
dialog = ConnectionDialog()
dialog.auth_combo.setCurrentIndex(1)  # SQL Server auth

# Enable password saving
dialog.save_password_check.setChecked(True)

if dialog.exec() == ConnectionDialog.Accepted:
    profile = dialog.get_profile()
    password = dialog.get_password()
    
    # Save to keyring if save_password is True
    if profile.save_password:
        manager.save_profile(profile, password)
```

## Dialog Controls

### Input Fields

| Field | Description | Required | Type |
|-------|-------------|----------|------|
| Profile Name | Friendly name for the connection | Yes | Text |
| Server | Hostname or IP address | Yes | Text |
| Port | SQL Server port | No | Number (default: 1433) |
| Database | Database name | No | Text |
| Driver | ODBC driver version | No | Dropdown |
| Authentication | Auth method | No | Dropdown |
| Username | SQL auth username | Conditional* | Text |
| Password | SQL auth password | Conditional* | Password |

*Required only when SQL Server Authentication is selected

### Buttons

- **Test Connection**: Validates the connection without saving
- **Connect**: Saves profile and closes dialog (with validation)
- **Cancel**: Closes dialog without saving

## Validation

### Test Connection Validation

- Server field is not empty
- Password field is not empty (for SQL Server auth)
- Can connect to server with timeout of 5 seconds

### Accept Validation

- Profile name is not empty
- Server field is not empty
- For SQL Server auth:
  - Username is not empty
  - Password is not empty

## Error Messages

| Condition | Message |
|-----------|---------|
| Missing server | "Server is required." |
| Missing password (SQL auth) | "Password is required for SQL Server authentication." |
| Missing profile name | "Profile name is required." |
| Missing username (SQL auth) | "Username is required for SQL Server authentication." |
| Connection refused | "Failed to connect to database: [pyodbc error]" |
| Authentication failed | "Failed to connect to database: [pyodbc error]" |
| Unexpected error | "An unexpected error occurred: [error details]" |

## Integration Example

```python
from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget
from app.dialogs import ConnectionDialog
from app.storage import ProfileManager
from app.models import AuthenticationMode
import pyodbc

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.profile_manager = ProfileManager()
        
        button = QPushButton("New Connection")
        button.clicked.connect(self.open_connection_dialog)
        
        layout = QVBoxLayout()
        layout.addWidget(button)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
    
    def open_connection_dialog(self):
        dialog = ConnectionDialog()
        
        if dialog.exec() == ConnectionDialog.Accepted:
            profile = dialog.get_profile()
            password = dialog.get_password()
            
            # Save profile
            self.profile_manager.save_profile(profile, password)
            
            # Connect to database
            try:
                conn_str = profile.get_connection_string(password)
                connection = pyodbc.connect(conn_str)
                # Use connection...
                connection.close()
            except pyodbc.Error as e:
                print(f"Connection error: {e}")
```

## Design Notes

- Auth mode changes automatically enable/disable credential fields
- Password field uses echo mode to hide input
- Connection strings are never stored or logged
- Test connection has 5-second timeout to prevent hanging UI
- All validations provide specific error messages for user guidance
