# Implementation progress (testing → security)

Single source of truth for the **Track 1 then Track 2** program. Update this file as steps complete.

**Last updated:** 2026-04-18  
**Baseline SHA:** run `git rev-parse HEAD` on `master` after merging the latest Track 1 work.

---

## Track 1 — Deep testing (complete before Track 2)

| Step | Status | Notes |
|------|--------|-------|
| 1.1 Baseline clone + env templates | Done | `backend/.env.example`, `frontend/.env.example` |
| 1.2 `scripts/verify-all.ps1` / `verify-all.sh` | Pending | Run locally; attach log or CI link |
| 1.3 Manual pipeline checklist (job A) | Pending | [PIPELINE-MANUAL-TEST-CHECKLIST.md](./PIPELINE-MANUAL-TEST-CHECKLIST.md) |
| 1.4 Manual pipeline checklist (job B) | Pending | Second clean job |
| 1.5 Role matrix (HR vs admin smoke) | Pending | Short table in Notes column or issue link |
| 1.6 WebSocket smoke (`WS_ALLOW_LEGACY_BROWSER_TOKEN=false`) | Pending | Document result |
| 1.7 Playwright full-stack (`PLAYWRIGHT_FULL_STACK=1`) | Done (dev) | `npm run build` then `npm run test:e2e:full`: smoke + setup + authed (incl. Approvals + Audit). Uses **`py -3.11`** on Windows; temp-dir SQLite by default (see `playwright.config.ts`). |
| 1.8 CHANGELOG testing pass note | Done | `[Unreleased]` entries for this wave |

### Automated coverage added (Track 1)

- `frontend/e2e/app.authenticated.spec.ts` — Approvals + Audit pages (stubbed API, full-stack project).
- `backend/tests/api/test_job_access_isolation.py` — non-owner `hr_manager` cannot read another user’s job (`403`).

---

## Handoff gate (all must be true before Track 2)

- [ ] Track 1 table: no open **blocker** without owner/issue.
- [ ] CI green on the baseline SHA (or documented waiver).

---

## Track 2 — Security / hardening (after gate)

| Order | Item | Status |
|-------|------|--------|
| 2.1 | Job-level auth policy + negative tests (extend as needed) | In progress | `GET /api/jobs/{id}` covered: non-owner `hr_manager` → 403; admin → 200 (`test_job_access_isolation.py`). Extend to workflow/candidates routes next. |
| 2.2 | Orchestration idempotency / durability | Not started |
| 2.3 | Restrict workflow `PATCH` state surface | Not started |
| 2.4 | CI blocks high/critical dependency issues | Not started |
| 2.5 | CSRF for cookie-auth mutations | Not started |
| 2.6 | Upload limits / parser hardening | Not started |
| 2.7 | Frontend route guards | Not started |
| 2.8 | Release checklist sign-off | Not started |

See [ENGINEERING_HARDENING_CHECKLIST.md](./ENGINEERING_HARDENING_CHECKLIST.md) for acceptance criteria.
