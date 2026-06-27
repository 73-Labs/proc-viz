def check_pymssql_available():
    """Check if pymssql is available."""
    try:
        import pymssql  # noqa: F401
        return True
    except ImportError:
        return False
