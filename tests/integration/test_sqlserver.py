"""End-to-end coverage for SQLServerDriver against init-db.sql."""

import os

import pytest

from app.db_accessor import DatabaseAccessor


pytestmark = pytest.mark.integration
DATABASE = os.getenv("PROC_VIZ_TEST_DATABASE", "DummyDB")


@pytest.fixture(scope="module")
def accessor(sqlserver_driver):
    return DatabaseAccessor(sqlserver_driver)


def names(objects):
    return {obj.name for obj in objects}


def test_databases_and_schemas(accessor):
    assert DATABASE in names(accessor.get_databases())
    assert {"dbo", "FunctionSchema"}.issubset(names(accessor.get_schemas(DATABASE)))


def test_objects(accessor):
    assert {"Employees"}.issubset(names(accessor.get_tables(DATABASE, "dbo")))
    assert {"sp_GetDepartmentStats", "sp_GetEmployeeInfo", "sp_GetManagerInfo"}.issubset(
        names(accessor.get_procedures(DATABASE, "dbo"))
    )
    assert {"fn_GetDepartmentAverage", "fn_GetEmployeeSalary", "fn_GetManagerBonus"}.issubset(
        names(accessor.get_functions(DATABASE, "FunctionSchema"))
    )


def test_source_and_parameters(accessor):
    source = accessor.get_procedure_source(DATABASE, "dbo", "sp_GetEmployeeInfo")
    assert source and "EXEC sp_GetManagerInfo" in source
    assert accessor.get_function_source(
        DATABASE, "FunctionSchema", "fn_GetDepartmentAverage"
    )
    params = accessor.get_procedure_parameters(DATABASE, "dbo", "sp_GetEmployeeInfo")
    assert [(param.name, param.data_type, param.direction) for param in params] == [
        ("@EmployeeID", "int", "IN")
    ]
    function_params = accessor.get_function_parameters(
        DATABASE, "FunctionSchema", "fn_GetDepartmentAverage"
    )
    assert any(param.name == "@Department" and param.direction == "IN" for param in function_params)


def test_dependencies_and_table_search(accessor):
    called = accessor.get_called_procedures(DATABASE, "dbo", "sp_GetEmployeeInfo")
    assert any(item["name"] == "sp_GetManagerInfo" for item in called)

    callers = accessor.get_calling_procedures(DATABASE, "dbo", "sp_GetManagerInfo")
    assert any(item["name"] == "sp_GetEmployeeInfo" for item in callers)

    table_users = accessor.get_objects_by_table(DATABASE, "Employees")
    assert {"sp_GetEmployeeInfo", "sp_GetDepartmentStats"}.issubset(
        {item["name"] for item in table_users}
    )
