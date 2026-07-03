"""Database explorer with proper UI layout matching reference."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QTabWidget, QTextEdit,
    QSplitter, QPushButton, QLabel
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QKeySequence
from PySide6.QtWidgets import QApplication
from app.db_accessor import DatabaseAccessor
from app.drivers.database_driver import DatabaseDriver
from app.widgets.sql_highlighter import SqlSyntaxHighlighter
from app.widgets.zoomable_text_edit import ZoomableTextEdit
from app.widgets.loading_spinner import LoadingOverlay
from app.widgets.parameters_widget import ParametersWidget


ICON_MAP = {
    'OBJECT_OR_COLUMN': '📦',
    'OBJECT_OR_TYPE': '📦',
    'TYPE': '📋',
    'SCHEMA': '📂',
    'TABLE': '📊',
    'PROCEDURE': '🔧',
    'FUNCTION': '𝑓',
}


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
        self.init_ui()
        self.loading_overlay = LoadingOverlay(self, "Loading schemas...")
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
        layout.addLayout(header_layout)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter routines (Ctrl+K)")
        self.filter_input.textChanged.connect(self.on_filter_changed)
        layout.addWidget(self.filter_input)

        self.table_filter_input = QLineEdit()
        self.table_filter_input.setPlaceholderText("Filter by table name (Press Enter)")
        self.table_filter_input.returnPressed.connect(self.on_table_filter_search)
        layout.addWidget(self.table_filter_input)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([""])
        self.tree.header().setStretchLastSection(True)
        self.tree.itemClicked.connect(self.on_item_selected)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.itemExpanded.connect(self.on_item_expanded)
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

            schemas = self.accessor.get_schemas(self.current_database)
            total_schemas = len(schemas)

            for idx, schema in enumerate(schemas, 1):
                self.loading_overlay.set_message(f"Loading schema {idx}/{total_schemas}: {schema.name}")

                schema_item = QTreeWidgetItem(self.tree)
                schema_item.setText(0, f"📋 {schema.name}")
                schema_item.setData(0, Qt.UserRole, ("schema", schema.database, schema.name))

                procedures = self.accessor.get_procedures(self.current_database, schema.name)
                if procedures:
                    for proc in procedures:
                        proc_item = QTreeWidgetItem(schema_item)
                        proc_item.setText(0, f"🔧 {proc.name}")
                        proc_item.setData(0, Qt.UserRole, ("procedure", self.current_database, schema.name, proc.name))
                        proc_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                        placeholder = QTreeWidgetItem(proc_item)
                        placeholder.setText(0, "Loading...")
                        self.procedure_count += 1

                functions = self.accessor.get_functions(self.current_database, schema.name)
                if functions:
                    for func in functions:
                        func_item = QTreeWidgetItem(schema_item)
                        func_item.setText(0, f"𝑓 {func.name}")
                        func_item.setData(0, Qt.UserRole, ("function", self.current_database, schema.name, func.name))
                        func_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                        placeholder = QTreeWidgetItem(func_item)
                        placeholder.setText(0, "Loading...")
                        self.procedure_count += 1

            self.loading_overlay.set_message("Finalizing...")

        except Exception as e:
            self.source_text.setText(f"Error loading procedures:\n{str(e)}")
        finally:
            self.loading_overlay.stop()

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

            schema_groups = {}
            for obj in results:
                schema = obj['schema']
                if schema not in schema_groups:
                    schema_groups[schema] = []
                schema_groups[schema].append(obj)

            for schema_name in sorted(schema_groups.keys()):
                schema_item = QTreeWidgetItem(self.tree)
                schema_item.setText(0, f"📋 {schema_name}")
                schema_item.setData(0, Qt.UserRole, ("schema", self.current_database, schema_name))

                for obj in sorted(schema_groups[schema_name], key=lambda x: x['name']):
                    obj_type = obj['type']
                    icon = self.get_icon_for_type(obj_type)
                    obj_item = QTreeWidgetItem(schema_item)
                    obj_item.setText(0, f"{icon} {obj['name']}")
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
        """Lazy-load dependencies when procedure/function item expanded."""
        data = item.data(0, Qt.UserRole)
        if not data or len(data) < 4:
            return

        item_type = data[0]
        if item_type not in ("procedure", "function"):
            return

        item_id = id(item)
        if item_id in self.expanded_items:
            return

        self.expanded_items.add(item_id)

        _, database, schema, name = data

        item.takeChildren()

        self.loading_overlay.start()
        self.loading_overlay.set_message(f"Loading dependencies for {schema}.{name}...")
        try:
            called = self.accessor.get_called_procedures(database, schema, name)
            for dep in called:
                child = QTreeWidgetItem(item)
                icon = self.get_icon_for_type(dep['type'])
                child.setText(0, f"{icon} {dep['name']}")
                child.setData(0, Qt.UserRole, (dep['type'].lower(), database, dep['schema'], dep['name']))
                child.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                QTreeWidgetItem(child)
        except Exception as e:
            print(f"Error loading called procedures for {schema}.{name}: {str(e)}")
        finally:
            self.loading_overlay.stop()

    def get_icon_for_type(self, obj_type: str) -> str:
        """Get icon for object type."""
        icon_map = {
            'PROCEDURE': '🔧',
            'FUNCTION': '𝑓',
            'VIEW': '📊',
        }
        return icon_map.get(obj_type, '📦')

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

    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts for zoom."""
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
        super().keyPressEvent(event)

    def _on_zoom_callback(self, action: str) -> None:
        """Handle zoom callback from ZoomableTextEdit."""
        if action == "zoom_in":
            self.zoom_in()
        elif action == "zoom_out":
            self.zoom_out()
