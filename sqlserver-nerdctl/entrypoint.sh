#!/bin/bash
set -e
/opt/mssql/bin/sqlservr &
SQL_PID=$!
echo "Waiting for SQL Server..."
for i in {1..60}; do
  if /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT 1" > /dev/null 2>&1; then
    echo "Ready!"
    break
  fi
  sleep 2
done
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i /scripts/init.sql
wait $SQL_PID
