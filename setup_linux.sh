#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
command -v python3 >/dev/null || { echo "Python 3 is required"; exit 1; }
python3 -m venv .venv
"$PROJECT_DIR/.venv/bin/python" -m pip install --upgrade pip
"$PROJECT_DIR/.venv/bin/python" -m pip install -r requirements.txt
mkdir -p data/cache logs
[[ -f .env ]] || cp .env.example .env
"$PROJECT_DIR/.venv/bin/python" -m app.cli init-db
echo "Setup complete. Edit .env, then run ./run_linux.sh"
