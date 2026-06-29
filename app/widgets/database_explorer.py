"""Database explorer with proper UI layout matching reference."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QTabWidget, QTextEdit,
    QSplitter, QPushButton, QLabel
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from app.db_accessor import DatabaseAccessor
from app.drivers.database_driver import DatabaseDriver
from app.widgets.sql_highlighter import SqlSyntaxHighlighter


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

    def __init__(self, driver: DatabaseDriver, profile):
        super().__init__()
        self.driver = driver
        self.profile = profile
        self.accessor = DatabaseAccessor(driver)
        self.current_database = profile.database
        self.procedure_count = 0
        self.init_ui()
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
        header_label = QLabel("Procedures")
        header_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter procedures (Ctrl+K)")
        self.filter_input.textChanged.connect(self.on_filter_changed)
        layout.addWidget(self.filter_input)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([""])
        self.tree.header().setStretchLastSection(True)
        self.tree.itemClicked.connect(self.on_item_selected)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.itemExpanded.connect(self.on_item_expanded)
        layout.addWidget(self.tree)

        self.expanded_items = set()
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

        self.source_text = QTextEdit()
        self.source_text.setReadOnly(True)
        self.source_text.setFont(self.get_monospace_font())
        SqlSyntaxHighlighter(self.source_text.document())
        self.tabs.addTab(self.source_text, "Source")

        self.parameters_text = QTextEdit()
        self.parameters_text.setReadOnly(True)
        self.tabs.addTab(self.parameters_text, "Parameters")

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.tabs.addTab(self.details_text, "Details")

        layout.addWidget(self.tabs)
        return panel

    def get_monospace_font(self) -> QFont:
        """Get monospace font for code."""
        font = QFont("Courier")
        font.setPointSize(9)
        return font

    def load_procedures(self):
        """Load procedures into tree."""
        try:
            self.tree.clear()
            self.procedure_count = 0
            self.expanded_items.clear()

            schemas = self.accessor.get_schemas(self.current_database)

            for schema in schemas:
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

            self.tree.expandAll()

        except Exception as e:
            self.source_text.setText(f"Error loading procedures:\n{str(e)}")

    def on_filter_changed(self, text: str):
        """Filter tree items based on search text."""
        for i in range(self.tree.topLevelItemCount()):
            schema_item = self.tree.topLevelItem(i)
            self.filter_tree_item(schema_item, text.lower())

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

            self.parameters_text.setText(f"Parameters for {schema}.{procedure}\n\n(To be implemented)")
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

            self.parameters_text.setText(f"Parameters for {schema}.{function}\n\n(To be implemented)")
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

            self.parameters_text.setText(f"View: {schema}.{view}")
            self.details_text.setText(f"Schema: {schema}\nType: View\nDatabase: {database}")

            self.tabs.setCurrentIndex(0)

        except Exception as e:
            self.source_text.setText(f"Error loading details:\n{str(e)}")

    def clear_details(self):
        """Clear details panel."""
        self.procedure_label.setText("")
        self.source_text.clear()
        self.parameters_text.clear()
        self.details_text.clear()

    def on_close_details(self):
        """Close details panel."""
        self.clear_details()
        self.tree.clearSelection()

    def get_procedure_count(self) -> int:
        """Get total procedure count."""
        return self.procedure_count

