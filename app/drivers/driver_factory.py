"""Factory for creating database driver instances."""

from typing import Any, Optional, Type
from app.drivers.database_driver import DatabaseDriver
from app.models.connection_profile import DatabaseType


class DriverFactory:
    """Factory for creating database drivers. Extensible for new database types."""

    _drivers = {}
    _defaults_loaded = False

    @classmethod
    def _ensure_defaults(cls) -> None:
        """Load built-in drivers on demand."""
        if cls._defaults_loaded:
            return

        from app.drivers.sqlserver_driver import SQLServerDriver

        cls._drivers.setdefault(DatabaseType.SQL_SERVER, SQLServerDriver)
        cls._defaults_loaded = True

    @classmethod
    def create_driver(cls, db_type: DatabaseType, connection: Any) -> DatabaseDriver:
        """Create driver for given database type.

        Args:
            db_type: Database type to create driver for
            connection: Database connection object

        Returns:
            DatabaseDriver instance

        Raises:
            ValueError: If database type not supported
            TypeError: If connection type incompatible with driver
        """
        cls._ensure_defaults()
        if db_type not in cls._drivers:
            raise ValueError(f"Unsupported database type: {db_type.value}")

        driver_class = cls._drivers[db_type]
        return driver_class(connection)

    @classmethod
    def register_driver(cls, db_type: DatabaseType, driver_class: Type[DatabaseDriver]) -> None:
        """Register new database driver.

        Args:
            db_type: Database type identifier
            driver_class: Driver class implementing DatabaseDriver interface
        """
        if not issubclass(driver_class, DatabaseDriver):
            raise TypeError(f"Driver must implement DatabaseDriver interface")

        cls._drivers[db_type] = driver_class
        if db_type == DatabaseType.SQL_SERVER:
            cls._defaults_loaded = True

    @classmethod
    def get_supported_types(cls) -> list:
        """Get list of supported database types."""
        return list(cls._drivers.keys())
