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
    driver: str = "ODBC Driver 17 for SQL Server"
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
            "driver": self.driver,
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
            driver=data.get("driver", "ODBC Driver 17 for SQL Server"),
            encrypt=data.get("encrypt", True),
            trust_certificate=data.get("trust_certificate", False),
            save_password=data.get("save_password", False),
        )

    def get_connection_string(self, password: Optional[str] = None) -> str:
        """Generate ODBC connection string."""
        conn_str = (
            f"Driver={{{self.driver}}};"
            f"Server={self.server},{self.port};"
            f"Database={self.database};"
        )

        if self.authentication_mode == AuthenticationMode.WINDOWS:
            conn_str += "Trusted_Connection=yes;"
        else:
            conn_str += f"UID={self.username};"
            if password:
                conn_str += f"PWD={password};"

        if self.encrypt:
            conn_str += "Encrypt=yes;"
        if self.trust_certificate:
            conn_str += "TrustServerCertificate=yes;"

        return conn_str
