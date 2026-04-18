# Implementation progress (testing → security)

Single source of truth for the **Track 1 then Track 2** program. Update this file as steps complete.

**Last updated:** 2026-04-10  
**Baseline:** use `git rev-parse HEAD` on `master` when you record a testing snapshot (do not rely on a stale SHA printed in this file).

---

## HUMAN INPUT REQUIRED (read first)

> **These items cannot be closed by automation or by an AI “decision.”**  
> A **person** must execute the check, record evidence (date + initials or link), and update the checklist or this table.  
> CI green **does not** replace: exploratory UI passes, role judgment, WebSocket behavior in a real browser, or release sign-off.

| Gate | What a human must do |
|------|----------------------|
| Track 1.3–1.6 | Run [PIPELINE-MANUAL-TEST-CHECKLIST.md](./PIPELINE-MANUAL-TEST-CHECKLIST.md) (two jobs), HR vs admin smoke, WS with `WS_ALLOW_LEGACY_BROWSER_TOKEN=false`. |
| Track 2.8 | [RELEASE_CHECKLIST.md](./RELEASE_CHECKLIST.md) — tag, rollback note, stakeholder sign-off. |
| Audit noise | If `pip-audit` / `npm audit` is too strict or too loose, **humans** adjust policy (severity filters, allowlists) — tooling only reports. |

**Legend (verification type):**

| Tag | Meaning |
|-----|---------|
| **A** | **Automated** — CI or `scripts/verify-*.sh` / `verify-*.ps1` can prove it. |
| **H** | **Human required** — no substitute for a person following the linked doc. |

---

## Overall completion (roll-up)

| Slice | Progress | Verification | Notes |
|-------|----------|--------------|--------|
| **Track 1** — Deep testing | **4 / 8 steps (50%)** | Mixed **A** + **H** | Automated slices done; **H** steps 1.3–1.6 **open** until a human checks boxes. |
| **Track 2** — Security / hardening | **7 / 8 items (88%)** | Mostly **A** | **2.1–2.7** done for **A** scope; **2.8** remains **H** (release sign-off). |
| **Program (indicative, automated only)** | **~65%** | **A** | `0.4 × (4/8) + 0.6 × (7/8)` ≈ **65%** for **A**-verifiable rows only — **do not** treat as product-ready while **H** rows are open. |

Re-open **2.1** if new job-scoped routes ship without matching isolation tests.

---

## Track 1 — Deep testing (complete before Track 2)

| Step | Status | V | Notes |
|------|--------|---|-------|
| 1.1 Baseline clone + env templates | Done | A | `backend/.env.example`, `frontend/.env.example` |
| 1.2 `scripts/verify-all.ps1` / `verify-all.sh` | Done (PS1) | A | `verify-all.ps1` green on Windows. **H:** run `verify-all.sh` or trust CI on Linux if you did not. |
| 1.3 Manual pipeline checklist (job A) | Pending | **H** | [PIPELINE-MANUAL-TEST-CHECKLIST.md](./PIPELINE-MANUAL-TEST-CHECKLIST.md) |
| 1.4 Manual pipeline checklist (job B) | Pending | **H** | Second clean job |
| 1.5 Role matrix (HR vs admin smoke) | Pending | **H** | Short table in Notes or issue link |
| 1.6 WebSocket smoke (`WS_ALLOW_LEGACY_BROWSER_TOKEN=false`) | Pending | **H** | Real browser; document result |
| 1.7 Playwright full-stack (`PLAYWRIGHT_FULL_STACK=1`) | Done (dev) | A | `npm run build` then `npm run test:e2e:full` |
| 1.8 CHANGELOG testing pass note | Done | A | `[Unreleased]` entries for this wave |

### Automated coverage added (Track 1)

- `frontend/e2e/app.authenticated.spec.ts` — Approvals + Audit pages (stubbed API, full-stack project).
- `frontend/e2e/smoke.spec.ts` — middleware redirect for unauthenticated **`/jobs`** (`next` query).
- `backend/tests/api/test_api.py` — CSRF on **PATCH**; job resume MIME + parse-timeout (**504**).
- `backend/tests/api/test_job_access_isolation.py` — non-owner `hr_manager` cannot read or mutate another user’s job / workflow / candidates (`403`).
- `backend/tests/integration/test_orchestration_coalesce.py` — concurrent `start_orchestration` coalesces a follow-up run.

---

## Handoff gate (all must be true before Track 2)

- [ ] **H** Track 1 table: no open **blocker** without owner/issue (human triage).
- [ ] **A** CI green on the baseline SHA (or documented waiver).

*Engineering note:* Track **2.1** tests run in CI regardless; full **Track 2** product hardening should still wait until **H** Track 1 gates are satisfied or explicitly waived in writing.

---

## Track 2 — Security / hardening (after gate)

| Order | Item | Status | V | Notes |
|-------|------|--------|---|-------|
| 2.1 | Job-level auth policy + negative tests | **Done** | A | `test_job_access_isolation.py` — workflow/job routes `403` for non-owner `hr_manager`. |
| 2.2 | Orchestration idempotency / durability | **Done (MVP)** | A | Async `start_orchestration` + per-job lock + coalesced follow-up; `test_orchestration_coalesce.py`. **H:** multi-worker / prod SRE review if scaled. |
| 2.3 | Restrict workflow `PATCH` state surface | **Done** | A | Admin-only, production disabled, allowlist; `test_manual_patch_*` + `test_manual_patch_records_state_patch_audit`. **H:** periodic review of allowlist keys. |
| 2.4 | CI blocks dependency issues | **Done (as shipped)** | A | Workflow job **`backend-security-audit`** runs **`pip-audit`** and **fails on any reported vuln** (see `.github/workflows/ci.yml`). **H:** pip-audit JSON has no CVSS tier — if you need **high/critical-only**, a human must add filtering or ignore rules. |
| 2.5 | CSRF for cookie-auth mutations | **Done** | A+H | Axios sends `x-csrf-token` on mutations; API tests for **POST** logout + **PATCH** workflow (`test_cookie_auth_*`). **H:** full UI regression. |
| 2.6 | Upload limits / parser hardening | **Done** | A+H | Oversize + **MIME** (`application/pdf` only on job upload) + **parse timeout** (`resume_parse_timeout_seconds`, **504**); tests in `test_api.py`. **H:** abuse cases in staging. |
| 2.7 | Frontend route guards | **Done** | A+H | `middleware.ts` redirects unauthenticated users; `useAuth` blocks protected UI until session resolves; Playwright: direct `/jobs` → `/?next=`. **H:** spot-check other deep links. |
| 2.8 | Release checklist sign-off | Not started | **H** | [RELEASE_CHECKLIST.md](./RELEASE_CHECKLIST.md) |

See [ENGINEERING_HARDENING_CHECKLIST.md](./ENGINEERING_HARDENING_CHECKLIST.md) for acceptance criteria.

---

## Completion log (recent)

| Date | Change |
|------|--------|
| 2026-04-18 | Track 1: Playwright Approvals/Audit; temp SQLite + `py -3.11` for E2E; `IMPLEMENTATION_PROGRESS` added. |
| 2026-04-18 | Track 2.1: workflow GET + approve/reject + candidates `403` tests; `verify-frontend.ps1` uses `py -3.11`; `verify-all.ps1` green. |
| 2026-04-18 | Track 2.1: workflow **PATCH state**, **interview-invite**, **interview-complete**, **responses**, **generate-offer** `403` tests; roll-up completion table + completion log. |
| 2026-04-18 | Bugfix: `POST .../responses` preserves **403** (no longer wrapped as **400**). |
| 2026-04-18 | Track **2.2 (MVP):** async `start_orchestration` + per-job lock + coalesced re-run; conftest uses `AsyncMock`; integration coalesce test. |
| 2026-04-18 | **HUMAN / A split:** banner + `V` column; Track **2.3** done (audit test); **2.4** documented as CI `pip-audit` blocking (**H** for severity-only tuning). |
| 2026-04-10 | Track **2.5–2.7:** CSRF PATCH test; job PDF MIME + parse timeout; `useAuth` protected shell gate; Playwright route-guard smoke. |
