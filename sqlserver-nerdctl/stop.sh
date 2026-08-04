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

echo "Stopping SQL Server container with $RUNTIME..."
$RUNTIME compose down

echo "SQL Server stopped"
