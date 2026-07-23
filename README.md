# proc-viz — SQL Server Procedure Visualizer

Desktop application for exploring, analyzing, and understanding SQL Server stored procedures. Browse procedures organized by schema, view dependencies, search by table name, and examine source code with syntax highlighting.

## Features

### Connection Management
- **Save multiple database profiles** — Store and switch between different SQL Server connections
- **Edit/delete/rename profiles** — Manage saved connections from UI
- **Secure password storage** — Passwords stored in system keyring, never plaintext
- **Connection status** — Visual indicators show active connections

### Procedure Exploration
- **Schema browser** — Hierarchical tree view of schemas → procedures → functions
- **Procedure search** — Quick filter by name (Ctrl+K)
- **Table name search** — Find all procedures/functions that reference a specific table
- **Lazy loading** — Efficient loading with progress indicators

### Analysis & Details
- **Dependency analysis** — See which procedures call which others
- **Called procedures** — View objects that a procedure invokes
- **Calling procedures** — See reverse dependencies (what calls this)
- **Procedure source code** — View full SQL definitions with syntax highlighting
- **Parameters** — View procedure input/output parameters
- **Details tab** — Additional metadata and information

### UI/UX
- **Tabbed interface** — Source, Parameters, Details tabs for procedure info
- **Syntax highlighting** — SQL code with proper color scheme
- **Loading overlays** — Dynamic status messages during data operations
- **Splitter layout** — Resizable panels for browser and details
- **Cross-platform** — Runs on Windows, macOS, Linux

## System Architecture

### Components

**Database Layer** (`app/drivers/`)
- `DatabaseDriver` — Abstract interface for database operations
- `SQLServerDriver` — SQL Server implementation using pymssql
- `ConnectionManager` — Creates and manages connections
- `DriverFactory` — Pluggable driver creation pattern

**Data Models** (`app/models/`)
- `ConnectionProfile` — Stores connection credentials and settings
- Data transfer objects for Database, Schema, Procedure, Function, Table, etc.

**Storage** (`app/storage/`)
- `ProfileManager` — Persists connection profiles to disk
- Secure password handling via system keyring

**UI Widgets** (`app/widgets/`)
- `DatabaseExplorer` — Main exploration widget with tree/details panels
- `SqlSyntaxHighlighter` — SQL code highlighting
- `LoadingOverlay` — Animated loading spinner with status messages

**UI Dialogs** (`app/dialogs/`)
- `ConnectionDialog` — New/edit connection UI
- `ConnectionManagerDialog` — Manage saved profiles

**Data Access** (`app/db_accessor.py`)
- `DatabaseAccessor` — Database-agnostic accessor wrapping driver

### How It Works

1. **Connection** — User creates profile with server/database/auth credentials
2. **Profile Storage** — Credentials saved securely (password in keyring, config in JSON)
3. **Schema Loading** — On connect, app fetches all schemas and procedures
4. **Tree Population** — Procedures organized hierarchically: Database → Schema → Procedures
5. **Selection** — User clicks procedure to view source, parameters, dependencies
6. **Dependency Query** — App queries SQL Server system views for dependency info
7. **Display** — Source code highlighted, dependencies shown as clickable tree items

### Data Flow

```
ConnectionDialog → Profile storage → ConnectionManager
                                          ↓
                                 DatabaseDriver (SQL Server)
                                          ↓
DatabaseExplorer ← DatabaseAccessor ← System views & object definitions
```

## Installation

### Requirements
- Python 3.8+
- SQL Server database (MSSQL 2016+)

### From Source

```bash
git clone https://github.com/73-Labs/proc-viz.git
cd proc-viz
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Development

```bash
python main.py
```

Or via installed command:
```bash
procedures-visualizer
```

### Build Standalone Executable

```bash
pip install -e ".[dev]"
pyinstaller --onefile --windowed --name procedures-visualizer --add-data app:app main.py
```

Executable in `dist/procedures-visualizer`

## Usage

### Create Connection

1. Click **Connect** or File → New Connection
2. Enter connection details:
   - **Server** — SQL Server hostname or IP
   - **Database** — Target database name
   - **Username** — Authentication user (Windows or SQL Server auth)
   - **Password** — User password (stored securely)
3. Click **Connect** to load procedures

### Explore Procedures

- **Left panel** — Hierarchical tree of procedures organized by schema
- **Filter box** (Ctrl+K) — Quick search by procedure name
- **Table filter** — Enter table name to find all procedures referencing it
- **Click procedure** — View source code, parameters, dependencies in right panel

### View Dependencies

- **Called procedures** — Objects this procedure invokes
- **Calling procedures** — Procedures that call this one
- **Dependency tree** — Click tree items to navigate between related objects

### Manage Connections

- **Manage button** — Open connection manager dialog
- **Edit** — Modify connection details or rename
- **Delete** — Remove saved profile
- **Dropdown** — Switch between saved profiles

## Development

### Project Structure

```
proc-viz/
├── app/
│   ├── dialogs/           # Connection and manager dialogs
│   ├── drivers/           # Database driver abstractions
│   ├── models/            # Data models and DTOs
│   ├── storage/           # Profile persistence
│   ├── widgets/           # UI components
│   ├── db_accessor.py     # Database accessor
│   ├── main_window.py     # Main application window
│   └── __init__.py
├── tests/                 # Test suite
├── main.py                # Application entry point
├── pyproject.toml         # Project configuration
├── requirements.txt       # Dependencies
├── docker-compose.yml     # SQL Server test container
├── init-db.sql            # Test database setup
└── README.md              # This file
```

### Add Database Support

1. Create driver: `app/drivers/YOUR_DATABASE_driver.py` extending `DatabaseDriver`
2. Implement required methods (get_databases, get_schemas, get_procedures, etc.)
3. Update `DriverFactory` to recognize new type
4. Add dependency to `pyproject.toml`

### Run Tests

```bash
./run_tests.sh
./run_tests.sh -v                    # Verbose
./run_tests.sh tests/test_file.py    # Specific file
```

### Run SQL Server integration tests

Unit tests are offline. Integration tests are opt-in and use the deterministic
database in `init-db.sql`:

```bash
docker compose up -d
PROC_VIZ_INTEGRATION=1 pytest -m integration -v
```

The fixture skips with a clear message when SQL Server is unavailable. For an
external test instance, set `PROC_VIZ_TEST_HOST`, `PROC_VIZ_TEST_PORT`,
`PROC_VIZ_TEST_USER`, `PROC_VIZ_TEST_PASSWORD`, and `PROC_VIZ_TEST_DATABASE`.
The database must be `DummyDB` or start with `proc_viz_test`.

### Code Style

- Follow PEP 8
- Use type hints for functions
- Keep modules focused (single responsibility)
- Test database code with real connections when possible

## Configuration

Profiles stored in:
- **Windows** — `%APPDATA%\proc-viz\profiles.json`
- **macOS/Linux** — `~/.config/proc-viz/profiles.json`

Passwords stored in system keyring (not in JSON file).

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+K | Focus procedure filter |
| Enter | Execute table name search |

## Building & Distribution

### Windows Installer (NSIS)
```bash
pip install pyinstaller nsis
pyinstaller --onefile --windowed --name procedures-visualizer --add-data app:app main.py
# Use NSIS to create installer from dist/
```

### macOS DMG
```bash
# Create DMG with pyinstaller + dmgbuild
pip install dmgbuild
```

### Linux AppImage
```bash
pip install appimage-builder
```

## Troubleshooting

### Connection Fails
- Verify SQL Server is running
- Check credentials (Windows auth vs SQL Server auth)
- Ensure database name is correct
- Check firewall (SQL Server default port 1433)

### Procedures Not Loading
- Check database connectivity
- Verify user has SELECT permissions on system views
- Check for network timeouts (slow connections)

### Password Not Saving
- System keyring might not be available
- Check system keyring service is running
- Try re-entering credentials

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Support

Report issues on [GitHub Issues](https://github.com/73-Labs/proc-viz/issues).
