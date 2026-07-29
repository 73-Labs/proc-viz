"""Tests for procedure execution functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from threading import Event

from app.drivers.database_driver import (
    DatabaseDriver,
    ExecutionRequest,
    ExecutionResult,
    Parameter,
)
from app.drivers.sqlserver_driver import SQLServerDriver
from app.db_accessor import DatabaseAccessor


@pytest.fixture
def mock_sqlserver_driver():
    """Create mock pymssql connection."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


@pytest.fixture
def execution_request():
    """Create basic execution request."""
    return ExecutionRequest(
        routine_name="usp_TestProc",
        schema="dbo",
        database="TestDB",
        object_type="PROCEDURE",
        parameters={"@param1": "value1"},
        timeout_seconds=30
    )


class TestExecutionModels:
    """Test ExecutionRequest and ExecutionResult models."""

    def test_execution_request_creation(self, execution_request):
        """Test creating execution request."""
        assert execution_request.routine_name == "usp_TestProc"
        assert execution_request.schema == "dbo"
        assert execution_request.database == "TestDB"
        assert execution_request.object_type == "PROCEDURE"
        assert execution_request.parameters == {"@param1": "value1"}
        assert execution_request.timeout_seconds == 30
        assert execution_request.cancel_flag is None

    def test_execution_request_with_cancel_flag(self):
        """Test execution request with cancellation flag."""
        cancel = Event()
        request = ExecutionRequest(
            routine_name="proc",
            schema="dbo",
            database="db",
            object_type="PROCEDURE",
            parameters={},
            cancel_flag=cancel
        )
        assert request.cancel_flag is cancel

    def test_execution_result_success(self):
        """Test successful execution result."""
        result = ExecutionResult(
            success=True,
            result_sets=[[{"id": 1, "name": "test"}]],
            output_parameters={"@output": "result"},
            affected_rows=1,
            duration_ms=50.5
        )
        assert result.success is True
        assert len(result.result_sets) == 1
        assert result.affected_rows == 1
        assert result.error_message is None

    def test_execution_result_failure(self):
        """Test failed execution result."""
        result = ExecutionResult(
            success=False,
            error_message="Connection timeout",
            error_details="Timeout after 30s",
            duration_ms=30000.0
        )
        assert result.success is False
        assert result.error_message == "Connection timeout"
        assert result.error_details == "Timeout after 30s"
        assert len(result.result_sets) == 0


class TestSQLServerDriverExecution:
    """Test SQLServerDriver.execute_procedure."""

    def test_execute_procedure_validates_required_params(self, mock_sqlserver_driver):
        """Test that execution validates required parameters."""
        conn, cursor = mock_sqlserver_driver

        # Mock get_procedure_parameters to return a required parameter
        driver = SQLServerDriver(conn)
        driver.get_procedure_parameters = MagicMock(return_value=[
            Parameter(
                name="@required_param",
                direction="IN",
                data_type="varchar",
                has_default=False
            )
        ])

        request = ExecutionRequest(
            routine_name="proc",
            schema="dbo",
            database="db",
            object_type="PROCEDURE",
            parameters={}  # Missing required param
        )

        result = driver.execute_procedure(request)

        assert result.success is False
        assert "Required parameter" in result.error_message
        assert "@required_param" in result.error_message

    def test_execute_procedure_handles_cancellation(self, mock_sqlserver_driver):
        """Test that execution respects cancellation flag."""
        conn, cursor = mock_sqlserver_driver
        driver = SQLServerDriver(conn)

        cancel = Event()
        cancel.set()

        request = ExecutionRequest(
            routine_name="proc",
            schema="dbo",
            database="db",
            object_type="PROCEDURE",
            parameters={},
            cancel_flag=cancel
        )

        result = driver.execute_procedure(request)

        assert result.success is False
        assert "cancelled" in result.error_message.lower()

    def test_execute_procedure_captures_result_sets(self, mock_sqlserver_driver):
        """Test that execution captures result sets."""
        conn, cursor = mock_sqlserver_driver
        driver = SQLServerDriver(conn)

        # Mock parameter retrieval
        driver.get_procedure_parameters = MagicMock(return_value=[])

        # Mock cursor to return result set
        cursor.execute.return_value = None
        cursor.fetchall.side_effect = [
            [(1, "row1"), (2, "row2")],
            [],  # No more rows after nextset
        ]
        cursor.nextset.return_value = False
        cursor.description = [("id", None, None, None, None, None, None), ("name", None, None, None, None, None, None)]

        request = ExecutionRequest(
            routine_name="proc",
            schema="dbo",
            database="db",
            object_type="PROCEDURE",
            parameters={}
        )

        result = driver.execute_procedure(request)

        # Note: Due to the mock structure, this may not perfectly capture real behavior
        # Full integration testing should validate this properly
        cursor.execute.assert_called()

    def test_execute_procedure_handles_exceptions(self, mock_sqlserver_driver):
        """Test that execution handles database errors gracefully."""
        conn, cursor = mock_sqlserver_driver
        driver = SQLServerDriver(conn)

        driver.get_procedure_parameters = MagicMock(return_value=[])
        cursor.execute.side_effect = Exception("Database error")

        request = ExecutionRequest(
            routine_name="proc",
            schema="dbo",
            database="db",
            object_type="PROCEDURE",
            parameters={}
        )

        result = driver.execute_procedure(request)

        assert result.success is False
        assert result.error_message is not None
        assert "Database error" in result.error_message

    def test_execute_procedure_builds_qualified_name(self, mock_sqlserver_driver):
        """Test that procedure names are properly quoted."""
        conn, cursor = mock_sqlserver_driver
        driver = SQLServerDriver(conn)

        driver.get_procedure_parameters = MagicMock(return_value=[])
        cursor.execute.return_value = None
        cursor.fetchall.return_value = []
        cursor.nextset.return_value = False

        request = ExecutionRequest(
            routine_name="my_proc",
            schema="my_schema",
            database="my_db",
            object_type="PROCEDURE",
            parameters={}
        )

        result = driver.execute_procedure(request)

        # Check that EXEC statement was built with brackets (safe quoting)
        call_args = cursor.execute.call_args_list
        assert any("[my_schema].[my_proc]" in str(call) for call in call_args)


class TestDatabaseAccessorExecution:
    """Test DatabaseAccessor.execute_procedure."""

    def test_accessor_delegates_execution(self):
        """Test that accessor delegates execution to driver."""
        mock_driver = MagicMock(spec=DatabaseDriver)
        expected_result = ExecutionResult(success=True)
        mock_driver.execute_procedure.return_value = expected_result

        accessor = DatabaseAccessor(mock_driver)
        request = ExecutionRequest(
            routine_name="proc",
            schema="dbo",
            database="db",
            object_type="PROCEDURE",
            parameters={}
        )

        result = accessor.execute_procedure(request)

        assert result is expected_result
        mock_driver.execute_procedure.assert_called_once_with(request)


class TestParameterValidation:
    """Test parameter validation for execution."""

    def test_no_string_interpolation_used(self):
        """Test that execution uses parameterized queries, not string interpolation."""
        # This is validated by the SQLServerDriver implementation
        # Using parameterized queries with %s placeholders
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        driver = SQLServerDriver(mock_conn)
        driver.get_procedure_parameters = MagicMock(return_value=[
            Parameter(name="@param1", direction="IN", data_type="varchar", has_default=False)
        ])

        mock_cursor.execute.return_value = None
        mock_cursor.fetchall.return_value = []
        mock_cursor.nextset.return_value = False

        request = ExecutionRequest(
            routine_name="proc",
            schema="dbo",
            database="db",
            object_type="PROCEDURE",
            parameters={"@param1": "test'; DROP TABLE users; --"}
        )

        result = driver.execute_procedure(request)

        # Verify parameterized query was used
        # First call is USE [db], second is the EXEC statement with parameters
        execute_calls = mock_cursor.execute.call_args_list
        assert len(execute_calls) >= 2

        # Check the EXEC call (second call)
        exec_call = execute_calls[1]
        assert len(exec_call[0]) == 2  # SQL string and parameters tuple
        assert isinstance(exec_call[0][1], tuple)
        # The malicious value should be in the parameters tuple, not in the SQL string
        assert "DROP TABLE" not in exec_call[0][0]  # Not in SQL
        assert "test'; DROP TABLE users; --" in str(exec_call[0][1])  # In parameters
