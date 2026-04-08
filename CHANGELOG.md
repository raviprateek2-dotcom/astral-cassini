# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added

- **Release safety toolkit:** added [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) and CI non-blocking security audit jobs (backend-security-audit, frontend-security-audit) plus README release-process guidance.
- **WebSocket auth hardening (Phase C):** **`GET /api/auth/ws-ticket`** mints a short-lived JWT (`aud=prohr-ws`, bound to `job_id`) for **`/ws/{job_id}?token=`**. Frontend fetches a ticket before connect/reconnect. Settings: **`ws_ticket_expire_minutes`**, **`ws_allow_legacy_browser_token`** (env: `WS_TICKET_EXPIRE_MINUTES`, `WS_ALLOW_LEGACY_BROWSER_TOKEN`).
- **`.python-version`** (3.11) and **`backend/mypy-full.ini`** â€” align local interpreters with CI/Docker; optional full-app **`mypy`** config for the non-blocking CI report job.

### Changed

- **API stability:** HTTP middleware returns **`{"detail": "Internal server error"}`** JSON on unhandled exceptions (still re-raises **`HTTPException`** / **`RequestValidationError`** for normal 4xx/422 behavior).
- **Time handling:** JWT and ORM timestamps use **timezone-aware UTC** (`datetime.now(timezone.utc)`) instead of deprecated **`datetime.utcnow`**.
- **`POST /api/resumes/upload`** is **deprecated** in favor of **`POST /api/jobs/{job_id}/resumes`**. OpenAPI marks the operation as deprecated; responses include `Deprecation`, `Sunset` (2027-04-07 GMT), and a `Link` hint. The endpoint remains available for admin/script use until removal is justified by metrics.

### Removed

- **`chroma_persist_dir`** removed from `app.config.Settings`. RAG uses **FAISS** only (`app/rag/embeddings.py`). If you had `CHROMA_PERSIST_DIR` in `.env`, it is now ignored (harmless).

