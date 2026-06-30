# Features Guide

Detailed description of proc-viz features and how to use them.

## Connection Management

### Create New Connection

1. Click **Connect** button or File → New Connection
2. **Connection Dialog** opens with fields:
   - **Server** — SQL Server instance (e.g., `localhost`, `192.168.1.10`, `myserver.database.windows.net`)
   - **Port** — SQL Server port (default 1433)
   - **Database** — Target database name
   - **Authentication** — Choose:
     - **Windows Auth** — Uses Windows credentials, no password needed
     - **SQL Server Auth** — SQL Server user + password
   - **Username** — Auth username (for SQL Server auth)
   - **Password** — Auth password (for SQL Server auth)
   - **Encrypt Connection** — Enable TLS encryption (recommended for remote servers)
3. Click **Test Connection** to verify before saving
4. Click **Connect** to establish connection

### Save Connection Profile

After successful connection:
- App prompts to save profile
- Enter profile name (e.g., "Production DB", "Dev Local")
- Profile saved securely (config in JSON, password in system keyring)

### Manage Saved Profiles

**Open Manager:** Click Manage button or File → Manage Connections

**In Connection Manager Dialog:**

| Action | Steps |
|--------|-------|
| **Edit** | Select profile, click Edit, modify details, click Save |
| **Rename** | Select profile, click Rename, enter new name |
| **Delete** | Select profile, click Delete, confirm deletion |
| **Use** | Click Close, select from Connection dropdown, click Connect |

### Switch Between Connections

Use Connection dropdown in toolbar to switch active profile.

**Important:** Only one connection active at a time. Connecting to new profile disconnects previous connection.

## Procedure Exploration

### Browse Procedures

Left panel shows hierarchical tree:
```
Database Name
├── dbo (schema)
│   ├── usp_GetUser (procedure)
│   ├── usp_InsertOrder (procedure)
│   └── fn_CalculateTotal (function)
├── Sales (schema)
│   ├── sp_GenerateReport (procedure)
│   └── fn_GetSalesTotal (function)
└── Reporting (schema)
    ├── sp_DailyReport (procedure)
    └── ...
```

Icons indicate object type:
- 📂 Schema
- 🔧 Stored Procedure
- 𝑓 Function
- 📊 Table
- 📦 Other objects

### Filter Procedures by Name

**Quick Filter (Ctrl+K):**
1. Click filter input or press Ctrl+K
2. Type procedure name (partial match)
3. Tree automatically hides non-matching items
4. Matching items highlighted in real-time

Examples:
- Type "Get" → shows all procedures with "Get" in name
- Type "sp_User" → shows "sp_UserCreate", "sp_UserUpdate", etc.

Clear filter to show all procedures again.

### Search by Table Name

**Find procedures that reference a table:**

1. Click table filter input (below procedure filter)
2. Enter table name (e.g., "Orders", "Users")
3. Press Enter to search
4. Loading overlay shows progress
5. Tree populated with all procedures/functions referencing that table

**Use cases:**
- Find all procedures that read from "Orders" table
- Find all procedures that modify "Users" table
- Analyze impact of changing/dropping a table

## Source Code Viewing

### View Procedure Definition

1. Click procedure in left tree
2. **Source tab** (right panel) shows full SQL code
3. SQL syntax highlighting applied:
   - Keywords in blue
   - Strings in red
   - Comments in green
   - Operators in standard color

### Copy Source Code

1. Click in Source tab
2. Select text (Ctrl+A for all)
3. Copy (Ctrl+C)
4. Paste into editor, SQL client, etc.

### Navigate Between Objects

Click procedure names in dependency tree (Called/Callers) to jump between related objects. Source automatically updates.

## Dependency Analysis

### Called Procedures (What This Calls)

Shows objects that this procedure invokes:

```
usp_InsertOrder
├── Called: usp_LogAction
├── Called: usp_NotifyCustomer
└── Called: fn_CalculateShipping
```

Click to view that procedure's details.

**Includes:**
- Stored procedures
- Functions (scalar, table-valued)
- Views
- Tables

### Calling Procedures (Who Calls This)

Shows procedures that invoke this object (reverse dependencies):

```
usp_LogAction
├── Callers: usp_InsertOrder
├── Callers: usp_UpdateOrder
└── Callers: usp_DeleteOrder
```

Useful for:
- Finding impact of modifying a procedure
- Finding unused procedures (no callers)
- Understanding dependency chains

### Lazy-Loaded Dependencies

Dependencies only load when you expand tree item. Avoids loading entire dependency graph upfront.

## Parameters

### View Procedure Parameters

Click procedure, navigate to **Parameters** tab.

Shows:
- Parameter name
- Data type (INT, VARCHAR, DATETIME, etc.)
- Default value (if any)
- Direction (INPUT, OUTPUT)
- Max length (for string types)

Example output:
```
Parameters for usp_InsertOrder:

@OrderID (OUTPUT) — INT
@CustomerID (INPUT) — INT
@OrderDate (INPUT) — DATETIME — Default: GETDATE()
@Items (INPUT) — XML
@Total (OUTPUT) — DECIMAL(10, 2)
```

## Details Tab

Additional metadata about procedure:

- **Created Date** — When procedure was created
- **Modified Date** — Last modification date
- **Object ID** — SQL Server internal ID
- **Owner** — Schema owner
- **Type** — Procedure type (stored procedure, function, etc.)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+K | Focus procedure filter |
| Ctrl+C | Copy selected text |
| Ctrl+A | Select all text |
| Enter | Execute table search (in table filter) |
| Tab | Move between UI elements |
| Esc | Clear filter |

## Status Bar

Bottom of window shows:
- **Active Connection** — Current database connection status
- **Procedure Count** — Number of procedures loaded
- **Selected Object** — Name of currently selected procedure/function

## Toolbar

Top toolbar provides quick access to common actions:

| Element | Purpose |
|---------|---------|
| Connection Dropdown | Select saved profile |
| Connect Button | Create new connection |
| Manage Button | Open connection manager |
| Disconnect Button | Close active connection |

## Dialogs

### Connection Test

**Within Connection Dialog:**
1. Fill connection details
2. Click **Test Connection**
3. Dialog shows result:
   - ✓ Connection successful
   - ✗ Connection failed — error message shown
4. You can retry with different credentials

### Confirmation Dialogs

When deleting saved profiles:
- Confirmation required before deletion
- Cannot undo after confirmation

## Loading Indicators

**Dynamic Loading Overlay:**
- Shown during long operations
- Animated spinner
- Status message with progress (e.g., "Loading schema 5/12: Sales")
- Cannot interact with app while loading

Operations that show loading:
- Initial schema loading
- Table search across large databases
- Connection establishment

## Error Handling

### Connection Errors

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| "Failed to connect" | Wrong server address | Verify server name/IP, check SQL Server running |
| "Login failed" | Wrong credentials | Re-enter username/password |
| "Connection timeout" | Server unreachable | Check firewall, network connectivity |
| "Database not found" | Wrong database name | Verify database exists and user has access |

Error messages shown in dialog with details.

### Permission Errors

Occur if user lacks database permissions:
- Cannot load schemas — Needs CONNECT permission
- Cannot view procedures — Needs VIEW DEFINITION permission
- Cannot query dependencies — Needs VIEW DEFINITION permission

Solution: Grant user appropriate permissions on SQL Server.

## Performance Tips

### For Large Databases

1. **Use filters early** — Narrow down procedures before exploring dependencies
2. **Table search** — More efficient than browsing tree for finding related objects
3. **Avoid expanding all items** — Dependencies lazy-load only when needed

### Connection Tips

1. **Use local network** — Faster than remote connections
2. **Enable encryption only if needed** — Slight performance cost for security
3. **Check network latency** — 50ms+ latency will be noticeable

## Workflow Examples

### Modify Procedure — Find Impact

Task: Update `usp_InsertOrder` and need to know what breaks

1. Open connection to production database
2. Find `usp_InsertOrder` in left tree
3. Click to select
4. View **Called** tab — see what it calls
5. View **Callers** tab — see what calls it
6. For each caller, click to see what they do
7. Document all affected procedures
8. Plan changes to avoid breaking dependent objects

### Migrate Table — Find All References

Task: Migrate `Orders` table to new schema, need to update all procedures

1. Click table filter input
2. Enter "Orders"
3. Press Enter
4. View results — all procedures accessing Orders table
5. Update each procedure's connection references
6. Test each procedure after changes

### Audit Unused Procedures

Task: Find procedures that nothing calls (removal candidates)

1. Expand schema in tree
2. For each procedure:
   - Click to select
   - Check **Callers** tab
   - If empty → procedure is unused
3. Document unused procedures
4. Verify they're not called from application code (outside database)
5. Plan removal

### Export Procedure Documentation

Task: Create documentation for procedures

1. For each procedure of interest:
   - Select it
   - View Source tab
   - View Parameters tab
   - View Callers/Called tabs
2. Copy source code (Ctrl+A, Ctrl+C)
3. Paste into document
4. Repeat for all procedures

## System Integration

### Windows Context Menu (Future)

Potential feature: Right-click on stored procedure in SQL Server Management Studio, launch proc-viz.

### Copy to Clipboard

- Select text in Source tab
- Ctrl+C to copy
- Paste into other applications

### Drag and Drop (Future)

Potential feature: Drag procedure from tree to text editor.

