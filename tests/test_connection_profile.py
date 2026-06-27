import pytest
from app.models.connection_profile import ConnectionProfile, AuthenticationMode


class TestAuthenticationMode:
    def test_windows_auth(self):
        assert AuthenticationMode.WINDOWS.value == "Windows"

    def test_sql_server_auth(self):
        assert AuthenticationMode.SQL_SERVER.value == "SQLServer"


class TestConnectionProfile:
    def test_create_windows_auth_profile(self):
        profile = ConnectionProfile(
            name="Test Profile",
            server="localhost",
            database="TestDB",
            authentication_mode=AuthenticationMode.WINDOWS,
        )
        assert profile.name == "Test Profile"
        assert profile.server == "localhost"
        assert profile.port == 1433
        assert profile.database == "TestDB"
        assert profile.authentication_mode == AuthenticationMode.WINDOWS
        assert profile.encrypt is True
        assert profile.trust_certificate is False
        assert profile.save_password is False

    def test_create_sql_server_auth_profile(self):
        profile = ConnectionProfile(
            name="SQL Auth Profile",
            server="sql.example.com",
            port=1434,
            database="MyDB",
            authentication_mode=AuthenticationMode.SQL_SERVER,
            username="sa",
        )
        assert profile.authentication_mode == AuthenticationMode.SQL_SERVER
        assert profile.username == "sa"
        assert profile.port == 1434

    def test_profile_to_dict(self):
        profile = ConnectionProfile(
            name="Test",
            server="localhost",
            database="DB",
            authentication_mode=AuthenticationMode.WINDOWS,
        )
        data = profile.to_dict()

        assert data["name"] == "Test"
        assert data["server"] == "localhost"
        assert data["database"] == "DB"
        assert data["authentication_mode"] == "Windows"
        assert data["encrypt"] is True
        assert "password" not in data

    def test_profile_from_dict(self):
        data = {
            "name": "Loaded Profile",
            "server": "db.example.com",
            "port": 1433,
            "database": "MyDB",
            "authentication_mode": "SQLServer",
            "username": "admin",
            "driver": "ODBC Driver 17 for SQL Server",
            "encrypt": True,
            "trust_certificate": False,
            "save_password": True,
        }
        profile = ConnectionProfile.from_dict(data)

        assert profile.name == "Loaded Profile"
        assert profile.server == "db.example.com"
        assert profile.authentication_mode == AuthenticationMode.SQL_SERVER
        assert profile.username == "admin"
        assert profile.save_password is True

    def test_connection_kwargs_windows_auth(self):
        profile = ConnectionProfile(
            name="Test",
            server="localhost",
            port=1433,
            database="TestDB",
            authentication_mode=AuthenticationMode.WINDOWS,
        )
        kwargs = profile.get_connection_kwargs()

        assert kwargs["host"] == "localhost"
        assert kwargs["port"] == 1433
        assert kwargs["database"] == "TestDB"
        assert "user" not in kwargs
        assert "password" not in kwargs
        assert kwargs["encryption"] == "require"

    def test_connection_kwargs_sql_server_auth(self):
        profile = ConnectionProfile(
            name="Test",
            server="localhost",
            database="TestDB",
            authentication_mode=AuthenticationMode.SQL_SERVER,
            username="admin",
        )
        kwargs = profile.get_connection_kwargs(password="secret")

        assert kwargs["user"] == "admin"
        assert kwargs["password"] == "secret"
        assert kwargs["host"] == "localhost"
        assert kwargs["database"] == "TestDB"

    def test_connection_kwargs_with_certificate_options(self):
        profile = ConnectionProfile(
            name="Test",
            server="localhost",
            database="TestDB",
            encrypt=True,
            trust_certificate=True,
        )
        kwargs = profile.get_connection_kwargs()

        assert kwargs["encryption"] == "require"
        assert kwargs["cafile"] is None

    def test_connection_kwargs_without_encrypt(self):
        profile = ConnectionProfile(
            name="Test",
            server="localhost",
            database="TestDB",
            encrypt=False,
            trust_certificate=False,
        )
        kwargs = profile.get_connection_kwargs()

        assert "encryption" not in kwargs or kwargs.get("encryption") != "require"
        assert "cafile" not in kwargs
