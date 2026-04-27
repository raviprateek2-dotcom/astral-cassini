#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"

echo "== PRO HR local bootstrap (macOS/Linux) =="
echo "Root: $ROOT"

if [[ ! -f "$BACKEND_DIR/.env" ]]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  echo "Created backend/.env from .env.example"
else
  echo "backend/.env already exists"
fi

if [[ ! -f "$FRONTEND_DIR/.env.local" ]]; then
  cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env.local"
  echo "Created frontend/.env.local from .env.example"
else
  echo "frontend/.env.local already exists"
fi

echo "== Backend dependencies =="
cd "$BACKEND_DIR"
if command -v python3.11 >/dev/null 2>&1; then
  python3.11 -m pip install -r requirements.txt
else
  python3 -m pip install -r requirements.txt
fi

echo "== Frontend dependencies =="
cd "$FRONTEND_DIR"
npm ci

echo
echo "Bootstrap complete."
echo "Run backend:  cd backend;  python3.11 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
echo "Run frontend: cd frontend; npm run dev -- -p 3000"
echo "Open: http://localhost:3000"
