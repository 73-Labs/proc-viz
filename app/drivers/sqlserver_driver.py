"""SQL Server database driver implementation."""

import pymssql
import re
from typing import List, Optional
from app.drivers.database_driver import (
    DatabaseDriver,
    Database,
    Schema,
    Procedure,
    Function,
    Table,
    ObjectDependency,
)


class SQLServerDriver(DatabaseDriver):
    """SQL Server driver using pymssql connection."""

    def __init__(self, connection: pymssql.Connection):
        self.conn = connection

    def get_databases(self) -> List[Database]:
        """Get list of accessible databases, excluding system databases."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT name FROM sys.databases
                WHERE database_id > 4
                ORDER BY name
            """)
            return [Database(name=row[0], schema="", database=row[0]) for row in cursor.fetchall()]
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
            return [Schema(name=row[0], schema=row[0], database=database) for row in cursor.fetchall()]
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

    def get_dependencies(self, database: str, schema: str, name: str) -> List[ObjectDependency]:
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
                deps.append(ObjectDependency(
                    schema=row[0],
                    name=row[1],
                    type=row[2]
                ))
            return deps
        finally:
            cursor.close()

    def get_called_procedures(self, database: str, schema: str, name: str) -> List[ObjectDependency]:
        """Get procedures/functions/views that this object calls (for dependency tree)."""
        cursor = self.conn.cursor()
        try:
            # Use sys.sql_expression_dependencies for static references
            cursor.execute(f"""
                SELECT DISTINCT
                    sed.referenced_schema_name,
                    sed.referenced_entity_name,
                    CASE
                        WHEN o.type = 'P' THEN 'PROCEDURE'
                        WHEN o.type IN ('FN', 'IF', 'TF') THEN 'FUNCTION'
                        WHEN o.type = 'V' THEN 'VIEW'
                    END as obj_type
                FROM [{database}].sys.sql_expression_dependencies sed
                INNER JOIN [{database}].sys.objects ref_obj ON
                    ref_obj.object_id = sed.referencing_id
                INNER JOIN [{database}].sys.schemas ref_schema ON
                    ref_schema.schema_id = ref_obj.schema_id
                INNER JOIN [{database}].sys.objects o ON
                    o.name = sed.referenced_entity_name
                INNER JOIN [{database}].sys.schemas o_schema ON
                    o_schema.schema_id = o.schema_id
                    AND o_schema.name = sed.referenced_schema_name
                WHERE ref_obj.name = %s
                AND ref_schema.name = %s
                AND o.type IN ('P', 'FN', 'IF', 'TF', 'V')
                ORDER BY sed.referenced_schema_name, sed.referenced_entity_name
            """, (name, schema))

            deps = {}
            for row in cursor.fetchall():
                schema_name = row[0].strip() if row[0] else None
                obj_name = row[1].strip() if row[1] else None
                obj_type = row[2].strip() if row[2] else None

                if schema_name and obj_name and obj_type:
                    key = (schema_name, obj_name)
                    deps[key] = ObjectDependency(schema=schema_name, name=obj_name, type=obj_type)

            # Parse source for explicit EXEC calls (catches dynamic SQL)
            source = self.get_procedure_source(database, schema, name)
            if not source:
                source = self.get_function_source(database, schema, name)

            if source:
                exec_calls = self._parse_exec_calls(database, source)
                for schema_name, obj_name, obj_type in exec_calls:
                    key = (schema_name, obj_name)
                    if key not in deps:
                        deps[key] = ObjectDependency(schema=schema_name, name=obj_name, type=obj_type)

            return list(deps.values())
        finally:
            cursor.close()

    def get_calling_procedures(self, database: str, schema: str, name: str) -> List[ObjectDependency]:
        """Get procedures/functions that call this object (reverse dependency)."""
        cursor = self.conn.cursor()
        try:
            # Find referenced object ID first
            cursor.execute(f"""
                SELECT object_id FROM [{database}].sys.objects
                WHERE name = %s
                AND schema_id = (
                    SELECT schema_id FROM [{database}].sys.schemas
                    WHERE name = %s
                )
            """, (name, schema))
            result = cursor.fetchone()
            if not result:
                return []

            obj_id = result[0]

            cursor.execute(f"""
                SELECT DISTINCT
                    ref_schema.name as referencing_schema,
                    ref_obj.name as referencing_name,
                    CASE
                        WHEN ref_obj.type = 'P' THEN 'PROCEDURE'
                        WHEN ref_obj.type IN ('FN', 'IF', 'TF') THEN 'FUNCTION'
                        WHEN ref_obj.type = 'V' THEN 'VIEW'
                    END as obj_type
                FROM [{database}].sys.sql_expression_dependencies sed
                INNER JOIN [{database}].sys.objects ref_obj ON
                    ref_obj.object_id = sed.referencing_id
                INNER JOIN [{database}].sys.schemas ref_schema ON
                    ref_schema.schema_id = ref_obj.schema_id
                WHERE sed.referenced_id = %s
                AND ref_obj.type IN ('P', 'FN', 'IF', 'TF')
                ORDER BY ref_schema.name, ref_obj.name
            """, (obj_id,))

            callers = []
            for row in cursor.fetchall():
                schema_name = row[0].strip() if row[0] else None
                obj_name = row[1].strip() if row[1] else None
                obj_type = row[2].strip() if row[2] else None

                if schema_name and obj_name and obj_type:
                    callers.append(ObjectDependency(
                        schema=schema_name,
                        name=obj_name,
                        type=obj_type
                    ))

            return callers
        finally:
            cursor.close()

    def _parse_exec_calls(self, database: str, source: str) -> list:
        """Parse procedure source for EXEC calls. Returns list of (schema, name, type)."""
        calls = []

        if not source:
            return calls

        pattern = r'\bEXEC(?:UTE)?\s+([^\s\(]+)'

        cursor = self.conn.cursor()
        try:
            for match in re.finditer(pattern, source, re.IGNORECASE):
                proc_ref = match.group(1).strip('[]')

                if '.' in proc_ref:
                    parts = proc_ref.split('.')
                    proc_schema = parts[0].strip('[]')
                    proc_name = parts[1].strip('[]')
                else:
                    proc_schema = 'dbo'
                    proc_name = proc_ref

                cursor.execute(f"""
                    SELECT type FROM [{database}].sys.objects
                    WHERE name = %s
                    AND schema_id = (
                        SELECT schema_id FROM [{database}].sys.schemas
                        WHERE name = %s
                    )
                """, (proc_name, proc_schema))

                result = cursor.fetchone()
                if result:
                    obj_type_code = result[0].strip() if result[0] else None
                    if obj_type_code == 'P':
                        obj_type = 'PROCEDURE'
                    elif obj_type_code in ('FN', 'IF', 'TF'):
                        obj_type = 'FUNCTION'
                    else:
                        continue

                    calls.append((proc_schema, proc_name, obj_type))
        finally:
            cursor.close()

        return calls

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
