#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV="${VENV:-$ROOT/.venv}"
if [ ! -d "$VENV" ]; then
  python -m venv "$VENV"
fi

# shellcheck source=/dev/null
. "$VENV/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt
mkdocs build --strict
