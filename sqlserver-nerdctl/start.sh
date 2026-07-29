#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting SQL Server container..."
nerdctl compose up -d --build

echo "Waiting for SQL Server to initialize..."
sleep 20

echo "Container status:"
nerdctl compose ps

echo "SQL Server ready at localhost:1433"
echo "Connection: sa / YourStrongPassword123!"
