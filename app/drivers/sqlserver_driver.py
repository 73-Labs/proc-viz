"""SQL Server database driver implementation."""

import pymssql
import re
import time
from typing import List, Optional, Dict, Any
from app.drivers.database_driver import (
    DatabaseDriver,
    Database,
    Schema,
    Procedure,
    Function,
    Table,
    ObjectDependency,
    Parameter,
    ExecutionRequest,
    ExecutionResult,
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

    def get_objects_by_table(self, database: str, table_name: str) -> List[ObjectDependency]:
        """Get procedures/functions/views that reference a specific table."""
        cursor = self.conn.cursor()
        try:
            search_pattern = f"%{table_name}%"
            cursor.execute(f"""
                SELECT DISTINCT
                    SCHEMA_NAME(o.schema_id) AS schema_name,
                    o.name AS object_name,
                    CASE
                        WHEN o.type = 'P' THEN 'PROCEDURE'
                        WHEN o.type IN ('FN', 'IF', 'TF') THEN 'FUNCTION'
                        WHEN o.type = 'V' THEN 'VIEW'
                    END as obj_type
                FROM [{database}].sys.sql_modules m
                JOIN [{database}].sys.objects o ON m.object_id = o.object_id
                WHERE o.type IN ('P', 'FN', 'IF', 'TF', 'V')
                  AND m.definition LIKE %s
                ORDER BY SCHEMA_NAME(o.schema_id), o.name
            """, (search_pattern,))

            results = []
            for row in cursor.fetchall():
                schema_name = row[0].strip() if row[0] else None
                obj_name = row[1].strip() if row[1] else None
                obj_type = row[2].strip() if row[2] else None

                if schema_name and obj_name and obj_type:
                    results.append(ObjectDependency(
                        schema=schema_name,
                        name=obj_name,
                        type=obj_type
                    ))

            return results
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

    def get_procedure_parameters(self, database: str, schema: str, procedure: str) -> list:
        """Get parameters for stored procedure."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT
                    p.name,
                    CASE
                        WHEN p.is_output = 1 AND p.is_readonly = 0 THEN 'INOUT'
                        WHEN p.is_output = 1 THEN 'OUT'
                        ELSE 'IN'
                    END as direction,
                    TYPE_NAME(p.user_type_id) as data_type,
                    p.max_length,
                    p.precision,
                    p.scale,
                    p.is_readonly,
                    p.has_default_value,
                    ISNULL(p.default_value, ''),
                    p.parameter_id
                FROM [{database}].sys.parameters p
                WHERE p.object_id = OBJECT_ID(N'[{database}].[{schema}].[{procedure}]')
                AND p.parameter_id > 0
                ORDER BY p.parameter_id
            """)

            params = []
            for row in cursor.fetchall():
                param = Parameter(
                    name=row[0],
                    direction=row[1],
                    data_type=row[2],
                    max_length=row[3] if row[3] and row[3] > 0 else None,
                    precision=row[4] if row[4] else None,
                    scale=row[5] if row[5] else None,
                    is_readonly=bool(row[6]),
                    has_default=bool(row[7]),
                    default_value=row[8] if row[8] else None,
                    ordinal_position=row[9]
                )
                params.append(param)

            return params
        finally:
            cursor.close()

    def get_function_parameters(self, database: str, schema: str, function: str) -> list:
        """Get parameters for function."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"""
                SELECT
                    p.name,
                    CASE
                        WHEN p.is_output = 1 AND p.is_readonly = 0 THEN 'INOUT'
                        WHEN p.is_output = 1 THEN 'OUT'
                        WHEN p.parameter_id = 0 THEN 'RETURN'
                        ELSE 'IN'
                    END as direction,
                    TYPE_NAME(p.user_type_id) as data_type,
                    p.max_length,
                    p.precision,
                    p.scale,
                    p.is_readonly,
                    p.has_default_value,
                    ISNULL(p.default_value, ''),
                    p.parameter_id
                FROM [{database}].sys.parameters p
                WHERE p.object_id = OBJECT_ID(N'[{database}].[{schema}].[{function}]')
                ORDER BY p.parameter_id
            """)

            params = []
            for row in cursor.fetchall():
                param = Parameter(
                    name=row[0],
                    direction=row[1],
                    data_type=row[2],
                    max_length=row[3] if row[3] and row[3] > 0 else None,
                    precision=row[4] if row[4] else None,
                    scale=row[5] if row[5] else None,
                    is_readonly=bool(row[6]),
                    has_default=bool(row[7]),
                    default_value=row[8] if row[8] else None,
                    ordinal_position=row[9]
                )
                params.append(param)

            return params
        finally:
            cursor.close()

    def execute_procedure(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute a stored procedure or function with given parameters."""
        start_time = time.time()
        cursor = self.conn.cursor()
        try:
            # Check for cancellation before starting
            if request.cancel_flag and request.cancel_flag.is_set():
                return ExecutionResult(
                    success=False,
                    error_message="Execution cancelled"
                )

            # Select database
            cursor.execute(f"USE [{request.database}]")

            # Get parameter metadata
            if request.object_type == "PROCEDURE":
                params = self.get_procedure_parameters(request.database, request.schema, request.routine_name)
            else:
                params = self.get_function_parameters(request.database, request.schema, request.routine_name)

            # Build parameter list for EXEC statement
            param_list = []
            param_values = []
            output_param_names = []

            for param in params:
                if request.cancel_flag and request.cancel_flag.is_set():
                    return ExecutionResult(
                        success=False,
                        error_message="Execution cancelled"
                    )

                param_name = param.name
                if not param_name.startswith("@"):
                    param_name = "@" + param_name

                if param.direction in ("IN", "INOUT"):
                    # Input parameter
                    if param.name in request.parameters:
                        value = request.parameters[param.name]
                        param_list.append(f"{param_name}=%s")
                        param_values.append(value)
                    elif param.has_default:
                        # Skip parameters with defaults if not provided
                        continue
                    else:
                        return ExecutionResult(
                            success=False,
                            error_message=f"Required parameter '{param.name}' not provided"
                        )

                if param.direction in ("OUT", "INOUT"):
                    # Output parameter
                    output_param_names.append(param_name)
                    if param.direction == "OUT":
                        # OUT parameters need to be initialized, but not passed a value
                        param_list.append(f"{param_name}=NULL OUTPUT")
                    else:
                        # INOUT parameters use the input value if provided
                        if param.name in request.parameters:
                            value = request.parameters[param.name]
                            param_list.append(f"{param_name}=%s OUTPUT")
                            param_values.append(value)
                        elif param.has_default:
                            param_list.append(f"{param_name}=NULL OUTPUT")
                        else:
                            return ExecutionResult(
                                success=False,
                                error_message=f"Required parameter '{param.name}' not provided"
                            )

            # Build EXEC statement
            qualified_name = f"[{request.schema}].[{request.routine_name}]"
            if param_list:
                exec_stmt = f"EXEC {qualified_name} {', '.join(param_list)}"
            else:
                exec_stmt = f"EXEC {qualified_name}"

            # Execute the procedure
            cursor.execute(exec_stmt, tuple(param_values))

            # Capture result sets and affected rows
            result_sets = []
            total_affected_rows = 0

            # Process all result sets
            # Note: need to iterate through all result sets even if first is empty
            for iteration in range(100):  # Safety limit to prevent infinite loops
                if request.cancel_flag and request.cancel_flag.is_set():
                    return ExecutionResult(
                        success=False,
                        error_message="Execution cancelled"
                    )

                # Try to fetch rows from current result set
                try:
                    rows = cursor.fetchall()
                    if rows:
                        # Got rows - convert to list of dicts if we have column info
                        if cursor.description:
                            col_names = [desc[0] for desc in cursor.description]
                            result_set = [dict(zip(col_names, row)) for row in rows]
                        else:
                            # No column info, convert to list as dicts with generic keys
                            result_set = [{f"col_{i}": v for i, v in enumerate(row)}
                                        if isinstance(row, (list, tuple)) else {"col": row}
                                        for row in rows]
                        result_sets.append(result_set)
                        total_affected_rows = len(rows)
                except Exception:
                    # fetchall() failed or no result set
                    pass

                # Check rowcount for affected rows (INSERT/UPDATE/DELETE)
                if not result_sets and cursor.rowcount and cursor.rowcount > 0:
                    total_affected_rows = cursor.rowcount

                # Move to next result set - if False, no more result sets
                if not cursor.nextset():
                    break

            # Capture output parameters
            # Note: pymssql doesn't easily expose output parameters after execution
            # For now, output parameters are not captured
            output_parameters = {}

            duration_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=True,
                result_sets=result_sets,
                output_parameters=output_parameters,
                affected_rows=total_affected_rows,
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            # Try to extract meaningful error from pymssql
            error_details = None
            if "ProgrammingError" in str(type(e)):
                error_details = error_msg
                # Extract first line for main message
                error_msg = error_msg.split('\n')[0] if '\n' in error_msg else error_msg

            # Add debug info for execution errors
            if not error_details and error_msg:
                error_details = f"Exception type: {type(e).__name__}\nFull error: {str(e)}"

            return ExecutionResult(
                success=False,
                error_message=error_msg,
                error_details=error_details,
                duration_ms=duration_ms
            )
        finally:
            cursor.close()

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
