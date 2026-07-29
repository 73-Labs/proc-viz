# SQL Server Setup

Local SQL Server development environment using nerdctl.

## Location

See `sqlserver-nerdctl/README.md` for full documentation.

## Quick Start

```bash
cd sqlserver-nerdctl
./start.sh
```

## Stop

```bash
cd sqlserver-nerdctl
./stop.sh
```

## Connection

- Host: `localhost:1433`
- User: `sa`
- Password: `YourStrongPassword123!`
- Database: `DummyDB`

## Requirements

- nerdctl
- buildkit (installed automatically by `start.sh`)
