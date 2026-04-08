#!/usr/bin/env bash
# Backend: install, Ruff, Mypy (core), Pytest. Run from repo root: bash scripts/verify-backend.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export SECRET_KEY="${SECRET_KEY:-ci-test-secret-key-must-be-32chars-minimum}"

echo "== Backend: install =="
cd "${ROOT}/backend"
python -m pip install -q -r requirements.txt
python -m pip install -q -r requirements-tools.txt

echo "== Backend: Ruff =="
python -m ruff check app tests

echo "== Backend: Mypy (core) =="
python -m mypy

echo "== Backend: Pytest =="
python -m pytest tests -q --tb=short

echo "== Backend verification passed =="
