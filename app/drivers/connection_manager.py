"""Manages database connections with support for multiple database types."""

import pymssql
from typing import Optional
from app.models.connection_profile import ConnectionProfile, DatabaseType
from app.drivers.database_driver import DatabaseDriver
from app.drivers.driver_factory import DriverFactory


class ConnectionManager:
    """Creates and manages database connections. Abstracts connection details from drivers."""

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
        if profile.db_type == DatabaseType.SQL_SERVER:
            return ConnectionManager._create_sqlserver_connection(profile, password)
        elif profile.db_type == DatabaseType.MYSQL:
            raise NotImplementedError("MySQL support coming soon")
        elif profile.db_type == DatabaseType.POSTGRESQL:
            raise NotImplementedError("PostgreSQL support coming soon")
        elif profile.db_type == DatabaseType.ORACLE:
            raise NotImplementedError("Oracle support coming soon")
        else:
            raise ValueError(f"Unsupported database type: {profile.db_type}")

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
