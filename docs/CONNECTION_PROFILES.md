# Connection Profiles

Connection profiles manage database connection settings with support for multiple authentication methods and secure password storage.

## Features

- **Multiple authentication modes**: Windows Authentication and SQL Server username/password
- **Secure password storage**: Passwords stored in system keyring (Windows Credential Manager)
- **Local profile storage**: Non-secret profile data stored in JSON (`~/.proc-viz/profiles.json`)
- **Optional password persistence**: "Save password" option for automatic login

## Models

### ConnectionProfile

Data class representing a database connection profile.

**Fields:**
- `name` (str): Profile name
- `server` (str): Database server hostname/IP
- `port` (int, default=1433): SQL Server port
- `database` (str): Database name
- `authentication_mode` (AuthenticationMode): Windows or SQL Server auth
- `username` (Optional[str]): Username for SQL Server authentication
- `driver` (str): ODBC driver (default: "ODBC Driver 17 for SQL Server")
- `encrypt` (bool, default=True): Enable connection encryption
- `trust_certificate` (bool, default=False): Trust self-signed certificates
- `save_password` (bool, default=False): Save password to keyring

**Methods:**
- `to_dict()`: Convert to dictionary (excludes password)
- `from_dict(data)`: Create from dictionary
- `get_connection_string(password)`: Generate ODBC connection string

## Usage

### Create a Windows Authentication Profile

```python
from app.models import ConnectionProfile, AuthenticationMode

profile = ConnectionProfile(
    name="Production Server",
    server="db.example.com",
    port=1433,
    database="MyDatabase",
    authentication_mode=AuthenticationMode.WINDOWS,
    encrypt=True,
    trust_certificate=False,
)
```

### Create SQL Server Authentication Profile

```python
profile = ConnectionProfile(
    name="Dev Server",
    server="localhost",
    port=1433,
    database="DevDB",
    authentication_mode=AuthenticationMode.SQL_SERVER,
    username="sa",
    save_password=True,  # Enable password saving
)
```

### Save Profile with Password

```python
from app.storage import ProfileManager

manager = ProfileManager()

# Save profile with password
manager.save_profile(profile, password="YourPassword123")

# Password is stored in Windows Credential Manager
# Profile data is stored in ~/.proc-viz/profiles.json
```

### Load Profile and Get Password

```python
# Load profile
profile = manager.load_profile("Dev Server")

# Retrieve password from keyring (if save_password was True)
password = manager.get_password("Dev Server")

# Generate connection string
conn_str = profile.get_connection_string(password)
```

### List All Profiles

```python
all_profiles = manager.load_all_profiles()
for profile in all_profiles:
    print(f"Name: {profile.name}, Server: {profile.server}")
```

### Delete Profile

```python
# Removes profile and password from storage
manager.delete_profile("Dev Server")
```

## Storage Locations

- **Profiles**: `~/.proc-viz/profiles.json`
  - Contains all profile settings except passwords
  - Plain JSON, human-readable
  
- **Passwords**: Windows Credential Manager (via `keyring`)
  - Service name: `proc-viz`
  - One entry per profile
  - Only accessible when user is logged in
  - Persists across application restarts

## Security Notes

- Passwords are never written to disk in plaintext
- Passwords are only stored in keyring if `save_password=True`
- Profile deletion automatically removes associated password from keyring
- Connection strings should not be logged or displayed to users
