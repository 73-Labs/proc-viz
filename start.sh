#!/bin/bash
set -e

# Start SQL Server in foreground
echo "Starting SQL Server..."
/opt/mssql/bin/sqlservr &
SERVER_PID=$!

# Wait for SQL Server to be ready (max 180 seconds)
echo "Waiting for SQL Server to be ready..."
READY=0
for i in {1..180}; do
  if nc -z localhost 1433 2>/dev/null; then
    echo "SQL Server is ready"
    READY=1
    break
  fi
  echo "Attempt $i/180..."
  sleep 1
done

if [ $READY -eq 0 ]; then
  echo "SQL Server failed to start within 180 seconds"
  kill $SERVER_PID 2>/dev/null || true
  exit 1
fi

# Run initialization script
if [ -f /docker-entrypoint-initdb.d/init-db.sql ]; then
  echo "Running initialization script..."
  if /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -i /docker-entrypoint-initdb.d/init-db.sql; then
    echo "Initialization complete"
  else
    echo "ERROR: Initialization script failed with exit code $?"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
  fi
else
  echo "ERROR: Initialization script not found at /docker-entrypoint-initdb.d/init-db.sql"
  kill $SERVER_PID 2>/dev/null || true
  exit 1
fi

# Keep container running
wait $SERVER_PID
