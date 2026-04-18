# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added

- **Progress / verification clarity:** [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) now leads with **HUMAN INPUT REQUIRED**, uses **A** vs **H** (automated vs human) on rows, and explains that **pip-audit** blocking does not replace human severity policy. [PIPELINE-MANUAL-TEST-CHECKLIST.md](docs/PIPELINE-MANUAL-TEST-CHECKLIST.md) warns not to trust pre-checked boxes without a real pass.
- **API test:** `test_manual_patch_records_state_patch_audit` — admin `PATCH .../state` records **`state_patch`** in workflow `audit_log`.
- **Orchestration scheduling (Track 2.2 MVP):** `start_orchestration` is **async**, uses a **per-job `asyncio.Lock`**, and **coalesces** a single follow-up run when a trigger arrives while `_run_orchestration_task` is still active (so `resume_workflow` is not lost mid-run). Integration test: `backend/tests/integration/test_orchestration_coalesce.py`.
- **Track 1 (testing) progress tracker:** [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) — checklist for deep testing then security hardening.
- **Playwright (full-stack):** authenticated coverage for **Approvals** (JD gate → approve → empty state) and **Audit** (timeline) in `frontend/e2e/app.authenticated.spec.ts`.
- **API regression:** `backend/tests/api/test_job_access_isolation.py` — non-owner `hr_manager` receives `403` on another user’s job, **all workflow GET/POST/PATCH routes** covered in-file (incl. patch state, interview flows, responses, generate-offer), and **candidates**; admin can read any job.
- **Windows scripts:** `scripts/verify-frontend.ps1` installs backend E2E deps with **`py -3.11`** (same as `verify-backend.ps1`), not unversioned `python`.
- **Release safety toolkit:** added [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) and CI non-blocking security audit jobs (backend-security-audit, frontend-security-audit) plus README release-process guidance.
- **WebSocket auth hardening (Phase C):** **`GET /api/auth/ws-ticket`** mints a short-lived JWT (`aud=prohr-ws`, bound to `job_id`) for **`/ws/{job_id}?token=`**. Frontend fetches a ticket before connect/reconnect. Settings: **`ws_ticket_expire_minutes`**, **`ws_allow_legacy_browser_token`** (env: `WS_TICKET_EXPIRE_MINUTES`, `WS_ALLOW_LEGACY_BROWSER_TOKEN`).
- **`.python-version`** (3.11) and **`backend/mypy-full.ini`** â€” align local interpreters with CI/Docker; optional full-app **`mypy`** config for the non-blocking CI report job.

### Changed

- **Orchestration:** `start_orchestration` is now **async** (`await` from `start_workflow` / `resume_workflow`). Test suite mocks it with **`AsyncMock`** (`conftest.py`).
- **API correctness:** `POST /api/workflow/{job_id}/responses` now re-raises **`HTTPException`** (e.g. **403** job access denied) instead of wrapping it as **400**.
- **Playwright full-stack:** backend webServer uses **`py -3.11`** on Windows (instead of `python`) so local runs match CI Python 3.11; set **`PLAYWRIGHT_BACKEND_PYTHON`** to override the interpreter used for uvicorn. Default **`DATABASE_URL`** for the spawned API uses the OS temp dir (override with **`E2E_DATABASE_URL`**) so SQLite under synced folders (e.g. OneDrive) does not hang Alembic during startup.
- **API stability:** HTTP middleware returns **`{"detail": "Internal server error"}`** JSON on unhandled exceptions (still re-raises **`HTTPException`** / **`RequestValidationError`** for normal 4xx/422 behavior).
- **Time handling:** JWT and ORM timestamps use **timezone-aware UTC** (`datetime.now(timezone.utc)`) instead of deprecated **`datetime.utcnow`**.
- **`POST /api/resumes/upload`** is **deprecated** in favor of **`POST /api/jobs/{job_id}/resumes`**. OpenAPI marks the operation as deprecated; responses include `Deprecation`, `Sunset` (2027-04-07 GMT), and a `Link` hint. The endpoint remains available for admin/script use until removal is justified by metrics.

### Removed

- **`chroma_persist_dir`** removed from `app.config.Settings`. RAG uses **FAISS** only (`app/rag/embeddings.py`). If you had `CHROMA_PERSIST_DIR` in `.env`, it is now ignored (harmless).

