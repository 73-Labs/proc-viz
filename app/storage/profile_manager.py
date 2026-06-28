import json
import platform
import keyring
import keyring.errors
from pathlib import Path
from typing import List, Optional
from app.models.connection_profile import ConnectionProfile


def _get_config_dir() -> Path:
    """Get platform-specific config directory."""
    if platform.system() == "Windows":
        return Path.home() / "AppData" / "Roaming" / "ProceduresVisualizer"
    else:
        return Path.home() / ".config" / "procedures-visualizer"


class ProfileManager:
    """Manages connection profiles with local storage and keyring integration."""

    KEYRING_SERVICE = "procedures-visualizer"

    def __init__(self):
        """Initialize profile manager and ensure directory exists."""
        self._profiles_file = _get_config_dir() / "profiles.json"
        self._profiles_file.parent.mkdir(parents=True, exist_ok=True)

    @property
    def PROFILES_FILE(self) -> Path:
        """Get profiles file path."""
        return self._profiles_file

    @PROFILES_FILE.setter
    def PROFILES_FILE(self, value: Path) -> None:
        """Set profiles file path (for testing)."""
        self._profiles_file = value

    def save_profile(self, profile: ConnectionProfile, password: Optional[str] = None) -> None:
        """Save profile to local storage and optionally store password in keyring."""
        profiles = self._load_profiles_from_file()

        profile_dict = profile.to_dict()
        profiles[profile.name] = profile_dict

        with open(self.PROFILES_FILE, "w") as f:
            json.dump(profiles, f, indent=2)

        if password and profile.save_password:
            keyring.set_password(self.KEYRING_SERVICE, profile.name, password)
        elif not profile.save_password:
            try:
                keyring.delete_password(self.KEYRING_SERVICE, profile.name)
            except keyring.errors.PasswordDeleteError:
                pass

    def load_profile(self, profile_name: str) -> Optional[ConnectionProfile]:
        """Load profile by name from local storage."""
        profiles = self._load_profiles_from_file()
        if profile_name not in profiles:
            return None
        return ConnectionProfile.from_dict(profiles[profile_name])

    def load_all_profiles(self) -> List[ConnectionProfile]:
        """Load all saved profiles."""
        profiles = self._load_profiles_from_file()
        return [ConnectionProfile.from_dict(p) for p in profiles.values()]

    def delete_profile(self, profile_name: str) -> None:
        """Delete profile from local storage and keyring."""
        profiles = self._load_profiles_from_file()
        if profile_name in profiles:
            del profiles[profile_name]
            with open(self.PROFILES_FILE, "w") as f:
                json.dump(profiles, f, indent=2)

        try:
            keyring.delete_password(self.KEYRING_SERVICE, profile_name)
        except keyring.errors.PasswordDeleteError:
            pass

    def get_password(self, profile_name: str) -> Optional[str]:
        """Retrieve password from keyring for given profile."""
        try:
            return keyring.get_password(self.KEYRING_SERVICE, profile_name)
        except Exception:
            return None

    def clear_password(self, profile_name: str) -> None:
        """Remove password from keyring."""
        try:
            keyring.delete_password(self.KEYRING_SERVICE, profile_name)
        except keyring.errors.PasswordDeleteError:
            pass

    def profile_exists(self, profile_name: str) -> bool:
        """Check if profile exists."""
        profiles = self._load_profiles_from_file()
        return profile_name in profiles

    def _load_profiles_from_file(self) -> dict:
        """Load all profiles from JSON file."""
        if not self.PROFILES_FILE.exists():
            return {}

        with open(self.PROFILES_FILE, "r") as f:
            return json.load(f)
