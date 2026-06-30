# Getting Started

Quick start guide for proc-viz.

## Installation (2 minutes)

### Prerequisites
- Python 3.8 or higher
- SQL Server instance (local or remote)
- User account with read permissions on SQL Server

### Install from Source

```bash
# Clone repository
git clone https://github.com/73-Labs/proc-viz.git
cd proc-viz

# Create virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# or
venv\Scripts\activate           # Windows

# Install dependencies
pip install -e .
```

### Run Application

```bash
python main.py
```

Or:
```bash
procedures-visualizer
```

## Your First Connection (2 minutes)

1. **Click Connect** in toolbar (or File → New Connection)

2. **Fill in connection details:**
   - **Server:** `localhost` (for local SQL Server)
   - **Port:** `1433` (default)
   - **Database:** your database name
   - **Authentication:** Windows Auth (if on domain) or SQL Server Auth (username/password)
   - **Username:** your username (SQL Server auth only)
   - **Password:** your password (SQL Server auth only)

3. **Click Test Connection** — should show ✓ Connection successful

4. **Click Connect** — wait for procedures to load

5. **Browse left panel** — tree shows Schema → Procedures

Done! You're connected.

## Browse Procedures (1 minute)

Left panel shows procedures organized by schema:

```
▼ dbo
  ├─ usp_CreateOrder
  ├─ usp_UpdateOrder
  └─ fn_GetTotal
▼ Sales
  └─ sp_GenerateReport
```

**Click any procedure** to see:
- **Source** — SQL code (highlighted)
- **Parameters** — Input/output parameters
- **Details** — Metadata

## Search (1 minute)

### By Name
Press **Ctrl+K** and type procedure name:
- Type "Get" → shows all procedures with "Get"
- Real-time filtering

### By Table
Click table filter input, enter table name, press Enter:
- Shows all procedures that reference that table
- Useful for finding impact of table changes

## View Dependencies (1 minute)

Select a procedure. Right panel shows tabs:
- **Called** — What this procedure calls
- **Callers** — What calls this procedure
- **Dependencies** — Full dependency tree

Click any listed procedure to jump to it.

## Save Your Connection (1 minute)

After connecting, app offers to save profile:
- Enter profile name (e.g., "Production DB")
- Password saved securely in system keyring
- Profile saved to configuration file

Later: Switch profiles in toolbar dropdown.

## Common Tasks

### Export Procedure Source Code

1. Select procedure in left panel
2. View Source tab (right panel)
3. Ctrl+A to select all, Ctrl+C to copy
4. Paste into editor

### Find All Procedures Using a Table

1. Click table filter input
2. Enter table name
3. Press Enter
4. All procedures referencing that table appear in tree

### Understand Procedure Call Chain

1. Select procedure
2. Expand "Called" section to see what it calls
3. Click called procedure to see what it calls
4. Explore call chain visually

### Find Where a Procedure is Used

1. Select procedure
2. Check "Callers" section
3. See list of procedures that call it
4. Click caller to explore further

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+K | Filter procedures |
| Ctrl+C | Copy selected text |
| Ctrl+A | Select all text |
| Enter | Execute table search |

## Troubleshooting

### "Connection Failed"
- Check SQL Server is running
- Verify server address/port
- Try connecting with SSMS first to verify credentials

### "Procedures Not Loading"
- Check user has SELECT permission on system views
- Try smaller database first
- Check for network timeout issues

### "Password Not Saving"
- System keyring might not be available
- Manually add profile next time
- Check OS keyring service is running

## Next Steps

1. **Read [FEATURES.md](FEATURES.md)** — Detailed feature documentation
2. **Read [ARCHITECTURE.md](ARCHITECTURE.md)** — Technical architecture overview
3. **Check [CONTRIBUTING.md](CONTRIBUTING.md)** — Contribute code improvements

## Questions?

- **GitHub Issues:** Report bugs or request features
- **README.md:** Full documentation
- **Code comments:** Check source code for implementation details

