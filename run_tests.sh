#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pytest_bin="${project_dir}/venv/bin/pytest"

if [[ ! -x "${pytest_bin}" ]]; then
    pytest_bin="pytest"
fi

export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"

echo "Running proc-viz tests..."
"${pytest_bin}" -q "$@"
