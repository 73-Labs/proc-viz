"""Widget for displaying and testing procedure/function parameters."""

from typing import List, Dict, Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QPushButton, QTextEdit, QScrollArea, QFrame,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QMessageBox, QDialog,
    QTabWidget
)
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QFont, QColor
from app.drivers.database_driver import Parameter, ExecutionRequest, ExecutionResult
from app.widgets.result_viewer import ResultViewer
from app.widgets.execution_worker import ExecutionWorker


class ParametersWidget(QWidget):
    """Display procedure/function parameters with test/execution section."""

    def __init__(self, execute_callback: Optional[Callable[[ExecutionRequest], ExecutionResult]] = None):
        super().__init__()
        self.parameters: List[Parameter] = []
        self.input_fields: Dict[str, QWidget] = {}
        self.procedure_info = ("", "", "", "")  # (database, schema, procedure, object_type)
        self.object_type = "PROCEDURE"
        self.execute_callback = execute_callback
        self.timeout_seconds = 30
        self.current_connection_info = {}  # For confirmation dialog
        self.thread_pool = QThreadPool()
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Parameters table
        self.params_table = QTableWidget()
        self.params_table.setColumnCount(8)
        self.params_table.setHorizontalHeaderLabels([
            "Parameter Name", "Direction", "Data Type", "Size/Precision",
            "Required", "Default", "Ordinal", "Notes"
        ])
        self.params_table.horizontalHeader().setStretchLastSection(True)
        self.params_table.setMaximumHeight(200)
        main_layout.addWidget(self.params_table)

        # Execution section
        exec_label = QLabel("Test / Execute")
        exec_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        main_layout.addWidget(exec_label)

        # Input fields container
        self.input_container = QFrame()
        self.input_layout = QVBoxLayout(self.input_container)
        self.input_layout.setContentsMargins(0, 0, 0, 0)
        self.input_layout.setSpacing(4)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.input_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(150)
        main_layout.addWidget(scroll_area)

        # SQL Preview section
        preview_label = QLabel("Generated EXEC Statement")
        preview_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        main_layout.addWidget(preview_label)

        self.sql_preview = QTextEdit()
        self.sql_preview.setReadOnly(True)
        self.sql_preview.setFont(self.get_monospace_font())
        self.sql_preview.setMaximumHeight(100)
        main_layout.addWidget(self.sql_preview)

        # Buttons
        button_layout = QHBoxLayout()
        copy_sig_btn = QPushButton("Copy Signature")
        copy_sig_btn.clicked.connect(self.copy_signature)
        button_layout.addWidget(copy_sig_btn)

        copy_exec_btn = QPushButton("Copy EXEC Statement")
        copy_exec_btn.clicked.connect(self.copy_exec_statement)
        button_layout.addWidget(copy_exec_btn)

        button_layout.addStretch()

        self.execute_btn = QPushButton("Execute")
        self.execute_btn.clicked.connect(self.on_execute_clicked)
        self.execute_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        if not self.execute_callback:
            self.execute_btn.setEnabled(False)
            self.execute_btn.setToolTip("Execution not available")
        button_layout.addWidget(self.execute_btn)

        main_layout.addLayout(button_layout)

        # Result viewer (initially hidden)
        result_label = QLabel("Execution Results")
        result_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        main_layout.addWidget(result_label)

        self.result_viewer = ResultViewer()
        self.result_viewer.hide()
        main_layout.addWidget(self.result_viewer)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def get_monospace_font(self) -> QFont:
        """Get monospace font for code."""
        font = QFont("Courier")
        font.setPointSize(9)
        return font

    def clear_layout(self, layout):
        """Recursively clear all items from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())


    def _format_size_info(self, param: Parameter) -> str:
        """Format parameter size/precision/scale info."""
        if param.data_type in ('int', 'bigint', 'smallint', 'tinyint', 'bit'):
            return ""
        if param.precision:
            if param.scale:
                return f"({param.precision},{param.scale})"
            return f"({param.precision})"
        if param.max_length and param.max_length > 0:
            return f"({param.max_length})"
        return ""

    def create_input_fields(self, parameters: List[Parameter]):
        """Create input fields for IN/INOUT parameters."""
        input_params = [p for p in parameters if p.direction in ('IN', 'INOUT')]

        if not input_params:
            no_params_label = QLabel("No input parameters")
            no_params_label.setStyleSheet("color: gray;")
            self.input_layout.addWidget(no_params_label)
            return

        for param in input_params:
            field_layout = QHBoxLayout()

            param_label = QLabel(f"{param.name}:")
            param_label.setMinimumWidth(120)
            field_layout.addWidget(param_label)

            input_widget = self.create_input_widget(param)
            self.input_fields[param.name] = input_widget
            field_layout.addWidget(input_widget)

            # Mark required if no default
            if not param.has_default and not param.is_readonly:
                required_label = QLabel("(required)")
                required_label.setStyleSheet("color: red; font-size: 9pt;")
                field_layout.addWidget(required_label)

            field_layout.addStretch()
            self.input_layout.addLayout(field_layout)

            # Connect to SQL preview update
            if hasattr(input_widget, 'textChanged'):
                input_widget.textChanged.connect(self.update_sql_preview)
            elif hasattr(input_widget, 'valueChanged'):
                input_widget.valueChanged.connect(self.update_sql_preview)
            elif hasattr(input_widget, 'stateChanged'):
                input_widget.stateChanged.connect(self.update_sql_preview)

    def create_input_widget(self, param: Parameter) -> QWidget:
        """Create appropriate input widget for parameter type."""
        data_type = param.data_type.lower()

        if data_type in ('int', 'bigint', 'smallint', 'tinyint'):
            widget = QSpinBox()
            widget.setMinimum(-2147483648)
            widget.setMaximum(2147483647)
            if param.has_default and param.default_value:
                try:
                    widget.setValue(int(param.default_value))
                except:
                    pass
            return widget

        if data_type in ('float', 'real', 'decimal', 'numeric'):
            widget = QDoubleSpinBox()
            widget.setMinimum(-999999999.99)
            widget.setMaximum(999999999.99)
            if param.has_default and param.default_value:
                try:
                    widget.setValue(float(param.default_value))
                except:
                    pass
            return widget

        if data_type in ('bit',):
            widget = QCheckBox()
            if param.has_default and param.default_value:
                widget.setChecked(param.default_value in ('1', 'true', 'True'))
            return widget

        if data_type in ('datetime', 'datetime2', 'date', 'time'):
            widget = QLineEdit()
            widget.setPlaceholderText(f"e.g., {self._get_date_placeholder(data_type)}")
            if param.has_default and param.default_value:
                widget.setText(str(param.default_value))
            return widget

        # Default: text input
        widget = QLineEdit()
        if param.max_length and param.max_length > 0:
            widget.setMaxLength(min(param.max_length, 32767))
        widget.setPlaceholderText(f"Enter {param.data_type} value")
        if param.has_default and param.default_value:
            widget.setText(str(param.default_value))
        return widget

    def _get_date_placeholder(self, data_type: str) -> str:
        """Get placeholder for date/time types."""
        placeholders = {
            'datetime': '2025-01-15 10:30:00',
            'datetime2': '2025-01-15 10:30:00.123',
            'date': '2025-01-15',
            'time': '10:30:00'
        }
        return placeholders.get(data_type, '2025-01-15')

    def get_input_value(self, widget: QWidget) -> str:
        """Get string representation of input widget value."""
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QSpinBox):
            return str(widget.value())
        elif isinstance(widget, QDoubleSpinBox):
            return str(widget.value())
        elif isinstance(widget, QCheckBox):
            return "1" if widget.isChecked() else "0"
        return ""

    def update_sql_preview(self):
        """Update SQL preview based on input values."""
        database, schema, procedure, _ = self.procedure_info

        if not procedure:
            self.sql_preview.setText("")
            return

        exec_cmd = f"EXEC [{schema}].[{procedure}]"

        # Add input parameters with values
        input_params = [p for p in self.parameters if p.direction in ('IN', 'INOUT')]
        if input_params:
            param_stmts = []
            for param in input_params:
                if param.name in self.input_fields:
                    value = self.get_input_value(self.input_fields[param.name]).strip()
                    if value:
                        # Quote string values
                        if param.data_type.lower() not in ('int', 'bigint', 'smallint', 'tinyint', 'float', 'real', 'decimal', 'numeric', 'bit'):
                            if not (value.startswith("'") and value.endswith("'")):
                                value = f"'{value}'"
                        param_stmts.append(f"    {param.name} = {value}")

            if param_stmts:
                exec_cmd += "\n" + ",\n".join(param_stmts)

        exec_cmd += ";"

        self.sql_preview.setText(exec_cmd)

    def copy_signature(self):
        """Copy procedure signature to clipboard."""
        database, schema, procedure, _ = self.procedure_info
        if not procedure:
            return

        sig = f"[{schema}].[{procedure}]"
        if self.parameters:
            param_sigs = []
            for param in self.parameters:
                param_sig = f"{param.name} {param.data_type}"
                if self._format_size_info(param):
                    param_sig += self._format_size_info(param)
                if param.has_default:
                    param_sig += " = DEFAULT"
                param_sigs.append(param_sig)
            sig += "\n    " + ",\n    ".join(param_sigs)

        self.copy_to_clipboard(sig)
        self.show_copy_message("Procedure signature copied to clipboard")

    def copy_exec_statement(self):
        """Copy generated EXEC statement to clipboard."""
        sql = self.sql_preview.toPlainText()
        if sql:
            self.copy_to_clipboard(sql)
            self.show_copy_message("EXEC statement copied to clipboard")

    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)

    def show_copy_message(self, message: str):
        """Show copy confirmation message."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Copied")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def clear(self):
        """Clear all parameters and fields."""
        self.parameters.clear()
        self.input_fields.clear()
        self.params_table.clearContents()
        self.params_table.setRowCount(0)
        self.sql_preview.clear()
        self.clear_layout(self.input_layout)
        self.result_viewer.hide()

    def set_connection_info(self, server: str, database: str):
        """Set connection info for confirmation dialog."""
        self.current_connection_info = {"server": server, "database": database}

    def on_execute_clicked(self):
        """Handle execute button click."""
        if not self.execute_callback:
            QMessageBox.warning(self, "Not Available", "Execution not configured")
            return

        # Validate inputs
        validation_errors = self.validate_inputs()
        if validation_errors:
            QMessageBox.warning(self, "Validation Error", validation_errors)
            return

        # Show confirmation dialog
        if not self.show_confirmation_dialog():
            return

        # Build execution request
        request = self.build_execution_request()

        # Disable execute button during execution
        self.execute_btn.setEnabled(False)
        self.execute_btn.setText("Executing...")

        # Create and run worker
        worker = ExecutionWorker(self.execute_callback, request)
        worker.signals.finished.connect(self.on_execution_complete)
        worker.signals.error.connect(self.on_execution_error)
        self.thread_pool.start(worker)

    def on_execution_complete(self, result: ExecutionResult):
        """Handle execution completion."""
        self.display_result(result)
        self.execute_btn.setEnabled(True)
        self.execute_btn.setText("Execute")

    def on_execution_error(self, error_msg: str):
        """Handle execution error."""
        self.execute_btn.setEnabled(True)
        self.execute_btn.setText("Execute")
        QMessageBox.critical(self, "Execution Error", f"Failed to execute:\n{error_msg}")

    def validate_inputs(self) -> str:
        """Validate required input parameters. Return error message or empty string."""
        errors = []
        input_params = [p for p in self.parameters if p.direction in ('IN', 'INOUT')]

        for param in input_params:
            if not param.has_default and not param.is_readonly:
                if param.name not in self.input_fields:
                    errors.append(f"Missing input field for {param.name}")
                    continue

                widget = self.input_fields[param.name]
                value = self.get_input_value(widget).strip()

                if not value:
                    errors.append(f"Required parameter '{param.name}' is empty")

        return "\n".join(errors)

    def show_confirmation_dialog(self) -> bool:
        """Show confirmation dialog before execution. Return True if confirmed."""
        database, schema, procedure, _ = self.procedure_info
        server = self.current_connection_info.get("server", "unknown")
        active_db = self.current_connection_info.get("database", database)

        msg = f"Execute procedure:\n\n"
        msg += f"Server: {server}\n"
        msg += f"Database: {active_db}\n"
        msg += f"Schema: {schema}\n"
        msg += f"Procedure: {procedure}\n"
        msg += f"\nTimeout: {self.timeout_seconds}s\n"
        msg += f"\nThis will execute on the server. Continue?"

        reply = QMessageBox.question(
            self,
            "Confirm Execution",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def build_execution_request(self) -> ExecutionRequest:
        """Build ExecutionRequest from current inputs."""
        database, schema, procedure, _ = self.procedure_info

        # Collect parameter values
        parameters = {}
        for param in self.parameters:
            if param.direction in ('IN', 'INOUT'):
                if param.name in self.input_fields:
                    widget = self.input_fields[param.name]
                    value = self.get_input_value(widget).strip()
                    if value:
                        parameters[param.name] = value

        return ExecutionRequest(
            routine_name=procedure,
            schema=schema,
            database=database,
            object_type=self.object_type,
            parameters=parameters,
            timeout_seconds=self.timeout_seconds
        )

    def display_result(self, result: ExecutionResult):
        """Display execution result."""
        self.result_viewer.show()
        self.result_viewer.display_result(result)

    def load_parameters(self, database: str, schema: str, procedure: str, parameters: List[Parameter], object_type: str = "PROCEDURE"):
        """Load parameters into table and create input fields."""
        # Clear old table and inputs first
        self.params_table.clearContents()
        self.params_table.setRowCount(0)

        self.procedure_info = (database, schema, procedure, object_type)
        self.object_type = object_type
        self.parameters = parameters

        # Clear previous inputs (including nested layouts)
        self.clear_layout(self.input_layout)
        self.input_fields.clear()

        # Populate table
        if parameters:
            self.params_table.setRowCount(len(parameters))
            for idx, param in enumerate(parameters):
                self.params_table.setItem(idx, 0, QTableWidgetItem(param.name))
                self.params_table.setItem(idx, 1, QTableWidgetItem(param.direction))
                self.params_table.setItem(idx, 2, QTableWidgetItem(param.data_type))

                # Size/Precision/Scale
                size_str = self._format_size_info(param)
                self.params_table.setItem(idx, 3, QTableWidgetItem(size_str))

                # Required (not readonly, not has_default)
                required = "No" if param.has_default or param.is_readonly else "Yes"
                self.params_table.setItem(idx, 4, QTableWidgetItem(required))

                # Default value
                default_str = param.default_value or ""
                self.params_table.setItem(idx, 5, QTableWidgetItem(default_str))

                # Ordinal position
                self.params_table.setItem(idx, 6, QTableWidgetItem(str(param.ordinal_position)))

                # Notes (description)
                notes = param.description or ""
                self.params_table.setItem(idx, 7, QTableWidgetItem(notes))

            # Create input fields for IN/INOUT parameters
            self.create_input_fields(parameters)
        else:
            # No parameters
            self.params_table.setRowCount(0)
            no_params_label = QLabel("No parameters")
            no_params_label.setStyleSheet("color: gray;")
            self.input_layout.addWidget(no_params_label)

        self.update_sql_preview()
