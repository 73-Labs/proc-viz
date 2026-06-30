"""Abstract database driver interface for extensible multi-database support."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class SchemaObject:
    """Base class for schema objects."""
    name: str
    schema: str
    database: str


@dataclass
class Database(SchemaObject):
    """Database container."""
    type: str = "DATABASE"


@dataclass
class Schema(SchemaObject):
    """Schema container."""
    type: str = "SCHEMA"


@dataclass
class Procedure(SchemaObject):
    """Stored procedure or equivalent."""
    type: str = "PROCEDURE"


@dataclass
class Function(SchemaObject):
    """Function or equivalent."""
    type: str = "FUNCTION"


@dataclass
class Table(SchemaObject):
    """Table object."""
    type: str = "TABLE"


@dataclass
class ObjectDependency:
    """Dependency between objects."""
    schema: str
    name: str
    type: str


class DatabaseDriver(ABC):
    """Abstract database driver interface. Implement for each target database."""

    @abstractmethod
    def get_databases(self) -> List[Database]:
        """Get list of accessible databases."""
        pass

    @abstractmethod
    def get_schemas(self, database: str) -> List[Schema]:
        """Get schemas in database."""
        pass

    @abstractmethod
    def get_procedures(self, database: str, schema: str) -> List[Procedure]:
        """Get stored procedures in schema."""
        pass

    @abstractmethod
    def get_functions(self, database: str, schema: str) -> List[Function]:
        """Get functions in schema."""
        pass

    @abstractmethod
    def get_tables(self, database: str, schema: str) -> List[Table]:
        """Get tables in schema."""
        pass

    @abstractmethod
    def get_procedure_source(self, database: str, schema: str, procedure: str) -> Optional[str]:
        """Get source code for stored procedure."""
        pass

    @abstractmethod
    def get_function_source(self, database: str, schema: str, function: str) -> Optional[str]:
        """Get source code for function."""
        pass

    @abstractmethod
    def get_dependencies(self, database: str, schema: str, name: str) -> List[ObjectDependency]:
        """Get objects that this procedure/function calls."""
        pass

    @abstractmethod
    def get_called_procedures(self, database: str, schema: str, name: str) -> List[ObjectDependency]:
        """Get procedures/functions/views that this object calls (for dependency tree)."""
        pass

    @abstractmethod
    def get_calling_procedures(self, database: str, schema: str, name: str) -> List[ObjectDependency]:
        """Get procedures/functions that call this object (reverse dependency)."""
        pass

    @abstractmethod
    def get_objects_by_table(self, database: str, table_name: str) -> List[ObjectDependency]:
        """Get procedures/functions/views that reference a specific table."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass
