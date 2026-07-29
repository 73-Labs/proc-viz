"""Result viewer widget for displaying procedure execution results."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTabWidget,
    QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from app.drivers.database_driver import ExecutionResult


class ResultViewer(QWidget):
    """Display execution results: result sets, output parameters, errors, statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Tab widget for different result views
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Result sets tab
        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.tabs.addTab(self.result_table, "Results")

        # Messages tab (info, errors, output params)
        self.messages_text = QTextEdit()
        self.messages_text.setReadOnly(True)
        self.tabs.addTab(self.messages_text, "Messages")

        self.setLayout(layout)

    def display_result(self, result: ExecutionResult):
        """Display execution result."""
        self.clear()

        if not result.success:
            self.show_error(result)
            return

        # Display result sets
        if result.result_sets:
            self.display_result_sets(result.result_sets)

        # Build messages
        messages = []

        # Show success message if no result sets
        if not result.result_sets:
            messages.append("Execution successful")

        # Show affected rows if any
        if result.affected_rows:
            messages.append(f"Rows affected: {result.affected_rows}")

        # Always show duration
        messages.append(f"Duration: {result.duration_ms:.2f}ms")

        # Output parameters
        if result.output_parameters:
            messages.append("\nOutput Parameters:")
            for param_name, value in result.output_parameters.items():
                messages.append(f"  {param_name}: {value}")

        if messages:
            self.messages_text.setText("\n".join(messages))
            if result.result_sets:
                # Show result table if there are results, but also show messages
                self.tabs.setCurrentWidget(self.result_table)
            else:
                # Show messages if no result sets
                self.tabs.setCurrentWidget(self.messages_text)

    def display_result_sets(self, result_sets):
        """Display first result set in table."""
        if not result_sets or not result_sets[0]:
            return

        first_set = result_sets[0]
        self.result_table.setColumnCount(len(first_set[0]))
        self.result_table.setHorizontalHeaderLabels(first_set[0].keys())
        self.result_table.setRowCount(len(first_set))

        for row_idx, row_data in enumerate(first_set):
            for col_idx, (col_name, value) in enumerate(row_data.items()):
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.result_table.setItem(row_idx, col_idx, item)

        self.result_table.resizeColumnsToContents()

    def show_error(self, result: ExecutionResult):
        """Display error message."""
        msg = f"<span style='color: red;'><b>Error:</b> {result.error_message}</span>"
        if result.error_details:
            msg += f"\n\n<b>Details:</b>\n{result.error_details}"
        msg += f"\n\nDuration: {result.duration_ms:.2f}ms"

        self.messages_text.setHtml(msg)
        self.tabs.setCurrentWidget(self.messages_text)

    def clear(self):
        """Clear all displays."""
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.messages_text.clear()
