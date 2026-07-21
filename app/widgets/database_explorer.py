"""Database explorer with proper UI layout matching reference."""

import json
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QTabWidget, QTextEdit,
    QSplitter, QPushButton, QLabel, QFileDialog, QMessageBox,
    QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QFont, QKeySequence, QIcon, QPixmap, QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication
from app.db_accessor import DatabaseAccessor
from app.drivers.database_driver import DatabaseDriver
from app.widgets.sql_highlighter import SqlSyntaxHighlighter
from app.widgets.zoomable_text_edit import ZoomableTextEdit
from app.widgets.loading_spinner import LoadingOverlay
from app.widgets.parameters_widget import ParametersWidget


ICON_COLORS = {
    'SCHEMA': QColor(100, 150, 255),
    'TABLE': QColor(0, 180, 100),
    'PROCEDURE': QColor(255, 140, 0),
    'FUNCTION': QColor(100, 200, 255),
    'VIEW': QColor(150, 150, 0),
    'DEFAULT': QColor(150, 150, 150),
}


class RoutineTreeWidget(QTreeWidget):
    """Tree widget that handles Enter key to show procedure/function details."""

    item_enter_pressed = Signal(QTreeWidgetItem)

    def keyPressEvent(self, event):
        """Handle Enter key to show details for selected procedure/function."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            current_item = self.currentItem()
            if current_item:
                self.item_enter_pressed.emit(current_item)
                event.accept()
                return
        super().keyPressEvent(event)


class DatabaseExplorer(QWidget):
    """Database explorer matching reference layout."""

    zoom_changed = Signal(int)

    def __init__(self, driver: DatabaseDriver, profile, syntax_colors=None, zoom_level=100):
        super().__init__()
        self.driver = driver
        self.profile = profile
        self.accessor = DatabaseAccessor(driver)
        self.current_database = profile.database
        self.procedure_count = 0
        self.syntax_colors = syntax_colors or {}
        self.highlighter = None
        self.zoom_level = zoom_level
        self.lazy_load_enabled = True
        self.loaded_schemas = set()
        self.init_ui()
        self.loading_overlay = LoadingOverlay(self, "Loading schemas...")
        self.loading_overlay.timeout_occurred.connect(self.on_loading_timeout)
        QTimer.singleShot(0, self.load_procedures)

    def init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        self.details_panel = self.create_right_panel()
        splitter.addWidget(self.details_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    def create_left_panel(self) -> QWidget:
        """Create left panel with procedures tree."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        header_layout = QHBoxLayout()
        header_label = QLabel("Routines")
        header_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        self.lazy_load_checkbox = QCheckBox("Lazy Load")
        self.lazy_load_checkbox.setChecked(True)
        self.lazy_load_checkbox.stateChanged.connect(self.on_lazy_load_toggled)
        header_layout.addWidget(self.lazy_load_checkbox)
        layout.addLayout(header_layout)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter routines (Ctrl+K)")
        self.filter_input.textChanged.connect(self.on_filter_changed)
        layout.addWidget(self.filter_input)

        table_search_layout = QHBoxLayout()
        self.schema_selector = QComboBox()
        self.schema_selector.setMaximumWidth(120)
        self.schema_selector.addItem("All Schemas")
        table_search_layout.addWidget(QLabel("Schema:"))
        table_search_layout.addWidget(self.schema_selector)
        table_search_layout.addStretch()
        layout.addLayout(table_search_layout)

        self.table_filter_input = QLineEdit()
        self.table_filter_input.setPlaceholderText("Filter by table name (Press Enter)")
        self.table_filter_input.returnPressed.connect(self.on_table_filter_search)
        layout.addWidget(self.table_filter_input)

        self.tree = RoutineTreeWidget()
        self.tree.setHeaderLabels([""])
        self.tree.header().setStretchLastSection(True)
        self.tree.itemClicked.connect(self.on_item_selected)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.item_enter_pressed.connect(lambda item: self.on_item_selected(item, 0))
        layout.addWidget(self.tree)

        self.expanded_items = set()
        self.table_filter_active = False
        return panel

    def create_right_panel(self) -> QWidget:
        """Create right panel with tabbed details."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        header_layout = QHBoxLayout()
        self.procedure_label = QLabel()
        self.procedure_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        header_layout.addWidget(self.procedure_label)
        header_layout.addStretch()
        export_btn = QPushButton("Export SQL")
        export_btn.setMaximumWidth(140)
        export_btn.clicked.connect(self.on_export_schema)
        header_layout.addWidget(export_btn)
        close_btn = QPushButton("×")
        close_btn.setMaximumWidth(30)
        close_btn.clicked.connect(self.on_close_details)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)

        self.tabs = QTabWidget()

        self.source_text = ZoomableTextEdit()
        self.source_text.setReadOnly(True)
        self.source_text.setFont(self.get_monospace_font())
        self.source_text.set_zoom_callback(self._on_zoom_callback)
        self.highlighter = SqlSyntaxHighlighter(self.source_text.document(), self.syntax_colors)
        self.set_zoom_level(self.zoom_level)
        self.tabs.addTab(self.source_text, "Source")

        self.parameters_widget = ParametersWidget()
        self.tabs.addTab(self.parameters_widget, "Parameters")

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.tabs.addTab(self.details_text, "Details")

        layout.addWidget(self.tabs)
        return panel

    def get_monospace_font(self) -> QFont:
        """Get monospace font for code (cross-platform)."""
        font = QFont()
        font_candidates = [
            "JetBrains Mono",
            "Fira Code",
            "Cascadia Code",
            "Source Code Pro",
            "DejaVu Sans Mono",
            "Liberation Mono",
            "Consolas",
            "Menlo",
            "Monaco",
            "Courier New",
        ]
        font.setStyleStrategy(QFont.PreferAntialias)
        font.setPointSize(12)
        font.setFixedPitch(True)

        for family in font_candidates:
            test_font = QFont(family)
            test_font.setStyleStrategy(QFont.PreferAntialias)
            fm = test_font.family()
            if fm == family or family in fm:
                font = test_font
                font.setPointSize(12)
                font.setFixedPitch(True)
                break

        return font

    def load_procedures(self):
        """Load procedures into tree."""
        self.loading_overlay.start()
        self.loading_overlay.set_message("Loading schemas...")
        try:
            self.tree.clear()
            self.procedure_count = 0
            self.expanded_items.clear()
            self.loaded_schemas.clear()

            schemas = self.accessor.get_schemas(self.current_database)
            total_schemas = len(schemas)

            for idx, schema in enumerate(schemas, 1):
                self.loading_overlay.set_message(f"Loading schema {idx}/{total_schemas}: {schema.name}")

                schema_item = QTreeWidgetItem(self.tree)
                schema_item.setText(0, schema.name)
                schema_item.setIcon(0, self._create_schema_icon())
                schema_item.setData(0, Qt.UserRole, ("schema", schema.database, schema.name))

                if self.lazy_load_enabled:
                    schema_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                    placeholder = QTreeWidgetItem(schema_item)
                    placeholder.setText(0, "Loading...")
                else:
                    self._load_schema_contents(schema_item, schema.name)

            self._populate_schema_selector(schemas)
            self.loading_overlay.set_message("Finalizing...")

        except Exception as e:
            self.source_text.setText(f"Error loading procedures:\n{str(e)}")
        finally:
            self.loading_overlay.stop()

    def _load_schema_contents(self, schema_item: QTreeWidgetItem, schema_name: str):
        """Load procedures and functions for a schema."""
        procedures = self.accessor.get_procedures(self.current_database, schema_name)
        if procedures:
            for proc in procedures:
                proc_item = QTreeWidgetItem(schema_item)
                proc_item.setText(0, proc.name)
                proc_item.setIcon(0, self.get_icon_for_type('PROCEDURE'))
                proc_item.setData(0, Qt.UserRole, ("procedure", self.current_database, schema_name, proc.name))
                proc_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                placeholder = QTreeWidgetItem(proc_item)
                placeholder.setText(0, "Loading...")
                self.procedure_count += 1

        functions = self.accessor.get_functions(self.current_database, schema_name)
        if functions:
            for func in functions:
                func_item = QTreeWidgetItem(schema_item)
                func_item.setText(0, func.name)
                func_item.setIcon(0, self.get_icon_for_type('FUNCTION'))
                func_item.setData(0, Qt.UserRole, ("function", self.current_database, schema_name, func.name))
                func_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                placeholder = QTreeWidgetItem(func_item)
                placeholder.setText(0, "Loading...")
                self.procedure_count += 1

    def _populate_schema_selector(self, schemas):
        """Populate schema selector with schema names."""
        self.schema_selector.blockSignals(True)
        current_count = self.schema_selector.count()
        if current_count > 1:
            for _ in range(current_count - 1):
                self.schema_selector.removeItem(1)
        for schema in schemas:
            self.schema_selector.addItem(schema.name)
        self.schema_selector.blockSignals(False)

    def on_lazy_load_toggled(self, state: int):
        """Handle lazy load checkbox toggled."""
        self.lazy_load_enabled = self.lazy_load_checkbox.isChecked()
        self.table_filter_active = False
        self.load_procedures()

    def on_loading_timeout(self):
        """Handle loading timeout (5 minutes exceeded)."""
        QMessageBox.warning(
            self,
            "Loading Timeout",
            "The loading operation timed out after 5 minutes. Please try again or check your database connection."
        )
        self.source_text.setText("Error: Loading operation timed out after 5 minutes.")

    def on_filter_changed(self, text: str):
        """Filter tree items based on search text."""
        if self.table_filter_active:
            return
        for i in range(self.tree.topLevelItemCount()):
            schema_item = self.tree.topLevelItem(i)
            self.filter_tree_item(schema_item, text.lower())

    def on_table_filter_search(self):
        """Search for objects that use a specific table."""
        table_name = self.table_filter_input.text().strip()
        if not table_name:
            self.table_filter_active = False
            self.load_procedures()
            return

        self.table_filter_active = True
        self.loading_overlay.start()
        self.loading_overlay.set_message(f"Searching for objects using table: {table_name}...")
        try:
            self.tree.clear()
            results = self.accessor.get_objects_by_table(self.current_database, table_name)

            if not results:
                self.source_text.setText(f"No objects found referencing table: {table_name}")
                return

            selected_schema = self.schema_selector.currentText()
            is_filtering_by_schema = selected_schema != "All Schemas"

            schema_groups = {}
            for obj in results:
                schema = obj['schema']
                if is_filtering_by_schema and schema != selected_schema:
                    continue
                if schema not in schema_groups:
                    schema_groups[schema] = []
                schema_groups[schema].append(obj)

            if not schema_groups:
                self.source_text.setText(f"No objects found in schema {selected_schema} referencing table: {table_name}")
                return

            for schema_name in sorted(schema_groups.keys()):
                schema_item = QTreeWidgetItem(self.tree)
                schema_item.setText(0, schema_name)
                schema_item.setIcon(0, self._create_schema_icon())
                schema_item.setData(0, Qt.UserRole, ("schema", self.current_database, schema_name))

                for obj in sorted(schema_groups[schema_name], key=lambda x: x['name']):
                    obj_type = obj['type']
                    obj_item = QTreeWidgetItem(schema_item)
                    obj_item.setText(0, obj['name'])
                    obj_item.setIcon(0, self.get_icon_for_type(obj_type))
                    obj_item.setData(0, Qt.UserRole, (obj_type.lower(), self.current_database, schema_name, obj['name']))
                    obj_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                    placeholder = QTreeWidgetItem(obj_item)
                    placeholder.setText(0, "Loading...")

        except Exception as e:
            self.source_text.setText(f"Error searching table references:\n{str(e)}")
        finally:
            self.loading_overlay.stop()

    def filter_tree_item(self, item: QTreeWidgetItem, text: str) -> bool:
        """Recursively filter tree items."""
        visible = False

        for i in range(item.childCount()):
            child = item.child(i)
            if self.filter_tree_item(child, text):
                visible = True

        if not text or text in item.text(0).lower():
            visible = True

        item.setHidden(not visible)
        return visible

    def on_item_selected(self, item: QTreeWidgetItem, column: int):
        """Handle tree item selection."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data[0]

        if item_type == "procedure":
            _, database, schema, procedure = data
            self.load_procedure_details(database, schema, procedure)

        elif item_type == "function":
            _, database, schema, function = data
            self.load_function_details(database, schema, function)

        elif item_type == "view":
            _, database, schema, view = data
            self.load_view_details(database, schema, view)

        else:
            self.clear_details()

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Expand/collapse on double click."""
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())

    def on_item_expanded(self, item: QTreeWidgetItem):
        """Lazy-load dependencies or schema contents when item expanded."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data[0]

        if item_type == "schema" and self.lazy_load_enabled:
            _, database, schema_name = data
            if schema_name in self.loaded_schemas:
                return
            self.loaded_schemas.add(schema_name)
            item.takeChildren()
            self.loading_overlay.start()
            self.loading_overlay.set_message(f"Loading procedures and functions for {schema_name}...")
            try:
                self._load_schema_contents(item, schema_name)
            except Exception as e:
                print(f"Error loading schema contents for {schema_name}: {str(e)}")
            finally:
                self.loading_overlay.stop()

        elif item_type in ("procedure", "function"):
            item_id = id(item)
            if item_id in self.expanded_items:
                return
            self.expanded_items.add(item_id)
            if len(data) < 4:
                return
            _, database, schema, name = data
            item.takeChildren()
            self.loading_overlay.start()
            self.loading_overlay.set_message(f"Loading dependencies for {schema}.{name}...")
            try:
                called = self.accessor.get_called_procedures(database, schema, name)
                for dep in called:
                    child = QTreeWidgetItem(item)
                    child.setText(0, dep['name'])
                    child.setIcon(0, self.get_icon_for_type(dep['type']))
                    child.setData(0, Qt.UserRole, (dep['type'].lower(), database, dep['schema'], dep['name']))
                    child.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                    QTreeWidgetItem(child)
            except Exception as e:
                print(f"Error loading called procedures for {schema}.{name}: {str(e)}")
            finally:
                self.loading_overlay.stop()

    def get_icon_for_type(self, obj_type: str) -> QIcon:
        """Create icon for object type."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        color = ICON_COLORS.get(obj_type, ICON_COLORS['DEFAULT'])
        pen = QPen(color)
        pen.setWidth(1.5)
        painter.setPen(pen)
        painter.setBrush(color)

        if obj_type == 'SCHEMA':
            painter.drawRect(2, 6, 12, 8)
            painter.drawRect(2, 3, 6, 4)
        elif obj_type == 'TABLE':
            painter.drawRect(2, 3, 12, 10)
            painter.drawLine(2, 7, 14, 7)
            painter.drawLine(5, 3, 5, 13)
            painter.drawLine(8, 3, 8, 13)
            painter.drawLine(11, 3, 11, 13)
        elif obj_type == 'PROCEDURE':
            painter.drawEllipse(2, 5, 5, 6)
            painter.drawEllipse(9, 5, 5, 6)
            painter.drawRect(5, 8, 6, 1)
            painter.drawLine(5, 4, 2, 1)
            painter.drawLine(11, 4, 14, 1)
        elif obj_type == 'FUNCTION':
            font = painter.font()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(2, 2, 12, 12, Qt.AlignCenter, "f(x)")
        elif obj_type == 'VIEW':
            points = [QPoint(3, 10), QPoint(5, 7), QPoint(7, 9), QPoint(10, 5), QPoint(13, 8)]
            painter.drawPolyline(points)
            painter.drawEllipse(8, 11, 2, 2)
        else:
            painter.fillRect(3, 3, 10, 10, color)

        painter.end()
        return QIcon(pixmap)

    def _create_schema_icon(self) -> QIcon:
        """Create schema icon."""
        return self.get_icon_for_type('SCHEMA')

    def load_procedure_details(self, database: str, schema: str, procedure: str):
        """Load procedure details."""
        try:
            self.procedure_label.setText(f"{schema}.{procedure}")

            source = self.accessor.get_procedure_source(database, schema, procedure)
            self.source_text.setText(source or f"No source found for {procedure}")

            # Load parameters
            parameters = self.accessor.get_procedure_parameters(database, schema, procedure)
            self.parameters_widget.load_parameters(database, schema, procedure, parameters)

            self.details_text.setText(f"Schema: {schema}\nType: Stored Procedure\nDatabase: {database}")

            self.tabs.setCurrentIndex(0)

        except Exception as e:
            self.source_text.setText(f"Error loading details:\n{str(e)}")

    def load_function_details(self, database: str, schema: str, function: str):
        """Load function details."""
        try:
            self.procedure_label.setText(f"{schema}.{function}")

            source = self.accessor.get_function_source(database, schema, function)
            self.source_text.setText(source or f"No source found for {function}")

            # Load parameters
            parameters = self.accessor.get_function_parameters(database, schema, function)
            self.parameters_widget.load_parameters(database, schema, function, parameters)

            self.details_text.setText(f"Schema: {schema}\nType: Function\nDatabase: {database}")

            self.tabs.setCurrentIndex(0)

        except Exception as e:
            self.source_text.setText(f"Error loading details:\n{str(e)}")

    def load_view_details(self, database: str, schema: str, view: str):
        """Load view details."""
        try:
            self.procedure_label.setText(f"{schema}.{view}")

            source = self.accessor.get_function_source(database, schema, view)
            self.source_text.setText(source or f"No source found for {view}")

            # Views have no parameters
            self.parameters_widget.load_parameters("", "", "", [])

            self.details_text.setText(f"Schema: {schema}\nType: View\nDatabase: {database}")

            self.tabs.setCurrentIndex(0)

        except Exception as e:
            self.source_text.setText(f"Error loading details:\n{str(e)}")

    def clear_details(self):
        """Clear details panel."""
        self.procedure_label.setText("")
        self.source_text.clear()
        self.parameters_widget.clear()
        self.details_text.clear()

    def on_close_details(self):
        """Close details panel."""
        self.clear_details()
        self.tree.clearSelection()

    def get_procedure_count(self) -> int:
        """Get total procedure count."""
        return self.procedure_count

    def update_theme(self, syntax_colors: dict) -> None:
        """Update syntax highlighting colors."""
        self.syntax_colors = syntax_colors
        if self.highlighter:
            self.highlighter.update_colors(syntax_colors)

    def set_zoom_level(self, level: int) -> None:
        """Set zoom level for code editor (50-200)."""
        level = max(50, min(200, level))
        self.zoom_level = level
        font = self.get_monospace_font()
        font.setPointSize(int(12 * level / 100))
        self.source_text.setFont(font)
        self.zoom_changed.emit(level)

    def get_zoom_level(self) -> int:
        """Get current zoom level."""
        return self.zoom_level

    def zoom_in(self) -> None:
        """Zoom in (increase font size)."""
        self.set_zoom_level(self.zoom_level + 10)

    def zoom_out(self) -> None:
        """Zoom out (decrease font size)."""
        self.set_zoom_level(self.zoom_level - 10)

    def reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        self.set_zoom_level(100)

    def on_export_schema(self) -> None:
        """Handle export schema button click."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Database Schema",
            f"{self.current_database}_schema.sql",
            "SQL Files (*.sql);;All Files (*)"
        )
        if file_path:
            try:
                sql_script = self.export_schema()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(sql_script)
                QMessageBox.information(self, "Export Successful", f"Schema exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error exporting schema:\n{str(e)}")

    def export_schema(self) -> str:
        """Export complete database schema as SQL script."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql_lines = [
            f"-- Database: {self.current_database}",
            f"-- Exported: {timestamp}",
            "",
        ]

        try:
            schemas = self.accessor.get_schemas(self.current_database)
            for schema in schemas:
                sql_lines.append(f"-- ============================================")
                sql_lines.append(f"-- Schema: {schema.name}")
                sql_lines.append(f"-- ============================================")
                sql_lines.append("")

                # Get tables
                try:
                    tables = self.accessor.get_tables(self.current_database, schema.name)
                    if tables:
                        sql_lines.append(f"-- Tables in {schema.name}")
                        for table in tables:
                            try:
                                table_ddl = self._get_table_create_statement(self.current_database, schema.name, table.name)
                                if table_ddl:
                                    sql_lines.append(table_ddl)
                                    sql_lines.append("")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Get procedures
                try:
                    procedures = self.accessor.get_procedures(self.current_database, schema.name)
                    if procedures:
                        sql_lines.append(f"-- Procedures in {schema.name}")
                        for proc in procedures:
                            try:
                                source = self.accessor.get_procedure_source(self.current_database, schema.name, proc.name)
                                if source:
                                    sql_lines.append(source)
                                    sql_lines.append("")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Get functions
                try:
                    functions = self.accessor.get_functions(self.current_database, schema.name)
                    if functions:
                        sql_lines.append(f"-- Functions in {schema.name}")
                        for func in functions:
                            try:
                                source = self.accessor.get_function_source(self.current_database, schema.name, func.name)
                                if source:
                                    sql_lines.append(source)
                                    sql_lines.append("")
                            except Exception:
                                pass
                except Exception:
                    pass

                sql_lines.append("")
        except Exception as e:
            raise RuntimeError(f"Failed to export schema: {str(e)}")

        return "\n".join(sql_lines)

    def _get_table_create_statement(self, database: str, schema: str, table: str) -> Optional[str]:
        """Generate CREATE TABLE statement from SQL Server system views."""
        try:
            conn = self.driver.conn
            cursor = conn.cursor()
            try:
                # Get table object ID
                cursor.execute(f"SELECT OBJECT_ID(N'[{database}].[{schema}].[{table}]')")
                table_id_result = cursor.fetchone()
                if not table_id_result or table_id_result[0] is None:
                    return None

                # Get table columns and their properties
                cursor.execute(f"""
                    SELECT
                        c.name,
                        t.name,
                        c.max_length,
                        c.precision,
                        c.scale,
                        c.is_nullable,
                        c.is_identity,
                        dc.definition,
                        c.column_id
                    FROM [{database}].sys.columns c
                    INNER JOIN [{database}].sys.types t ON c.user_type_id = t.user_type_id
                    LEFT JOIN [{database}].sys.default_constraints dc ON c.default_object_id = dc.object_id
                    WHERE c.object_id = OBJECT_ID(N'[{database}].[{schema}].[{table}]')
                    ORDER BY c.column_id
                """)

                columns = cursor.fetchall()
                if not columns:
                    return None

                # Get primary key constraint
                cursor.execute(f"""
                    SELECT kcu.column_name
                    FROM [{database}].information_schema.table_constraints tc
                    JOIN [{database}].information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_schema = %s
                    AND tc.table_name = %s
                    AND tc.constraint_type = 'PRIMARY KEY'
                """, (schema, table))
                pk_columns = set(row[0] for row in cursor.fetchall())

                sql = f"CREATE TABLE [{schema}].[{table}] (\n"
                col_defs = []

                for col_name, col_type, max_len, precision, scale, nullable, is_identity, default_val, col_id in columns:
                    col_def = f"    [{col_name}] {col_type}"

                    # Add size info for variable-length types
                    if col_type in ('varchar', 'char', 'nvarchar', 'nchar') and max_len and max_len > 0:
                        size = max_len if col_type.startswith('n') is False else max_len // 2
                        col_def += f"({size})" if size != -1 else "(MAX)"
                    elif col_type in ('decimal', 'numeric') and precision:
                        col_def += f"({precision},{scale})"

                    # Add identity
                    if is_identity:
                        col_def += " IDENTITY(1,1)"

                    # Add primary key
                    if col_name in pk_columns:
                        col_def += " PRIMARY KEY"

                    # Add default
                    if default_val:
                        col_def += f" DEFAULT {default_val}"

                    # Add nullable
                    if not nullable:
                        col_def += " NOT NULL"

                    col_defs.append(col_def)

                sql += ",\n".join(col_defs)
                sql += "\n);"

                return sql
            finally:
                cursor.close()
        except Exception:
            return None

    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts for zoom and filter."""
        if event.modifiers() & Qt.ControlModifier:
            if event.key() in (Qt.Key_Plus, Qt.Key_Equal):
                self.zoom_in()
                event.accept()
                return
            elif event.key() == Qt.Key_Minus:
                self.zoom_out()
                event.accept()
                return
            elif event.key() == Qt.Key_0:
                self.reset_zoom()
                event.accept()
                return
            elif event.key() == Qt.Key_K:
                self.filter_input.setFocus()
                self.filter_input.selectAll()
                event.accept()
                return
        super().keyPressEvent(event)

    def _on_zoom_callback(self, action: str) -> None:
        """Handle zoom callback from ZoomableTextEdit."""
        if action == "zoom_in":
            self.zoom_in()
        elif action == "zoom_out":
            self.zoom_out()
