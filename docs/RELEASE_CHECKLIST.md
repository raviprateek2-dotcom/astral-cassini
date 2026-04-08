# Release Checklist

Use this before tagging or deploying a release.

## 1) CI and quality gates

- [ ] GitHub Actions `backend` job is green (ruff, scoped mypy, pytest).
- [ ] GitHub Actions `frontend` job is green (lint, unit tests, build, Playwright smoke).
- [ ] `mypy-full-report` has been reviewed (informational debt tracker).

## 2) Security and dependency checks

- [ ] Backend dependency audit reviewed (`pip-audit`) and critical issues addressed.
- [ ] Frontend audit reviewed (`npm audit --audit-level=high`) and high/critical issues addressed.
- [ ] New secrets are not committed (`.env`, credentials, tokens).

## 3) WebSocket auth rollout safety

- [ ] `WS_ALLOW_LEGACY_BROWSER_TOKEN=false` in staging and production.
- [ ] Smoke check: login -> open job page -> live updates stream over WebSocket.
- [ ] Rollback path documented (`WS_ALLOW_LEGACY_BROWSER_TOKEN=true` temporarily only if required).

## 4) Data and migration safety

- [ ] Any schema/config changes include backward-compatible behavior or clear migration notes.
- [ ] `backend/.env.example` and docs updated for new runtime config.

## 5) Release metadata and rollback

- [ ] `CHANGELOG.md` updated under `[Unreleased]`.
- [ ] Version/tag selected (semantic tag, e.g. `v0.4.0`).
- [ ] Release notes include user impact + rollback instructions.
- [ ] Last known good image/commit noted for rollback.
