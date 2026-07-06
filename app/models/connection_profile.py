from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any, Dict



class AuthenticationMode(Enum):
    WINDOWS = "Windows"
    SQL_SERVER = "SQLServer"
    PASSWORD = "Password"


class DatabaseType(Enum):
    """Supported database types."""
    SQL_SERVER = "sqlserver"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"


@dataclass
class ConnectionProfile:
    """Database connection profile with support for multiple authentication methods and database types."""

    name: str
    server: str
    database: str = ""
    port: int = 1433
    db_type: DatabaseType = DatabaseType.SQL_SERVER
    authentication_mode: AuthenticationMode = AuthenticationMode.WINDOWS
    username: Optional[str] = None
    encrypt: bool = True
    trust_certificate: bool = False
    save_password: bool = False
    connection_options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization (excludes password)."""
        return {
            "name": self.name,
            "server": self.server,
            "port": self.port,
            "database": self.database,
            "db_type": self.db_type.value,
            "authentication_mode": self.authentication_mode.value,
            "username": self.username,
            "encrypt": self.encrypt,
            "trust_certificate": self.trust_certificate,
            "save_password": self.save_password,
            "connection_options": self.connection_options,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConnectionProfile":
        """Create profile from dictionary (load from JSON)."""
        auth_mode = AuthenticationMode(data.get("authentication_mode", "Windows"))
        db_type = DatabaseType(data.get("db_type", "sqlserver"))
        return cls(
            name=data["name"],
            server=data["server"],
            port=data.get("port", 1433),
            database=data.get("database", ""),
            db_type=db_type,
            authentication_mode=auth_mode,
            username=data.get("username"),
            encrypt=data.get("encrypt", True),
            trust_certificate=data.get("trust_certificate", False),
            save_password=data.get("save_password", False),
            connection_options=data.get("connection_options", {}),
        )

    def get_connection_kwargs(self, password: Optional[str] = None) -> dict:
        """Generate connection parameters for selected database type."""
        if self.db_type == DatabaseType.SQL_SERVER:
            return self._get_sqlserver_kwargs(password)
        if self.db_type == DatabaseType.MYSQL:
            return self._get_mysql_kwargs(password)
        if self.db_type == DatabaseType.POSTGRESQL:
            return self._get_postgresql_kwargs(password)
        if self.db_type == DatabaseType.ORACLE:
            return self._get_oracle_kwargs(password)
        raise ValueError(f"Unsupported database type: {self.db_type}")

    def _get_sqlserver_kwargs(self, password: Optional[str] = None) -> dict:
        """Build pymssql-style kwargs for SQL Server."""
        kwargs = {
            "host": self.server,
            "port": self.port,
            "database": self.database,
        }

        if self.authentication_mode in (AuthenticationMode.SQL_SERVER, AuthenticationMode.PASSWORD):
            kwargs["user"] = self.username
            if password:
                kwargs["password"] = password

        if self.encrypt:
            kwargs["encryption"] = "require"

        return kwargs

    def _get_mysql_kwargs(self, password: Optional[str] = None) -> dict:
        """Build generic MySQL connection kwargs."""
        kwargs = {
            "host": self.server,
            "port": self.port or 3306,
            "database": self.database,
            "charset": self.connection_options.get("charset", "utf8mb4"),
        }

        if self.username:
            kwargs["user"] = self.username
        if password:
            kwargs["password"] = password

        kwargs.update(self.connection_options)
        return kwargs

    def _get_postgresql_kwargs(self, password: Optional[str] = None) -> dict:
        """Build generic PostgreSQL connection kwargs."""
        kwargs = {
            "host": self.server,
            "port": self.port or 5432,
            "dbname": self.database,
        }

        if self.username:
            kwargs["user"] = self.username
        if password:
            kwargs["password"] = password

        if self.encrypt:
            kwargs["sslmode"] = self.connection_options.get("sslmode", "require")
        elif self.connection_options.get("sslmode"):
            kwargs["sslmode"] = self.connection_options["sslmode"]

        if self.trust_certificate:
            kwargs["sslrootcert"] = self.connection_options.get("sslrootcert")

        kwargs.update(self.connection_options)
        return kwargs

    def _get_oracle_kwargs(self, password: Optional[str] = None) -> dict:
        """Build generic Oracle connection kwargs."""
        kwargs = {
            "host": self.server,
            "port": self.port or 1521,
            "service_name": self.connection_options.get("service_name", self.database),
        }

        if self.username:
            kwargs["user"] = self.username
        if password:
            kwargs["password"] = password

        kwargs.update(self.connection_options)
        return kwargs
