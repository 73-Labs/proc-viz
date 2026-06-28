# proc-viz

Database procedure visualization and exploration tool. Browse, analyze, and understand SQL Server stored procedures with an intuitive desktop interface.

## Features

- **Visual procedure browser** — Explore stored procedures organized by schema
- **Dependency analysis** — See which procedures call which, and which are called by whom
- **SQL preview** — View procedure definitions directly in the UI
- **Connection profiles** — Save multiple database connections with secure password storage
- **Cross-platform** — Runs on Windows, macOS, and Linux

## Requirements

- Python 3.8+
- SQL Server database (MSSQL)

## Installation

### From source (development)

```bash
git clone https://github.com/73-Labs/proc-viz.git
cd proc-viz
python -m pip install -e .
```

### Run

```bash
procedures-visualizer
```

Or directly:
```bash
python main.py
```

### Build standalone executable

```bash
pip install -e ".[dev]"
pyinstaller --onefile --windowed --name procedures-visualizer --add-data app:app main.py
```

Executable will be in `dist/procedures-visualizer`

## Development

### Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Project structure

```
proc-viz/
├── app/                 # Main application code
│   ├── main_window.py   # Main UI window
│   ├── widgets/         # Custom UI components
│   ├── dialogs/         # Dialog windows
│   └── storage.py       # Profile & config management
├── tests/               # Test suite
├── main.py              # Entry point
└── pyproject.toml       # Project configuration
```

## Usage

1. Launch the application
2. Create a new database connection or load a saved profile
3. Enter SQL Server credentials and connection details
4. Browse stored procedures in the left panel
5. Select a procedure to view its definition and dependencies

Passwords are securely stored using the system keyring (no plaintext storage).

## License

MIT License - see [LICENSE](LICENSE) for details

## Contributing

Contributions welcome! Please:
- Fork the repository
- Create a feature branch (`git checkout -b feature/amazing-feature`)
- Commit changes (`git commit -m 'Add amazing feature'`)
- Push to branch (`git push origin feature/amazing-feature`)
- Open a Pull Request

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md)
