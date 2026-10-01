#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
[[ -x .venv/bin/python ]] || { echo "Run ./setup_linux.sh first"; exit 1; }
exec "$PROJECT_DIR/.venv/bin/python" -m app.main
