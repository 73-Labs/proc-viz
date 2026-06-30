import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.models.connection_profile import ConnectionProfile, AuthenticationMode
from app.storage.profile_manager import ProfileManager


@pytest.fixture
def temp_profile_dir():
    """Create temporary directory for profile storage."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def profile_manager(temp_profile_dir):
    """Create ProfileManager with temporary storage."""
    manager = ProfileManager()
    manager.PROFILES_FILE = temp_profile_dir / "profiles.json"
    return manager


class TestProfileManager:
    def test_save_profile_without_password(self, profile_manager):
        profile = ConnectionProfile(
            name="Test",
            server="localhost",
            database="TestDB",
            authentication_mode=AuthenticationMode.WINDOWS,
        )

        profile_manager.save_profile(profile)

        assert profile_manager.PROFILES_FILE.exists()
        with open(profile_manager.PROFILES_FILE) as f:
            data = json.load(f)
        assert "Test" in data
        assert data["Test"]["server"] == "localhost"

    @patch("keyring.set_password")
    def test_save_profile_with_password(self, mock_keyring, profile_manager):
        profile = ConnectionProfile(
            name="Test",
            server="localhost",
            database="TestDB",
            authentication_mode=AuthenticationMode.SQL_SERVER,
            username="admin",
            save_password=True,
        )

        profile_manager.save_profile(profile, password="secret123")

        mock_keyring.assert_called_once_with("procedures-visualizer", "Test", "secret123")

    @patch("keyring.delete_password")
    def test_save_profile_delete_password(self, mock_keyring, profile_manager):
        profile = ConnectionProfile(
            name="Test",
            server="localhost",
            database="TestDB",
            save_password=False,
        )

        profile_manager.save_profile(profile, password="secret123")

        mock_keyring.assert_called_once_with("procedures-visualizer", "Test")

    def test_load_profile(self, profile_manager):
        profile_data = {
            "Test": {
                "name": "Test",
                "server": "localhost",
                "port": 1433,
                "database": "TestDB",
                "authentication_mode": "Windows",
                "username": None,
                "driver": "ODBC Driver 17 for SQL Server",
                "encrypt": True,
                "trust_certificate": False,
                "save_password": False,
            }
        }

        with open(profile_manager.PROFILES_FILE, "w") as f:
            json.dump(profile_data, f)

        loaded = profile_manager.load_profile("Test")

        assert loaded is not None
        assert loaded.name == "Test"
        assert loaded.server == "localhost"
        assert loaded.database == "TestDB"

    def test_load_profile_not_found(self, profile_manager):
        loaded = profile_manager.load_profile("NonExistent")
        assert loaded is None

    def test_load_all_profiles(self, profile_manager):
        profiles_data = {
            "Profile1": {
                "name": "Profile1",
                "server": "server1",
                "port": 1433,
                "database": "DB1",
                "authentication_mode": "Windows",
                "username": None,
                "driver": "ODBC Driver 17 for SQL Server",
                "encrypt": True,
                "trust_certificate": False,
                "save_password": False,
            },
            "Profile2": {
                "name": "Profile2",
                "server": "server2",
                "port": 1433,
                "database": "DB2",
                "authentication_mode": "SQLServer",
                "username": "admin",
                "driver": "ODBC Driver 17 for SQL Server",
                "encrypt": True,
                "trust_certificate": False,
                "save_password": True,
            },
        }

        with open(profile_manager.PROFILES_FILE, "w") as f:
            json.dump(profiles_data, f)

        all_profiles = profile_manager.load_all_profiles()

        assert len(all_profiles) == 2
        names = {p.name for p in all_profiles}
        assert "Profile1" in names
        assert "Profile2" in names

    def test_load_all_profiles_empty(self, profile_manager):
        all_profiles = profile_manager.load_all_profiles()
        assert all_profiles == []

    @patch("keyring.delete_password")
    def test_delete_profile(self, mock_keyring, profile_manager):
        profiles_data = {
            "ToDelete": {
                "name": "ToDelete",
                "server": "localhost",
                "port": 1433,
                "database": "DB",
                "authentication_mode": "Windows",
                "username": None,
                "driver": "ODBC Driver 17 for SQL Server",
                "encrypt": True,
                "trust_certificate": False,
                "save_password": False,
            }
        }

        with open(profile_manager.PROFILES_FILE, "w") as f:
            json.dump(profiles_data, f)

        profile_manager.delete_profile("ToDelete")

        with open(profile_manager.PROFILES_FILE) as f:
            data = json.load(f)
        assert "ToDelete" not in data
        mock_keyring.assert_called_once_with("procedures-visualizer", "ToDelete")

    @patch("keyring.get_password")
    def test_get_password(self, mock_keyring, profile_manager):
        mock_keyring.return_value = "stored_password"

        password = profile_manager.get_password("Test")

        assert password == "stored_password"
        mock_keyring.assert_called_once_with("procedures-visualizer", "Test")

    @patch("keyring.get_password")
    def test_get_password_not_found(self, mock_keyring, profile_manager):
        mock_keyring.return_value = None

        password = profile_manager.get_password("NonExistent")

        assert password is None

    @patch("keyring.delete_password")
    def test_clear_password(self, mock_keyring, profile_manager):
        profile_manager.clear_password("Test")

        mock_keyring.assert_called_once_with("procedures-visualizer", "Test")

    def test_profile_exists(self, profile_manager):
        profiles_data = {"Existing": {"name": "Existing", "server": "localhost"}}

        with open(profile_manager.PROFILES_FILE, "w") as f:
            json.dump(profiles_data, f)

        assert profile_manager.profile_exists("Existing") is True
        assert profile_manager.profile_exists("NonExistent") is False

    def test_profile_exists_no_file(self, profile_manager):
        assert profile_manager.profile_exists("Any") is False

    def test_roundtrip_save_and_load(self, profile_manager):
        original = ConnectionProfile(
            name="Roundtrip",
            server="db.example.com",
            port=1434,
            database="MyDB",
            authentication_mode=AuthenticationMode.SQL_SERVER,
            username="admin",
            encrypt=False,
            trust_certificate=True,
            save_password=True,
        )

        with patch("keyring.set_password"):
            profile_manager.save_profile(original, password="test123")

        loaded = profile_manager.load_profile("Roundtrip")

        assert loaded.name == original.name
        assert loaded.server == original.server
        assert loaded.port == original.port
        assert loaded.database == original.database
        assert loaded.authentication_mode == original.authentication_mode
        assert loaded.username == original.username
        assert loaded.encrypt == original.encrypt
        assert loaded.trust_certificate == original.trust_certificate
        assert loaded.save_password == original.save_password

    @patch("keyring.get_password")
    @patch("keyring.set_password")
    def test_rename_profile(self, mock_set, mock_get, profile_manager):
        profiles_data = {
            "OldName": {
                "name": "OldName",
                "server": "localhost",
                "port": 1433,
                "database": "DB",
                "authentication_mode": "Windows",
                "username": None,
                "encrypt": True,
                "trust_certificate": False,
                "save_password": True,
            }
        }

        with open(profile_manager.PROFILES_FILE, "w") as f:
            json.dump(profiles_data, f)

        mock_get.return_value = "stored_password"

        profile_manager.rename_profile("OldName", "NewName")

        with open(profile_manager.PROFILES_FILE) as f:
            data = json.load(f)

        assert "OldName" not in data
        assert "NewName" in data
        assert data["NewName"]["name"] == "NewName"
        assert data["NewName"]["server"] == "localhost"
        mock_set.assert_called_once_with("procedures-visualizer", "NewName", "stored_password")

    def test_rename_profile_not_found(self, profile_manager):
        with pytest.raises(ValueError, match="Profile 'NonExistent' not found"):
            profile_manager.rename_profile("NonExistent", "NewName")

    def test_rename_profile_already_exists(self, profile_manager):
        profiles_data = {
            "Profile1": {"name": "Profile1", "server": "localhost"},
            "Profile2": {"name": "Profile2", "server": "localhost"},
        }

        with open(profile_manager.PROFILES_FILE, "w") as f:
            json.dump(profiles_data, f)

        with pytest.raises(ValueError, match="Profile 'Profile2' already exists"):
            profile_manager.rename_profile("Profile1", "Profile2")
