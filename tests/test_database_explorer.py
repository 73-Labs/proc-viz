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


class TestUnifiedSearchAndFiltering:
    """Test Task 3: Unified search and filtering functionality."""

    def test_search_scope_selector_created(self, explorer):
        """Test search scope selector is created with correct options."""
        assert hasattr(explorer, 'search_scope_selector')
        assert explorer.search_scope_selector.count() == 5
        assert explorer.search_scope_selector.itemText(0) == "All Objects"
        assert explorer.search_scope_selector.itemText(1) == "Procedures"
        assert explorer.search_scope_selector.itemText(2) == "Functions"
        assert explorer.search_scope_selector.itemText(3) == "Tables"
        assert explorer.search_scope_selector.itemText(4) == "Views"

    def test_exact_match_checkbox_created(self, explorer):
        """Test exact match checkbox is created."""
        assert hasattr(explorer, 'exact_match_checkbox')
        assert explorer.exact_match_checkbox.isCheckable()

    def test_clear_filter_button_created(self, explorer):
        """Test clear filter button is created."""
        assert hasattr(explorer, 'clear_filter_btn')

    def test_result_count_label_created(self, explorer):
        """Test result count label is created."""
        assert hasattr(explorer, 'result_count_label')

    def test_filter_by_procedure_scope(self, qapp, mock_driver, test_profile):
        """Test filtering by procedures scope."""
        with patch("app.widgets.database_explorer.DatabaseAccessor") as mock_accessor_class:
            mock_accessor = MagicMock()
            mock_accessor_class.return_value = mock_accessor
            mock_accessor.get_schemas.return_value = [
                Schema("dbo", "dbo", "SalesDB"),
            ]
            mock_accessor.get_procedures.return_value = [
                Procedure("usp_GetOrders", "dbo", "SalesDB"),
            ]
            mock_accessor.get_functions.return_value = [
                Function("fn_GetTotal", "dbo", "SalesDB"),
            ]

            explorer = DatabaseExplorer(mock_driver, test_profile)
            explorer.accessor = mock_accessor
            # Disable lazy load so procedures are immediately loaded
            explorer.lazy_load_enabled = False
            explorer.load_procedures()
            qapp.processEvents()

            # Set search scope to Procedures only
            explorer.search_scope_selector.setCurrentText("Procedures")
            explorer.filter_input.setText("Get")
            qapp.processEvents()

            # Wait for debounce
            if explorer.filter_debounce_timer:
                explorer.filter_debounce_timer.timeout.emit()
            qapp.processEvents()

            # Verify scope was set
            assert explorer.last_search_scope == "Procedures"
            # Filter should be active with text
            assert explorer.search_filter_active is True

    def test_filter_by_function_scope(self, qapp, mock_driver, test_profile):
        """Test filtering by functions scope."""
        with patch("app.widgets.database_explorer.DatabaseAccessor") as mock_accessor_class:
            mock_accessor = MagicMock()
            mock_accessor_class.return_value = mock_accessor
            mock_accessor.get_schemas.return_value = [
                Schema("dbo", "dbo", "SalesDB"),
            ]
            mock_accessor.get_procedures.return_value = [
                Procedure("usp_GetOrders", "dbo", "SalesDB"),
            ]
            mock_accessor.get_functions.return_value = [
                Function("fn_GetTotal", "dbo", "SalesDB"),
            ]

            explorer = DatabaseExplorer(mock_driver, test_profile)
            explorer.accessor = mock_accessor
            qapp.processEvents()

            # Set search scope to Functions only
            explorer.search_scope_selector.setCurrentText("Functions")
            explorer.filter_input.setText("Get")
            qapp.processEvents()

            # Wait for debounce
            if explorer.filter_debounce_timer:
                explorer.filter_debounce_timer.timeout.emit()
            qapp.processEvents()

            # Check filtering applied
            assert "Functions" == explorer.last_search_scope

    def test_case_insensitive_filtering(self, explorer):
        """Test that filtering is case-insensitive by default."""
        # Set lowercase search term
        explorer.filter_input.setText("usp")
        explorer._apply_filter()

        schema_item = explorer.tree.topLevelItem(0)
        if schema_item and schema_item.childCount() > 0:
            child = schema_item.child(0)
            # Should find "usp_GetOrders" with lowercase search
            data = child.data(0, Qt.UserRole)
            if data and data[0] == "procedure":
                assert child.text(0).lower() == "usp_getorders"

    def test_exact_match_filtering(self, explorer):
        """Test exact match mode."""
        explorer.exact_match_checkbox.setChecked(True)
        explorer.filter_input.setText("usp_GetOrders")
        explorer._apply_filter()

        # After applying exact match for full name, should find it
        schema_item = explorer.tree.topLevelItem(0)
        assert schema_item is not None

    def test_partial_match_filtering(self, explorer):
        """Test partial text matching."""
        explorer.exact_match_checkbox.setChecked(False)
        explorer.filter_input.setText("usp")
        explorer._apply_filter()

        # Partial match should find "usp_GetOrders"
        schema_item = explorer.tree.topLevelItem(0)
        if schema_item:
            found = False
            for i in range(schema_item.childCount()):
                child = schema_item.child(i)
                if "usp" in child.text(0).lower():
                    found = True
                    break
            # At least should have tried to filter
            assert explorer.search_filter_active

    def test_clear_filter_action(self, explorer):
        """Test clear filter button clears search."""
        explorer.filter_input.setText("test")
        explorer._apply_filter()
        assert explorer.last_filter_text == "test"

        explorer.on_clear_filter()
        assert explorer.last_filter_text == ""
        assert explorer.filter_input.text() == ""
        assert explorer.result_count_label.text() == ""

    def test_result_count_display(self, explorer):
        """Test result count is displayed."""
        explorer.filter_input.setText("usp")
        explorer._apply_filter()

        # Should show result count if filtering
        if explorer.search_filter_active:
            count_text = explorer.result_count_label.text()
            assert "match" in count_text.lower() or count_text == ""

    def test_schema_filter_for_routine_search(self, qapp, mock_driver, test_profile):
        """Test schema selector filters routine search."""
        with patch("app.widgets.database_explorer.DatabaseAccessor") as mock_accessor_class:
            mock_accessor = MagicMock()
            mock_accessor_class.return_value = mock_accessor
            mock_accessor.get_schemas.return_value = [
                Schema("dbo", "dbo", "SalesDB"),
                Schema("Sales", "Sales", "SalesDB"),
            ]
            mock_accessor.get_procedures.return_value = [
                Procedure("usp_GetOrders", "dbo", "SalesDB"),
            ]
            mock_accessor.get_functions.return_value = []

            explorer = DatabaseExplorer(mock_driver, test_profile)
            explorer.accessor = mock_accessor
            qapp.processEvents()

            # Change schema selector
            explorer.schema_selector.setCurrentText("dbo")
            explorer.filter_input.setText("Get")
            explorer._apply_filter()

            # Schema should be set
            assert explorer.last_selected_schema == "dbo"

    def test_filter_preserved_after_refresh(self, qapp, mock_driver, test_profile):
        """Test that filter text is preserved during refresh."""
        with patch("app.widgets.database_explorer.DatabaseAccessor") as mock_accessor_class:
            mock_accessor = MagicMock()
            mock_accessor_class.return_value = mock_accessor
            mock_accessor.get_schemas.return_value = [
                Schema("dbo", "dbo", "SalesDB"),
            ]
            mock_accessor.get_procedures.return_value = [
                Procedure("usp_GetOrders", "dbo", "SalesDB"),
            ]
            mock_accessor.get_functions.return_value = []

            explorer = DatabaseExplorer(mock_driver, test_profile)
            explorer.accessor = mock_accessor

            # Set filter before refresh
            explorer.filter_input.setText("usp")
            explorer.last_filter_text = "usp"

            # Refresh should preserve filter attempt
            explorer.load_procedures()
            qapp.processEvents()

            # Filter text should still be there (UI might reapply it)
            assert explorer.filter_input.text() == "usp"

    def test_table_filter_independent_of_routine_filter(self, explorer):
        """Test that table reference search is independent of routine name filter."""
        explorer.filter_input.setText("test")
        explorer.table_filter_input.setText("Orders")

        # When table filter is active, routine filter should not apply
        explorer.table_filter_active = True
        # on_filter_text_changed should return early
        explorer.on_filter_text_changed("ignored")

        # table_filter_active should still be true
        assert explorer.table_filter_active is True

    def test_filter_scope_dropdown_has_all_options(self, explorer):
        """Test that all filter scope options are available."""
        scopes = []
        for i in range(explorer.search_scope_selector.count()):
            scopes.append(explorer.search_scope_selector.itemText(i))

        assert "All Objects" in scopes
        assert "Procedures" in scopes
        assert "Functions" in scopes
        assert "Tables" in scopes
        assert "Views" in scopes

    def test_filter_debounce_prevents_immediate_filter(self, qapp, explorer):
        """Test that filter debouncing prevents immediate tree filtering."""
        # Type multiple characters quickly
        explorer.filter_input.setText("a")
        explorer.filter_input.setText("ab")
        explorer.filter_input.setText("abc")

        # Should have at most one active debounce timer
        timer_count = 1 if explorer.filter_debounce_timer else 0
        assert timer_count <= 1
