"""Tree view widget for database explorer."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QTextEdit, QSplitter, QLabel
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
import pymssql
from app.db_accessor import DatabaseAccessor, Procedure, Function


class DatabaseExplorer(QWidget):
    """Database explorer with tree view and source display."""

    def __init__(self, connection: pymssql.Connection, profile):
        super().__init__()
        self.connection = connection
        self.profile = profile
        self.accessor = DatabaseAccessor(connection)
        self.init_ui()
        QTimer.singleShot(0, self.load_databases)

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"Database: {self.profile.server}/{self.profile.database}"))
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Splitter: tree + source
        splitter = QSplitter(Qt.Horizontal)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Objects")
        self.tree.itemClicked.connect(self.on_item_selected)
        splitter.addWidget(self.tree)

        self.source_text = QTextEdit()
        self.source_text.setReadOnly(True)
        splitter.addWidget(self.source_text)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        self.setLayout(layout)

    def load_databases(self):
        """Load databases and populate tree."""
        try:
            databases = self.accessor.get_databases()
            for db in databases:
                db_item = QTreeWidgetItem(self.tree)
                db_item.setText(0, f"📁 {db.name}")
                db_item.setData(0, Qt.UserRole, ("database", db.name))

                # Lazy load schemas
                self.load_schemas(db_item, db.name)

        except Exception as e:
            self.source_text.setText(f"Error loading databases:\n{str(e)}")

    def load_schemas(self, db_item: QTreeWidgetItem, database: str):
        """Load schemas for database."""
        try:
            schemas = self.accessor.get_schemas(database)
            for schema in schemas:
                schema_item = QTreeWidgetItem(db_item)
                schema_item.setText(0, f"📋 {schema.name}")
                schema_item.setData(0, Qt.UserRole, ("schema", database, schema.name))

                # Procedures
                self.load_procedures(schema_item, database, schema.name)

                # Functions
                self.load_functions(schema_item, database, schema.name)

                # Tables
                self.load_tables(schema_item, database, schema.name)

        except Exception as e:
            error_item = QTreeWidgetItem(db_item)
            error_item.setText(0, f"Error: {str(e)}")

    def load_procedures(self, schema_item: QTreeWidgetItem, database: str, schema: str):
        """Load procedures for schema."""
        try:
            procedures = self.accessor.get_procedures(database, schema)
            if procedures:
                procs_item = QTreeWidgetItem(schema_item)
                procs_item.setText(0, f"⚙️  Procedures")
                procs_item.setData(0, Qt.UserRole, ("procedures_folder", database, schema))

                for proc in procedures:
                    proc_item = QTreeWidgetItem(procs_item)
                    proc_item.setText(0, f"🔧 {proc.name}")
                    proc_item.setData(0, Qt.UserRole, ("procedure", database, schema, proc.name))
        except Exception as e:
            error_item = QTreeWidgetItem(schema_item)
            error_item.setText(0, f"Error loading procedures: {str(e)}")

    def load_functions(self, schema_item: QTreeWidgetItem, database: str, schema: str):
        """Load functions for schema."""
        try:
            functions = self.accessor.get_functions(database, schema)
            if functions:
                funcs_item = QTreeWidgetItem(schema_item)
                funcs_item.setText(0, f"📐 Functions")
                funcs_item.setData(0, Qt.UserRole, ("functions_folder", database, schema))

                for func in functions:
                    func_item = QTreeWidgetItem(funcs_item)
                    func_item.setText(0, f"𝑓 {func.name}")
                    func_item.setData(0, Qt.UserRole, ("function", database, schema, func.name))
        except Exception as e:
            error_item = QTreeWidgetItem(schema_item)
            error_item.setText(0, f"Error loading functions: {str(e)}")

    def load_tables(self, schema_item: QTreeWidgetItem, database: str, schema: str):
        """Load tables for schema."""
        try:
            tables = self.accessor.get_tables(database, schema)
            if tables:
                tables_item = QTreeWidgetItem(schema_item)
                tables_item.setText(0, f"📊 Tables")
                tables_item.setData(0, Qt.UserRole, ("tables_folder", database, schema))

                for table in tables:
                    table_item = QTreeWidgetItem(tables_item)
                    table_item.setText(0, f"📑 {table.name}")
                    table_item.setData(0, Qt.UserRole, ("table", database, schema, table.name))
        except Exception as e:
            error_item = QTreeWidgetItem(schema_item)
            error_item.setText(0, f"Error loading tables: {str(e)}")

    def on_item_selected(self, item: QTreeWidgetItem, column: int):
        """Handle tree item selection."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data[0]

        if item_type == "procedure":
            _, database, schema, procedure = data
            try:
                source = self.accessor.get_procedure_source(database, schema, procedure)
                if source:
                    self.source_text.setText(source)
                else:
                    self.source_text.setText(f"No source found for {procedure}")
            except Exception as e:
                self.source_text.setText(f"Error loading source:\n{str(e)}")

        elif item_type == "function":
            _, database, schema, function = data
            try:
                source = self.accessor.get_function_source(database, schema, function)
                if source:
                    self.source_text.setText(source)
                else:
                    self.source_text.setText(f"No source found for {function}")
            except Exception as e:
                self.source_text.setText(f"Error loading source:\n{str(e)}")

        else:
            self.source_text.clear()
