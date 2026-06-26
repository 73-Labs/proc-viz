# Debugging Guide

Setup VSCode debugging to troubleshoot ODBC driver installation and other issues.

## Prerequisites

Install debugpy in your environment:

```bash
pip install debugpy
```

## VSCode Debug Configurations

Three debug configurations available in `.vscode/launch.json`:

### 1. Debug App (Main)

Run the app with debugger attached:

1. Open `main.py`
2. Set breakpoints by clicking left of line numbers
3. Press **F5** or go to Run → Start Debugging
4. Select **"Python: Debug App"**

App will start and break at breakpoints.

### 2. Debug Tests

Run tests with debugger:

1. Press **F5** → Select **"Python: Debug Tests"**
2. Set breakpoints in test files
3. Debugger will pause at breakpoints

Runs: `pytest tests/test_odbc_manager.py -v -s`

### 3. Debug Driver Installation

Dedicated config for ODBC driver debugging:

1. Press **F5** → Select **"Python: Debug Driver Installation"**
2. Breakpoints in `app/drivers/odbc_manager.py` will trigger

Automatically sets `DEBUG=1` env var for logging.

## Debugging ODBC Driver Download

To debug why MSI download fails:

### Set Breakpoints

Open `app/drivers/odbc_manager.py`:

1. Line 110: `urllib.request.urlretrieve(msi_url, installer_path)` — Download start
2. Line 112: File size check — After download
3. Line 120: `subprocess.run(...)` — Installation start
4. Line 126: Return status — Installation result

### Debug Steps

1. Press **F5** → Select **"Python: Debug Driver Installation"**
2. Click "New Connection" button in app
3. Click "Test Connection"
4. When prompted, click "Yes" to install driver
5. Debugger pauses at breakpoints

### Inspect Variables

When paused at breakpoint:

- **Hover over variables** to see values
- **Debug Console** (Ctrl+Shift+J): Execute Python code
  ```python
  installer_path
  msi_url
  result.returncode
  result.stderr
  ```
- **Variables panel** (left sidebar): Shows all local/global vars
- **Call stack** (left sidebar): Shows function call chain

### Common Breakpoint Locations

```python
# Line 91: URL retrieval
logger.info("Starting ODBC Driver 18 MSI download...")

# Line 93: Download attempt
urllib.request.urlretrieve(msi_url, installer_path)

# Line 110: Installation attempt
result = subprocess.run([...])

# Line 118: Check result
logger.error(f"MSI installation failed with code {result.returncode}")
```

## Logging Output

All log messages appear in the **Debug Console**:

```
2024-01-15 10:30:45,123 - app.drivers.odbc_manager - INFO - Starting ODBC Driver installation process
2024-01-15 10:30:45,124 - app.drivers.odbc_manager - INFO - Platform: Windows
2024-01-15 10:30:45,125 - app.drivers.odbc_manager - INFO - Attempting installation via Chocolatey
2024-01-15 10:30:50,200 - app.drivers.odbc_manager - WARNING - Chocolatey not found on system
2024-01-15 10:30:50,201 - app.drivers.odbc_manager - INFO - Chocolatey failed, attempting MSI installation
```

Logs include:
- **INFO**: Normal flow (driver found, starting download, etc.)
- **WARNING**: Non-critical issues (driver not found, choco missing, etc.)
- **ERROR**: Failures (download failed, installation failed, etc.)

## Debugging Network Issues

If download fails with network error:

1. Set breakpoint at `urllib.request.urlretrieve(...)`
2. In Debug Console, test URL manually:
   ```python
   import urllib.request
   urllib.request.urlopen("https://go.microsoft.com/fwlink/?linkid=2249004")
   ```
3. Check internet connection
4. Try with proxy if behind corporate firewall

## Debugging File Issues

If installer path problems:

1. Breakpoint at `installer_path = temp_dir / "msodbcsql18.msi"`
2. In Debug Console:
   ```python
   import tempfile
   temp_dir = Path(tempfile.gettempdir())
   print(temp_dir)
   print(temp_dir.exists())
   print(os.access(str(temp_dir), os.W_OK))  # Check write permission
   ```

## Debugging MSI Execution

If installation fails (returncode != 0):

1. Breakpoint at installation subprocess.run()
2. In Debug Console inspect:
   ```python
   result.returncode  # Should be 0
   result.stderr.decode()  # Show error message
   result.stdout.decode()  # Show output
   ```

Common MSI errors:
- **1602**: User canceled installation
- **1603**: Fatal error during installation
- **1641**: System restart required

## Tips

- **Run → Stop Debugging** (Shift+F5): Stop debugger anytime
- **Debug → Step Into** (F11): Step into function calls
- **Debug → Step Over** (F10): Execute current line, skip functions
- **Debug → Step Out** (Shift+F11): Return from function
- **Debug → Continue** (F5): Resume from breakpoint
- **Debug → Pause** (F6): Pause running code

## Logging Levels

Change logging level in `app/drivers/odbc_manager.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

- **DEBUG**: Detailed info (function calls, variable values)
- **INFO**: General flow (download started, installation complete)
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures

## Watch Expressions

Add expressions to watch in Debug panel:

1. **Debug → Watch** (Ctrl+Shift+J)
2. Click **+** button
3. Enter Python expression:
   ```python
   installer_path.exists()
   result.returncode == 0
   len(drivers)
   ```

Expressions update as you step through code.

## Troubleshooting Debugger

If debugger doesn't work:

1. Verify Python extension installed (ms-python.python)
2. Verify debugpy: `pip install debugpy`
3. Check Python interpreter in VSCode:
   - Ctrl+Shift+P → "Python: Select Interpreter"
   - Choose your project's Python
4. Restart VSCode
5. Clear `.vscode/debug` folder if it exists

## Performance Debugging

If installation hangs/is slow:

1. Set breakpoint in slow section
2. Let it pause, then step with F10 to find slow line
3. Use `timeout` parameters to prevent hangs
4. Check network: `tracert go.microsoft.com` (PowerShell)

## Next Steps

After debugging:

1. Check logs in Debug Console
2. Note error messages and line numbers
3. Add error handling for edge cases
4. Update `app/drivers/odbc_manager.py` with fixes
5. Add tests for failure scenarios
