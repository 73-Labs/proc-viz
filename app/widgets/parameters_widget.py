"""Widget for displaying and testing procedure/function parameters."""

from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QPushButton, QTextEdit, QScrollArea, QFrame,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from app.drivers.database_driver import Parameter


class ParametersWidget(QWidget):
    """Display procedure/function parameters with test/execution section."""

    def __init__(self):
        super().__init__()
        self.parameters: List[Parameter] = []
        self.input_fields: Dict[str, QWidget] = {}
        self.procedure_info = ("", "", "")  # (database, schema, procedure)
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
        main_layout.addLayout(button_layout)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def get_monospace_font(self) -> QFont:
        """Get monospace font for code."""
        font = QFont("Courier")
        font.setPointSize(9)
        return font

    def load_parameters(self, database: str, schema: str, procedure: str, parameters: List[Parameter]):
        """Load parameters into table and create input fields."""
        self.procedure_info = (database, schema, procedure)
        self.parameters = parameters

        # Clear previous inputs
        for i in reversed(range(self.input_layout.count())):
            widget = self.input_layout.takeAt(i).widget()
            if widget:
                widget.deleteLater()
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
        database, schema, procedure = self.procedure_info

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
        database, schema, procedure = self.procedure_info
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
        self.params_table.setRowCount(0)
        self.sql_preview.clear()

        for i in reversed(range(self.input_layout.count())):
            widget = self.input_layout.takeAt(i).widget()
            if widget:
                widget.deleteLater()
