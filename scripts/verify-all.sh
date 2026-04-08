#!/usr/bin/env bash
# Full project: verify-backend + verify-frontend (same steps as CI when run together).
# Usage: bash scripts/verify-all.sh
# Optional: SECRET_KEY, CI=true, PORT, PLAYWRIGHT_BACKEND_URL
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
bash "${SCRIPT_DIR}/verify-backend.sh"
bash "${SCRIPT_DIR}/verify-frontend.sh"
echo "== All verification steps passed =="
