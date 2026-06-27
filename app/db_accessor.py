"""Query SQL Server system tables for schema objects."""

import pymssql
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Database:
    name: str


@dataclass
class Schema:
    name: str
    database: str


@dataclass
class Procedure:
    name: str
    schema: str
    database: str
    type: str = "PROCEDURE"


@dataclass
class Function:
    name: str
    schema: str
    database: str
    type: str = "FUNCTION"


@dataclass
class Table:
    name: str
    schema: str
    database: str
    type: str = "TABLE"


class DatabaseAccessor:
    """Access SQL Server database structure and object definitions."""

    def __init__(self, conn: pymssql.Connection):
        self.conn = conn

    def get_databases(self) -> List[Database]:
        """Get list of accessible databases."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT name FROM sys.databases
                WHERE database_id > 4
                ORDER BY name
            """)
            return [Database(name=row[0]) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def get_schemas(self, database: str) -> List[Schema]:
        """Get schemas in database."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT name FROM [{database}].sys.schemas
                ORDER BY name
            """)
            return [Schema(name=row[0], database=database) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def get_procedures(self, database: str, schema: str) -> List[Procedure]:
        """Get stored procedures in schema."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT name FROM [{database}].sys.procedures
                WHERE schema_id = (
                    SELECT schema_id FROM [{database}].sys.schemas
                    WHERE name = %s
                )
                ORDER BY name
            """, (schema,))
            return [Procedure(name=row[0], schema=schema, database=database) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def get_functions(self, database: str, schema: str) -> List[Function]:
        """Get functions in schema."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT name FROM [{database}].sys.objects
                WHERE type IN ('IF', 'FN', 'TF')
                AND schema_id = (
                    SELECT schema_id FROM [{database}].sys.schemas
                    WHERE name = %s
                )
                ORDER BY name
            """, (schema,))
            return [Function(name=row[0], schema=schema, database=database) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def get_tables(self, database: str, schema: str) -> List[Table]:
        """Get tables in schema."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT name FROM [{database}].sys.tables
                WHERE schema_id = (
                    SELECT schema_id FROM [{database}].sys.schemas
                    WHERE name = %s
                )
                ORDER BY name
            """, (schema,))
            return [Table(name=row[0], schema=schema, database=database) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def get_procedure_source(self, database: str, schema: str, procedure: str) -> Optional[str]:
        """Get source code for stored procedure."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT definition FROM [{database}].sys.sql_modules
                WHERE object_id = OBJECT_ID(N'[{database}].[{schema}].[{procedure}]')
            """)
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()

    def get_function_source(self, database: str, schema: str, function: str) -> Optional[str]:
        """Get source code for function."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT definition FROM [{database}].sys.sql_modules
                WHERE object_id = OBJECT_ID(N'[{database}].[{schema}].[{function}]')
            """)
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()

    def get_dependencies(self, database: str, schema: str, name: str) -> List[Dict[str, str]]:
        """Get objects that this procedure/function calls."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT DISTINCT
                    referenced_schema_name,
                    referenced_entity_name,
                    referenced_class_desc
                FROM [{database}].sys.sql_expression_dependencies
                WHERE referencing_id = OBJECT_ID(N'[{database}].[{schema}].[{name}]')
                ORDER BY referenced_schema_name, referenced_entity_name
            """)
            deps = []
            for row in cursor.fetchall():
                deps.append({
                    'schema': row[0],
                    'name': row[1],
                    'type': row[2]
                })
            return deps
        finally:
            cursor.close()
