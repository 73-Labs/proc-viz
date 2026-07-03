import json
from pathlib import Path
from typing import Optional


def _get_config_dir() -> Path:
    """Get platform-specific config directory."""
    import platform
    if platform.system() == "Windows":
        return Path.home() / "AppData" / "Roaming" / "ProceduresVisualizer"
    else:
        return Path.home() / ".config" / "procedures-visualizer"


class SettingsManager:
    """Manages application settings including theme preferences."""

    def __init__(self):
        """Initialize settings manager."""
        self._settings_file = _get_config_dir() / "settings.json"
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)
        self._settings = self._load_settings()

    def get_theme(self) -> str:
        """Get current theme name."""
        return self._settings.get("theme", "light")

    def set_theme(self, theme_name: str) -> None:
        """Set current theme and save."""
        self._settings["theme"] = theme_name
        self._save_settings()

    def get_zoom_level(self) -> int:
        """Get current zoom level in percent (100 = normal)."""
        return self._settings.get("zoom_level", 100)

    def set_zoom_level(self, zoom: int) -> None:
        """Set zoom level and save."""
        zoom = max(50, min(200, zoom))
        self._settings["zoom_level"] = zoom
        self._save_settings()

    def _load_settings(self) -> dict:
        """Load settings from JSON file."""
        if not self._settings_file.exists():
            return {"theme": "light"}

        try:
            with open(self._settings_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"theme": "light"}

    def _save_settings(self) -> None:
        """Save settings to JSON file."""
        with open(self._settings_file, "w") as f:
            json.dump(self._settings, f, indent=2)
