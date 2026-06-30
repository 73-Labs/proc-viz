"""Multi-database accessor using pluggable drivers."""

from typing import List, Dict, Optional
from app.drivers.database_driver import (
    DatabaseDriver,
    Database,
    Schema,
    Procedure,
    Function,
    Table,
    ObjectDependency,
)


class DatabaseAccessor:
    """Database-agnostic accessor. Uses pluggable drivers for different databases."""

    def __init__(self, driver: DatabaseDriver):
        """Initialize with database driver.

        Args:
            driver: DatabaseDriver implementation for target database
        """
        self.driver = driver

    def get_databases(self) -> List[Database]:
        """Get list of accessible databases."""
        return self.driver.get_databases()

    def get_schemas(self, database: str) -> List[Schema]:
        """Get schemas in database."""
        return self.driver.get_schemas(database)

    def get_procedures(self, database: str, schema: str) -> List[Procedure]:
        """Get stored procedures in schema."""
        return self.driver.get_procedures(database, schema)

    def get_functions(self, database: str, schema: str) -> List[Function]:
        """Get functions in schema."""
        return self.driver.get_functions(database, schema)

    def get_tables(self, database: str, schema: str) -> List[Table]:
        """Get tables in schema."""
        return self.driver.get_tables(database, schema)

    def get_procedure_source(self, database: str, schema: str, procedure: str) -> Optional[str]:
        """Get source code for stored procedure."""
        return self.driver.get_procedure_source(database, schema, procedure)

    def get_function_source(self, database: str, schema: str, function: str) -> Optional[str]:
        """Get source code for function."""
        return self.driver.get_function_source(database, schema, function)

    def get_dependencies(self, database: str, schema: str, name: str) -> List[Dict[str, str]]:
        """Get objects that this procedure/function calls."""
        deps = self.driver.get_dependencies(database, schema, name)
        return [{'schema': d.schema, 'name': d.name, 'type': d.type} for d in deps]

    def get_called_procedures(self, database: str, schema: str, name: str) -> List[Dict[str, str]]:
        """Get procedures/functions/views that this object calls (for dependency tree)."""
        deps = self.driver.get_called_procedures(database, schema, name)
        return [{'schema': d.schema, 'name': d.name, 'type': d.type} for d in deps]

    def get_calling_procedures(self, database: str, schema: str, name: str) -> List[Dict[str, str]]:
        """Get procedures/functions that call this object (reverse dependency)."""
        callers = self.driver.get_calling_procedures(database, schema, name)
        return [{'schema': c.schema, 'name': c.name, 'type': c.type} for c in callers]

    def get_objects_by_table(self, database: str, table_name: str) -> List[Dict[str, str]]:
        """Get procedures/functions/views that reference a specific table."""
        results = self.driver.get_objects_by_table(database, table_name)
        return [{'schema': r.schema, 'name': r.name, 'type': r.type} for r in results]

    def close(self) -> None:
        """Close database connection."""
        self.driver.close()
