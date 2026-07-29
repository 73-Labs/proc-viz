# SQL Server nerdctl Setup

Local SQL Server 2022 development environment using nerdctl (containerd).

## Quick Start

**Start container:**
```bash
./start.sh
```

**Stop container:**
```bash
./stop.sh
```

Container available at `localhost:1433`  
User: `sa`  
Password: `YourStrongPassword123!`

## Files

- `compose.yaml` — Container configuration
- `Dockerfile` — Image build (runs as root for init scripts)
- `init.sql` — Database initialization (creates DummyDB with tables, procedures, functions)
- `entrypoint.sh` — Startup script (waits for SQL Server, runs init.sql)
- `start.sh` — Convenience script to start container
- `stop.sh` — Convenience script to stop container

## Database

**Database:** DummyDB  
**Tables:** Employees  
**Procedures:** sp_GetDepartmentStats, sp_GetEmployeeInfo, sp_GetManagerInfo  
**Functions:** fn_GetDepartmentAverage, fn_GetDepartmentDetails, fn_GetEmployeeSalary, fn_GetManagerBonus

## Commands

**Check status:**
```bash
nerdctl compose ps
```

**View logs:**
```bash
nerdctl compose logs -f
```

**Run SQL query:**
```bash
nerdctl exec sqlserver-nerdctl-sqlserver-1 /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourStrongPassword123!" -C -Q "SELECT * FROM DummyDB.dbo.Employees;"
```

**Interactive shell:**
```bash
nerdctl exec -it sqlserver-nerdctl-sqlserver-1 /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourStrongPassword123!" -C
```

## Rebuild

Delete volume and rebuild from scratch:
```bash
nerdctl compose down -v
nerdctl rmi sqlserver-nerdctl-sqlserver
./start.sh
```

## Aliases (Optional)

Add to `~/.bashrc`:
```bash
alias sqlstart='~/dev/73Labs/proc-viz/sqlserver-nerdctl/start.sh'
alias sqlstop='~/dev/73Labs/proc-viz/sqlserver-nerdctl/stop.sh'
```

Then use:
```bash
sqlstart
sqlstop
```

## Notes

- Data persists in Docker volume `sqlserver-nerdctl_sqlserver-data`
- Volume survives container restarts but not `down -v`
- Init script runs only on first container creation
- Requires nerdctl and buildkit installed
