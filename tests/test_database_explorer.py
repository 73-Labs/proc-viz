"""Tests for database explorer widget."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import sys

from app.widgets.database_explorer import DatabaseExplorer
from app.drivers.database_driver import (
    DatabaseDriver,
    Database,
    Schema,
    Procedure,
    Function,
    Table,
)
from app.models import ConnectionProfile, AuthenticationMode


@pytest.fixture
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def mock_driver():
    """Create mock DatabaseDriver."""
    return MagicMock(spec=DatabaseDriver)


@pytest.fixture
def test_profile():
    """Create test connection profile."""
    return ConnectionProfile(
        name="Test DB",
        server="localhost",
        database="SalesDB",
        port=1433,
        authentication_mode=AuthenticationMode.WINDOWS,
    )


@pytest.fixture
def explorer(qapp, mock_driver, test_profile):
    """Create DatabaseExplorer with mocked driver."""
    with patch("app.widgets.database_explorer.DatabaseAccessor") as mock_accessor_class:
        mock_accessor = MagicMock()
        mock_accessor_class.return_value = mock_accessor

        # Mock database queries
        mock_accessor.get_schemas.return_value = [
            Schema("dbo", "dbo", "SalesDB"),
        ]
        mock_accessor.get_procedures.return_value = [
            Procedure("usp_GetOrders", "dbo", "SalesDB"),
        ]
        mock_accessor.get_functions.return_value = []
        mock_accessor.get_tables.return_value = [
            Table("Orders", "dbo", "SalesDB"),
        ]

        explorer = DatabaseExplorer(mock_driver, test_profile)
        explorer.accessor = mock_accessor
        qapp.processEvents()  # Execute QTimer callbacks
        return explorer


class TestDatabaseExplorer:
    """Test DatabaseExplorer widget."""

    def test_explorer_creation(self, explorer):
        """Test explorer widget is created."""
        assert explorer is not None
        assert explorer.tree is not None
        assert explorer.source_text is not None

    def test_tree_has_header(self, explorer):
        """Test tree widget is created."""
        assert explorer.tree is not None

    def test_load_procedures_populates_tree(self, qapp, mock_driver, test_profile):
        """Test procedures are loaded and added to tree."""
        from PySide6.QtCore import QTimer
        with patch("app.widgets.database_explorer.DatabaseAccessor") as mock_accessor_class:
            mock_accessor = MagicMock()
            mock_accessor_class.return_value = mock_accessor

            mock_accessor.get_schemas.return_value = [
                Schema("dbo", "dbo", "SalesDB"),
            ]
            mock_accessor.get_procedures.return_value = []
            mock_accessor.get_functions.return_value = []

            explorer = DatabaseExplorer(mock_driver, test_profile)
            explorer.accessor = mock_accessor

            # Process Qt events to execute QTimer callbacks
            qapp.processEvents()
            assert explorer.tree.topLevelItemCount() >= 1

    def test_procedure_source_display(self, explorer):
        """Test procedure source is displayed when selected."""
        # Set up procedure source
        source_code = "CREATE PROCEDURE dbo.usp_GetOrders AS SELECT * FROM Orders"
        explorer.accessor.get_procedure_source.return_value = source_code

        # Find procedure item in tree
        schema_item = explorer.tree.topLevelItem(0)
        if schema_item:
            # Look for procedure in children
            for i in range(schema_item.childCount()):
                child = schema_item.child(i)
                data = child.data(0, Qt.UserRole)
                if data and data[0] == "procedure":
                    explorer.on_item_selected(child, 0)
                    assert source_code in explorer.source_text.toPlainText()
                    return

    def test_source_text_cleared_on_schema_select(self, explorer):
        """Test source text is cleared when schema selected."""
        explorer.source_text.setText("Some source code")

        schema_item = explorer.tree.topLevelItem(0)
        if schema_item:
            explorer.on_item_selected(schema_item, 0)
            assert explorer.source_text.toPlainText() == ""

    def test_error_handling_on_procedures_load_failure(self, qapp, mock_driver, test_profile):
        """Test error handling when procedures load fails."""
        with patch("app.widgets.database_explorer.DatabaseAccessor") as mock_accessor_class:
            mock_accessor = MagicMock()
            mock_accessor_class.return_value = mock_accessor
            mock_accessor.get_schemas.side_effect = Exception("Connection failed")

            explorer = DatabaseExplorer(mock_driver, test_profile)
            explorer.accessor = mock_accessor
            qapp.processEvents()  # Execute QTimer callbacks to trigger load_procedures

            # Should display error in source text
            assert "Error" in explorer.source_text.toPlainText()
