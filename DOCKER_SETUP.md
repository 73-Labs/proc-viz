# Docker Setup for SQL Server

This project includes SQL Server with automatic database initialization.

## Using docker-compose

```bash
docker-compose up -d
```

Database initializes automatically when container starts.

## Using nerdctl

Build image:
```bash
nerdctl build -t proc-viz-sqlserver .
```

Run container:
```bash
nerdctl run -d \
  --name proc-viz-sqlserver \
  -e ACCEPT_EULA=Y \
  -e MSSQL_SA_PASSWORD='YourStrongPassword123!' \
  -e MSSQL_PID=Express \
  -p 1433:1433 \
  -v proc-viz-sqlserver:/var/opt/mssql \
  proc-viz-sqlserver
```

## How it works

1. `start.sh` — wrapper script that:
   - Starts SQL Server daemon in background
   - Waits up to 60 seconds for server to be ready
   - Runs `init-db.sql` to create database and seed data
   - Keeps container running

2. `Dockerfile` — adds startup script and init SQL to base image

3. `init-db.sql` — creates DummyDB, tables, procedures, functions

## Connection details

- **Server:** localhost:1433
- **User:** sa
- **Password:** YourStrongPassword123!
- **Database:** DummyDB

## Verify setup

```bash
sqlcmd -S localhost -U sa -P 'YourStrongPassword123!' -d DummyDB -Q "SELECT * FROM Employees"
```

## Stop container

```bash
# docker-compose
docker-compose down

# nerdctl
nerdctl stop proc-viz-sqlserver
nerdctl rm proc-viz-sqlserver
```
