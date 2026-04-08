#!/usr/bin/env bash
# Frontend: npm ci, lint, Jest, production build, Playwright full-stack E2E.
# Installs backend requirements.txt only (enough for uvicorn in Playwright). Run: bash scripts/verify-frontend.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export SECRET_KEY="${SECRET_KEY:-ci-test-secret-key-must-be-32chars-minimum}"

echo "== Backend deps for E2E (uvicorn) =="
cd "${ROOT}/backend"
python -m pip install -q -r requirements.txt

echo "== Frontend: install =="
cd "${ROOT}/frontend"
npm ci

echo "== Frontend: ESLint =="
npm run lint

echo "== Frontend: Jest =="
npm test -- --ci --passWithNoTests

echo "== Frontend: production build =="
npm run build

echo "== Frontend: Playwright (Chromium) + full-stack E2E =="
npx playwright install --with-deps chromium
export CI="${CI:-}"
npm run test:e2e:full

echo "== Frontend verification passed =="
