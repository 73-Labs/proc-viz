from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class AuthenticationMode(Enum):
    WINDOWS = "Windows"
    SQL_SERVER = "SQLServer"


@dataclass
class ConnectionProfile:
    """Database connection profile with support for multiple authentication methods."""

    name: str
    server: str
    port: int = 1433
    database: str = ""
    authentication_mode: AuthenticationMode = AuthenticationMode.WINDOWS
    username: Optional[str] = None
    encrypt: bool = True
    trust_certificate: bool = False
    save_password: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization (excludes password)."""
        return {
            "name": self.name,
            "server": self.server,
            "port": self.port,
            "database": self.database,
            "authentication_mode": self.authentication_mode.value,
            "username": self.username,
            "encrypt": self.encrypt,
            "trust_certificate": self.trust_certificate,
            "save_password": self.save_password,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConnectionProfile":
        """Create profile from dictionary (load from JSON)."""
        auth_mode = AuthenticationMode(data.get("authentication_mode", "Windows"))
        return cls(
            name=data["name"],
            server=data["server"],
            port=data.get("port", 1433),
            database=data.get("database", ""),
            authentication_mode=auth_mode,
            username=data.get("username"),
            encrypt=data.get("encrypt", True),
            trust_certificate=data.get("trust_certificate", False),
            save_password=data.get("save_password", False),
        )

    def get_connection_kwargs(self, password: Optional[str] = None) -> dict:
        """Generate pymssql connection parameters."""
        kwargs = {
            "host": self.server,
            "port": self.port,
            "database": self.database,
        }

        if self.authentication_mode == AuthenticationMode.SQL_SERVER:
            kwargs["user"] = self.username
            if password:
                kwargs["password"] = password

        if self.encrypt:
            kwargs["encryption"] = "require"
        if self.trust_certificate:
            kwargs["cafile"] = None

        return kwargs
