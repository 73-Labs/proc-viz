"""Fixtures for the opt-in SQL Server integration suite."""

import os
import re
from pathlib import Path

import pytest

pymssql = pytest.importorskip("pymssql")


def _setting(name: str, default: str) -> str:
    return os.getenv(name, default)


def _quote_database(name: str) -> str:
    if not re.fullmatch(r"(?:DummyDB|proc_viz_test[A-Za-z0-9_]*)", name):
        raise ValueError(
            "PROC_VIZ_TEST_DATABASE must be DummyDB or start with proc_viz_test"
        )
    return f"[{name}]"


def _split_seed_script(script: str) -> list[str]:
    """Split CREATE statements into SQL Server batches."""
    parts = re.split(r"(?=^CREATE\s+(?:TABLE|PROCEDURE|FUNCTION)\b)", script, flags=re.I | re.M)
    return [part.strip() for part in parts if part.strip() and re.search(r"\bCREATE\s+", part, re.I)]


@pytest.fixture(scope="session")
def sqlserver_connection():
    if os.getenv("PROC_VIZ_INTEGRATION") != "1":
        pytest.skip("set PROC_VIZ_INTEGRATION=1 to run SQL Server integration tests")

    host = _setting("PROC_VIZ_TEST_HOST", "127.0.0.1")
    port = int(_setting("PROC_VIZ_TEST_PORT", "1433"))
    user = _setting("PROC_VIZ_TEST_USER", "sa")
    password = _setting("PROC_VIZ_TEST_PASSWORD", "YourStrongPassword123!")
    database = _setting("PROC_VIZ_TEST_DATABASE", "DummyDB")
    quoted_database = _quote_database(database)

    try:
        master = pymssql.connect(
            server=host, port=port, user=user, password=password,
            database="master", login_timeout=5, timeout=30, autocommit=True,
        )
    except pymssql.Error as exc:
        pytest.skip(f"SQL Server unavailable at {host}:{port}: {exc}")

    try:
        cursor = master.cursor()
        cursor.execute(
            f"IF DB_ID(N'{database}') IS NULL CREATE DATABASE {quoted_database}"
        )
        cursor.close()
    finally:
        master.close()

    try:
        connection = pymssql.connect(
            server=host, port=port, user=user, password=password,
            database=database, login_timeout=5, timeout=30, autocommit=True,
        )
    except pymssql.Error as exc:
        pytest.skip(f"cannot open integration database {database}: {exc}")

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT 1 FROM sys.tables WHERE schema_id = SCHEMA_ID(N'dbo') "
            "AND name = N'Employees'"
        )
        initialized = cursor.fetchone() is not None
        if not initialized:
            cursor.execute(
                "IF SCHEMA_ID(N'FunctionSchema') IS NULL "
                "EXEC(N'CREATE SCHEMA [FunctionSchema]')"
            )
            script = (Path(__file__).parents[2] / "init-db.sql").read_text()
            for batch in _split_seed_script(script):
                cursor.execute(batch)
        cursor.close()
        yield connection
    finally:
        connection.close()


@pytest.fixture(scope="session")
def sqlserver_driver(sqlserver_connection):
    from app.drivers.sqlserver_driver import SQLServerDriver

    return SQLServerDriver(sqlserver_connection)
