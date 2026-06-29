"""Tests for database accessor."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.db_accessor import DatabaseAccessor
from app.drivers.database_driver import (
    DatabaseDriver,
    Database,
    Schema,
    Procedure,
    Function,
    Table,
    ObjectDependency,
)


@pytest.fixture
def mock_driver():
    """Create mock DatabaseDriver."""
    return MagicMock(spec=DatabaseDriver)


class TestDatabaseAccessor:
    """Test DatabaseAccessor delegates to driver correctly."""

    def test_get_databases(self, mock_driver):
        """Test fetching databases."""
        mock_driver.get_databases.return_value = [
            Database(name="master", schema="", database="master"),
            Database(name="tempdb", schema="", database="tempdb"),
            Database(name="SalesDB", schema="", database="SalesDB"),
            Database(name="ReportingDB", schema="", database="ReportingDB"),
        ]

        accessor = DatabaseAccessor(mock_driver)
        databases = accessor.get_databases()

        assert len(databases) == 4
        assert databases[0].name == "master"
        assert databases[2].name == "SalesDB"
        mock_driver.get_databases.assert_called_once()

    def test_get_schemas(self, mock_driver):
        """Test fetching schemas."""
        mock_driver.get_schemas.return_value = [
            Schema(name="dbo", schema="dbo", database="SalesDB"),
            Schema(name="sales", schema="sales", database="SalesDB"),
            Schema(name="reporting", schema="reporting", database="SalesDB"),
        ]

        accessor = DatabaseAccessor(mock_driver)
        schemas = accessor.get_schemas("SalesDB")

        assert len(schemas) == 3
        assert schemas[0].name == "dbo"
        assert schemas[0].database == "SalesDB"
        mock_driver.get_schemas.assert_called_once_with("SalesDB")

    def test_get_procedures(self, mock_driver):
        """Test fetching procedures."""
        mock_driver.get_procedures.return_value = [
            Procedure(name="usp_GetOrders", schema="dbo", database="SalesDB"),
            Procedure(name="usp_CreateOrder", schema="dbo", database="SalesDB"),
        ]

        accessor = DatabaseAccessor(mock_driver)
        procedures = accessor.get_procedures("SalesDB", "dbo")

        assert len(procedures) == 2
        assert procedures[0].name == "usp_GetOrders"
        assert procedures[0].schema == "dbo"
        assert procedures[0].database == "SalesDB"
        mock_driver.get_procedures.assert_called_once_with("SalesDB", "dbo")

    def test_get_functions(self, mock_driver):
        """Test fetching functions."""
        mock_driver.get_functions.return_value = [
            Function(name="fn_FormatDate", schema="dbo", database="SalesDB"),
            Function(name="fn_GetCustomerCount", schema="dbo", database="SalesDB"),
        ]

        accessor = DatabaseAccessor(mock_driver)
        functions = accessor.get_functions("SalesDB", "dbo")

        assert len(functions) == 2
        assert functions[0].name == "fn_FormatDate"
        assert functions[0].type == "FUNCTION"

    def test_get_tables(self, mock_driver):
        """Test fetching tables."""
        mock_driver.get_tables.return_value = [
            Table(name="Orders", schema="dbo", database="SalesDB"),
            Table(name="Customers", schema="dbo", database="SalesDB"),
            Table(name="Products", schema="dbo", database="SalesDB"),
        ]

        accessor = DatabaseAccessor(mock_driver)
        tables = accessor.get_tables("SalesDB", "dbo")

        assert len(tables) == 3
        assert tables[0].name == "Orders"

    def test_get_procedure_source(self, mock_driver):
        """Test fetching procedure source code."""
        source_code = "CREATE PROCEDURE dbo.usp_GetOrders AS SELECT * FROM Orders"
        mock_driver.get_procedure_source.return_value = source_code

        accessor = DatabaseAccessor(mock_driver)
        source = accessor.get_procedure_source("SalesDB", "dbo", "usp_GetOrders")

        assert source == source_code
        mock_driver.get_procedure_source.assert_called_once_with("SalesDB", "dbo", "usp_GetOrders")

    def test_get_procedure_source_not_found(self, mock_driver):
        """Test procedure source when not found."""
        mock_driver.get_procedure_source.return_value = None

        accessor = DatabaseAccessor(mock_driver)
        source = accessor.get_procedure_source("SalesDB", "dbo", "nonexistent")

        assert source is None

    def test_get_function_source(self, mock_driver):
        """Test fetching function source code."""
        source_code = "CREATE FUNCTION dbo.fn_GetDate() RETURNS DATETIME AS RETURN GETDATE()"
        mock_driver.get_function_source.return_value = source_code

        accessor = DatabaseAccessor(mock_driver)
        source = accessor.get_function_source("SalesDB", "dbo", "fn_GetDate")

        assert source == source_code

    def test_driver_delegation(self, mock_driver):
        """Test accessor properly delegates to driver."""
        mock_driver.get_called_procedures.return_value = [
            ObjectDependency(schema="dbo", name="usp_Other", type="PROCEDURE"),
        ]

        accessor = DatabaseAccessor(mock_driver)
        result = accessor.get_called_procedures("SalesDB", "dbo", "usp_GetOrders")

        assert len(result) == 1
        assert result[0]["name"] == "usp_Other"
        assert result[0]["type"] == "PROCEDURE"
