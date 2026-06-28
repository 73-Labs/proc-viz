# Contributing to proc-viz

Thank you for your interest in contributing! This guide explains how to set up a development environment and submit changes.

## Development Setup

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/proc-viz.git
   cd proc-viz
   ```

3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

4. Verify tests pass:
   ```bash
   pytest
   ```

## Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and test locally:
   ```bash
   pytest  # Run test suite
   python main.py  # Test the app manually
   ```

3. Commit with clear messages:
   ```bash
   git commit -m "Add feature: describe what you did"
   ```

4. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Open a Pull Request on GitHub with:
   - Clear description of the change
   - Link to any related issues
   - Screenshots for UI changes

## Code Standards

- Follow PEP 8 style guide
- Add tests for new functionality
- Keep commits focused and atomic
- No hardcoded credentials or secrets
- Update README if adding user-facing features

## Testing

Run tests with pytest:
```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_foo.py  # Run specific test file
```

## Reporting Issues

Use GitHub Issues to report bugs:
- Clear title describing the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version, OS, and app version

## Questions?

Open a GitHub Discussion or issue. We're here to help!

Thanks for contributing! 🎉
