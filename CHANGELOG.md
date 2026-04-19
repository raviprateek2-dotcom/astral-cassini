# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added

- **Frontend demo mode:** **`NEXT_PUBLIC_DEMO_MODE`** (`1` / `true`) skips API login and cookie session checks so the login page can open the app without a backend password (middleware + **`useAuth`** honor local demo profile). Documented in README / **`frontend/.env.example`** — insecure; demos only.
- **Vercel (repo root):** root **`vercel.json`** runs **`npm ci` / `npm run build`** with **`--prefix frontend`**; root **`package.json`** lists **`next@16.2.3`** so detection works when the Vercel project root is not set to **`frontend/`** (see README).
- **Deployed demo logins:** `Settings.seed_demo_users` / **`SEED_DEMO_USERS`** plus **`ALLOW_SEED_DEMO_USERS_OUTSIDE_DEV`** (default **false**) so `admin@prohr.ai` / `hr@prohr.ai` can be seeded when **`APP_ENV`** is not `development`/`dev`/`local` — only for private demos; requires **`DEMO_ADMIN_PASSWORD`** and **`DEMO_HR_PASSWORD`** (8+ chars each). See **README** environment table and **Vercel** subsection.
- **GitHub Pages:** `.github/workflows/nextjs.yml` builds a static export from **`frontend/`** (disables middleware for export, sets **`GITHUB_PAGES=true`** in CI). Replaces the old repo-root **`npx --no-install next build`** template that failed on this monorepo.
- **Upload / parser safety:** `Settings.resume_parse_timeout_seconds` (default **45s**); job and deprecated resume uploads run PDF parsing in **`asyncio.to_thread`** with **`asyncio.wait_for`** — timeout returns **504**. Job route **`POST /api/jobs/{job_id}/resumes`** requires **`Content-Type: application/pdf`** (no `application/octet-stream`). Tests: MIME rejection, octet-stream rejection, parse-timeout path.
- **Route guard UX:** `AuthProvider` shows a full-screen loading state on protected routes only while **`/api/auth/me`** is in flight (avoids blank deadlock if `/me` fails; middleware still handles missing cookie).
- **E2E:** smoke test asserts unauthenticated navigation to **`/jobs`** is redirected to **`/?next=...`** (Next middleware).
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

- **Frontend:** **`package.json` `overrides`** pin transitive **`follow-redirects`** to **1.16.0** (GHSA-r4q5-vmmm-2653; npm had no **1.15.12** release). **`package-lock.json`** updated so **`npm audit`** is clean. **`npm-audit-gate`** also ignores **`follow-redirects`** when **`node_modules`** is **>= 1.16.0** (covers moderate-only JSON + older gate logic).
- **CI:** Ruff ignores **`E402`** in **`tests/conftest.py`** (imports after orchestration patch). **`npm-audit-gate`** only treats **high/critical** findings as failures, matching **`npm audit --audit-level=high`**. Dependency bumps for **`pip-audit`:** `langchain-openai` **1.1.14**, `python-multipart` **0.0.26**, `pytest` **9.0.3**, `pytest-asyncio` **1.3.0**.
- **Job resume upload:** **`Content-Type`** must be **`application/pdf`** (removed `application/octet-stream` for this route so MIME cannot bypass PDF checks).
- **Orchestration:** `start_orchestration` is now **async** (`await` from `start_workflow` / `resume_workflow`). Test suite mocks it with **`AsyncMock`** (`conftest.py`).
- **API correctness:** `POST /api/workflow/{job_id}/responses` now re-raises **`HTTPException`** (e.g. **403** job access denied) instead of wrapping it as **400**.
- **Playwright full-stack:** backend webServer uses **`py -3.11`** on Windows (instead of `python`) so local runs match CI Python 3.11; set **`PLAYWRIGHT_BACKEND_PYTHON`** to override the interpreter used for uvicorn. Default **`DATABASE_URL`** for the spawned API uses the OS temp dir (override with **`E2E_DATABASE_URL`**) so SQLite under synced folders (e.g. OneDrive) does not hang Alembic during startup.
- **API stability:** HTTP middleware returns **`{"detail": "Internal server error"}`** JSON on unhandled exceptions (still re-raises **`HTTPException`** / **`RequestValidationError`** for normal 4xx/422 behavior).
- **Time handling:** JWT and ORM timestamps use **timezone-aware UTC** (`datetime.now(timezone.utc)`) instead of deprecated **`datetime.utcnow`**.
- **`POST /api/resumes/upload`** is **deprecated** in favor of **`POST /api/jobs/{job_id}/resumes`**. OpenAPI marks the operation as deprecated; responses include `Deprecation`, `Sunset` (2027-04-07 GMT), and a `Link` hint. The endpoint remains available for admin/script use until removal is justified by metrics.

### Removed

- **GitHub Pages repo-root template** (old `.github/workflows/nextjs.yml` that ran **`npx --no-install next build`** at repository root): incompatible with **`next`** living under **`frontend/`**. Full product deploy still uses **Vercel** (Root Directory **`frontend`**) or **Docker Compose**; optional static **Pages** build is a separate, `frontend/`-scoped workflow.
- **`chroma_persist_dir`** removed from `app.config.Settings`. RAG uses **FAISS** only (`app/rag/embeddings.py`). If you had `CHROMA_PERSIST_DIR` in `.env`, it is now ignored (harmless).

