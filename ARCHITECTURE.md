# Architecture

Design patterns, database layer, and UI architecture for proc-viz.

## Design Principles

- **Separation of Concerns** — Database logic separate from UI
- **Pluggable Drivers** — Easy to add new database types
- **Type Safety** — Full type hints throughout codebase
- **Single Responsibility** — Each class has one reason to change

## Database Layer

### DatabaseDriver Abstract Interface

```python
class DatabaseDriver(ABC):
    """Abstract interface for database operations."""
    
    def get_databases(self) -> List[Database]
    def get_schemas(self, database: str) -> List[Schema]
    def get_procedures(self, database: str, schema: str) -> List[Procedure]
    def get_functions(self, database: str, schema: str) -> List[Function]
    def get_tables(self, database: str, schema: str) -> List[Table]
    def get_procedure_source(self, db: str, schema: str, name: str) -> Optional[str]
    def get_function_source(self, db: str, schema: str, name: str) -> Optional[str]
    def get_dependencies(self, db: str, schema: str, name: str) -> List[ObjectDependency]
    def get_called_procedures(self, db: str, schema: str, name: str) -> List[ObjectDependency]
    def get_calling_procedures(self, db: str, schema: str, name: str) -> List[ObjectDependency]
    def get_objects_by_table(self, database: str, table_name: str) -> List[ObjectDependency]
    def close(self)
```

All database operations go through this interface. Implementations provide SQL Server, MySQL, PostgreSQL, etc.

### SQLServerDriver

SQL Server-specific implementation using `pymssql`.

**Key Queries:**
- `sys.schemas` — Get schemas
- `sys.procedures` — Get stored procedures
- `sys.objects + sys.parameters` — Get functions with parameters
- `sys.tables` — Get tables
- `sys.sql_modules` — Get object source code
- `sys.sql_expression_dependencies` — Get dependency graph
- `OBJECT_DEFINITION()` — Get full procedure definition

**Connection:**
- Uses Windows auth or SQL Server auth
- Connection string built from profile
- Timeout set to 30s
- Autocommit enabled (read-only operations)

### ConnectionManager

Factory for creating connections.

```python
ConnectionManager.create_connection(profile, password) -> DatabaseDriver
```

Returns appropriate driver based on `profile.db_type`. Handles connection pooling and error handling.

### DatabaseAccessor

Thin wrapper around driver. Converts DTOs for UI consumption.

```python
accessor = DatabaseAccessor(driver)
accessor.get_schemas(database)  # Returns List[Schema]
accessor.get_dependencies(db, schema, name)  # Returns List[Dict]
```

Used by UI to avoid direct driver access.

## Data Models

Located in `app/models/`:

**ConnectionProfile**
```python
class ConnectionProfile:
    name: str              # Profile name
    db_type: DatabaseType  # SQL_SERVER, MYSQL, etc.
    server: str            # Server hostname
    port: int              # Database port
    database: str          # Database name
    username: str          # Auth username
    auth_type: str         # 'windows' or 'sql'
    encrypt: bool          # TLS encryption
```

**Database Objects**
```python
Database(name: str)
Schema(name: str, object_count: int)
Procedure(name: str, schema: str)
Function(name: str, schema: str)
Table(name: str, schema: str)
ObjectDependency(schema: str, name: str, type: str)
```

Simple dataclasses for passing data between layers.

## Storage Layer

**ProfileManager** (`app/storage/profile_manager.py`)

Persists ConnectionProfiles to JSON:
- Saves: `~/.config/proc-viz/profiles.json` (Linux/macOS) or `%APPDATA%\proc-viz/profiles.json` (Windows)
- Passwords saved separately in system keyring
- CRUD operations: load, save, delete, rename profiles

Uses `keyring` library for secure password storage:
- Windows — Windows Credential Manager
- macOS — Keychain
- Linux — Secret Service or fallback

## UI Layer

### MainWindow

Entry point (`app/main_window.py`). Sets up:
- Menu bar (File, Edit, View, Database, Tools, Help)
- Toolbar (connection dropdown, connect/disconnect/manage buttons)
- Central content area (initially shows welcome screen)
- Status bar
- Loading overlay for async operations

### DatabaseExplorer

Main exploration widget (`app/widgets/database_explorer.py`).

**Left Panel:**
- Header label "Procedures"
- Procedure filter input (Ctrl+K)
- Table name filter input (Enter to search)
- Tree widget with schemas → procedures/functions

**Right Panel (Tabbed):**
- **Source** — SQL code with syntax highlighting
- **Parameters** — Procedure parameters and types
- **Details** — Metadata: created, modified, etc.

**Tree Structure:**
```
Database
├── Schema 1
│   ├── Procedure A
│   │   ├── Called: Proc B
│   │   └── Callers: Proc C
│   └── Function X
│       ├── Called: Proc D
│       └── Callers: None
├── Schema 2
│   └── ...
```

Lazy-loaded: children only fetch when parent expands.

### Dialogs

**ConnectionDialog** (`app/dialogs/connection_dialog.py`)
- New connection or edit existing
- Server, port, database, username, password fields
- Auth type selector (Windows / SQL Server auth)
- Connection test button
- Validate on submit

**ConnectionManagerDialog** (`app/dialogs/connection_manager_dialog.py`)
- List of saved profiles
- Edit, rename, delete buttons
- Double-click to edit
- Confirmation before delete

### Widgets

**SqlSyntaxHighlighter** (`app/widgets/sql_highlighter.py`)
- Highlights SQL keywords, strings, comments
- Applied to QTextEdit in Source tab

**LoadingOverlay** (`app/widgets/loading_spinner.py`)
- Animated spinner overlay
- Dynamic status messages (e.g., "Loading schema 3/12: dbo")
- Used during connection and schema loading

## Control Flow

### Initial Launch
1. MainWindow.__init__() → show welcome screen
2. User clicks Connect → ConnectionDialog shown
3. User enters credentials, clicks Connect
4. ConnectionManager.create_connection() creates SQLServerDriver
5. MainWindow shows DatabaseExplorer widget
6. DatabaseExplorer.load_procedures() triggered
7. Loading overlay shown, status updates each schema
8. Tree populated with procedures from get_schemas() + get_procedures()

### Procedure Selection
1. User clicks procedure in left tree
2. DatabaseExplorer.on_item_selected() triggered
3. Accessor methods called:
   - get_procedure_source() → populate Source tab
   - get_dependencies() → show Called procedures
   - get_calling_procedures() → show Callers
4. UI updated with results

### Procedure Search (Filter)
1. User types in filter input
2. QLineEdit.textChanged signal fires
3. DatabaseExplorer.on_filter_changed() called
4. Tree items filtered by text match (client-side)
5. Non-matching items hidden

### Table Search
1. User enters table name, presses Enter
2. DatabaseExplorer.on_table_filter_search() called
3. accessor.get_objects_by_table(table_name) queries database
4. Results populated in tree (procedures/functions referencing table)
5. Loading overlay shows progress

## Extensibility

### Adding New Database Type

1. Create driver class in `app/drivers/yourdatabase_driver.py`:
   ```python
   class YourDatabaseDriver(DatabaseDriver):
       def __init__(self, connection):
           self.conn = connection
       
       def get_schemas(self, database):
           # Implement using your DB client
           pass
   ```

2. Add database type to `DatabaseType` enum in models
3. Update `DriverFactory.create_driver()` to handle new type
4. Add connection creation to `ConnectionManager`
5. Add dependency to pyproject.toml

### Adding New UI Feature

1. Add method to `DatabaseExplorer` class
2. Connect signal to method (e.g., button click)
3. Use accessor methods for data access
4. Update UI elements

Example: Add Export button
```python
export_btn = QPushButton("Export")
export_btn.clicked.connect(self.export_procedures)
# ... 
def export_procedures(self):
    # Implement export logic
    pass
```

## Performance Considerations

### Lazy Loading
- Tree items only loaded when expanded
- Reduces initial schema load time
- Suitable for large databases (thousands of procedures)

### Caching
- Currently no in-memory caching
- Could cache procedure source code
- Could cache dependency graphs

### Database Queries
- Use indexed system views (sys.procedures, sys.schemas)
- Single queries per operation where possible
- Dependency queries use sys.sql_expression_dependencies (indexed by SQL Server)

### UI Responsiveness
- Use QTimer.singleShot() for initial load
- Loading overlay prevents user interaction during long operations
- Consider QThread for very large databases (future enhancement)

## Testing

Unit tests in `tests/` directory.

**Test Database Setup:**
```bash
docker-compose up  # Starts SQL Server with test data
pytest             # Runs tests against test database
```

See test files for examples of testing database layer and UI components.

## Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| PySide6 | Qt for Python UI framework | ≥6.7.0 |
| pymssql | SQL Server client library | ≥2.2.0 |
| keyring | Secure password storage | ≥24.1.0 |
| pytest | Testing framework | ≥7.4.0 (dev) |
| PyInstaller | Executable building | ≥6.5.0 (dev) |

