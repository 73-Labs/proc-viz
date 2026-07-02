"""Manages database connections with support for multiple database types."""

from typing import Optional, Callable, Dict
from app.models.connection_profile import ConnectionProfile, DatabaseType
from app.drivers.database_driver import DatabaseDriver
from app.drivers.driver_factory import DriverFactory


class ConnectionManager:
    """Creates and manages database connections. Abstracts connection details from drivers."""

    _connection_creators: Dict[DatabaseType, Callable[[ConnectionProfile, Optional[str]], DatabaseDriver]] = {}

    @classmethod
    def register_connection_creator(
        cls,
        db_type: DatabaseType,
        creator: Callable[[ConnectionProfile, Optional[str]], DatabaseDriver],
    ) -> None:
        """Register connection creator for database type."""
        cls._connection_creators[db_type] = creator

    @staticmethod
    def create_connection(profile: ConnectionProfile, password: Optional[str] = None) -> DatabaseDriver:
        """Create database connection using profile.

        Args:
            profile: Connection profile with database configuration
            password: Password for SQL Server authentication (if needed)

        Returns:
            DatabaseDriver instance ready to use

        Raises:
            ValueError: If database type not supported
            Exception: If connection fails
        """
        creator = ConnectionManager._connection_creators.get(profile.db_type)
        if creator is None:
            raise NotImplementedError(f"{profile.db_type.value} support coming soon")
        return creator(profile, password)

    @staticmethod
    def _create_sqlserver_connection(
        profile: ConnectionProfile, password: Optional[str] = None
    ) -> DatabaseDriver:
        """Create SQL Server connection.

        Args:
            profile: SQL Server connection profile
            password: Password for SQL Server auth mode

        Returns:
            SQLServerDriver instance
        """
        import pymssql

        kwargs = profile.get_connection_kwargs(password)

        # Add timeout and other SQL Server specific options
        kwargs['timeout'] = 30
        kwargs['autocommit'] = True

        try:
            conn = pymssql.connect(**kwargs)
            driver = DriverFactory.create_driver(DatabaseType.SQL_SERVER, conn)
            return driver
        except pymssql.Error as e:
            raise ConnectionError(f"Failed to connect to SQL Server: {e}")
        except Exception as e:
            raise Exception(f"Connection error: {e}")


ConnectionManager.register_connection_creator(
    DatabaseType.SQL_SERVER,
    ConnectionManager._create_sqlserver_connection,
)
