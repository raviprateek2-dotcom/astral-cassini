# Implementation progress (testing → security)

Single source of truth for the **Track 1 then Track 2** program. Update this file as steps complete.

**Last updated:** 2026-04-18  
**Baseline:** use `git rev-parse HEAD` on `master` when you record a testing snapshot (do not rely on a stale SHA printed in this file).

---

## Overall completion (roll-up)

| Slice | Progress | Notes |
|-------|----------|--------|
| **Track 1** — Deep testing | **4 / 8 steps (50%)** | Automated paths done; **manual + WS** (1.3–1.6) still drive release confidence. |
| **Track 2** — Security / hardening | **1 / 8 items (12.5%)** | **2.1 Done** — job/workflow API isolation tests for current routes; **2.2–2.8** not started. |
| **Program (indicative)** | **~28%** | `0.4 × 50% + 0.6 × 12.5%` ≈ **27.5%** (Track 1 weight 40%, Track 2 weight 60%). *Dashboard only — manual Track 1 gates matter more than this number.* |

Re-open **2.1** if new job-scoped routes ship without matching isolation tests.

---

## Track 1 — Deep testing (complete before Track 2)

| Step | Status | Notes |
|------|--------|-------|
| 1.1 Baseline clone + env templates | Done | `backend/.env.example`, `frontend/.env.example` |
| 1.2 `scripts/verify-all.ps1` / `verify-all.sh` | Done (PS1) | `verify-all.ps1` green on Windows (backend + frontend + Playwright full-stack). Run `verify-all.sh` on Linux/macOS or rely on GitHub Actions for parity. |
| 1.3 Manual pipeline checklist (job A) | Pending | [PIPELINE-MANUAL-TEST-CHECKLIST.md](./PIPELINE-MANUAL-TEST-CHECKLIST.md) |
| 1.4 Manual pipeline checklist (job B) | Pending | Second clean job |
| 1.5 Role matrix (HR vs admin smoke) | Pending | Short table in Notes column or issue link |
| 1.6 WebSocket smoke (`WS_ALLOW_LEGACY_BROWSER_TOKEN=false`) | Pending | Document result |
| 1.7 Playwright full-stack (`PLAYWRIGHT_FULL_STACK=1`) | Done (dev) | `npm run build` then `npm run test:e2e:full`: smoke + setup + authed (incl. Approvals + Audit). Uses **`py -3.11`** on Windows; temp-dir SQLite by default (see `playwright.config.ts`). |
| 1.8 CHANGELOG testing pass note | Done | `[Unreleased]` entries for this wave |

### Automated coverage added (Track 1)

- `frontend/e2e/app.authenticated.spec.ts` — Approvals + Audit pages (stubbed API, full-stack project).
- `backend/tests/api/test_job_access_isolation.py` — non-owner `hr_manager` cannot read or mutate another user’s job / workflow / candidates (`403`).

---

## Handoff gate (all must be true before Track 2)

- [ ] Track 1 table: no open **blocker** without owner/issue.
- [ ] CI green on the baseline SHA (or documented waiver).

*Engineering note:* Track **2.1** tests run in CI regardless; full **Track 2** product hardening (2.2+) should still wait until manual Track 1 gates are satisfied or explicitly waived.

---

## Track 2 — Security / hardening (after gate)

| Order | Item | Status |
|-------|------|--------|
| 2.1 | Job-level auth policy + negative tests | **Done** | `test_job_access_isolation.py`: `GET /api/jobs/{id}`; admin read-all; workflow **GET** (status, audit, interviews, recommendations); **approve / reject / patch state / interview-invite / interview-complete / responses / generate-offer**; **GET candidates** — all **403** for non-owner `hr_manager`. |
| 2.2 | Orchestration idempotency / durability | Not started | |
| 2.3 | Restrict workflow `PATCH` state surface | Not started | Allowlist + admin-only already in code; verify audit + tests vs checklist. |
| 2.4 | CI blocks high/critical dependency issues | Not started | |
| 2.5 | CSRF for cookie-auth mutations | Not started | |
| 2.6 | Upload limits / parser hardening | Not started | |
| 2.7 | Frontend route guards | Not started | |
| 2.8 | Release checklist sign-off | Not started | |

See [ENGINEERING_HARDENING_CHECKLIST.md](./ENGINEERING_HARDENING_CHECKLIST.md) for acceptance criteria.

---

## Completion log (recent)

| Date | Change |
|------|--------|
| 2026-04-18 | Track 1: Playwright Approvals/Audit; temp SQLite + `py -3.11` for E2E; `IMPLEMENTATION_PROGRESS` added. |
| 2026-04-18 | Track 2.1: workflow GET + approve/reject + candidates `403` tests; `verify-frontend.ps1` uses `py -3.11`; `verify-all.ps1` green. |
| 2026-04-18 | Track 2.1: workflow **PATCH state**, **interview-invite**, **interview-complete**, **responses**, **generate-offer** `403` tests; roll-up completion table + completion log. |
| 2026-04-18 | Bugfix: `POST .../responses` preserves **403** (no longer wrapped as **400**). |
