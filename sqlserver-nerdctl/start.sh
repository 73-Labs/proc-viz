#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detect container runtime (prefer docker)
if command -v docker &> /dev/null; then
  RUNTIME="docker"
elif command -v nerdctl &> /dev/null; then
  RUNTIME="nerdctl"
else
  echo "ERROR: Neither docker nor nerdctl found. Install one and try again."
  exit 1
fi

echo "Starting SQL Server container with $RUNTIME..."
$RUNTIME compose up -d --build

echo "Waiting for SQL Server to initialize..."
sleep 20

echo "Container status:"
$RUNTIME compose ps

echo "SQL Server ready at localhost:1433"
echo "Connection: sa / YourStrongPassword123!"
