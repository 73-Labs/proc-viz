"""Tests for database accessor."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.db_accessor import DatabaseAccessor, Database, Schema, Procedure, Function, Table


@pytest.fixture
def mock_connection():
    """Create mock pymssql connection."""
    return Mock()


class TestDatabaseAccessor:
    """Test DatabaseAccessor queries."""

    def test_get_databases(self, mock_connection):
        """Test fetching databases."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("master",),
            ("tempdb",),
            ("SalesDB",),
            ("ReportingDB",),
        ]
        mock_connection.cursor.return_value = mock_cursor

        accessor = DatabaseAccessor(mock_connection)
        databases = accessor.get_databases()

        assert len(databases) == 4
        assert databases[0].name == "master"
        assert databases[2].name == "SalesDB"
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_get_schemas(self, mock_connection):
        """Test fetching schemas."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("dbo",),
            ("sales",),
            ("reporting",),
        ]
        mock_connection.cursor.return_value = mock_cursor

        accessor = DatabaseAccessor(mock_connection)
        schemas = accessor.get_schemas("SalesDB")

        assert len(schemas) == 3
        assert schemas[0].name == "dbo"
        assert schemas[0].database == "SalesDB"

    def test_get_procedures(self, mock_connection):
        """Test fetching procedures."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("usp_GetOrders",),
            ("usp_CreateOrder",),
        ]
        mock_connection.cursor.return_value = mock_cursor

        accessor = DatabaseAccessor(mock_connection)
        procedures = accessor.get_procedures("SalesDB", "dbo")

        assert len(procedures) == 2
        assert procedures[0].name == "usp_GetOrders"
        assert procedures[0].schema == "dbo"
        assert procedures[0].database == "SalesDB"

    def test_get_functions(self, mock_connection):
        """Test fetching functions."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("fn_FormatDate",),
            ("fn_GetCustomerCount",),
        ]
        mock_connection.cursor.return_value = mock_cursor

        accessor = DatabaseAccessor(mock_connection)
        functions = accessor.get_functions("SalesDB", "dbo")

        assert len(functions) == 2
        assert functions[0].name == "fn_FormatDate"
        assert functions[0].type == "FUNCTION"

    def test_get_tables(self, mock_connection):
        """Test fetching tables."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("Orders",),
            ("Customers",),
            ("Products",),
        ]
        mock_connection.cursor.return_value = mock_cursor

        accessor = DatabaseAccessor(mock_connection)
        tables = accessor.get_tables("SalesDB", "dbo")

        assert len(tables) == 3
        assert tables[0].name == "Orders"

    def test_get_procedure_source(self, mock_connection):
        """Test fetching procedure source code."""
        mock_cursor = MagicMock()
        source_code = "CREATE PROCEDURE dbo.usp_GetOrders AS SELECT * FROM Orders"
        mock_cursor.fetchone.return_value = (source_code,)
        mock_connection.cursor.return_value = mock_cursor

        accessor = DatabaseAccessor(mock_connection)
        source = accessor.get_procedure_source("SalesDB", "dbo", "usp_GetOrders")

        assert source == source_code

    def test_get_procedure_source_not_found(self, mock_connection):
        """Test procedure source when not found."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection.cursor.return_value = mock_cursor

        accessor = DatabaseAccessor(mock_connection)
        source = accessor.get_procedure_source("SalesDB", "dbo", "nonexistent")

        assert source is None

    def test_get_function_source(self, mock_connection):
        """Test fetching function source code."""
        mock_cursor = MagicMock()
        source_code = "CREATE FUNCTION dbo.fn_GetDate() RETURNS DATETIME AS RETURN GETDATE()"
        mock_cursor.fetchone.return_value = (source_code,)
        mock_connection.cursor.return_value = mock_cursor

        accessor = DatabaseAccessor(mock_connection)
        source = accessor.get_function_source("SalesDB", "dbo", "fn_GetDate")

        assert source == source_code

    def test_connection_cleanup_on_error(self, mock_connection):
        """Test cursor is closed even on error."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = Exception("Query error")
        mock_connection.cursor.return_value = mock_cursor

        accessor = DatabaseAccessor(mock_connection)

        with pytest.raises(Exception):
            accessor.get_databases()

        mock_cursor.close.assert_called_once()
