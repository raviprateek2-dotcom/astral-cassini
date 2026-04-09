#!/usr/bin/env bash
# Backend: install, Ruff, Mypy (core), Pytest. Run from repo root: bash scripts/verify-backend.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export SECRET_KEY="${SECRET_KEY:-ci-test-secret-key-must-be-32chars-minimum}"

if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  PYTHON_BIN="python"
fi

PY_VER="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "$PY_VER" != "3.11" ]; then
  echo "Python 3.11 is required for backend verification. Found: $PY_VER"
  exit 1
fi

echo "== Backend: install =="
cd "${ROOT}/backend"
$PYTHON_BIN -m pip install -q -r requirements.txt
$PYTHON_BIN -m pip install -q -r requirements-tools.txt

echo "== Backend: Ruff =="
$PYTHON_BIN -m ruff check app tests

echo "== Backend: Mypy (core) =="
$PYTHON_BIN -m mypy

echo "== Backend: Alembic upgrade head =="
$PYTHON_BIN -m alembic -c alembic.ini upgrade head

echo "== Backend: Pytest =="
$PYTHON_BIN -m pytest tests -q --tb=short

echo "== Backend verification passed =="
